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
    temp_list = list()
    index = 0
    location = 0
    for symbol in watchlist:
        if index % 4 == 0:
            temp_list.append(InlineKeyboardButton(text=symbol, callback_data=f'data_{index}'))
            keyword_list.append(temp_list)
            temp_list = list()
        else:
            temp_list.append(InlineKeyboardButton(text=symbol, callback_data=f'data_{index}'))
        index = index + 1
    if len(temp_list) < 4:
        keyword_list.append(temp_list)
    keyword_list.append([InlineKeyboardButton(text='Add', callback_data='add', switch_inline_query='add')])
    keyboard = InlineKeyboardMarkup(keyword_list)
    return keyboard


def back_to_watchlist():
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(text="Back",
                                                           callback_data="back_watch",
                                                           )],
                                     ]
                                    )
    return keyboard
