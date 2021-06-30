import threading
import json
import random
import string
import re
import requests
import pandas as pd
from websocket import create_connection
# from DBHelper import DBHelper
#
# try:
#     import thread
# except ImportError:
#     import _thread as thread
import time


class TradingViewWSS(threading.Thread):

    def __init__(self, database_connection):
        # websocket.enableTrace(True)
        threading.Thread.__init__(self)
        self.db = database_connection
        self.headers = json.dumps({
            'Connection': 'upgrade',
            'Host': 'data.tradingview.com',
            'Origin': 'https://data.tradingview.com',
            'Cache-Control': 'no-cache',
            'Upgrade': 'websocket',
            'Sec-WebSocket-Extensions': 'permessage-deflate; client_max_window_bits',
            'Sec-WebSocket-Key': '1H41q97V8BbMKUq0knV1UA==',
            'Sec-WebSocket-Version': '13',
            'User-Agent': 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36 Edg/83.0.478.56',
            'Pragma': 'no-cache',
            'Upgrade': 'websocket'
        })
        self.market_status = self.get_market_status()
        self.symbol_list = list()
        self.ws = create_connection('wss://data.tradingview.com/socket.io/websocket', headers=self.headers)
        self.session = self.generate_session()
        self.symbol_list.append(self.session)
        print(f'Session: {self.session}')
        self.chart_session = self.generate_chart_session()
        print(f'Chart session: {self.chart_session}')
        self.__run_first_request()
        # self.make_fast_query()

    def run(self) -> None:
        a = ""
        while True:
            try:
                # if not self.ws.connected:
                #     self.ws = create_connection('wss://data.tradingview.com/socket.io/websocket', headers=self.headers)
                time.sleep(1)
                response = self.ws.recv()
                print(response)
                if "qsd" in response or "du" in response:
                    recv_message = response.split('~')
                    print(f'JSON:\n{recv_message[len(recv_message) - 1]}')
                    for message in recv_message:
                        if "qsd" not in message:
                            continue
                        recv_message = json.loads(message)
                        try:
                            self.parse_json(pd.DataFrame(json.loads(message))['p'][1])
                        except Exception as error:
                            print(f"ERROR! {error}")
                pattern = re.compile("~m~\d+~m~~h~\d+$")
                if pattern.match(response):
                    recv_message = self.ws.recv()
                    self.ws.send(response)
                    print("\nGetting new message...\n " + str(response) + "\n\n")
                # a = a + response + "\n"
            except Exception as error:
                print(error)
                # self.ws.close()
                break

    def parse_json(self, sec_data):
        print(f'#### DATA ####\n{sec_data}\n#### END DATA ####')
        if sec_data["s"] == "ok" and "rtc" in sec_data["v"] or "rchp" in sec_data[
            "v"] and self.market_status == 'pre-market':
            print(f'RealTime')
            print(f'Symbol: {sec_data["n"]}\nPrice: {sec_data["v"]["rtc"]}\nChange: {sec_data["v"]["rchp"]}')
            if sec_data["v"]["rchp"] == 0:
                if 'local_description' in sec_data["v"]:
                    self.db.update_symbol(sec_data["n"], sec_data["v"]["ch"], sec_data["v"]["lp"],
                                          sec_data["v"]['local_description'])
                else:
                    self.db.update_symbol(sec_data["n"], sec_data["v"]["ch"], sec_data["v"]["lp"],
                                          None)
            else:
                if 'local_description' in sec_data["v"]:
                    self.db.update_symbol(sec_data["n"], sec_data["v"]["rchp"], sec_data["v"]["rtc"],
                                          sec_data["v"]['local_description'])
                else:
                    self.db.update_symbol(sec_data["n"], sec_data["v"]["rchp"], sec_data["v"]["rtc"],
                                          None)
        elif "lp" in sec_data["v"] and "ch" in sec_data["v"]:
            print("Non-Real")
            if "chp" in sec_data["v"]:
                print(f'Symbol: {sec_data["n"]}\nPrice: {sec_data["v"]["lp"]}\nChange: {sec_data["v"]["chp"]}')
                if 'local_description' in sec_data["v"]:
                    self.db.update_symbol(sec_data["n"], sec_data["v"]["chp"], sec_data["v"]["lp"], None)
                else:
                    self.db.update_symbol(sec_data["n"], sec_data["v"]["chp"], sec_data["v"]["lp"], None)
            else:
                print(f'Symbol: {sec_data["n"]}\nPrice: {sec_data["v"]["lp"]}\nChange: {sec_data["v"]["ch"]}')
                self.db.update_symbol(sec_data["n"], sec_data["v"]["ch"], sec_data["v"]["lp"], None)
        else:
            print(f"Cant find parameters at the JSON file.\n{sec_data}]n")

    def __run_first_request(self):
        self.ws.send(self.generate_json("set_auth_token", ["unauthorized_user_token"]))
        self.ws.send(self.generate_json("chart_create_session", [self.chart_session, "disable_statistics"]))
        self.ws.send(self.generate_json("quote_create_session", [self.session]))
        self.ws.send(self.generate_json("quote_set_fields",
                                        [self.session, "ch", "chp", "current_session", "description",
                                         "local_description", "language",
                                         "exchange",
                                         "fractional", "is_tradable", "lp", "lp_time", "minmov", "minmove2",
                                         "original_name", "pricescale",
                                         "pro_name", "short_name", "type", "update_mode", "volume", "currency_code",
                                         "rchp", "rtc"]))
        # self.ws.send(
        #     self.generate_json("quote_add_symbols", [self.session, "NYSE:TGT", {"flags": ['force_permission']}]))
        first_scan = self.db.get_all_symbols()
        first_scan = json.dumps(first_scan)
        clean_noises = re.sub('[^A-Za-z0-9:,.]+', '', first_scan)
        if clean_noises:
            cleaned_data = clean_noises.split(",")
            for clean in cleaned_data:
                self.add_symbols(clean)
        self.ws.send(self.generate_json("create_series",
                                        [self.chart_session, "s" + "5", "s" + "5", "symbol_" + "5", "5", 100]))
        # self.ws.send(self.generate_json("quote_fast_symbols", [self.session, "NYSE:TGT"]))
        self.ws.send(self.generate_json("create_study",
                                        [self.chart_session, "st" + "5", "st" + "5", "s" + "5",
                                         "Volume@tv-basicstudies-118",
                                         {"length": 20, "col_prev_close": "false"}]))
        self.ws.send(self.generate_json("quote_hibernate_all", [self.session]))

    def add_symbols(self, symbol):
        if symbol not in self.symbol_list:
            self.symbol_list.append(symbol)
            self.ws.send(
                self.generate_json("quote_add_symbols", [self.session, symbol, {"flags": ["force_permission"]}]))

    def make_fast_query(self, symbol=None):
        if self.ws.connected:
            if symbol:
                self.ws.send((
                    self.generate_json("quote_fast_symbols", [self.session, symbol])
                ))
            else:
                self.ws.send((self.generate_json("quote_fast_symbols", self.symbol_list)))

    def get_market_status(self):
        """
        Getting the market status if its pre-market / market / post-market or close
        :return: return market status
        """
        url_request = "https://scanner.tradingview.com/america/scan"
        json_data = json.dumps({
            "columns": [
                "current_session"
            ],
            "range": [
                0,
                1
            ],
            "symbols": {
                "tickers": [
                ]
            }
        })
        market_status = self.__make_request('GET', url_request, data=json_data)["data"][0]["d"][0]
        if market_status == "market":
            return "market"
        elif market_status == "pre_market":
            return "pre-market"
        elif market_status == 'out_of_session':
            return "close"

    def disconnect(self):
        if self.ws.connected:
            self.ws.close()

    @staticmethod
    def __make_request(method, url, data=None):
        """
            Making request to url and return json response.
            :arg method: can be GET / POST / PUT
                 url: is the url path
                 data: if want to send json request
            :return: return json if there is response
        """
        try:
            response = requests.request(method=method, url=url, data=data)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 400:
                raise Exception("Json parse error")
        except requests.exceptions.RequestException:
            return None

    @staticmethod
    def generate_session():
        random_string = ''.join(random.choice(string.ascii_lowercase) for i in range(12))
        return f"qs_{random_string}"

    @staticmethod
    def generate_chart_session():
        random_string = ''.join(random.choice(string.ascii_lowercase) for i in range(12))
        return f"cs_{random_string}"

    def generate_json(self, m, p):
        json_response = json.dumps({
            "m": m,
            "p": p
        }, separators=(',', ':'))
        print(f'### DEBUG ###\n{json_response}')
        return self.prepend_header(json_response)

    @staticmethod
    def prepend_header(st):
        return f'~m~{str(len(st))}~m~{st}'
        # return "~m~" + str(len(st)) + "~m~" + st


def search_for_symbol(symbol):
    exchange_list = ['NASDAQ', 'NYSE', 'EURONEXT PARIS', 'LSIN', 'NYSE ARCA & MKT']
    try:
        response = requests.get(url=f'https://symbol-search.tradingview.com/symbol_search/?text={symbol}').json()
        allowed_symbols = dict()
        index = 0
        for company in response:
            if company.get('exchange') in exchange_list and company.get(
                    'type') == 'stock' and symbol.upper() == company.get('symbol'):
                allowed_symbols[index] = company
                index = index + 1
        return allowed_symbols
    except requests.exceptions.HTTPError as error:
        raise Exception(error)


def on_message(ws, message):
    print(f'### Got new message:###\n{message}\n')


def on_error(ws, error):
    print(f'### Got error: ####\n{error}\n')


def on_close(ws):
    print("### closed ###")

#
# trading = TradingViewWSS()
# trading.start()
# time.sleep(10)
# trading.add_symbols("NYSE:DIS")
# trading.add_symbols("NYSE:CAT")
# trading.add_symbols("NASDAQ:AAPL")
# time.sleep(5)
# trading.make_fast_query()
# print(trading.get_market_status())
# company = search_for_symbol('arkg')
# print(company)
# print(f'Total buttons:\n{len(company)}')
