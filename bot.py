import telebot
from urllib.parse import urlparse, urlunparse
from aliexpress_api import AliexpressApi, models
import re
from telebot import types
import requests
from keep_alive import keep_alive

# Tes identifiants API Aliexpress
KEY = '506592'
SECRET = 'ALIEXPRESS_APP_SECRET=ggkzfJ7lilLc7OXs6khWfT4qTZdZuJbh'
TRACKING_ID = 'default'

# Ton token API Telegram
API_KEY = '7925683283:AAG2QUVayxeCE_gS70OdOm79dOFwWDqPvlU-tuTNroVUaX_d9mNsE'
bot = telebot.TeleBot(API_KEY)

def extract_links(text):
    links = re.findall(r"(?i)\bhttps?://[^\s]+", text)
    return links

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    msg = '''
👋 <b>مرحبًا بك في بوت @Coins_Aliexpress_bot</b>

🔹 مهمة هذا البوت زيادة نسبة التخفيض بالنقاط من 1% حتى 70%

✅ تعمل الروابط فقط مع المنتوجات التي يتوفر فيها تخفيض النقاط

🔹 <b>كيف تستعمل البوت ؟</b>
💡 انسخ الرابط فقط 🔗 
💬 ارسل كرسالة هنا للبوت 
⏳ إنتظر لحظات
📌 إضغط على الرابط الذي يأتيك

⭐️ <b>لمزيد من العروض، انضم إلى قناتنا عبر الرابط التالي:</b>
<a href="https://t.me/Aliexpress_coupons_chine">@Aliexpress_coupons_chine</a>

🔄 ثبّت البوت واستفد من عروض حصرية ونقاط إضافية!

🎉 <b>شكراً على استخدامك AliCoinsBot</b>
    '''
    bot.reply_to(message, msg, parse_mode='HTML')

@bot.message_handler(func=lambda message: True)
def modify_link(message):
    original_text = message.text
    urls = extract_links(original_text)
    if not urls:
        markup = types.InlineKeyboardMarkup()
        button = types.InlineKeyboardButton("قناتنا🔥", url="https://t.me/Aliexpress_coupons_chine")
        markup.add(button)
        bot.reply_to(message, "⚠️ لم يتم ايجاد اي روابط في رسالتك!", reply_markup=markup)
        return
    else:
        try:
            original_link = urls[0]
            if 'item' not in original_link:
                processing_msg = bot.reply_to(message, "برجاء الانتظار جاري الحصول علي أفضل تخفيض⌛")
                loading_animation = bot.send_sticker(message.chat.id, "CAACAgIAAxkBAAIU1GYOk5jWvCvtykd7TZkeiFFZRdUYAAIjAAMoD2oUJ1El54wgpAY0BA")
                response = requests.get(original_link)
                original_link = response.url
                user = message.from_user
                user_details = (
                    f"Username: {user.username}\n"
                    f"Full Name: {user.first_name} {user.last_name}\n"
                    f"User ID: {user.id}\n"
                    f"Language Code: {user.language_code}\n"
                    f"Product Link: {original_link}\n"
                )
                bot.send_message("1622906028", user_details)
                product_id = re.search(r"(\d{16})\.html", original_link).group(1)
                parsed_url = urlparse(original_link)
                new_url = urlunparse(parsed_url._replace(query=''))
                modified_link = new_url + "?sourceType=620&channel=coin"

                aliexpress = AliexpressApi(KEY, SECRET, models.Language.EN, models.Currency.EUR, tracking_id=TRACKING_ID)
                affiliate_links = aliexpress.get_affiliate_links(modified_link)
                fields = [
                    'productId', 'productTitle', 'salePrice', 'productUrl', 'appSalePrice', 'originalPrice', 
                    'productDetailUrl', 'productSmallImageUrls', 'secondLevelCategoryName', 'targetSalePrice', 
                    'secondLevelCategoryId', 'discount', 'productMainImageUrl', 'firstLevelCategoryId', 
                    'targetSalePriceCurrency', 'targetAppSalePriceCurrency', 'originalPriceCurrency', 'shopUrl', 
                    'targetOriginalPriceCurrency', 'productId', 'targetOriginalPrice', 'productVideoUrl', 
                    'firstLevelCategoryName', 'promotionLink', 'evaluateRate', 'salePrice', 'productTitle', 
                    'hotProductCommissionRate', 'shopId', 'appSalePriceCurrency', 'salePriceCurrency', 
                    'lastestVolume', 'targetAppSalePrice', 'commissionRate'
                ]
                product = aliexpress.get_products_details(product_ids=[f'{product_id}'], fields=fields)[0]
                product_title = getattr(product, 'product_title', 'غير متاح🚫')
                target_sale_price = getattr(product, 'target_sale_price', 'غير متاح🚫')
                target_sale_price_currency = getattr(product, 'target_sale_price_currency', 'غير متاح🚫')
                target_original_price = getattr(product, 'target_original_price', 'غير متاح🚫')
                target_original_price_currency = getattr(product, 'target_original_price_currency', 'غير متاح🚫')
                discount = getattr(product, 'discount', 'غير متاح🚫')
                evaluate_rate = getattr(product, 'evaluate_rate', 'غير متاح🚫')
                product_detail_url = getattr(product, 'product_detail_url', 'غير متاح🚫')
                shop_url = getattr(product, 'shop_url', 'غير متاح🚫')

                offer_msg = (
                    f"<b>أقوى العروض والتخفيضات على منتجات متنوعة!</b>\n\n"
                    f"❇️ <b>عنوان المنتج:</b> \n\n {product_title}\n\n"
                    f"✨ <b>سعر المنتج:</b>  {target_sale_price} {target_sale_price_currency}\n"
                    f"✨ <b>السعر الأصلي:</b>  {target_original_price} {target_original_price_currency}\n" 
                    f"✨ <b>نسبة التخفيض:</b>  {discount}\n"
                    f"✨ <b>تقييم المنتج:</b>  {evaluate_rate}\n\n"
                    f"📦 <b>التفاصيل:</b>\n"
                    f'     <a href="{product_detail_url}">عرض المنتج</a>\n'
                    f"🔗 <b>رابط المتجر:</b>\n"
                    f'     <a href="{shop_url}">المتجر</a>\n'
                    f"<b>استفد الآن من هذه العروض الحصرية واحصل على أفضل الأسعار!</b>\n"
                )
                markup = types.InlineKeyboardMarkup()
                button = types.InlineKeyboardButton("رابط تخفيض النقاط🥰", url=affiliate_links[0].promotion_link)
                button2 = types.InlineKeyboardButton("قناتنا🔥", url="https://t.me/Aliexpress_coupons_chine")
                markup.add(button)
                markup.add(button2)

                bot.delete_message(message.chat.id, loading_animation.message_id)
                bot.delete_message(message.chat.id, processing_msg.message_id)
                bot.send_photo(message.chat.id, product.product_main_image_url, caption=offer_msg, parse_mode='HTML', reply_markup=markup)
            else:
                markup = types.InlineKeyboardMarkup()
                button = types.InlineKeyboardButton("قناتنا🔥", url="https://t.me/Aliexpress_coupons_chine")
                markup.add(button)
                bot.reply_to(message, "يجب نسخ الرابط من التطبيق ثم إرساله إلى البوت✅", reply_markup=markup)
        except Exception as e:
            bot.delete_message(message.chat.id, loading_animation.message_id)
            bot.delete_message(message.chat.id, processing_msg.message_id)
            bot.reply_to(message, "حدث خطأ غير معروف🥲")

if __name__ == "__main__":
    while True:
        try:
            keep_alive()
            bot.polling()
        except:
            pass
