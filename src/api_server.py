import re

from src.pytradingview.pyTrading import PyTrading
from src.pytradingview.DBHelper import DBHelper
from flask import Flask, json, request

api = Flask(__name__)
pytrading_api = PyTrading()

database = DBHelper()


@api.route('/symbol/<ticker>', methods=['GET'])
def get_symbol_info(ticker):
    data = database.get_symbol(ticker)
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
