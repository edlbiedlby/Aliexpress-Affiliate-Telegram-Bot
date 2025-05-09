#!/usr/bin/env python

# coding: utf-8

from flask import Flask, request
import telebot
from telebot import types
from aliexpress_api import AliexpressApi, models
import re
import json
import requests
from urllib.parse import urlparse, parse_qs, urlencode

TOKEN = '7925683283:AAG2QUVayxeCE_gS70OdOm79dOFwWDqPvlU'
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

aliexpress = AliexpressApi('506592', 'ggkzfJ7lilLc7OXs6khWfT4qTZdZuJbh', models.Language.EN, models.Currency.EUR, 'default')




# -*- coding: utf-8 -*-
import logging
import os
import re
import json
import asyncio
import time
from datetime import datetime, timedelta
import aiohttp  
from dotenv import load_dotenv
from urllib.parse import urlparse, urlunparse, urlencode
import iop
from concurrent.futures import ThreadPoolExecutor
from aliexpress_utils import get_product_details_by_id 

# Telegram imports
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, JobQueue 
from telegram.constants import ParseMode, ChatAction


# --- Environment Variable Loading ---
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ALIEXPRESS_APP_KEY = os.getenv('ALIEXPRESS_APP_KEY')
ALIEXPRESS_APP_SECRET = os.getenv('ALIEXPRESS_APP_SECRET')
TARGET_CURRENCY = os.getenv('TARGET_CURRENCY', 'USD')
TARGET_LANGUAGE = os.getenv('TARGET_LANGUAGE', 'en')
QUERY_COUNTRY = os.getenv('QUERY_COUNTRY', 'US')
ALIEXPRESS_TRACKING_ID = os.getenv('ALIEXPRESS_TRACKING_ID', 'default')

# --- Basic Logging Setup ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

# --- AliExpress API Configuration ---
ALIEXPRESS_API_URL = 'https://api-sg.aliexpress.com/sync'
QUERY_FIELDS = 'product_main_image_url,target_sale_price,product_title,target_sale_price_currency'

# Thread pool for blocking API calls
executor = ThreadPoolExecutor(max_workers=10)

# --- Cache Configuration ---
CACHE_EXPIRY_DAYS = 1
CACHE_EXPIRY_SECONDS = CACHE_EXPIRY_DAYS * 24 * 60 * 60

# --- Environment Variable Validation ---
if not all([TELEGRAM_BOT_TOKEN, ALIEXPRESS_APP_KEY, ALIEXPRESS_APP_SECRET, ALIEXPRESS_TRACKING_ID]):
    logger.error("Error: Missing required environment variables. Check TELEGRAM_BOT_TOKEN, ALIEXPRESS_*, TRACKING_ID.")
    exit()

# --- Initialize AliExpress API Client ---
try:
    aliexpress_client = iop.IopClient(ALIEXPRESS_API_URL, ALIEXPRESS_APP_KEY, ALIEXPRESS_APP_SECRET)
    logger.info("AliExpress API client initialized.")
except Exception as e:
    logger.exception(f"Error initializing AliExpress API client: {e}")
    logger.error("Check API URL and credentials.")
    exit()

# --- Regex Optimization: Precompile patterns ---

URL_REGEX = re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+|\b(?:s\.click\.|a\.)?aliexpress\.(?:com|ru|es|fr|pt|it|pl|nl|co\.kr|co\.jp|com\.br|com\.tr|com\.vn|us|id|th|ar)(?:\.[\w-]+)?/[^\s<>"]*', re.IGNORECASE)
PRODUCT_ID_REGEX = re.compile(r'/item/(\d+)\.html')
STANDARD_ALIEXPRESS_DOMAIN_REGEX = re.compile(r'https?://(?!a\.|s\.click\.)([\w-]+\.)?aliexpress\.(com|ru|es|fr|pt|it|pl|nl|co\.kr|co\.jp|com\.br|com\.tr|com\.vn|us|id\.aliexpress\.com|th\.aliexpress\.com|ar\.aliexpress\.com)(\.([\w-]+))?(/.*)?', re.IGNORECASE)
SHORT_LINK_DOMAIN_REGEX = re.compile(r'https?://(?:s\.click\.aliexpress\.com/e/|a\.aliexpress\.com/_)[a-zA-Z0-9_-]+/?', re.IGNORECASE)


# --- Offer Parameter Mapping ---
OFFER_PARAMS = {
    "coin": {"name": "🪙 Coin", "params": {"sourceType": "620", "channel": "coin" , "afSmartRedirect": "y"}},
    "super": {"name": "🔥 Super Deals", "params": {"sourceType": "562", "channel": "sd" , "afSmartRedirect": "y"}},
    "limited": {"name": "⏳ Limited Offers", "params": {"sourceType": "561", "channel": "limitedoffers" , "afSmartRedirect": "y"}},
    "bigsave": {"name": "💰 Big Save", "params": {"sourceType": "680", "channel": "bigSave" , "afSmartRedirect": "y"}},
}
OFFER_ORDER = ["coin", "super", "limited", "bigsave"]

# --- Cache Implementation with Expiry ---
class CacheWithExpiry:
    def __init__(self, expiry_seconds):
        self.cache = {}
        self.expiry_seconds = expiry_seconds
        self._lock = asyncio.Lock()

    async def get(self, key):
        """Get item from cache if it exists and is not expired (async safe)"""
        async with self._lock:
            if key in self.cache:
                item, timestamp = self.cache[key]
                if time.time() - timestamp < self.expiry_seconds:
                    logger.debug(f"Cache hit for key: {key}")
                    return item
                else:
                    logger.debug(f"Cache expired for key: {key}")
                    del self.cache[key]
            logger.debug(f"Cache miss for key: {key}")
            return None

    async def set(self, key, value):
        """Add item to cache with current timestamp (async safe)"""
        async with self._lock:
            self.cache[key] = (value, time.time())
            logger.debug(f"Cached value for key: {key}")

    async def clear_expired(self):
        """Remove all expired items from cache (async safe)"""
        async with self._lock:
            current_time = time.time()
            expired_keys = [k for k, (_, t) in self.cache.items()
                            if current_time - t >= self.expiry_seconds]
            count = 0
            for key in expired_keys:
                try:
                    del self.cache[key]
                    count += 1
                except KeyError:
                    pass
            return count

# Initialize caches
product_cache = CacheWithExpiry(CACHE_EXPIRY_SECONDS)
link_cache = CacheWithExpiry(CACHE_EXPIRY_SECONDS)
resolved_url_cache = CacheWithExpiry(CACHE_EXPIRY_SECONDS)

# --- Helper Functions ---

async def resolve_short_link(short_url: str, session: aiohttp.ClientSession) -> str | None:
    """Follows redirects for a short URL to find the final destination URL."""
    cached_final_url = await resolved_url_cache.get(short_url)
    if cached_final_url:
        logger.info(f"Cache hit for resolved short link: {short_url} -> {cached_final_url}")
        return cached_final_url

    logger.info(f"Resolving short link: {short_url}")
    try:
        async with session.get(short_url, allow_redirects=True, timeout=10) as response:
            if response.status == 200 and response.url:
                final_url = str(response.url)
                logger.info(f"Resolved {short_url} to {final_url}")
                
                if '.aliexpress.us' in final_url:
                    logger.info(f"Detected US domain in {final_url}, converting to .com domain")
                    final_url = final_url.replace('.aliexpress.us', '.aliexpress.com')
                    logger.info(f"Converted URL: {final_url}")
                
                # Replace _randl_shipto=US with _randl_shipto=QUERY_COUNTRY
                if '_randl_shipto=' in final_url:
                    logger.info(f"Found _randl_shipto parameter in URL, replacing with QUERY_COUNTRY value")
                    final_url = re.sub(r'_randl_shipto=[^&]+', f'_randl_shipto={QUERY_COUNTRY}', final_url)
                    logger.info(f"Updated URL with correct country: {final_url}")
                    
                    # Re-fetch the URL with the updated country parameter to get the correct product ID
                    try:
                        logger.info(f"Re-fetching URL with updated country parameter: {final_url}")
                        async with session.get(final_url, allow_redirects=True, timeout=10) as country_response:
                            if country_response.status == 200 and country_response.url:
                                final_url = str(country_response.url)
                                logger.info(f"Re-fetched URL with correct country: {final_url}")
                    except Exception as e:
                        logger.warning(f"Error re-fetching URL with updated country parameter: {e}")
                
                # Extract product ID after domain conversion to ensure we get the correct ID
                product_id = extract_product_id(final_url)
                if STANDARD_ALIEXPRESS_DOMAIN_REGEX.match(final_url) and product_id:
                    # Re-fetch product details with the new product ID if domain was changed
                    logger.info(f"Using product ID {product_id} from converted URL")
                    await resolved_url_cache.set(short_url, final_url)
                    return final_url
                else:
                    logger.warning(f"Resolved URL {final_url} doesn't look like a valid AliExpress product page.")
                    return None
            else:
                logger.error(f"Failed to resolve short link {short_url}. Status: {response.status}")
                return None
    except asyncio.TimeoutError:
        logger.error(f"Timeout resolving short link: {short_url}")
        return None
    except aiohttp.ClientError as e:
        logger.error(f"HTTP ClientError resolving short link {short_url}: {e}")
        return None
    except Exception as e:
        logger.exception(f"Unexpected error resolving short link {short_url}: {e}")
        return None


def extract_product_id(url):
    """Extracts the product ID from an AliExpress URL.
    Handles different domain formats including .us domain.
    """
    # First, ensure we're working with a standardized URL format
    # Convert .us domain to .com domain if needed
    if '.aliexpress.us' in url:
        url = url.replace('.aliexpress.us', '.aliexpress.com')
        logger.info(f"Converted .us URL to .com format for product ID extraction: {url}")
    
    # Try standard product ID extraction
    match = PRODUCT_ID_REGEX.search(url)
    if match:
        return match.group(1)
    
    # If standard extraction fails, try alternative patterns that might be used in different domains
    # Some domains might use different URL structures
    alt_patterns = [
        r'/p/[^/]+/([0-9]+)\.html',  # Alternative pattern sometimes used
        r'product/([0-9]+)'
    ]
    
    for pattern in alt_patterns:
        alt_match = re.search(pattern, url)
        if alt_match:
            product_id = alt_match.group(1)
            logger.info(f"Extracted product ID {product_id} using alternative pattern {pattern}")
            return product_id
    
    logger.warning(f"Could not extract product ID from URL: {url}")
    return None

# Renamed from extract_valid_aliexpress_urls_with_ids
def extract_potential_aliexpress_urls(text):
    """Finds potential AliExpress URLs (standard and short) in text using regex."""
    return URL_REGEX.findall(text)


def clean_aliexpress_url(url: str, product_id: str) -> str | None:
    """Reconstructs a clean base URL (scheme, domain, path) for a given product ID."""
    try:
        parsed_url = urlparse(url)
        # Ensure the path segment is correct for the product ID
        path_segment = f'/item/{product_id}.html'
        base_url = urlunparse((
            parsed_url.scheme or 'https',
            parsed_url.netloc,
            path_segment,
            '', '', ''
        ))
        return base_url
    except ValueError:
        logger.warning(f"Could not parse or reconstruct URL: {url}")
        return None


def build_url_with_offer_params(base_url, params_to_add):
    """Adds offer parameters to a base URL."""
    if not params_to_add:
        return base_url

    try:
        parsed_url = urlparse(base_url)
        
        # Remove country subdomain (like 'ar.', 'es.', etc.) from netloc
        netloc = parsed_url.netloc
        if '.' in netloc and netloc.count('.') > 1:
            # Extract domain parts
            parts = netloc.split('.')
            # Keep only the main domain (aliexpress.com)
            if len(parts) >= 2 and 'aliexpress' in parts[-2]:
                netloc = f"aliexpress.{parts[-1]}"
        
        new_query_string = urlencode(params_to_add)
        # Reconstruct URL ensuring path is preserved correctly
        reconstructed_url = urlunparse((
            parsed_url.scheme,
            netloc,
            parsed_url.path,
            '',
            new_query_string,
            ''
        ))
        # Add the star.aliexpress.com prefix to the reconstructed URL
        reconstructed_url = f"https://star.aliexpress.com/share/share.htm?&redirectUrl={reconstructed_url}"
        return reconstructed_url
    except ValueError:
        logger.error(f"Error building URL with params for base: {base_url}")
        return base_url


# --- Maintenance Task ---
async def periodic_cache_cleanup(context: ContextTypes.DEFAULT_TYPE):
    """Periodically clean up expired cache items (Job Queue callback)"""
    try:
        product_expired = await product_cache.clear_expired()
        link_expired = await link_cache.clear_expired()
        resolved_expired = await resolved_url_cache.clear_expired()
        logger.info(f"Cache cleanup: Removed {product_expired} product, {link_expired} link, {resolved_expired} resolved URL items.")
        logger.info(f"Cache stats: {len(product_cache.cache)} products, {len(link_cache.cache)} links, {len(resolved_url_cache.cache)} resolved URLs in cache.")
    except Exception as e:
        logger.error(f"Error in periodic cache cleanup job: {e}")


# --- API Call Functions (Adapted for Async Cache) ---

async def fetch_product_details_v2(product_id):
    """Fetches product details using aliexpress.affiliate.productdetail.get with async cache."""
    cached_data = await product_cache.get(product_id)
    if cached_data:
        logger.info(f"Cache hit for product ID: {product_id}")
        return cached_data

    logger.info(f"Fetching product details for ID: {product_id}")

    def _execute_api_call():
        """Execute blocking API call in a thread pool."""
        try:
            request = iop.IopRequest('aliexpress.affiliate.productdetail.get')
            request.add_api_param('fields', QUERY_FIELDS)
            request.add_api_param('product_ids', product_id)
            request.add_api_param('target_currency', TARGET_CURRENCY)
            request.add_api_param('target_language', TARGET_LANGUAGE)
            request.add_api_param('tracking_id', ALIEXPRESS_TRACKING_ID)
            request.add_api_param('country', QUERY_COUNTRY)

            return aliexpress_client.execute(request)
        except Exception as e:
            logger.error(f"Error in API call thread for product {product_id}: {e}")
            return None

    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(executor, _execute_api_call)

    if not response or not response.body:
        logger.error(f"Product detail API call failed or returned empty body for ID: {product_id}")
        return None

    try:
        response_data = response.body
        # Handle potential non-JSON string response (though SDK should return structured)
        if isinstance(response_data, str):
            try:
                response_data = json.loads(response_data)
            except json.JSONDecodeError as json_err:
                logger.error(f"Failed to decode JSON response for product {product_id}: {json_err}. Response: {response_data[:500]}")
                return None

        if 'error_response' in response_data:
            error_details = response_data.get('error_response', {})
            error_msg = error_details.get('msg', 'Unknown API error')
            error_code = error_details.get('code', 'N/A')
            logger.error(f"API Error for Product ID {product_id}: Code={error_code}, Msg={error_msg}")
            return None

        detail_response = response_data.get('aliexpress_affiliate_productdetail_get_response')
        if not detail_response:
            logger.error(f"Missing 'aliexpress_affiliate_productdetail_get_response' key for ID {product_id}. Response: {response_data}")
            return None

        resp_result = detail_response.get('resp_result')
        if not resp_result:
             logger.error(f"Missing 'resp_result' key for ID {product_id}. Response: {detail_response}")
             return None

        resp_code = resp_result.get('resp_code')
        if resp_code != 200:
             resp_msg = resp_result.get('resp_msg', 'Unknown response message')
             logger.error(f"API response code not 200 for ID {product_id}. Code: {resp_code}, Msg: {resp_msg}")
             return None

        result = resp_result.get('result', {})
        products = result.get('products', {}).get('product', [])

        if not products:
            logger.warning(f"No products found in API response for ID {product_id}")
            return None

        product_data = products[0] 

        product_info = {
            'image_url': product_data.get('product_main_image_url'),
            'price': product_data.get('target_sale_price'),
            'currency': product_data.get('target_sale_price_currency', TARGET_CURRENCY),
            'title': product_data.get('product_title', f'Product {product_id}')
        }

        # Cache the result
        await product_cache.set(product_id, product_info)
        expiry_date = datetime.now() + timedelta(days=CACHE_EXPIRY_DAYS)
        logger.info(f"Cached product {product_id} until {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}")

        return product_info

    except Exception as e:
        logger.exception(f"Error parsing product details response for ID {product_id}: {e}")
        return None

async def generate_affiliate_links_batch(target_urls: list[str]) -> dict[str, str | None]:
    """
    Generates affiliate links for a list of target URLs using a single API call for uncached URLs.
    Checks cache first, then fetches missing links in a batch.
    Returns a dictionary mapping each original target_url to its affiliate link (or None if failed).
    """
    results_dict = {}
    uncached_urls = []

    # 1. Check cache for each URL
    for url in target_urls:
        cached_link = await link_cache.get(url)
        if cached_link:
            logger.info(f"Cache hit for affiliate link: {url}")
            results_dict[url] = cached_link
        else:
            logger.debug(f"Cache miss for affiliate link: {url}")
            results_dict[url] = None # Initialize as None
            uncached_urls.append(url)

    # 2. If all URLs were cached, return immediately
    if not uncached_urls:
        logger.info("All affiliate links retrieved from cache.")
        return results_dict

    logger.info(f"Generating affiliate links for {len(uncached_urls)} uncached URLs: {', '.join(uncached_urls[:3])}...")

    # 3. Prepare and execute the batch API call
    # Check if URLs already have the star.aliexpress.com prefix before adding it
    prefixed_urls = []
    for url in uncached_urls:
        # Only add the prefix if it's not already there
        if "star.aliexpress.com/share/share.htm" not in url:
            prefixed_urls.append(f"https://star.aliexpress.com/share/share.htm?&redirectUrl={url}")
        else:
            prefixed_urls.append(url)
    source_values_str = ",".join(prefixed_urls)

    def _execute_batch_link_api():
        """Execute blocking batch API call in a thread pool."""
        try:
            request = iop.IopRequest('aliexpress.affiliate.link.generate')
            request.add_api_param('promotion_link_type', '0')
            request.add_api_param('source_values', source_values_str) # Comma-separated URLs
            request.add_api_param('tracking_id', ALIEXPRESS_TRACKING_ID)
            return aliexpress_client.execute(request)
        except Exception as e:
            logger.error(f"Error in batch link API call thread for URLs: {e}")
            return None

    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(executor, _execute_batch_link_api)

    # 4. Process the batch response
    if not response or not response.body:
        logger.error(f"Batch link generation API call failed or returned empty body for {len(uncached_urls)} URLs.")
        # Return the dictionary with cached values and Nones for failed ones
        return results_dict

    try:
        response_data = response.body
        if isinstance(response_data, str):
            try:
                response_data = json.loads(response_data)
            except json.JSONDecodeE
# Keyboards
keyboardStart = types.InlineKeyboardMarkup(row_width=1)
keyboardStart.add(
    types.InlineKeyboardButton("⭐️ألعاب لجمع العملات المعدنية⭐️", callback_data="games"),
    types.InlineKeyboardButton("⭐️تخفيض العملات على منتجات السلة 🛒⭐️", callback_data='click'),
    types.InlineKeyboardButton("🎬 شاهد كيفية عمل البوت 🎬", url="https://t.me/AliXPromotion/8"),
    types.InlineKeyboardButton("💰 حمل تطبيق Aliexpress للحصول على مكافأة 5 دولار 💰", url="https://a.aliexpress.com/_mtV0j3q")
)

keyboard = types.InlineKeyboardMarkup(row_width=1)
keyboard.add(
    types.InlineKeyboardButton("⭐️ألعاب لجمع العملات المعدنية⭐️", callback_data="games"),
    types.InlineKeyboardButton("⭐️تخفيض العملات على منتجات السلة 🛒⭐️", callback_data='click'),
    types.InlineKeyboardButton("❤️ اشترك في القناة للمزيد من العروض ❤️", url="https://t.me/AliXPromotion")
)

keyboard_games = types.InlineKeyboardMarkup(row_width=1)
keyboard_games.add(
    types.InlineKeyboardButton("⭐️ صفحة مراجعة وجمع النقاط يوميا ⭐️", url="https://s.click.aliexpress.com/e/_on0MwkF"),
    types.InlineKeyboardButton("⭐️ لعبة Merge boss ⭐️", url="https://s.click.aliexpress.com/e/_DlCyg5Z"),
    types.InlineKeyboardButton("⭐️ لعبة Fantastic Farm ⭐️", url="https://s.click.aliexpress.com/e/_DBBkt9V"),
    types.InlineKeyboardButton("⭐️ لعبة قلب الاوراق Flip ⭐️", url="https://s.click.aliexpress.com/e/_DdcXZ2r"),
    types.InlineKeyboardButton("⭐️ لعبة GoGo Match ⭐️", url="https://s.click.aliexpress.com/e/_DDs7W5D")
)

def resolve_short_link(short_url):
    try:
        response = requests.get(short_url, allow_redirects=True, timeout=10)
        return response.url
    except Exception as e:
        print(f"Erreur lors de la résolution du lien : {e}")
        return short_url

@bot.message_handler(commands=['start'])
def welcome_user(message):
    bot.send_message(
        message.chat.id,
        "مرحبا بك، ارسل لنا رابط المنتج الذي تريد شرائه لنوفر لك افضل سعر له 👌",
        reply_markup=keyboardStart
    )

@bot.callback_query_handler(func=lambda call: call.data == 'click')
def button_click(callback_query):
    text = (
        "✅1- ادخل الى السلة من هنا:\n"
        "https://s.click.aliexpress.com/e/_opGCtMf\n"
        "✅2- اختر المنتجات التي تريد تخفيض سعرها\n"
        "✅3- اضغط على زر دفع ليحولك لصفحة التأكيد\n"
        "✅4- انسخ الرابط هنا في البوت للحصول على رابط التخفيض"
    )
    img_link = "https://i.postimg.cc/HkMxWS1T/photo-5893070682508606111-y.jpg"
    bot.send_photo(callback_query.message.chat.id, img_link, caption=text, reply_markup=keyboard)

def extract_link(text):
    link_pattern = r'^(?:www\.|s\.click\.|a\.)?[\w-]*aliexpress\.(?:com|ru|es|fr|pt|it|pl|nl|co\.kr|co\.jp|com\.br|com\.tr|com\.vn|id|th|ar)'
    match = re.search(link_pattern, text)
    return match.group(0) if match else None

def get_affiliate_links(message, message_id, link):
    try:
        affiliate_links = aliexpress.get_affiliate_links(link)
        if not affiliate_links or not getattr(affiliate_links[0], 'promotion_link', None):
            bot.delete_message(message.chat.id, message_id)
            bot.send_message(message.chat.id, "⚠️ لم أتمكن من جلب رابط العرض لهذا المنتج. تأكد من الرابط وأعد المحاولة.")
            return

        promo_link = affiliate_links[0].promotion_link
        details = aliexpress.get_products_details([link])
        if not details or not getattr(details[0], 'product_title', None):
            bot.delete_message(message.chat.id, message_id)
            bot.send_message(message.chat.id, "⚠️ لم أتمكن من جلب تفاصيل هذا المنتج. ربما يكون الرابط خاطئًا أو المنتج لم يعد متاحًا.")
            return

        product = details[0]
        bot.delete_message(message.chat.id, message_id)
        bot.send_photo(
            message.chat.id,
            product.product_main_image_url,
            caption=(
                f"🛒 منتجك هو : 🔥\n"
                f"{product.product_title} 🛍\n"
                f"سعر المنتج : {product.target.sale_price} دولار 💵\n"
                f"💰 رابط العرض : {promo_link}\n\n"
                "#AliXPromotion ✅"
            ),
            reply_markup=keyboard
        )
    except Exception as e:
        bot.delete_message(message.chat.id, message_id)
        bot.send_message(message.chat.id, f"⚠️ حدث خطأ 🤷🏻‍♂️: {str(e)}")

def build_shopcart_link(link):
    parsed = urlparse(link)
    params = parse_qs(parsed.query)
    shopcart_ids = params.get("availableProductShopcartIds", [])
    if not shopcart_ids:
        return None
    shopcart_link = "https://www.aliexpress.com/p/trade/confirm.html?"
    extra = json.dumps({"channelInfo": {"sourceType": "620"}}, separators=(',', ':'))
    query = urlencode({
        "availableProductShopcartIds": ",".join(shopcart_ids),
        "extraParams": extra
    })
    return shopcart_link + query

def get_affiliate_shopcart_link(link, message):
    try:
        shopcart_link = build_shopcart_link(link)
        if not shopcart_link:
            bot.send_message(message.chat.id, "⚠️ الرابط غير صالح للسلة.")
            return
        affiliate_link = aliexpress.get_affiliate_links(shopcart_link)[0].promotion_link
        img_link = "https://i.postimg.cc/HkMxWS1T/photo-5893070682508606111-y.jpg"
        bot.send_photo(message.chat.id, img_link, caption=f"✅ هذا رابط تخفيض السلة:\n{affiliate_link}")
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ حدث خطأ 🤷🏻‍♂️: {str(e)}")

@bot.message_handler(func=lambda message: True)
def handle_links(message):
    link = extract_link(message.text)
    if not link or "aliexpress.com" not in link:
        bot.send_message(message.chat.id, "⚠️ الرابط غير صحيح! تأكد من رابط المنتج أو أعد المحاولة.")
        return

    # Résoudre les liens courts
    if "a.aliexpress.com" in link or "s.click.aliexpress.com" in link:
        link = resolve_short_link(link)

    sent = bot.send_message(message.chat.id, "⏳ جاري تجهيز العروض...")
    if "availableProductShopcartIds" in link:
        get_affiliate_shopcart_link(link, message)
    else:
        get_affiliate_links(message, sent.message_id, link)

@bot.callback_query_handler(func=lambda call: call.data == "games")
def send_games(call):
    img_link = "https://i.postimg.cc/zvDbVTS0/photo-5893070682508606110-x.jpg"
    bot.send_photo(
        call.message.chat.id,
        img_link,
        caption="⭐️ روابط ألعاب جمع العملات المعدنية 👇",
        reply_markup=keyboard_games
    )

# Flask webhook
@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '!', 200

@app.route('/')
def index():
    return 'Bot is running!', 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url='https://aliexpress-affiliate-telegram-bot-ju24.onrender.com/' + TOKEN)
    app.run(host="0.0.0.0", port=10000)
