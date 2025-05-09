import requests  
import hashlib  
import time  
import hmac  
import json  
import telegram  

# TES IDENTIFIANTS  
APP_KEY = '506592'  
APP_SECRET = 'ggkzfJ7lilLc7OXs6khWfT4qTZdZuJbh'  
TRACKING_ID = 'default'  
TELEGRAM_TOKEN = '7925683283:AAG2QUVayxeCE_gS70OdOm79dOFwWDqPvlU'  

bot = telegram.Bot(token=TELEGRAM_TOKEN)  

def generate_signature(app_key, secret, params):  
    sorted_params = ''.join(f'{k}{v}' for k, v in sorted(params.items()))  
    sign_str = app_key + sorted_params + secret  
    sign = hmac.new(secret.encode(), sign_str.encode(), hashlib.sha256).hexdigest()  
    return sign  

def get_product_details(product_id):  
    url = 'https://api.aliexpress.com/v1/product'  
    params = {  
        'app_key': APP_KEY,  
        'method': 'getProductDetails',  
        'timestamp': str(int(time.time() * 1000)),  
        'product_id': product_id  
    }  
    params['sign'] = generate_signature(APP_KEY, APP_SECRET, params)  
    response = requests.get(url, params=params)  
    return response.json()  

def build_message(product):  
    title = product['title']  
    current_price = product['price']['current']  
    discount_price = product['price'].get('discount', current_price)  
    ratings = product['ratings']  
    store_name = product['store']['name']  
    store_ratings = product['store']['ratings']  
    links = product['affiliate_links']  

    message = f"""  
ـ **{title}**  

ـ Current Price: {current_price}$  
🌟 Discount Link: {discount_price}$  
{links.get('discount')}  

🔥 Super Link: {links.get('super')}  
🚨 Limited Offer: {links.get('limited')}  

📊 Product Ratings: {ratings}  
➖ Store Name: {store_name}  
🟠 Store Ratings: {store_ratings}  
"""  
    return message  

def send_to_telegram(chat_id, text):  
    bot.send_message(chat_id=chat_id, text=text, parse_mode=telegram.ParseMode.MARKDOWN)  

# EXEMPLE D’UTILISATION  
if __name__ == '__main__':  
    chat_id = 'TON_CHAT_ID'  # Remplace par ton chat ID  
    product_id = '1005006251633924'  # Remplace par un ID réel  
    product = get_product_details(product_id)  
    message = build_message(product)  
    send_to_telegram(chat_id, message)
