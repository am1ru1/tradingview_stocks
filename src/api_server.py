import re
import logging
import threading
import time
import signal

from src.pytradingview.TradingViewWebsocket import TradingViewWSS, search_for_symbol
from src.pytradingview.DBHelper import DBHelper
from flask import Flask, json, request

logger = logging.getLogger('FlaskApp')
log_format = logging.Formatter("%(asctime)s — %(name)s — %(levelname)s — %(funcName)s:%(lineno)d — %(message)s")
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler("Application.log")
console_handler.setFormatter(log_format)
file_handler.setFormatter(log_format)
logger.setLevel(logging.DEBUG)
logger.addHandler(console_handler)
logger.addHandler(file_handler)


def signal_handler(signum, frame):
    pytrading_api.disconnect()


api = Flask(__name__)
database = DBHelper()
exit_event = threading.Event()
signal.signal(signal.SIGINT, signal_handler)
pytrading_api = TradingViewWSS(database_connection=database)
pytrading_api.daemon = True
pytrading_api.start()


@api.route('/symbol/<ticker>', methods=['GET', 'POST', 'DELETE', 'PATCH'])
def get_symbol_info(ticker):
    logger.debug(f'Getting {ticker} info')
    if request.method == 'DELETE':
        if ticker in pytrading_api.symbol_list:
            pytrading_api.symbol_list.remove(ticker)
    if request.method == 'PATCH':
        response = search_for_symbol(ticker)
        if response:
            if response[0].get("prefix"):
                pytrading_api.add_symbols(f'{response[0].get("prefix")}:{response[0].get("symbol")}')
                data = database.get_symbol(f'{response[0].get("prefix")}:{response[0].get("symbol")}')
            else:
                pytrading_api.add_symbols(f'{response[0].get("exchange")}:{response[0].get("symbol")}')
                data = database.get_symbol(f'{response[0].get("exchange")}:{response[0].get("symbol")}')
            return json.dumps(data)
    if request.method == 'POST':
        response = search_for_symbol(ticker)
        if response:
            if response[0].get("prefix"):
                pytrading_api.add_symbols(f'{response[0].get("prefix")}:{response[0].get("symbol")}')
                pytrading_api.make_fast_query(f'{response[0].get("prefix")}:{response[0].get("symbol")}')
            else:
                pytrading_api.add_symbols(f'{response[0].get("exchange")}:{response[0].get("symbol")}')
                pytrading_api.make_fast_query(f'{response[0].get("exchange")}:{response[0].get("symbol")}')
            # time.sleep(5)
            return {
                'status': 'Success',
                'message': f'Added {ticker.upper()} to watchlist'
            }
        else:
            return {
                'status': 'Error',
                'message': f'Cant find {ticker}, wrong symbol?'
            }
    response = search_for_symbol(ticker)
    if "prefix" in response[0]:
        data = database.get_symbol(f'{response[0].get("prefix")}:{response[0].get("symbol")}')
    else:
        data = database.get_symbol(f'{response[0].get("exchange")}:{response[0].get("symbol")}')
    if 'Error' in data:
        logger.warning(f'Cant find {ticker}')
    else:
        logger.debug(f'Ticker info:{json.dumps(data)}')
    return json.dumps(data)


@api.route('/users/<user_id>/<ticker>', methods=['POST'])
def update_watchlist(user_id, ticker):
    if request.method == 'POST':
        if ',' in ticker:
            for symbol in ticker.split(','):
                database.update_watchlist(user_id=user_id, symbol=symbol)
        else:
            database.update_watchlist(user_id=user_id, symbol=ticker)
    return json.dumps("status: ok")


@api.route('/symbol/search/<key>', methods=['POST'])
def search_info(key):
    if key:
        list_info = search_for_symbol(key)
        if list_info:
            return json.dumps(list_info)
        else:
            return {
                "status": f'cant find {key}'
            }
    else:
        return {
            "status": "Empty key"
        }


@api.route('/users/<user_id>/', methods=['GET', 'POST'])
def check_watchlist(user_id):
    if request.method == 'POST':
        database.create_user_table()
    if request.method == 'GET':
        response = list()
        data = json.dumps(database.get_user_watchlist(user_id))
        clean_noises = re.sub('[^A-Za-z0-9:,]+', '', data)
        for symbol in clean_noises.split(','):
            response.append(database.get_symbol(symbol))
        return json.dumps(response)


if __name__ == '__main__':
    api.run(threaded=True, debug=True)
