import json
import re
import sqlite3
import logging

logger = logging.getLogger('DatabaseHandler')
log_format = logging.Formatter("%(asctime)s — %(name)s — %(levelname)s — %(funcName)s:%(lineno)d — %(message)s")
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler("Application.log")
console_handler.setFormatter(log_format)
file_handler.setFormatter(log_format)
logger.setLevel(logging.DEBUG)
logger.addHandler(console_handler)
logger.addHandler(file_handler)


class DBHelper(object):

    def __init__(self):
        logger.info('Init database')
        self.con = sqlite3.connect(
            '/Users/nir.vaknin/Documents/nir/python/tradingview_crawl/resources/symbols_data.sql',
            check_same_thread=False)
        self.cur = self.con.cursor()
        self.create_symbol_table()
        self.create_user_table()

    def create_user_table(self):
        self.cur.execute("""CREATE TABLE IF NOT EXISTS users(
                                       user_id TEXT,
                                       symbols TEXT);
                                """)
        self.con.commit()

    def update_watchlist(self, user_id, symbol):
        watchlist = list()
        user_watchlist = self.get_user_watchlist(user_id)
        if user_watchlist:
            watchlist = list(user_watchlist)
            if symbol not in user_watchlist[0]:
                user_watchlist = user_watchlist + (symbol,)
                watchlist = list(user_watchlist)
        try:
            if watchlist:
                query = """ UPDATE users
                            SET symbols = ?
                            WHERE user_id = ?"""
                self.cur.execute(query, [str(watchlist), user_id])
            else:
                query = """INSERT INTO users(user_id, symbols)
                            values(?, ?)"""
                self.cur.execute(query, [user_id, str(symbol.upper())])
            self.con.commit()
        except sqlite3.Error as error:
            raise Exception(error)

    def get_user_watchlist(self, user_id):
        logger.debug(f'Getting {user_id} watchlist data')
        self.cur.execute(""" SELECT symbols from users
                    WHERE user_id = ?""", [user_id])
        data = self.cur.fetchone()
        return data

    def create_symbol_table(self):
        self.cur.execute("""CREATE TABLE IF NOT EXISTS symbols(
                               symbol TEXT,
                               company_name TEXT,
                               percent_chg REAL,
                               price REAL);
                        """)
        self.con.commit()

    def update_symbol(self, symbol, percent, price, company):
        data = self.get_symbol(symbol)
        if 'Error' in data:
            query = """
                    INSERT INTO symbols(symbol, percent_chg , price, company_name)
                    values (?, ?, ?, ?);
                  """
            self.cur.execute(query, [symbol, percent, price, company])
        else:
            query = """ UPDATE symbols
                        SET percent_chg = ?,
                            price = ?
                        WHERE symbol = ?
                        """
            self.cur.execute(query, [percent, price, symbol])
        self.con.commit()
        logger.debug(f'Update {symbol} info')

    def get_symbol(self, symbol):
        self.cur.execute("""
                         SELECT symbol, percent_chg, price, company_name
                         FROM symbols
                         WHERE symbol = ? """, [symbol])
        data = self.cur.fetchall()
        logger.debug(f'Getting {symbol} info from DB')
        return self.__make_data_beautiful(data)

    def get_all_symbols(self):
        self.cur.execute("""
                                 SELECT symbol
                                 FROM symbols """)
        data = self.cur.fetchall()
        return data

    @staticmethod
    def __make_data_beautiful(data):
        if not data:
            return {'Error': 'Not found'}
        data = json.dumps(data)
        beautiful_data = dict()
        clean_noises = re.sub('[^A-Za-z0-9:,.-]+', ' ', data)
        cleaned_data = clean_noises.split(",")
        for symbol in cleaned_data:
            beautiful_data = {
                'name': cleaned_data[0].upper(),
                'company': cleaned_data[3],
                'percent_change': cleaned_data[1],
                'price': cleaned_data[2]
            }
        return beautiful_data
