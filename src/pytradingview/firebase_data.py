import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate('/Users/nir.vaknin/Documents/nir/python/tradingview_crawl/resources/stocks-c5bed-71f5c3ad4598.json')
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()


class Stock(object):

    def __init__(self, symbol, company_name, price, change_percent):
        self.symbol = symbol
        self.company_name = company_name
        self.price = price
        self.change_percent = change_percent

    @staticmethod
    def from_dict(source):
        stock = Stock(symbol=source['symbol'], company_name=source['company_name'], price=source['price'],
                      change_percent=source['change_percent'])
        return stock

    def to_dict(self):
        dest = {
            'symbol': self.symbol,
            'company_name': self.company_name,
            'price': self.price,
            'change_percent': self.change_percent
        }
        return dest

    def __repr__(self):
        return (f'Stock(\
                symbol={self.symbol}, \
                company_name={self.company_name}, \
                price={self.price}, \
                change_percent={self.change_percent}\
                )'
                )


def set_new_symbol(symbol_data: Stock) -> bool:
    """
    symbol_data structure should include:
    symbol - symbol of of the stock
    price - price of the stock
    company name - the name of the company
    change - the change in percent
    :param symbol_data:
    :return: True for success inserting new data
    """
    if db is None:
        return False
    if symbol_data:
        new_data = db.collection('stocks').document(symbol_data.symbol)
        new_data.set(symbol_data.to_dict())
        return True


def update_symbol(symbol_data: Stock) -> bool:
    if db is None:
        return False
    if symbol_data:
        update_data = db.collection('stocks').document(symbol_data.symbol)
        if update_data.get().exists:
            if symbol_data.company_name:
                update_data.update(symbol_data.to_dict())
            else:
                update_data.update({
                    'price': symbol_data.price,
                    'change_percent': symbol_data.change_percent,
                })
        else:
            return set_new_symbol(symbol_data)
        return True


def get_symbol_data(symbol_name) -> Stock:
    if symbol_name:
        data = db.collection('stocks').document(symbol_name)
        if data.get().exists:
            return Stock.from_dict(data.get().to_dict())


def get_all_symbols():
    symbols = db.collection('stocks').stream()
    list_symbols = []
    for symbol in symbols:
        print(f'{symbol.id} => {symbol.to_dict()}')
        list_symbols.append(symbol.id)
    return list_symbols



# new_data = db.collection(u'stocks').document('aapl')
# new_data.set({
#     'company_name': "Apple Company",
#     'percent_chg': 0,
#     'price': 100.0,
#     'symbol': "AAPL"
# })
#
# new_data = db.collection(u'stocks').document('goog')
# new_data.set({
#     'company_name': "Google Company",
#     'percent_chg': 0,
#     'price': 2000.0,
#     'symbol': "GOOG"
# })
#
# read_data = db.collection(u'stocks').document('goog')
# data = read_data.get()
# if data.exists:
#     print(json.dumps(data.to_dict()))
#
# read_data.update({
#     'price': 2001.32
# })
#
# data = read_data.get()
# if data.exists:
#     print(json.dumps(data.to_dict()))
#
# #
# # for symbol in symbols:
# #     print(f'{symbol.to_dict()["price"]}')

#
# test_data = Stock('NKE', 'Nike Inc.', 134.1, -0.2)
# set_new_symbol(test_data)
# test_data.price = 134
# test_data.change_percent = -0.23
# update_symbol(test_data)