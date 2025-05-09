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
    link_pattern = r'(https?://\S+|www.\S+)'
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
