import requests import hashlib import time import hmac import json import telegram

AliExpress API credentials

APP_KEY = '506592' APP_SECRET = 'ggkzfJ7lilLc7OXs6khWfT4qTZdZuJbh' TRACKING_ID = 'default'

Telegram bot token and chat ID

TELEGRAM_TOKEN = '7925683283:AAG2QUVayxeCE_gS70OdOm79dOFwWDqPvlU' CHAT_ID = '<TON_CHAT_ID>'  # Remplace par ton chat ID

bot = telegram.Bot(token=TELEGRAM_TOKEN)

Function to get product details from AliExpress API

def get_product_details(product_id): api_url = 'https://api.aliexpress.com/v1/product/detail' timestamp = str(int(time.time() * 1000)) sign_str = APP_KEY + timestamp + APP_SECRET sign = hmac.new(APP_SECRET.encode(), sign_str.encode(), hashlib.sha256).hexdigest().upper()

params = {
    'app_key': APP_KEY,
    'method': 'aliexpress.affiliate.product.detail.get',
    'timestamp': timestamp,
    'sign': sign,
    'product_id': product_id,
    'tracking_id': TRACKING_ID,
    'currency': 'USD',
    'country': 'CA'  # Canada
}

response = requests.get(api_url, params=params)
try:
    data = response.json()
    return data['result']
except Exception as e:
    print('Error:', e)
    print('Response:', response.text)
    return None

Function to generate message

def generate_message(product): message = f"ـ Offer for {product['product_title']}\n" message += f"ـ Current price: {product['sale_price']['amount']} {product['sale_price']['currency']}\n\n"

if 'coupon_link' in product:
    message += f"🌟 Coupon link: {product['coupon_link']}\n"
if 'super_deal_link' in product:
    message += f"🔥 Super Deal link: {product['super_deal_link']}\n"
if 'limited_offer_link' in product:
    message += f"🚨 Limited Offer link: {product['limited_offer_link']}\n"

message += f"\n📊 Product rating: {product['evaluate_rate']}\n"
message += f"➖ Store name: {product['shop_name']}\n"
message += f"🟠 Store rating: {product['shop_evaluate_rate']}\n"

return message

Main logic

if name == 'main': product_id = '1005006789012345'  # Remplace par l’ID du produit à tester product = get_product_details(product_id)

if product:
    message = generate_message(product)
    bot.send_message(chat_id=CHAT_ID, text=message)
    print('Message sent.')
else:
    print('Failed to get product details.')

