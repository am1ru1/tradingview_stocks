import re
import logging
import threading
import time
import signal

from src.pytradingview.TradingViewWebsocket import TradingViewWSS
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
pytrading_api.join()


@api.route('/symbol/<ticker>', methods=['GET', 'POST'])
def get_symbol_info(ticker):
    logger.debug(f'Getting {ticker} info')
    if request.method == 'POST':
        pytrading_api.add_symbols(ticker)
        time.sleep(5)
        pytrading_api.make_fast_query()
        return {
            'action': 'started..'
        }
    data = database.get_symbol(ticker)
    if 'Error' in data:
        logger.warning(f'Cant find {ticker}')
    else:
        logger.debug(f'Ticker info:{json.dumps(data)}')
    return json.dumps(data)


@api.route('/users/<user_id>/<ticker>', methods=['POST'])
def update_watchlist(user_id, ticker):
    if request.method == 'POST':
        database.update_watchlist(user_id=user_id, symbol=ticker)
    return json.dumps("status: ok")


@api.route('/users/<user_id>/', methods=['GET'])
def check_watchlist(user_id):
    if request.method == 'GET':
        response = list()
        data = json.dumps(database.get_user_watchlist(user_id))
        clean_noises = re.sub('[^A-Za-z0-9:,]+', '', data)
        for symbol in clean_noises.split(','):
            response.append(database.get_symbol(symbol))
        return json.dumps(response)


if __name__ == '__main__':
    api.run(threaded=True, debug=True)
