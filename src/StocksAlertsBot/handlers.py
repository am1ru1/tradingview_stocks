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
