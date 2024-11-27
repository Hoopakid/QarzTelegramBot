import os
import asyncio
import aiohttp
import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from state import ProductDetailState
from analyze import insert_data, read_qarz_data, change_status_qarz, get_products, read_all_data, change_status_otkaz, get_analyzed_information, insert_data_to_products, delete_data_from_products, get_sorted_data
from btn import payment_option, serving_options, product_editing

load_dotenv()

BOT_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_CHAT_ID = os.environ.get('ADMIN_CHAT_ID')

user_otkaz_selection = {}
user_qarz_selection = {}
user_zakaz_selection = {}
user_product_selection = {}

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

def create_inline_keyboard(selected_products):
    keyboard = []
    keys = []
    products = get_products()

    for index, product in enumerate(products, start=1):
        status = "✅" if product in selected_products else "➕"
        keys.append(InlineKeyboardButton(text=f"{status} {product}", callback_data=f"toggle_{product}"))
        
        if index % 2 == 0:
            keyboard.append(keys)
            keys = []

    if keys:
        keyboard.append(keys)

    keyboard.append([
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data='confirm'),
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data='cancel')
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def create_otkaz_keyboard(selected_products):
    otkaz_products = [f"{product['product_id']} - {product['client_full_name']}" for product in read_all_data()['data']]
    keyboard = []
    keys = []

    for index, product in enumerate(otkaz_products, start=1):
        status = "✅" if product in selected_products else "➕"
        keys.append(InlineKeyboardButton(text=f"{status} {product}", callback_data=f"otkaz_{product}"))
        keyboard.append(keys)
        keys = []
    
    keyboard.append([
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data='confirm_otkaz'),
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data='cancel_otkaz')
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def create_qarz_keyboard(selected_products):
    qarz_products = [f"{product['product_id']} - {product['client_full_name']}" for product in read_qarz_data()['data']]
    keyboard = []
    keys = []

    for index, product in enumerate(qarz_products, start=1):
        status = "✅" if product in selected_products else "➕"
        keys.append(InlineKeyboardButton(text=f"{status} {product}", callback_data=f"qarz_{product}"))
        keyboard.append(keys)
        keys = []
    
    keyboard.append([
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data='confirm_qarz'),
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data='cancel_qarz')
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def create_products_keyboard(selected_products):
    products = get_products()
    keyboard = []
    keys = []

    for product in products:
        status = "✅" if product in selected_products else "➕"
        keys.append(InlineKeyboardButton(text=f"{status} {product}", callback_data=f"mahsulot_{product}"))
        keyboard.append(keys)
        keys = []
    
    keyboard.append([
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data='confirm_mahsulot'),
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data='cancel_mahsulot')
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def create_confrim_cancel(text1, text2, callback1, callback2):
    confirm = InlineKeyboardButton(text=text1, callback_data=callback1)
    cancel = InlineKeyboardButton(text=text2, callback_data=callback2)
    final = InlineKeyboardMarkup(inline_keyboard=[[confirm], [cancel]])
    return final    


def confirm_cancel_qarz():
    confirm = InlineKeyboardButton(text="❎ Zakazni qarzdorlikdan olib tashlash", callback_data="conf_qarz")
    cancel = InlineKeyboardButton(text='↩️ Ortga qaytish', callback_data="canc_qarz")
    final = InlineKeyboardMarkup(inline_keyboard=[[confirm], [cancel]])
    return final

async def send_message(message: str):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': ADMIN_CHAT_ID,
        'text': message
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            if response.status == 200:
                return {'success': True}
            else:
                return {'success': False}
            
def generate_custom_calendar(month: int = None, year: int = None):
    now = datetime.datetime.now()
    if not month:
        month = now.month
    if not year:
        year = now.year

    first_day = datetime.datetime(year, month, 1)
    last_day = (first_day + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)

    inline_keyboard = []

    inline_keyboard.append([
        InlineKeyboardButton(text="1 Kunlik", callback_data="day:daily"),
        InlineKeyboardButton(text="1 Haftalik", callback_data="day:weekly"),
        InlineKeyboardButton(text="1 Oylik", callback_data="day:monthly"),
    ])

    days_row = []
    for day in range(1, last_day.day + 1):
        days_row.append(InlineKeyboardButton(
            text=str(day),
            callback_data=f"day:{year}-{month:02}-{day:02}"
        ))
        if len(days_row) == 7:
            inline_keyboard.append(days_row)
            days_row = []
    if days_row:
        inline_keyboard.append(days_row)

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)



@dp.message(CommandStart())
async def start_bot(message: Message):
    await message.answer('Assalomu alaykum botimizga xush kelibsiz')
    await message.answer('Kerakli xizmatni tanlang', reply_markup=serving_options())

# Zakaz berish section
@dp.message(lambda msg: msg.text == "Zakaz berish")
async def order_section(message: Message):
    user_zakaz_selection[message.chat.id] = []
    keyboard = create_inline_keyboard(user_zakaz_selection[message.chat.id])
    await message.answer("Mahsulotlarni tanlang", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data.startswith("toggle_"))
async def toggle_product(callback_query: types.CallbackQuery):
    user_id = callback_query.message.chat.id
    product_name = callback_query.data.split("_", 1)[1]

    if product_name in user_zakaz_selection[user_id]:
        user_zakaz_selection[user_id].remove(product_name)
    else:
        user_zakaz_selection[user_id].append(product_name)
    
    keyboard = create_inline_keyboard(user_zakaz_selection[user_id])
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)

@dp.callback_query(lambda c: c.data == "confirm")
async def confirm_selection(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.delete()
    user_id = callback_query.message.chat.id
    selected_products = user_zakaz_selection.get(user_id, [])
    if not selected_products:
        await callback_query.answer("Zakaz tanlanmadi!", show_alert=True)
        await callback_query.message.answer('Kerakli xizmatni tanlang', reply_markup=serving_options())
        return
    
    await callback_query.message.answer(f"Tanlangan zakazlar: {', '.join(selected_products)}")
    await state.update_data({'selected_products': selected_products})
    await handler(callback_query.message, state)

@dp.callback_query(lambda c: c.data == 'cancel')
async def cancel_selection(callback_query: types.CallbackQuery):
    await callback_query.answer("Bekor qilindi", show_alert=True)
    await callback_query.message.answer("Kerakli xizmatni tanlang", reply_markup=serving_options())

async def handler(message: Message, state: FSMContext):
    products = await state.get_data()
    selected_products = products.get('selected_products', [])
    
    await message.answer(f"{selected_products[0]} dan nechta buyurtma bermoqchisiz")
    current_product = selected_products[0]
    selected_products.remove(current_product)

    await state.update_data({'current_product': current_product,'selected_products': selected_products})
    await state.set_state(ProductDetailState.product_count)

@dp.message(ProductDetailState.product_count)
async def receive_product_count(message: Message, state: FSMContext):
    try:
        product_count = int(message.text)
        if product_count <= 0:
            raise ValueError("Product count must be positive.")

        await state.update_data({'product_count': product_count})
        await message.answer("Zakaz uchun narx yuboring")
        await state.set_state(ProductDetailState.product_price)
    except ValueError:
        await message.answer("Iltimos, zakaz sonini son ko'rinishida yuboring.")
        products = await state.get_data()
        current_product = products.get('current_product')
        await message.answer(f"{current_product} dan nechta buyurtma bermoqchisiz")
        await state.set_state(ProductDetailState.product_count)

@dp.message(ProductDetailState.product_price)
async def receive_product_price(message: Message, state: FSMContext):
    try:
        product_price = int(message.text)
        if product_price <= 0:
            raise ValueError("Mahsulot narxi musbat bo'lishi kerak.")

        await state.update_data({'product_price': product_price})
        await message.answer("Zakaz uchun izoh yuboring")
        await state.set_state(ProductDetailState.product_description)

    except ValueError:
        await message.answer("Iltimos, zakaz narxini musbat son ko'rinishida yuboring.")

@dp.message(ProductDetailState.product_description)
async def receive_product_description(message: Message, state: FSMContext):
    data = await state.get_data()
    current_product = data.get('current_product')
    product_count = data.get('product_count')
    product_price = data.get('product_price')

    product_entry = {
        'name': current_product,
        'count': product_count,
        'price': product_price,
        'decription': message.text
    }

    products = data.get('products', [])
    products.append(product_entry)
    await state.update_data({'products': products})

    selected_products = data.get('selected_products', [])
    if selected_products:
        await handler(message, state)
    else:
        await message.answer("Ism familiyangizni yuboring")
        await state.set_state(ProductDetailState.client_full_name)

@dp.message(ProductDetailState.client_full_name)
async def receive_client_full_name(message: Message, state: FSMContext):
    try:
        client_full_name = message.text
        await state.update_data({'client_full_name': client_full_name})
        await message.answer('Telefon raqamingizni yuboring (+998123456789)')
        await state.set_state(ProductDetailState.client_phone_number)
    except Exception:
        await message.answer("Kechirasiz, dasturda biror xatolik yuz berdi qaytadan urinib ko'ring")
        await state.set_state(ProductDetailState.client_full_name)

@dp.message(ProductDetailState.client_phone_number)
async def receive_client_phone_number(message: Message, state: FSMContext):
    try:
        contact_number = message.text
        if len(contact_number) == 13 and contact_number.startswith('+998'):
            await state.update_data({'client_phone_number': contact_number})
            payment = payment_option()
            await message.answer("To'lov turini tanlang", reply_markup=payment)
            await state.set_state(ProductDetailState.payment_choice)
        else:
            await message.answer("Iltimos, telefon raqamni shu formatda yuboring (+998123456789)")
            await state.set_state(ProductDetailState.client_phone_number)
    except Exception:
        await message.answer("Kechirasiz, dasturda biror xatolik yuz berdi qaytadan urinib ko'ring")
        await state.set_state(ProductDetailState.client_phone_number)

@dp.message(ProductDetailState.payment_choice)
async def recieve_payment_choice(message: Message, state: FSMContext):
    valid_choices = ["Karta orqali", "Qarzga berish", "Naqd to'lov"]

    try:
        if message.text in valid_choices:
            await state.update_data({'payment_choice': message.text})
            data = await state.get_data()
        
            combined_product_name = ", ".join([p['name'] for p in data['products']])
            combined_product_count = ", ".join(str(p['count']) for p in data['products'])
            combined_product_price = ", ".join(str(p['price'] * p['count']) for p in data['products'])
            
            temp = {
                "product_name": combined_product_name,
                "product_count": combined_product_count,
                "product_price": combined_product_price,
                "client_phone_number": data["client_phone_number"],
                "client_full_name": data["client_full_name"],
                "payment_choice": data["payment_choice"]
            }
            success = insert_data(temp)
            if success['success'] is True:
                returned_id = success['returned_id']
                current_date = datetime.datetime.now().date()
                returning_message = f"#Zakaz_{returned_id}\n{current_date}\n"

                for i in data['products']:
                
                    returning_message += f"\n📦 Mahsulot: {i['name']}\n🔢 Soni: {i['count']} ta\n💰 Narxi: {i['price']}\n💰Umumiy narx: {i['price'] * i['count']}\n📝 Izoh: {i['decription']}\n"
                
                returning_message += f"\n💳 To'lov turi: {data['payment_choice']}\n📱Telefon raqam: {data['client_phone_number']}\n🤵 Mijoz: {data['client_full_name']}" 
                await send_message(returning_message)
                await message.answer('Mahsulot muvaffaqiyatli qabul qilindi')
                await message.answer("Kerakli xizmatni tanlang", reply_markup=serving_options())
                await state.clear()
            else:
                await message.answer("Kechirasiz, dasturda biror xatolik yuz berdi qaytadan urinib ko'ring")
                await state.clear()
                await message.answer("Kerakli xizmatni tanlang", reply_markup=serving_options())
        else:
            await message.answer("Iltimos, quyidagi variantlardan birini tanlang:", reply_markup=payment_option())
            await state.set_state(ProductDetailState.payment_choice)

    except Exception as e:
        print(f"{e}")
        await message.answer("Kechirasiz, dasturda biror xatolik yuz berdi qaytadan urinib ko'ring", reply_markup=payment_option())
        await state.set_state(ProductDetailState.payment_choice)

# @dp.message(ProductDetailState.product_description)
# async def receive_product_description(message: Message, state: FSMContext):
#     try:
#         await state.update_data({'product_description': message.text})
#         data = await state.get_data()
        
#         combined_product_name = ", ".join([p['name'] for p in data['products']])
#         combined_product_count = ", ".join(str(p['count']) for p in data['products'])
#         combined_product_price = ", ".join(str(p['price'] * p['count']) for p in data['products'])

#         temp = {
#             "product_name": combined_product_name,
#             "product_count": combined_product_count,
#             "product_price": combined_product_price,
#             "client_phone_number": data["client_phone_number"],
#             "client_full_name": data["client_full_name"],
#             "payment_choice": data["payment_choice"],
#             "product_description": data["product_description"]
#         }
#         success = insert_data(temp)
#         if success['success'] is True:
#             returned_id = success['returned_id']
#             current_date = datetime.datetime.now().date()
#             returning_message = f"#Zakaz_{returned_id}\n{current_date}\n"
            
#             for i in data['products']:
            
#                 returning_message += f"\n📦 Mahsulot: {i['name']}\n🔢 Soni: {i['count']} ta\n💰 Narxi: {i['price']}\n💰Umumiy narx: {i['price'] * i['count']}\n"
            
#             returning_message += f"\n💳 To'lov turi: {data['payment_choice']}\n📱Telefon raqam: {data['client_phone_number']}\n🤵 Mijoz: {data['client_full_name']}\n📝 Izoh: {data['product_description']}" 
#             await send_message(returning_message)
#             await message.answer('Mahsulot muvaffaqiyatli qabul qilindi')
#             await message.answer("Kerakli xizmatni tanlang", reply_markup=serving_options())
#             await state.clear()
#         else:
#             await message.answer("Kechirasiz, dasturda biror xatolik yuz berdi qaytadan urinib ko'ring")
#             await state.clear()
#             await message.answer("Kerakli xizmatni tanlang", reply_markup=serving_options())
        
#     except Exception:
#         await message.answer("Kechirasiz, dasturda biror xatolik yuz berdi qaytadan urinib ko'ring")
#         await state.set_state(ProductDetailState.product_description)

# TODO OTKAZ SECION
@dp.message(lambda msg: msg.text == 'Bekor qildirish')
async def delete_product(message: Message, state: FSMContext):
    try:
        otkaz_products = [f"{product['product_id']} - {product['client_full_name']}" for product in read_all_data()['data']]
        if not otkaz_products:
            await message.answer("Xozirda zakaz mavjud emas")
            await message.answer("Xizmat turini tanlang", reply_markup=serving_options())
            return

        user_otkaz_selection[message.chat.id] = []
        keyboard = create_otkaz_keyboard(user_otkaz_selection[message.chat.id])
        await message.answer("Bekor qilmoqchi bo'lgan mahsulotni tanlang", reply_markup=keyboard)

    except Exception:
        await message.answer("Kechirasiz, dasturda biror xatolik yuz berdi qaytadan urinib ko'ring")
        await state.clear()
        await message.answer("Xizmat turini tanlang", reply_markup=serving_options())
        
@dp.callback_query(lambda c: c.data.startswith("otkaz_"))
async def qarz_product(callback_query: types.CallbackQuery):
    user_id = callback_query.message.chat.id
    product_name = callback_query.data.split("_", 1)[1]

    user_otkaz_selection[user_id] = [product_name] if product_name not in user_otkaz_selection[user_id] else []

    keyboard = create_otkaz_keyboard(user_otkaz_selection[user_id])
    
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)

@dp.callback_query(lambda c: c.data == "confirm_otkaz")
async def confirm_selection(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.delete()
    user_id = callback_query.message.chat.id
    selected_products = user_otkaz_selection.get(user_id, [])
    if not selected_products:
        await callback_query.answer("Mahsulot tanlanmadi!", show_alert=True)
        await state.clear()
        await callback_query.message.answer('Kerakli xizmatni tanlang', reply_markup=serving_options())
        return
    
    for product in read_all_data()['data']:
        if f"{product['product_id']} - {product['client_full_name']}" == selected_products[0]:
            splitted_name = product['product_name'].split(', ')
            splitted_count = product['product_count'].split(', ')
            splitted_price = product['product_price'].split(', ')

            returning_message = ""
            for name, count, price in zip(splitted_name, splitted_count, splitted_price):
                returning_message += (
                    f"\n📦 Mahsulot: {name}\n"
                    f"🔢 Soni: {count} ta\n"
                    f"💰 Narxi: {price}\n"
                    f"💰 Umumiy narx: {int(price) * int(count)}\n"
                )

            returning_message += (
                f"\n💳 To'lov turi: {product['payment_choice']}\n"
                f"📱Telefon raqam: {product['client_phone_number']}\n"
                f"🤵 Mijoz: {product['client_full_name']}"
            )

            await callback_query.message.answer(
                returning_message, 
                reply_markup=create_confrim_cancel(
                    "❎ Mahsulotni bekor qilish", 
                    "↩️ Ortga qaytish", 
                    "canc", 
                    "conf"
                )
            )
            await state.update_data({'selected_products': selected_products, "product_id": product['product_id']})
            return

@dp.callback_query(lambda c: c.data == "cancel_otkaz")
async def cancel_otkaz(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.delete()
    await callback_query.answer("Bekor qilindi", show_alert=True)
    await state.clear()
    await callback_query.message.answer("Kerakli xizmatni tanlang", reply_markup=serving_options())

@dp.callback_query(lambda c: c.data == 'canc')
async def cancel_product(callback_query: types.CallbackQuery, state:FSMContext):
    await callback_query.message.delete()
    data = await state.get_data()
    product_id = data['product_id']
    success = change_status_otkaz(product_id)
    if success['success'] == True:
        await callback_query.message.answer('Zakaz muvaffaqiyatli bekor qilindi')
        await state.clear()
        await callback_query.message.answer("Kerakli xizmatni tanlang", reply_markup=serving_options())
    else:
        await callback_query.message.answer("Kechirasiz, dasturda biror xatolik yuz berdi")
        await callback_query.message.answer("Kerakli xizmatni tanlang", reply_markup=serving_options())
        await state.clear()
        return
    
@dp.callback_query(lambda c: c.data == 'conf')
async def cancel_process(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.delete()
    await state.clear()
    await callback_query.message.answer("Kerakli xizmatni tanlang", reply_markup=serving_options())    

# TODO QARZ SECTION
@dp.message(lambda msg: msg.text == 'Qarzdorlik')
async def qarzdorlik(message: Message, state: FSMContext):
    try:
        qarz_products = [f"{product['product_id']} - {product['client_full_name']}" for product in read_qarz_data()['data']]
        if not qarz_products:
            await message.answer("Xozirda qarzdorligi mavjud bo'lgan zakaz mavjud emas")
            await message.answer("Xizmat turini tanlang", reply_markup=serving_options())
            return
        
        user_qarz_selection[message.chat.id] = []
        keyboard = create_qarz_keyboard(user_qarz_selection[message.chat.id])
        await message.answer("Qarzdorlikdan olmoqchi bo'lgan zakazni tanlang", reply_markup=keyboard)

    except Exception:
        await message.answer("Kechirasiz, dasturda biror xatolik yuz berdi qaytadan urinib ko'ring")
        await state.clear()
        await message.answer("Xizmat turini tanlang", reply_markup=serving_options())
        
@dp.callback_query(lambda c: c.data.startswith("qarz_"))
async def qarz_product(callback_query: types.CallbackQuery):
    user_id = callback_query.message.chat.id
    product_name = callback_query.data.split("_", 1)[1]

    user_qarz_selection[user_id] = [product_name] if product_name not in user_qarz_selection[user_id] else []

    keyboard = create_qarz_keyboard(user_qarz_selection[user_id])
    
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)

@dp.callback_query(lambda c: c.data.startswith('confirm_qarz'))
async def confirm_qarz(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.delete()
    user_id = callback_query.message.chat.id
    selected_products = user_qarz_selection.get(user_id, [])
    if not selected_products:
        await callback_query.answer("Zakaz tanlanmadi!", show_alert=True)
        await state.clear()
        await callback_query.message.answer('Kerakli xizmatni tanlang', reply_markup=serving_options())
        return
    
    for product in read_qarz_data()['data']:
        if f"{product['product_id']} - {product['client_full_name']}" == selected_products[0]:
            splitted_name = product['product_name'].split(', ')
            splitted_count = product['product_count'].split(', ')
            splitted_price = product['product_price'].split(', ')

            returning_message = ""
            for name, count, price in zip(splitted_name, splitted_count, splitted_price):
                returning_message += (
                    f"\n📦 Mahsulot: {name}\n"
                    f"🔢 Soni: {count} ta\n"
                    f"💰 Narxi: {price}\n"
                    f"💰 Umumiy narx: {int(price) * int(count)}\n"
                )

            returning_message += (
                f"\n💳 To'lov turi: {product['payment_choice']}\n"
                f"📱Telefon raqam: {product['client_phone_number']}\n"
                f"🤵 Mijoz: {product['client_full_name']}"
            )

            await callback_query.message.answer(
                returning_message, 
                reply_markup=create_confrim_cancel(
                    "❎ Qarzdorlikdan olib tashlash", 
                    "↩️ Ortga qaytish", 
                    "cancel_product", 
                    "confirm_process"
                )
            )
            await state.update_data({'selected_products': selected_products, "product_id": product['product_id']})
            return

@dp.callback_query(lambda c: c.data == 'cancel_qarz')
async def cancel_qarz(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.delete()
    await callback_query.answer("Bekor qilindi", show_alert=True)
    await callback_query.message.answer("Kerakli xizmatni tanlang", reply_markup=serving_options())
    await state.clear()

@dp.callback_query(lambda c: c.data == 'cancel_product')
async def confirm_qarzprocess(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.delete()
    data = await state.get_data()
    product_id = data['product_id']
    success = change_status_qarz(product_id)
    if success['success'] == True:
        await callback_query.message.answer("Zakaz muvaffaqiyatli qarzdorlikdan olib tashlandi")
        await callback_query.message.answer("Kerakli xizmatni tanlang", reply_markup=serving_options())
        await state.clear()
    else:
        await callback_query.message.answer("Dasturda biror xatolik yuz berdi")
        await callback_query.message.answer("Kerakli xizmatni tanlang", reply_markup=serving_options())
        await state.clear()
    
@dp.callback_query(lambda c: c.data == 'confirm_process')
async def cancel_qarzprocess(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.delete()
    await callback_query.message.answer("Kerakli xizmatni tanlang", reply_markup=serving_options())
    await state.clear()

@dp.message(lambda msg: msg.text == "Statistika")
async def get_stats(message: Message):
    await message.answer("Kerakli bo'lgan sanani tanlang", reply_markup=generate_custom_calendar(datetime.datetime.now().month, datetime.datetime.now().year))

# TODO Stats
@dp.callback_query(lambda c: c.data.startswith("day:"))
async def process_day_callback(callback_query: types.CallbackQuery):
    await callback_query.answer()
    selected_date = callback_query.data.split(":")[1]
    stats_message = ''
    if selected_date == 'monthly':
        stats_message = get_analyzed_information(is_month=True)
        if stats_message['success'] is False:
            stats_message = 'Ushbu sanada zakazlar mavjud emas'
        else:
            stats_message = stats_message['message']
    elif selected_date == 'daily':
        stats_message = get_analyzed_information(is_today=True)
        if stats_message['success'] is False:
            stats_message = 'Ushbu sanada zakazlar mavjud emas'
        else:
            stats_message = stats_message['message']
    elif selected_date == 'weekly':
        stats_message = get_analyzed_information(is_week=True)
        if stats_message['success'] is False:
            stats_message = 'Ushbu sanada zakazlar mavjud emas'
        else:
            stats_message = stats_message['message']
    else:
        stats_message = get_analyzed_information(start_date=True, starting_date=selected_date)
        if stats_message['success'] is False:
            stats_message = 'Ushbu sanada zakazlar mavjud emas'
        else:
            stats_message = stats_message['message']

    current_message = callback_query.message.text.strip()

    new_markup = generate_custom_calendar(datetime.datetime.now().month, datetime.datetime.now().year)

    stats_message = stats_message.strip()

    if stats_message != current_message:
        await bot.edit_message_text(
            text=stats_message,
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            reply_markup=new_markup
        )


# PRODUCTS
@dp.message(lambda msg: msg.text == 'Mahsulotlar')
async def ask_for_choice(message: Message):
    try:
        await message.answer("Mahsulot uchun amalni tanlang", reply_markup=product_editing())
    except Exception:
        await message.answer("Kechirasiz, dasturda biror xatolik yuz berdi")
        await message.anser("Kerakli xizmatni tanlang", reply_markup=serving_options())

@dp.message(lambda msg: msg.text == "➕ Mahsulot qo'shish")
async def add_product(message: Message, state: FSMContext):
    try:
        await message.answer("Yangi mahsulot nomini yuboring")
        await state.set_state(ProductDetailState.new_product_name)
    except Exception:
        await message.answer("Kechirasiz dasturda biror xatolik yuz berdi")
        await ask_for_choice(message)

@dp.message(ProductDetailState.new_product_name)
async def receive_new_product_name(message: Message, state: FSMContext):
    try:
        new_product_name = message.text
        success = insert_data_to_products(new_product_name)
        if success['success'] is True:
            await message.answer("Yangi mahsulot muvaffaqiyatli saqlandi")
            await message.answer("Kerakli xizmatni tanlang", reply_markup=serving_options())
            await state.clear()
        else:
            await message.answer("Kechirasiz dasturda biror xatolik yuz berdi")
            await message.answer("Kerakli xizmatni tanlang", reply_markup=serving_options())
            await state.clear()
    except Exception as e:
        print(f'{e}')
        await message.answer("Kechirasiz dasturda biror xatolik yuz berdi")        
        await message.answer("Kerakli xizmatni tanlang", reply_markup=serving_options())



@dp.message(lambda msg: msg.text == "➖ Mahsulotni o'chirish")
async def mahsulot_(message: Message, state: FSMContext):
    try:
        products = get_products()
        if not products:
            await message.answer("Xozirda mahsulotlar mavjud emas")
            await message.answer("Xizmat turini tanlang", reply_markup=serving_options())
            await state.clear()
            return
        
        user_product_selection[message.chat.id] = []
        keyboard = create_products_keyboard(user_product_selection[message.chat.id])
        await message.answer("O'chirmoqchi bo'lgan mahsulotni tanlang", reply_markup=keyboard)

    except Exception:
        await message.answer("Kechirasiz, dasturda biror xatolik yuz berdi qaytadan urinib ko'ring")
        await state.clear()
        await message.answer("Xizmat turini tanlang", reply_markup=serving_options())
        
@dp.callback_query(lambda c: c.data.startswith("mahsulot_"))
async def qarz_product(callback_query: types.CallbackQuery):
    user_id = callback_query.message.chat.id
    product_name = callback_query.data.split("_", 1)[1]

    user_product_selection[user_id] = [product_name] if product_name not in user_product_selection[user_id] else []

    keyboard = create_products_keyboard(user_product_selection[user_id])
    
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)

@dp.callback_query(lambda c: c.data == 'confirm_mahsulot')
async def confirm_mahs(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.delete()
    user_id = callback_query.message.chat.id
    selected_products = user_product_selection.get(user_id, [])
    if not selected_products:
        await callback_query.answer("Mahsulot tanlanmadi!", show_alert=True)
        await state.clear()
        await callback_query.message.answer('Kerakli xizmatni tanlang', reply_markup=serving_options())
        return
    
    datas = get_sorted_data()
    if datas['success'] is True:
        for data in datas['sorted']:
            if data['product_name'] == selected_products[0]:
                succes = delete_data_from_products(data['product_id'])
                if succes['success'] is True:
                    await callback_query.message.answer("Mahsulot muvaffaqiyatli o'chirib tashlandi")
                    await callback_query.message.answer("Kerakli xizmatni tanlang", reply_markup=serving_options())
                    await state.clear()
                else:
                    await callback_query.message.answer("Kechirasiz, dasturda biror xatolik yuz berdi")
                    await callback_query.message.answer("Kerakli xizmatni tanlang", reply_markup=serving_options())
                    await state.clear()
    else:
        await callback_query.message.answer("Kechirasiz, dasturda biror xatolik yuz berdi")
        await callback_query.message.answer("Kerakli xizmatni tanlang", reply_markup=serving_options())

@dp.callback_query(lambda c: c.data == 'cancel_mahsulot')
async def cancel_mahsulot(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.delete()
    await callback_query.answer("Bekor qilindi", show_alert=True)
    await callback_query.message.answer("Kerakli xizmatni tanlang", reply_markup=serving_options())
    await state.clear()


async def main():
    await dp.start_polling(bot, skip_updates=True)

if __name__ == '__main__':
    asyncio.run(main())
