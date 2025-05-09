import requests import hashlib import time import hmac import json import telegram

AliExpress API credentials

APP_KEY = '506592' APP_SECRET = 'ggkzfJ7lilLc7OXs6khWfT4qTZdZuJbh' TRACKING_ID = 'default'

Telegram bot token

TELEGRAM_TOKEN = '7925683283:AAG2QUVayxeCE_gS70OdOm79dOFwWDqPvlU' CHAT_ID = 'YOUR_CHAT_ID'  # Replace with your Telegram user or channel ID

bot = telegram.Bot(token=TELEGRAM_TOKEN)

def get_product_details(product_id): method = 'aliexpress.affiliate.product.detail.get' sign_method = 'sha256' timestamp = str(int(time.time() * 1000))

params = {
    'app_key': APP_KEY,
    'method': method,
    'format': 'json',
    'sign_method': sign_method,
    'timestamp': timestamp,
    'v': '2.0',
    'product_ids': product_id,
    'target_currency': 'CAD',
    'target_language': 'EN',
    'tracking_id': TRACKING_ID
}

sorted_params = ''.join(f'{k}{v}' for k, v in sorted(params.items()))
string_to_sign = APP_SECRET + sorted_params + APP_SECRET
sign = hmac.new(APP_SECRET.encode('utf-8'), string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest().upper()

params['sign'] = sign
response = requests.get('https://api.aliexpress.com/openapi/param2/2/portals.open/api.' + method, params=params)

if response.status_code == 200:
    data = response.json()
    if 'result' in data and 'products' in data['result']:
        return data['result']['products'][0]
return None

def build_affiliate_links(product_id): base = f'https://s.click.aliexpress.com/deep_link.htm?aff_short_key=_9z3fYk&dl_target_url=https://www.aliexpress.com/item/{product_id}.html' discount_link = base + '&aff_platform=promotion' super_deal_link = base + '&aff_platform=super_deals' limited_offer_link = base + '&aff_platform=limited_offer' return discount_link, super_deal_link, limited_offer_link

def send_telegram_message(message): bot.send_message(chat_id=CHAT_ID, text=message, parse_mode=telegram.ParseMode.MARKDOWN)

def main(): product_id = input('Enter AliExpress product ID: ') details = get_product_details(product_id) if not details: print('Failed to get product details.') return

discount_link, super_deal_link, limited_offer_link = build_affiliate_links(product_id)

message = (
    f"**Product:** {details['product_title']}\n"
    f"**Current Price (CAD):** {details['sale_price']}\n"
    f"\n🌟 **Discount Point Link:** {discount_link}\n"
    f"🔥 **Super Deal Link:** {super_deal_link}\n"
    f"🚨 **Limited Offer Link:** {limited_offer_link}\n"
    f"\n📊 **Product Rating:** {details['evaluate_rate']}\n"
    f"➖ **Store Name:** {details['shop_name']}\n"
    f"🟠 **Store Rating:** {details['shop_evaluate_rate']}"
)

send_telegram_message(message)
print('Message sent to Telegram!')

if name == 'main': main()

