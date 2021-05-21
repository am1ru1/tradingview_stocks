import sqlite3
import os


class DBHelper(object):

    def __init__(self):
        self.con = sqlite3.connect(
            '/Users/nir.vaknin/Documents/nir/python/tradingview_crawl/resources/symbols_data.sql',
            check_same_thread=False)
        # self.con.row_factory = sqlite3.Row
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
        user_watchlist = self.get_user_watchlist(user_id)
        if user_watchlist:
            watchlist = list(user_watchlist)
            if symbol not in user_watchlist[0]:
                watchlist.append(symbol)
                # user_watchlist[0] = user_watchlist[0] + symbol
        try:
            # if user_watchlist:
            if watchlist:
                query = """ UPDATE users
                            SET symbols = ?
                            WHERE user_id = ?"""
                self.cur.execute(query, [str(watchlist), user_id])
            else:
                query = """INSERT INTO users(user_id, symbols)
                            values(?, ?)"""
                self.cur.execute(query, [user_id, symbol])
            self.con.commit()
        except sqlite3.Error as error:
            raise Exception(error)

    def get_user_watchlist(self, user_id):
        self.cur.execute(""" SELECT symbols from users
                    WHERE user_id = ?""", [user_id])
        data = self.cur.fetchone()
        return data

    def create_symbol_table(self):
        self.cur.execute("""CREATE TABLE IF NOT EXISTS symbols(
                               symbol TEXT,
                               percent_chg REAL,
                               price REAL);
                        """)
        self.con.commit()

    def update_symbol(self, symbol, percent, price):
        data = self.get_symbol(symbol)
        if data:
            query = """ UPDATE symbols
                        SET percent_chg = ?,
                            price = ?
                        WHERE symbol = ?
                        """
            self.cur.execute(query, [percent, price, symbol])
        else:
            query = """
                    INSERT INTO symbols(symbol, percent_chg , price)
                    values (?, ?, ?);
                  """
            self.cur.execute(query, [symbol, percent, price])
        self.con.commit()

    def get_symbol(self, symbol):
        self.cur.execute("""
                         SELECT symbol, percent_chg, price
                         FROM symbols
                         WHERE symbol = ? """, [symbol])
        data = self.cur.fetchall()
        return data
