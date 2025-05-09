#!/usr/bin/env python
# coding: utf-8

import telebot
from telebot import types
from aliexpress_api import AliexpressApi, models
import re
import requests, json
from urllib.parse import urlparse, parse_qs
import os

# Récupération des clés API et du token à partir des variables d'environnement
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
aliexpress_app_key = os.getenv("ALIEXPRESS_APP_KEY")
aliexpress_app_secret = os.getenv("ALIEXPRESS_APP_SECRET")
aliexpress_tracking_id = os.getenv("ALIEXPRESS_TRACKING_ID")

bot = telebot.TeleBot(bot_token)

aliexpress = AliexpressApi(aliexpress_app_key, aliexpress_app_secret,
                           models.Language.EN, models.Currency.EUR, aliexpress_tracking_id)

keyboardStart = types.InlineKeyboardMarkup(row_width=1)
btn1 = types.InlineKeyboardButton("⭐️ألعاب لجمع العملات المعدنية⭐️", callback_data="games")
btn2 = types.InlineKeyboardButton("⭐️تخفيض العملات على منتجات السلة 🛒⭐️", callback_data='click')
btn4 = types.InlineKeyboardButton("🎬 شاهد كيفية عمل البوت 🎬", url="https://t.me/AliXPromotion/8")
btn5 = types.InlineKeyboardButton(
    "💰  حمل تطبيق Aliexpress عبر الضغط هنا للحصول على مكافأة 5 دولار  💰", 
    url="https://a.aliexpress.com/_mtV0j3q")
keyboardStart.add(btn1, btn2, btn4, btn5)

keyboard = types.InlineKeyboardMarkup(row_width=1)
btn1 = types.InlineKeyboardButton("⭐️ألعاب لجمع العملات المعدنية⭐️", callback_data="games")
btn2 = types.InlineKeyboardButton("⭐️تخفيض العملات على منتجات السلة 🛒⭐️", callback_data='click')
btn3 = types.InlineKeyboardButton("❤️ اشترك في القناة للمزيد من العروض ❤️", url="https://t.me/AliXPromotion")
keyboard.add(btn1, btn2, btn3)

keyboard_games = types.InlineKeyboardMarkup(row_width=1)
btn1 = types.InlineKeyboardButton(" ⭐️ صفحة مراجعة وجمع النقاط يوميا ⭐️", url="https://s.click.aliexpress.com/e/_on0MwkF")
btn2 = types.InlineKeyboardButton("⭐️ لعبة Merge boss ⭐️", url="https://s.click.aliexpress.com/e/_DlCyg5Z")
btn3 = types.InlineKeyboardButton("⭐️ لعبة Fantastic Farm ⭐️", url="https://s.click.aliexpress.com/e/_DBBkt9V")
btn4 = types.InlineKeyboardButton("⭐️ لعبة قلب الاوراق Flip ⭐️", url="https://s.click.aliexpress.com/e/_DdcXZ2r")
btn5 = types.InlineKeyboardButton("⭐️ لعبة GoGo Match ⭐️", url="https://s.click.aliexpress.com/e/_DDs7W5D")
keyboard_games.add(btn1, btn2, btn3, btn4, btn5)

@bot.message_handler(commands=['start'])
def welcome_user(message):
    bot.send_message(message.chat.id, "مرحبا بك، ارسل لنا رابط المنتج الذي تريد شرائه لنوفر لك افضل سعر له 👌 \n", reply_markup=keyboardStart)

@bot.callback_query_handler(func=lambda call: call.data == 'click')
def button_click(callback_query):
    bot.edit_message_text(chat_id=callback_query.message.chat.id,
                          message_id=callback_query.message.message_id,
                          text="...")
    
    text = "✅1-ادخل الى السلة من هنا:\n" \
           " https://s.click.aliexpress.com/e/_opGCtMf \n" \
           "✅2-قم باختيار المنتجات التي تريد تخفيض سعرها\n" \
           "✅3-اضغط على زر دفع ليحولك لصفحة التأكيد \n" \
           "✅4-اضغط على الايقونة في الاعلى وانسخ الرابط هنا في البوت لتتحصل على رابط التخفيض"

    img_link1 = "https://i.postimg.cc/HkMxWS1T/photo-5893070682508606111-y.jpg"
    bot.send_photo(callback_query.message.chat.id, img_link1, caption=text, reply_markup=keyboard)

def get_affiliate_links(message, message_id, link):
    try:
        limit_links = aliexpress.get_affiliate_links(
            f'https://star.aliexpress.com/share/share.htm?platform=AE&businessType=ProductDetail&redirectUrl={link}?sourceType=561&aff_fcid='
        )
        limit_links = limit_links[0].promotion_link

        try:
            img_link = aliexpress.get_products_details([
                '1000006468625',
                f'https://star.aliexpress.com/share/share.htm?platform=AE&businessType=ProductDetail&redirectUrl={link}'
            ])
            price_pro = img_link[0].target.sale_price
            title_link = img_link[0].product_title
            img_link = img_link[0].product_main_image_url
            affiliate_link = limit_links
            super_links = "Super links not defined"
            
            bot.delete_message(message.chat.id, message_id)
            bot.send_photo(message.chat.id,
                           img_link,
                           caption=" \n🛒 منتجك هو  : 🔥 \n"
                           f" {title_link} 🛍 \n"
                           f"  سعر المنتج  : "
                           f" {price_pro}  دولار 💵\n"
                           " \n قارن بين الاسعار واشتري 🔥 \n"
                           "💰 عرض العملات (السعر النهائي عند الدفع)  : \n"
                           f"الرابط {affiliate_link} \n"
                           f"💎 عرض السوبر  : \n"
                           f"الرابط {super_links} \n"
                           f"♨️ عرض محدود  : \n"
                           f"الرابط {limit_links} \n\n"
                           "#AliXPromotion ✅",
                           reply_markup=keyboard)

        except Exception as e:
            bot.delete_message(message.chat.id, message_id)
            bot.send_message(message.chat.id, f"حدث خطأ: {e}")

    except Exception as e:
        bot.send_message(message.chat.id, f"حدث خطأ أثناء الحصول على الروابط: {e}")

def extract_link(text):
    # Regular expression pattern to match links
    link_pattern = r'https?://\S+|www\.\S+'
    links = re.findall(link_pattern, text)
    if links:
        return links[0]
    return None

@bot.message_handler(func=lambda message: True)
def get_link(message):
    link = extract_link(message.text)
    sent_message = bot.send_message(message.chat.id, 'المرجو الانتظار قليلا، يتم تجهيز العروض ⏳')
    message_id = sent_message.message_id

    if link and "aliexpress.com" in link:
        get_affiliate_links(message, message_id, link)
    else:
        bot.delete_message(message.chat.id, message_id)
        bot.send_message(message.chat.id, "الرابط غير صحيح ! تأكد من رابط المنتج أو اعد المحاولة.\n قم بإرسال <b> الرابط فقط</b> بدون عنوان المنتج", parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    img_link2 = "https://i.postimg.cc/zvDbVTS0/photo-5893070682508606110-x.jpg"
    bot.send_photo(call.message.chat.id, img_link2, caption="روابط ألعاب جمع العملات المعدنية لإستعمالها في خفض السعر لبعض المنتجات، قم بالدخول يوميا لها للحصول على أكبر عدد ممكن في اليوم 👇", reply_markup=keyboard_games)

# Keep the bot alive
def keep_alive():
    from flask import Flask
    app = Flask(__name__)

    @app.route('/')
    def home():
        return "Bot is running!"

    app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
