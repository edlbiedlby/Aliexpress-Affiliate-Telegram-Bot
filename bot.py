#!/usr/bin/env python
# coding: utf-8

import telebot
from flask import Flask, request
from telebot import types
from aliexpress_api import AliexpressApi, models
import re
import json
from urllib.parse import urlparse, parse_qs, urlencode

# Initialisation du bot Telegram
bot = telebot.TeleBot('7925683283:AAG2QUVayxeCE_gS70OdOm79dOFwWDqPvlU')

# Supprimer tout webhook actif
bot.remove_webhook()

# Initialisation de l’API AliExpress
aliexpress = AliexpressApi('506592', 'ggkzfJ7lilLc7OXs6khWfT4qTZdZuJbh',
                           models.Language.EN, models.Currency.EUR, 'default')

# Création de l’application Flask
app = Flask(__name__)

# Route pour gérer les mises à jour envoyées par Telegram
@app.route('/webhook', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

# Configuration du webhook
WEBHOOK_URL = 'https://providersmmpro.com/webhook'  # Remplacez par l’URL de votre webhook
bot.set_webhook(url=WEBHOOK_URL)

# Clavier de démarrage
keyboardStart = types.InlineKeyboardMarkup(row_width=1)
btn1 = types.InlineKeyboardButton("⭐️ألعاب لجمع العملات المعدنية⭐️", callback_data="games")
btn2 = types.InlineKeyboardButton("⭐️تخفيض العملات على منتجات السلة 🛒⭐️", callback_data='click')
btn3 = types.InlineKeyboardButton("🎬 شاهد كيفية عمل البوت 🎬", url="https://t.me/AliXPromotion/8")
btn4 = types.InlineKeyboardButton(
    "💰 حمل تطبيق Aliexpress عبر الضغط هنا للحصول على مكافأة 5 دولار 💰",
    url="https://a.aliexpress.com/_mtV0j3q")
keyboardStart.add(btn1, btn2, btn3, btn4)

# Clavier général
keyboard = types.InlineKeyboardMarkup(row_width=1)
btn1 = types.InlineKeyboardButton("⭐️ألعاب لجمع العملات المعدنية⭐️", callback_data="games")
btn2 = types.InlineKeyboardButton("⭐️تخفيض العملات على منتجات السلة 🛒⭐️", callback_data='click')
btn3 = types.InlineKeyboardButton("❤️ اشترك في القناة للمزيد من العروض ❤️", url="https://t.me/AliXPromotion")
keyboard.add(btn1, btn2, btn3)

# Clavier des jeux
keyboard_games = types.InlineKeyboardMarkup(row_width=1)
btn1 = types.InlineKeyboardButton("⭐️ صفحة مراجعة وجمع النقاط يوميا ⭐️", url="https://s.click.aliexpress.com/e/_on0MwkF")
btn2 = types.InlineKeyboardButton("⭐️ لعبة Merge boss ⭐️", url="https://s.click.aliexpress.com/e/_DlCyg5Z")
btn3 = types.InlineKeyboardButton("⭐️ لعبة Fantastic Farm ⭐️", url="https://s.click.aliexpress.com/e/_DBBkt9V")
btn4 = types.InlineKeyboardButton("⭐️ لعبة قلب الاوراق Flip ⭐️", url="https://s.click.aliexpress.com/e/_DdcXZ2r")
btn5 = types.InlineKeyboardButton("⭐️ لعبة GoGo Match ⭐️", url="https://s.click.aliexpress.com/e/_DDs7W5D")
keyboard_games.add(btn1, btn2, btn3, btn4, btn5)

# Commande /start
@bot.message_handler(commands=['start'])
def welcome_user(message):
    bot.send_message(
        message.chat.id,
        "مرحبا بك، ارسل لنا رابط المنتج الذي تريد شرائه لنوفر لك افضل سعر له 👌 \n",
        reply_markup=keyboardStart)

# Gestion du callback "click"
@bot.callback_query_handler(func=lambda call: call.data == 'click')
def button_click(callback_query):
    bot.edit_message_text(chat_id=callback_query.message.chat.id,
                          message_id=callback_query.message.message_id,
                          text="...")

    text = "✅1-ادخل الى السلة من هنا:\n" \
           " https://s.click.aliexpress.com/e/_opGCtMf \n" \
           "✅2-قم باختيار المنتجات التي تريد تخفيض سعرها\n" \
           "✅3-اضغط على زر دفع ليحولك لصفحة التأكيد \n" \
           "✅4-اضغط على الايقونة في الاعلى وانسخ الرابط  هنا في البوت لتتحصل على رابط التخفيض"

    img_link1 = "https://i.postimg.cc/HkMxWS1T/photo-5893070682508606111-y.jpg"
    bot.send_photo(callback_query.message.chat.id,
                   img_link1,
                   caption=text,
                   reply_markup=keyboard)

# Extraction du lien affilié et des informations du produit
def get_affiliate_links(message, message_id, link):
    try:
        limit_links = aliexpress.get_affiliate_links(link)
        limit_links = limit_links[0].promotion_link

        try:
            product_details = aliexpress.get_products_details([link])
            price_pro = product_details[0].target.sale_price
            title_link = product_details[0].product_title
            img_link = product_details[0].product_main_image_url

            bot.delete_message(message.chat.id, message_id)
            bot.send_photo(message.chat.id,
                           img_link,
                           caption=" \n🛒 منتجك هو  : 🔥 \n"
                           f" {title_link} 🛍 \n"
                           f"  سعر المنتج  : {price_pro}  دولار 💵\n"
                           f"\n قارن بين الاسعار واشتري 🔥 \n"
                           f"💰 عرض العملات (السعر النهائي عند الدفع)  : \n"
                           f"الرابط {limit_links} \n\n"
                           "#AliXPromotion ✅",
                           reply_markup=keyboard)

        except:
            bot.delete_message(message.chat.id, message_id)
            bot.send_message(message.chat.id, f"💰 عرض العملات (السعر النهائي عند الدفع) : \n"
                                              f"الرابط {limit_links} \n\n"
                                              "#AliXPromotion ✅",
                             reply_markup=keyboard)

    except:
        bot.send_message(message.chat.id, "حدث خطأ 🤷🏻‍♂️")

# Extraction du lien produit
def extract_link(text):
    link_pattern = r'https?://\S+|www\.\S+'
    links = re.findall(link_pattern, text)
    if links:
        return links[0]

# Construction du lien de panier d’achat
def build_shopcart_link(link):
    params = get_url_params(link)
    shop_cart_link = "https://www.aliexpress.com/p/trade/confirm.html?"
    shop_cart_params = {
        "availableProductShopcartIds": ",".join(params.get("availableProductShopcartIds", [])),
        "extraParams": json.dumps({"channelInfo": {"sourceType": "620"}}, separators=(',', ':'))
    }
    return create_query_string_url(link=shop_cart_link, params=shop_cart_params)

def get_url_params(link):
    parsed_url = urlparse(link)
    params = parse_qs(parsed_url.query)
    return params

def create_query_string_url(link, params):
    return link + urlencode(params)

# Gestion des liens affiliés du panier d’achat
def get_affiliate_shopcart_link(link, message):
    try:
        shopcart_link = build_shopcart_link(link)
        affiliate_link = aliexpress.get_affiliate_links(shopcart_link)[0].promotion_link

        text2 = f"هذا رابط تخفيض السلة \n{affiliate_link}"

        img_link3 = "https://i.postimg.cc/HkMxWS1T/photo-5893070682508606111-y.jpg"
        bot.send_photo(message.chat.id, img_link3, caption=text2)

    except:
        bot.send_message(message.chat.id, "حدث خطأ 🤷🏻‍♂️")

# Gestion des messages contenant un lien
@bot.message_handler(func=lambda message: True)
def get_link(message):
    link = extract_link(message.text)

    sent_message = bot.send_message(message.chat.id, 'المرجو الانتظار قليلا، يتم تجهيز العروض ⏳')
    message_id = sent_message.message_id

    if link and "aliexpress.com" in link:
        if "availableProductShopcartIds" in message.text.lower():
            get_affiliate_shopcart_link(link, message)
        else:
            get_affiliate_links(message, message_id, link)
    else:
        bot.delete_message(message.chat.id, message_id)
        bot.send_message(message.chat.id,
                         "الرابط غير صحيح ! تأكد من رابط المنتج أو اعد المحاولة.\n"
                         " قم بإرسال <b> الرابط فقط</b> بدون عنوان المنتج",
                         parse_mode='HTML')

# Gestion des callbacks jeux
@bot.callback_query_handler(func=lambda call: call.data == "games")
def handle_games_callback(call):
    img_link2 = "https://i.postimg.cc/zvDbVTS0/photo-5893070682508606110-x.jpg"
    bot.send_photo(
        call.message.chat.id,
        img_link2,
        caption="روابط ألعاب جمع العملات المعدنية لإستعمالها في خفض السعر لبعض المنتجات، قم بالدخول يوميا لها للحصول على أكبر عدد ممكن في اليوم 👇",
        reply_markup=keyboard_games)

if __name__ == "__main__":
    # Lancer l’application Flask
    app.run(host='0.0.0.0', port=5000)
