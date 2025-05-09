import requests
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

BOT_TOKEN = '7925683283:AAG2QUVayxeCE_gS70OdOm79dOFwWDqPvlU'

def get_product_name(product_id):
    url = f'https://api.aliexpress.com/product/{product_id}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get('product_title', 'Produit inconnu'), data.get('sale_price', 'Prix inconnu')
    else:
        return 'Erreur', 'Erreur'

def start(update, context):
    update.message.reply_text("Envoie-moi un lien AliExpress, je te donne le nom et le prix !")

def handle_message(update, context):
    message = update.message.text
    if 'aliexpress.com' in message:
        try:
            product_id = message.split('item/')[1].split('.html')[0]
            name, price = get_product_name(product_id)
            affiliate_link = f"https://s.click.aliexpress.com/e/_d{product_id}"
            reply = f"Nom du produit : {name}\nPrix : {price}\nLien affilié : {affiliate_link}"
            update.message.reply_text(reply)
        except Exception as e:
            update.message.reply_text("Erreur lors du traitement du lien.")
    else:
        update.message.reply_text("Envoie-moi un lien AliExpress valide.")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
