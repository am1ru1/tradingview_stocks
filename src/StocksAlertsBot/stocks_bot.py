import os
import logging
import time

from selenium import webdriver
import requests
from telegram import Update, Chat, ChatMember, ParseMode, ChatMemberUpdated
from handlers import *
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    ConversationHandler,
    CallbackQueryHandler,
    PrefixHandler, PicklePersistence,
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
base_url = 'http://127.0.0.1:5000/'
logger = logging.getLogger(__name__)


def start(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    context.user_data['watchlist'] = []
    context.user_data['real_name'] = []
    logger.info("User %s started the conversation.", user.first_name)
    update.message.reply_text("OK lets start add some stocks!\nSend the symbol or the company name")
    update.message.reply_text(text='Choose the stock type',
                              reply_markup=menu_keyboard())


def search(update: Update, _: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    query.edit_message_text(text=f"Send the stock symbol of the company name")


def update_watchlist(update: Update, context: CallbackContext) -> None:
    message = update.message.text.split(' ')
    logger.info(f'{update.message.from_user.username} asked for {update.message.text}')
    watchlist = context.user_data.get('watchlist')
    real_name = context.user_data.get('real_name')
    if watchlist is None:
        watchlist = list()
    if real_name is None:
        real_name = list()
    if len(message) >= 2:
        if ',' in message[1]:
            for symbol in message[1].split(','):
                if symbol in watchlist:
                    continue
                if 'add' in message[0]:
                    watchlist.append(symbol)
                    logger.info(f'Adding to  watchlist {message[1]}')
                    url = f'{base_url}symbol/{symbol}'
                    response = requests.post(url)
                elif 'remove' in message[0]:
                    logger.info(f'Removing {message[1]} from watchlist')
                    watchlist.remove(symbol)
                    url = f'{base_url}symbol/{symbol}'
                    requests.delete(url)
                    update.message.reply_text(f'{symbol} has been removed from your watchlist')
        elif message[1] in watchlist:
            if 'remove' in message[0]:
                watchlist.remove(message[1])
                url = f'{base_url}symbol/{message[1]}'
                response = requests.delete(url)
                update.message.reply_text(f'{message[0]} has been removed from your watchlist')
        elif message[1] not in watchlist:
            if 'add' in message[0]:
                watchlist.append(message[1])
                url = f'{base_url}symbol/{message[1]}'
                response = requests.post(url)
                market_name = response.json()['symbol']
                real_name.append(market_name)
        # context.user_data['watchlist'] = watchlist
        # for symbol in watchlist:
        #     url = f'{base_url}symbol/{symbol}'
        #     response = requests.post(url)
        #     if response.json()['status'] == 'Error' or response.status_code == 500:
        #         update.message.reply_text(f'Cant find {symbol}, wrong symbol?')
        context.user_data['real_name'] = real_name
        update.message.reply_text(f'Your watchlist updated to {watchlist}')


def watchlist(update: Update, context: CallbackContext) -> None:
    if update.callback_query:
        update.callback_query.answer()
    logger.info(f'{update.effective_chat.username} asked for watchlist')
    if update.callback_query:
        update.callback_query.message.edit_text(text='Choose the stock type',
                                                reply_markup=watchlist_keyboard(context.user_data['real_name']))
    else:
        update.message.reply_text(text='Choose the stock type',
                                  reply_markup=watchlist_keyboard(context.user_data['real_name']))


def get_status(update: Update, context: CallbackContext) -> None:
    watchlist = context.user_data.get('watchlist')
    market_status = requests.get(f'{base_url}/market').json()['market']
    logger.info(f'{update.message.from_user} asked for {update.message.text}')
    message = str()
    for symbol in watchlist:
        url = f'{base_url}symbol/{symbol}'
        response = requests.get(url).json()
        if response.get('Error'):
            update.message.reply_text(f'Cant find {symbol}..')
            continue
        update.message.reply_text(
            make_html(response['percent_change'], response['name'], response['company'], response['price'],
                      market_status),
            parse_mode='HTML')


def get_symbol_keyboard(update: Update, context: CallbackContext):
    update.callback_query.answer()
    symbol_index = context.match.string.split('_')
    market_status = requests.get(f'{base_url}/market').json()['market']
    symbol = context.user_data.get('watchlist')[int(symbol_index[1])]
    logger.info(f'{update.effective_user.username} Requested symbol : {symbol}')
    url = f'{base_url}symbol/{symbol}'
    response = requests.patch(url).json()
    if response is None:
        update.callback_query.message.edit_text(f'Cant find {symbol}..', reply_markup=back_to_watchlist())
        return
    update.callback_query.message.edit_text(
        make_html(response['change_percent'], response['symbol'], response['company_name'], response['price'], market_status),
        parse_mode='HTML', reply_markup=back_to_watchlist())


def get_symbol(update: Update, context: CallbackContext) -> None:
    message = update.message.text
    logger.info(f'{update.message.from_user} asked for {update.message.text}')
    message = message.split(' ')
    market_status = requests.get(f'{base_url}/market').json()['market']
    if len(message) == 2:
        symbol = message[1]
        url = f'{base_url}symbol/{symbol}'
        response = requests.patch(url).json()
        if response.get('Error'):
            update.message.reply_text(f'Cant find {symbol}..')
            return
        update.message.reply_text(
            make_html(response['change_percent'], response['symbol'], response['company_name'], response['price'],
                      market_status),
            parse_mode='HTML')


def make_html(percent, symbol, company_name, price, market_status):
    # price_desc = percent_calc(percent)
    # message = None
    message = f'<b>Company: </b> {company_name} \n<b>Symbol:</b> {symbol}\n<b>Change percent: </b>{percent_calc(percent)} \n<b>Price</b>:{price}\n<b>Market:</b>{market_status}'
    return message


def capture(update: Update, context: CallbackContext) -> None:
    option = webdriver.ChromeOptions()
    option.add_argument('headless')
    option.add_argument("--window-size=415,330")
    browser = webdriver.Chrome('/Users/nir.vaknin/Downloads/chromedriver 8',
                               options=option)
    browser.get(f'{base_url}/tradingview/')
    time.sleep(2)
    stocks = browser.find_element_by_id('chart')
    browser.save_screenshot('stocks.png')
    browser.set_window_size(stocks.size)
    stocks.screenshot('chart.png')


def percent_calc(percent):
    if isinstance(percent, type) or percent == "" or percent is None:
        return f'0'
    if percent == 0:
        return f'{percent}%'
    elif percent > 3:
        return f'{percent}%  &#128293;'
    elif 0 < percent < 3:
        return f'{percent}% &#128316;'
    elif 0 > percent > -3:
        return f'{percent}% &#9196;'
    elif percent < -3:
        return f'{percent}% &#128680;'


if __name__ == '__main__':
    token = os.getenv('TLGR')
    bot_persistence = PicklePersistence(filename='bot_stats.back')
    updater = Updater(token=token, persistence=bot_persistence)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('status', get_status))
    dispatcher.add_handler(CommandHandler('get', get_symbol))
    dispatcher.add_handler(CommandHandler('add', update_watchlist))
    dispatcher.add_handler(CommandHandler('remove', update_watchlist))
    dispatcher.add_handler(CallbackQueryHandler(search, pattern='stock'))
    dispatcher.add_handler(CallbackQueryHandler(get_symbol_keyboard, pattern='data'))
    dispatcher.add_handler(PrefixHandler('!', ['add', 'remove'], update_watchlist))
    dispatcher.add_handler(PrefixHandler('!', 'status', get_status))
    dispatcher.add_handler(CommandHandler('watchlist', watchlist))
    dispatcher.add_handler(CallbackQueryHandler(watchlist, pattern='back_watch'))
    dispatcher.add_handler(CommandHandler('capture', capture))
    updater.start_polling()
    updater.idle()
