from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup


def payment_option():
    card = KeyboardButton(text="Karta orqali")
    borrow = KeyboardButton(text="Qarzga berish")
    cash = KeyboardButton(text="Naqd to'lov")
    final = ReplyKeyboardMarkup(keyboard=[[card], [borrow], [cash]], one_time_keyboard=True, resize_keyboard=True)
    return final


def serving_options():
    order = KeyboardButton(text="Zakaz berish")
    stats = KeyboardButton(text="Statistika")
    products = KeyboardButton(text="Mahsulotlar")
    cancel = KeyboardButton(text='Bekor qildirish')
    borrowing = KeyboardButton(text="Qarzdorlik")
    edit_order = KeyboardButton(text="Zakazni tahrirlash")
    final = ReplyKeyboardMarkup(keyboard=[[order], [stats, cancel], [borrowing, products], [edit_order]],
                                resize_keyboard=True, one_time_keyboard=True)
    return final


def product_editing():
    add_product = KeyboardButton(text="➕ Mahsulot qo'shish")
    remove_product = KeyboardButton(text="➖ Mahsulotni o'chirish")
    final = ReplyKeyboardMarkup(keyboard=[[add_product], [remove_product]], resize_keyboard=True,
                                one_time_keyboard=True)
    return final


def inline_qarzdorlik_button():
    cancel_product = InlineKeyboardButton(text="Qarzdorlikni bekor qildirish", callback_data="cancel_borrowing")
    decrease_borrowing = InlineKeyboardButton(text="Qarzdorlikni kamaytirish", callback_data="decrease_borrowing")
    final = InlineKeyboardMarkup(inline_keyboard=[[cancel_product], [decrease_borrowing]])
    return final


def inline_edit_button():
    with_id = KeyboardButton(text="ID orqali")
    with_name = KeyboardButton(text="Zakaz orqali")
    final = ReplyKeyboardMarkup(keyboard=[[with_id, with_name]], resize_keyboard=True, one_time_keyboard=True)
    return final
