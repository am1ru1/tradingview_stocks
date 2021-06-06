from telegram import InlineKeyboardMarkup, InlineKeyboardButton


def menu_keyboard() -> InlineKeyboardMarkup:
    """
    Create search menu keyboard
    :return:
    Return stocks / crypto keyboard
    """
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(text="Stocks",
                                                           callback_data="stock",
                                                           )],
                                     [InlineKeyboardButton(text="ETF",
                                                           callback_data="etf",
                                                           )],
                                     [InlineKeyboardButton(text="Crypto",
                                                           callback_data="crypto",
                                                           )]
                                     ]
                                    )
    return keyboard


def watchlist_keyboard(watchlist) -> InlineKeyboardMarkup:
    """
    Create watchlist buttons menu
    :return:
    Return watchlist keyboard
    """
    keyword_list = list()
    index = 0
    for symbol in watchlist:
        keyword_list.append(InlineKeyboardButton(text=symbol, callback_data=f"data_{index}"))
        index = index + 1
    keyboard = InlineKeyboardMarkup([keyword_list])
    return keyboard
