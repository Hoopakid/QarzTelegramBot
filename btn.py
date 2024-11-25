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
    cancel = KeyboardButton(text='Bekor qildirish')
    borrowing = KeyboardButton(text="Qarzdorlik")
    final = ReplyKeyboardMarkup(keyboard=[[order], [stats], [cancel], [borrowing]], resize_keyboard=True)
    return final
