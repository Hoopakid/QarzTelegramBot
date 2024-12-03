import os
import asyncio
import aiohttp
import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile

from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from state import ProductDetailState, OtkazState, BorrowingState
from analyze import insert_data, read_qarz_data, change_status_qarz, get_products, read_all_data, change_status_otkaz, get_analyzed_information, insert_data_to_products, delete_data_from_products, get_sorted_data, get_product_by_id, get_qarz_product_by_id, get_only_product, insert_to_qarzdorlik, export_statistics_to_excel
from btn import payment_option, serving_options, product_editing, inline_qarzdorlik_button

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

async def send_message(message: str, topic_id):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': ADMIN_CHAT_ID,
        'text': message,
        'message_thread_id': topic_id
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            if response.status == 200:
                return {'success': True}
            else:
                return {'success': False}
            
MONTHS = [
    "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun", 
    "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr"
]

def generate_month_selector():
    inline_keyboard = []
    a = []
    for i, month_name in enumerate(MONTHS, start=1):
        a.append(InlineKeyboardButton(text=month_name, callback_data=f"month:{i}"))
        if len(a) == 2:
            inline_keyboard.append(a)
            a = []
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

def generate_custom_calendar(month: int = None, year: int = None, add_exc=False):
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
    if add_exc is True:
        inline_keyboard.append([InlineKeyboardButton(text="📊 Excel ga ko'chirish", callback_data="import_excel")])
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
async def cancel_selection(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer("Bekor qilindi", show_alert=True)
    await state.clear()
    await callback_query.message.answer("Kerakli xizmatni tanlang", reply_markup=serving_options())

async def handler(message: Message, state: FSMContext):
    try:
        products = await state.get_data()
        selected_products = products.get('selected_products', [])
        
        await message.answer(f"{selected_products[0]} dan nechta buyurtma bermoqchisiz")
        current_product = selected_products[0]
        selected_products.remove(current_product)

        await state.update_data({'current_product': current_product,'selected_products': selected_products})
        await state.set_state(ProductDetailState.product_count)
    except Exception as e:
        print(f"{e}")
        await message.answer("Kechirasiz, dasturda biror xatolik yuz berdi qaytadan urunib ko'ring")
        await message.answer("Kerakli xizmatni tanlang", reply_markup=serving_options())
        await state.clear()

@dp.message(ProductDetailState.product_count)
async def receive_product_count(message: Message, state: FSMContext):
    try:
        product_count = int(message.text)
        if product_count <= 0:
            await message.answer("Iltimos, zakaz sonini son ko'rinishida yuboring.")
            products = await state.get_data()
            current_product = products.get('current_product')
            await message.answer(f"{current_product} dan nechta buyurtma bermoqchisiz")
            await state.set_state(ProductDetailState.product_count)
        else:
            await state.update_data({'product_count': product_count})
            await message.answer("Zakaz uchun narx yuboring")
            await state.set_state(ProductDetailState.product_price)
    
    except Exception as e:
        print(f"{e}")
        await message.answer("Kechirasiz, dasturda biror xatolik yuz berdi qaytadan urunib ko'ring")
        await message.answer("Kerakli xizmatni tanlang", reply_markup=serving_options())
        await state.clear()
 
@dp.message(ProductDetailState.product_price)
async def receive_product_price(message: Message, state: FSMContext):
    try:
        product_price = int(message.text)
        if product_price <= 0:
            await message.answer("Iltimos, zakaz narxini musbat son ko'rinishida yuboring")
        else:
            await state.update_data({'product_price': product_price})
            await message.answer("Zakaz uchun izoh yuboring")
            await state.set_state(ProductDetailState.product_description)

    except Exception as e:
        print(f"{e}")
        await message.answer("Kechirasiz, dasturda biror xatolik yuz berdi qaytadan urunib ko'ring")
        await message.answer("Kerakli xizmatni tanlang", reply_markup=serving_options())
        await state.clear()

@dp.message(ProductDetailState.product_description)
async def receive_product_description(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        current_product = data.get('current_product')
        product_count = data.get('product_count')
        product_price = data.get('product_price')

        product_entry = {
            'name': current_product,
            'count': product_count,
            'price': product_price,
            'description': message.text
        }

        products = data.get('products', [])
        products.append(product_entry)
        await state.update_data({'products': products})

        selected_products = data.get('selected_products', [])
        if selected_products:
            await handler(message, state)
        else:
            await message.answer("Sotib oluvchi korxona nomini yuboring")
            await state.set_state(ProductDetailState.client_full_name)
    except Exception as e:
        print(f"{e}")
        await message.answer("Kechirasiz, dasturda biror xatolik yuz berdi qaytadan urunib ko'ring")
        await message.answer("Kerakli xizmatni tanlang", reply_markup=serving_options())
        await state.clear()


@dp.message(ProductDetailState.client_full_name)
async def receive_client_full_name(message: Message, state: FSMContext):
    try:
        client_full_name = message.text
        await state.update_data({'client_full_name': client_full_name})
        await message.answer('Telefon raqamingizni yuboring (+998123456789)')
        await state.set_state(ProductDetailState.client_phone_number)
    except Exception as e:
        print(f"{e}")
        await message.answer("Kechirasiz, dasturda biror xatolik yuz berdi qaytadan urunib ko'ring")
        await message.answer("Kerakli xizmatni tanlang", reply_markup=serving_options())
        await state.clear()

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
    except Exception as e:
        print(f"{e}")
        await message.answer("Kechirasiz, dasturda biror xatolik yuz berdi qaytadan urunib ko'ring")
        await message.answer("Kerakli xizmatni tanlang", reply_markup=serving_options())
        await state.clear()

@dp.message(ProductDetailState.payment_choice)
async def recieve_payment_choice(message: Message, state: FSMContext):
    valid_choices = ["Karta orqali", "Qarzga berish", "Naqd to'lov"]

    try:
        if message.text in valid_choices:
            await state.update_data({'payment_choice': message.text})
            if message.text == "Qarzga berish":
                await message.answer("Qarzdorlik to'lov turi uchun izoh kiriting")
                await state.set_state(ProductDetailState.description_for_qarzdorlik)
            else:
                await state.update_data({'description_for_qarzdorlik': None})
                await message.answer("Shartnoma raqamini kiriting")
                await state.set_state(ProductDetailState.contract_number)
        else:
            await message.answer("Iltimos, quyidagi variantlardan birini tanlang:", reply_markup=payment_option())
            await state.set_state(ProductDetailState.payment_choice)

    except Exception as e:
        print(f"{e}")
        await message.answer("Kechirasiz, dasturda biror xatolik yuz berdi qaytadan urinib ko'ring")
        await message.answer("Kerakli xizmatni tanlang", reply_markup=serving_options())
        await state.clear()

@dp.message(ProductDetailState.description_for_qarzdorlik)
async def receive_description_for_qarzdorlik(message: Message, state: FSMContext):
    try:
        await state.update_data({'description_for_qarzdorlik': message.text})
        await message.answer("Shartnoma raqamini kiriting")
        await state.set_state(ProductDetailState.contract_number)

    except Exception as e:
        print(f"{e}")
        await message.answer("Kechirasiz, dasturda biror xatolik yuz berdi qaytadan urinib ko'ring")
        await message.answer("Kerakli xizmatni tanlang", reply_markup=serving_options())
        await state.clear() 

@dp.message(ProductDetailState.contract_number)
async def receive_contract_number(message: Message, state: FSMContext):
    try:
        await state.update_data({'contract_number': message.text})
        await message.answer("Buyurtmani qabul qilib olgan korxonani kiriting")
        await state.set_state(ProductDetailState.enterprise_name)
    except Exception as e:
        print(f"{e}")
        await message.answer("Kechirasiz, dasturda biror xatolik yuz berdi qaytadan urunib ko'ring")
        await message.answer("Kerakli xizmatni tanlang", reply_markup=serving_options())
        await state.clear()

@dp.message(ProductDetailState.enterprise_name)
async def receive_enterprise_name(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        
        combined_product_name = "# ".join([p['name'] for p in data['products']])
        combined_product_count = "# ".join(str(p['count']) for p in data['products'])
        combined_product_per_price = "# ".join(str(p['price']) for p in data['products'])
        combined_product_price = "# ".join(str(p['price'] * p['count']) for p in data['products'])
        combined_product_description = "# ".join(p['description'] for p in data['products'])
        
        temp = {
            "product_name": combined_product_name,
            "product_count": combined_product_count,
            "product_per_price": combined_product_per_price, 
            "product_price": combined_product_price,
            "product_description": combined_product_description,
            "client_phone_number": data["client_phone_number"],
            "client_enterprise": data["client_full_name"],
            "payment_choice": data["payment_choice"],
            "qarzdorlik_description": data['description_for_qarzdorlik'],
            "contract_number": data["contract_number"],
            "enterprise_name": message.text
        }
        
        success = insert_data(temp)
        if success['success'] is True:
            returned_id = success['returned_id']
            current_date = datetime.datetime.now().date()
            returning_message = f"#Zakaz_{returned_id}\n{current_date}\n"

            for i in data['products']:
            
                returning_message += f"\n📦 Mahsulot: {i['name']}\n🔢 Soni: {i['count']} ta\n💰 Sotilgan narxi: {i['price']}\n💰Shartnomaning umumiy narxi: {i['price'] * i['count']}\n💬 Izoh: {i['description']}\n"
            
            returning_message += f"\n💳 To'lov turi: {data['payment_choice']}\n📱Mijozning telefon raqami: {data['client_phone_number']}\n🤵 Sotib oluvchi korxona: {data['client_full_name']}\n🎫 Shartnoma raqami: {data['contract_number']}\n🏢 Buyurtma qabul qilgan korxona: {message.text}\n" 
            if data['description_for_qarzdorlik'] is not None:
                returning_message += f"💬 Qarzdorlik uchun izoh: {data['description_for_qarzdorlik']}"
            await send_message(returning_message, 105)
            await message.answer('Zakaz muvaffaqiyatli qabul qilindi')
            await message.answer("Kerakli xizmatni tanlang", reply_markup=serving_options())
            await state.clear()
        else:
            await message.answer("Kechirasiz, dasturda biror xatolik yuz berdi qaytadan urinib ko'ring")
            await state.clear()
            await message.answer("Kerakli xizmatni tanlang", reply_markup=serving_options())
    except Exception as e:
        print(f"{e}")
        await message.answer("Kechirasiz, dasturda biror xatolik yuz berdi qaytadan urunib ko'ring")
        await message.answer("Kerakli xizmatni tanlang", reply_markup=serving_options())
        await state.clear()

# TODO OTKAZ SECION
@dp.message(lambda msg: msg.text == 'Bekor qildirish')
async def delete_product(message: Message, state: FSMContext):
    try:
        await message.answer("Bekor qilmoqchi bo'lgan zakazni id sini kiriting")
        await state.set_state(OtkazState.product_id)
    except Exception:
        await message.answer("Kechirasiz, dasturda biror xatolik yuz berdi qaytadan urinib ko'ring")
        await state.clear()
        await message.answer("Xizmat turini tanlang", reply_markup=serving_options())
        
@dp.message(OtkazState.product_id)
async def confirm_selection(message: Message, state: FSMContext):
    try:
        product_id = int(message.text)
        if product_id <= 0:
            await message.answer("Iltimos, zakaz id sini musbat son ko'rinishida yuboring")
        else:
            detail = get_product_by_id(product_id)    
            if detail['success'] is False:
                await message.answer("Kechirasiz, bu id da zakaz mavjud emas")
            else:
                product = detail['product']
                await state.update_data({"product_otkaz_id": product_id})
                date_formatted = product['created_at'].strftime('%Y-%d-%m')
                
                returning_message = f"#Zakaz_{product['id']}\n{date_formatted}\n"

                product_name = product['product_name'].split("# ")
                product_description = product['product_description'].split('# ')
                product_count = product['product_count'].split('# ')
                product_per_price = product['product_per_price'].split('# ')
                product_price = product['product_price'].split('# ')

                for name, desc, count, per, price in zip(product_name, product_description, product_count, product_per_price, product_price):
                    returning_message += f"\n📦 Mahsulot: {name}\n🔢 Soni: {count}\n💰 Sotilgan narxi: {per}\n💰Shartnomaning umumiy narxi: {price}\n💬 Izoh: {desc}\n"
                
                returning_message += f"\n💳 To'lov turi: {product['payment_choice']}\n📱Mijozning telefon raqami: {product['client_phone_number']}\n🤵 Sotib oluvchi korxona: {product['client_enterprise']}\n🎫 Shartnoma raqami: {product['contract_number']}\n🏢 Buyurtma qabul qilgan korxona: {product['enterprise_name']}"
                if product['qarzdorlik_description'] is not None:
                    returning_message += f"\n💬 Qarzdorlik uchun izoh: {product['qarzdorlik_description']}"
                await message.answer(
                    returning_message, 
                    reply_markup=create_confrim_cancel(
                        "❎ Mahsulotni bekor qilish", 
                        "↩️ Ortga qaytish", 
                        "canc", 
                        "conf"
                    )
                )
    except Exception as e:
        print(f"{e}")
        await message.answer("Kechirasiz, dasturda biror xatolik yuz berdi qaytadan urinib ko'ring")
        await state.clear()
        await message.answer("Xizmat turini tanlang", reply_markup=serving_options())
        
@dp.callback_query(lambda c: c.data == 'canc')
async def cancel_product(callback_query: types.CallbackQuery, state:FSMContext):
    await callback_query.message.delete()
    data = await state.get_data()
    product_id = data['product_otkaz_id']
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
        qarz_products = read_qarz_data()['data']
        if not qarz_products:
            await message.answer("Xozirda qarzdorligi mavjud bo'lgan zakaz mavjud emas")
            await message.answer("Xizmat turini tanlang", reply_markup=serving_options())
            return
        
        await message.answer("Qarzdorlik uchun amalni tanlang", reply_markup=inline_qarzdorlik_button())

    except Exception as e:
        print(f"{e}")
        await message.answer("Kechirasiz, dasturda biror xatolik yuz berdi qaytadan urinib ko'ring")
        await state.clear()
        await message.answer("Xizmat turini tanlang", reply_markup=serving_options())

@dp.callback_query(lambda c: c.data == 'cancel_borrowing')
async def ask_for_product_id(callback_query: types.CallbackQuery, state: FSMContext):
    try: 
        await callback_query.message.delete()
        await callback_query.message.answer("Qarzdorlikdan olib tashlamoqchi bo'lgan zakazning id sini kiriting")
        await state.set_state(BorrowingState.product_id)
    except Exception:
        await callback_query.message.answer("Kechirasiz, dasturda biror xatolik yuz berdi qaytadan urinib ko'ring")
        await state.clear()
        await callback_query.message.answer("Xizmat turini tanlang", reply_markup=serving_options())


@dp.message(BorrowingState.product_id)
async def confirm_qarz(message: Message, state: FSMContext):
    try:
        product_id = int(message.text)
        if product_id <= 0:
            await message.answer("Iltimos, zakaz id sini musbat son ko'rinishida yuboring")
            await state.set_state(BorrowingState.product_id)
        else:
            detail = get_product_by_id(product_id)    
            if detail['success'] is False:
                await message.answer("Kechirasiz, bu id da zakaz mavjud emas")
                await message.answer("Kerakli xizmatni tanlang", reply_markup=serving_options())
            else:
                product = detail['product']
                await state.update_data({"product_qarz_id": product_id})
                date_formatted = product['created_at'].strftime('%Y-%d-%m')
                
                returning_message = f"#Zakaz_{product['id']}\n{date_formatted}\n"

                product_name = product['product_name'].split("# ")
                product_description = product['product_description'].split('# ')
                product_count = product['product_count'].split('# ')
                product_per_price = product['product_per_price'].split('# ')
                product_price = product['product_price'].split('# ')

                for name, desc, count, per, price in zip(product_name, product_description, product_count, product_per_price, product_price):
                    returning_message += f"\n📦 Mahsulot: {name}\n🔢 Soni: {count}\n💰 Sotilgan narxi: {per}\n💰Shartnomaning umumiy narxi: {price}\n💬 Izoh: {desc}\n"
                
                returning_message += f"\n💳 To'lov turi: {product['payment_choice']}\n📱Mijozning telefon raqami: {product['client_phone_number']}\n🤵 Sotib oluvchi korxona: {product['client_enterprise']}\n🎫 Shartnoma raqami: {product['contract_number']}\n🏢 Buyurtma qabul qilgan korxona: {product['enterprise_name']}"
                if product['qarzdorlik_description'] is not None:
                    returning_message += f"\n💬 Qarzdorlik uchun izoh: {product['qarzdorlik_description']}"
                await message.answer(
                    returning_message, 
                    reply_markup=create_confrim_cancel(
                        "❎ Mahsulotni qarzdorlikdan olib tashlash", 
                        "↩️ Ortga qaytish", 
                        "cancel_product", 
                        "confirm_process"
                    )
                )
    except Exception as e:
        print(f"{e}")
        await message.answer("Kechirasiz, dasturda biror xatolik yuz berdi qaytadan urinib ko'ring")
        await state.clear()
        await message.answer("Xizmat turini tanlang", reply_markup=serving_options())
    

@dp.callback_query(lambda c: c.data == 'cancel_product')
async def confirm_qarzprocess(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.delete()
    data = await state.get_data()
    product_id = data['product_qarz_id']
    success = change_status_qarz(product_id)
    if success['success'] == True:
        detail = get_only_product(product_id)
        if detail['success'] == True:
            product = detail['data']

            splitted_product_name = product['product_name'].split('# ')
            splitted_product_count = product['product_count'].split('# ')
            splitted_product_per_price = product['product_per_price'].split('# ')
            splitted_product_price = product['product_price'].split('# ')
            splitted_product_description = product['product_description'].split('# ')
        
            returning_message = f"#Qarzdorlik_bekor_qilindi_{product['id']}\n📅 Bekor qilingan sana: {datetime.datetime.today().date()}\n"

            for name, count, per_price, price, desc in zip(splitted_product_name, splitted_product_count, splitted_product_per_price, splitted_product_price, splitted_product_description):
                returning_message += f"\n📦 Mahsulot: {name}\n🔢 Soni: {count}\n💰 Sotilgan narxi: {per_price}\n💰Shartnomaning umumiy narxi: {price}\n💬 Izoh: {desc}\n"
            
            returning_message += f"\n💳 To'lov turi: {product['payment_choice']}\n📱Mijozning telefon raqami: {product['client_phone_number']}\n🤵 Sotib oluvchi korxona: {product['client_enterprise']}\n🎫 Shartnoma raqami: {product['contract_number']}\n🏢 Buyurtma qabul qilgan korxona: {product['enterprise_name']}"
            if product['qarzdorlik_description'] is not None:
                returning_message += f"\n💬 Qarzdorlik uchun izoh: {product['qarzdorlik_description']}"
            
            await send_message(returning_message, 106)

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

@dp.callback_query(lambda c: c.data == 'decrease_borrowing')
async def receive_qarz_decreasing_id(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Qarzdorligini kamaytirmoqchi bo'lgan zakazning id sini kiriting")
    await state.set_state(BorrowingState.product_temp_id)

@dp.message(BorrowingState.product_temp_id)
async def show_the_details_of_product(message: Message, state: FSMContext):
    try:
        product_id = int(message.text)
        if product_id <= 0:
            await message.answer("Iltimos, zakaz id sini musbat son ko'rinishida yuboring")
            await state.set_state(BorrowingState.product_temp_id)
        else:
            detail = get_product_by_id(product_id)    
            if detail['success'] is False:
                await message.answer("Kechirasiz, bu id da zakaz mavjud emas")
                await message.answer("Kerakli xizmatni tanlang", reply_markup=serving_options())
            else:
                product = detail['product']
                await state.update_data({"product_decrease_id": product_id})
                date_formatted = product['created_at'].strftime('%Y-%d-%m')
                
                returning_message = f"#Zakaz_{product['id']}\n{date_formatted}\n"

                product_name = product['product_name'].split("# ")
                product_description = product['product_description'].split('# ')
                product_count = product['product_count'].split('# ')
                product_per_price = product['product_per_price'].split('# ')
                product_price = product['product_price'].split('# ')

                for name, desc, count, per, price in zip(product_name, product_description, product_count, product_per_price, product_price):
                    returning_message += f"\n📦 Mahsulot: {name}\n🔢 Soni: {count}\n💰 Sotilgan narxi: {per}\n💰Shartnomaning umumiy narxi: {price}\n💬 Izoh: {desc}\n"
                
                returning_message += f"\n💳 To'lov turi: {product['payment_choice']}\n📱Mijozning telefon raqami: {product['client_phone_number']}\n🤵 Sotib oluvchi korxona: {product['client_enterprise']}\n🎫 Shartnoma raqami: {product['contract_number']}\n🏢 Buyurtma qabul qilgan korxona: {product['enterprise_name']}"
                if product['qarzdorlik_description'] is not None:
                    returning_message += f"\n💬 Qarzdorlik uchun izoh: {product['qarzdorlik_description']}"
                await message.answer(
                    returning_message, 
                    reply_markup=create_confrim_cancel(
                        "❎ Davom etish", 
                        "↩️ Ortga qaytish", 
                        "continue", 
                        "back"
                    )
                )
    except Exception as e:
        print(f"{e}")
        await message.answer("Kechirasiz, dasturda biror xatolik yuz berdi qaytadan urinib ko'ring")
        await state.clear()
        await message.answer("Xizmat turini tanlang", reply_markup=serving_options())
    
async def ask_borrowing_sum(message: Message, state: FSMContext):
    await message.answer("Iltimos, summa ni musbat son ko'rinishida yuboring")
    await state.set_state(BorrowingState.product_price_borrowing)

@dp.callback_query(lambda c: c.data == 'continue')
async def receive_sum_for_borrowing(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        await callback_query.message.answer('Qarzdorlikni qancha summasini kamaytirmoqchisiz')
        await state.set_state(BorrowingState.product_price_borrowing)
    
    except Exception as e:
        print(f"{e}")
        await callback_query.message.answer("Kechirasiz, dasturda biror xatolik yuz berdi qaytadan urinib ko'ring")
        await state.clear()
        await callback_query.message.answer("Xizmat turini tanlang", reply_markup=serving_options())
    
@dp.message(BorrowingState.product_price_borrowing)
async def receive_sum(message: Message, state: FSMContext):
    try:
        borrowing_sum = int(message.text)
        if borrowing_sum <= 0:
            await ask_borrowing_sum(message)
        data = await state.get_data()
        inserting = insert_to_qarzdorlik(data['product_decrease_id'], borrowing_sum)
        if inserting['success'] is True:
            detail = get_only_product(data['product_decrease_id'])
            if detail['success'] == True:
                product = detail['data']

                splitted_product_name = product['product_name'].split('# ')
                splitted_product_count = product['product_count'].split('# ')
                splitted_product_per_price = product['product_per_price'].split('# ')
                splitted_product_price = product['product_price'].split('# ')
                splitted_product_description = product['product_description'].split('# ')
            
                returning_message = f"#Qarzdorlik_kamaytirildi_{product['id']}\n📅 Kamaytirilgan sana: {datetime.datetime.today().date()}\n"

                for name, count, per_price, price, desc in zip(splitted_product_name, splitted_product_count, splitted_product_per_price, splitted_product_price, splitted_product_description):
                    returning_message += f"\n📦 Mahsulot: {name}\n🔢 Soni: {count}\n💰 Sotilgan narxi: {per_price}\n💰Shartnomaning umumiy narxi: {price}\n💬 Izoh: {desc}\n"
                
                returning_message += f"\n💳 To'lov turi: {product['payment_choice']}\n📱Mijozning telefon raqami: {product['client_phone_number']}\n🤵 Sotib oluvchi korxona: {product['client_enterprise']}\n🎫 Shartnoma raqami: {product['contract_number']}\n🏢 Buyurtma qabul qilgan korxona: {product['enterprise_name']}"
                if product['qarzdorlik_description'] is not None:
                    returning_message += f"\n💬 Qarzdorlik uchun izoh: {product['qarzdorlik_description']}"
                returning_message += f"\n\n💰 Qancha summa kamaytirildi: {borrowing_sum}"
                await send_message(returning_message, 106)
            
            await message.answer(f"Ushbu zakazdan {borrowing_sum} so'm qarzdorlikdan muvaffaqiyatli olib tashlandi")
            await message.answer("Kerakli xizmatni tanlang", reply_markup=serving_options())
            await state.clear()

    except Exception as e:
        print(f"{e}")
        await message.answer("Kechirasiz, dasturda biror xatolik yuz berdi qaytadan urinib ko'ring")
        await state.clear()
        await message.answer("Xizmat turini tanlang", reply_markup=serving_options())

@dp.callback_query(lambda c: c.data == 'back')
async def back_to(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.delete()
    await state.clear()
    await callback_query.message.answer('Kerakli xizmatni tanlang', reply_markup=serving_options())

# TODO Stats
@dp.message(lambda msg: msg.text == "Statistika")
async def get_stats(message: Message):
    await message.answer(
        "Statistika uchun oyni tanlang",
        reply_markup=generate_month_selector()
    )

@dp.callback_query(lambda c: c.data.startswith("month:"))
async def process_month_callback(callback_query: types.CallbackQuery):
    await callback_query.answer()
    selected_month = int(callback_query.data.split(":")[1])
    year = datetime.datetime.now().year

    await bot.edit_message_text(
        text=f"{MONTHS[selected_month - 1]} -- kunini tanlang:",
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=generate_custom_calendar(selected_month, year)
    )

@dp.callback_query(lambda c: c.data.startswith("day:"))
async def process_day_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    selected_date = callback_query.data.split(":")[1]
    stats_message = ''
    temp = None
    if selected_date == 'monthly':
        stats_message = get_analyzed_information(is_month=True)
        temp = stats_message
        if stats_message['success'] is False:
            stats_message = 'Ushbu sanada zakazlar mavjud emas'
        else:
            stats_message = stats_message['message']
    elif selected_date == 'daily':
        stats_message = get_analyzed_information(is_today=True)
        temp = stats_message
        if stats_message['success'] is False:
            stats_message = 'Ushbu sanada zakazlar mavjud emas'
        else:
            stats_message = stats_message['message']
    elif selected_date == 'weekly':
        stats_message = get_analyzed_information(is_week=True)
        temp = stats_message
        if stats_message['success'] is False:
            stats_message = 'Ushbu sanada zakazlar mavjud emas'
        else:
            stats_message = stats_message['message']
    else:
        stats_message = get_analyzed_information(start_date=True, starting_date=selected_date)
        temp = stats_message
        if stats_message['success'] is False:
            stats_message = 'Ushbu sanada zakazlar mavjud emas'
        else:
            stats_message = stats_message['message']

    current_message = callback_query.message.text.strip()
    if stats_message != 'Ushbu sanada zakazlar mavjud emas':
        new_markup = generate_custom_calendar(datetime.datetime.now().month, datetime.datetime.now().year, add_exc=True)
    else:
        new_markup = generate_custom_calendar(datetime.datetime.now().month, datetime.datetime.now().year)
    stats_message = stats_message.strip()


    if stats_message != current_message:
        await state.update_data({'excel': temp})
        await bot.edit_message_text(
            text=stats_message,
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            reply_markup=new_markup
        )

@dp.callback_query(lambda c: c.data == 'import_excel')
async def import_to_excel(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.delete()
    st = await state.get_data()
    data = st['excel']
    file_name = 'statistics.xlsx'
    success = export_statistics_to_excel(data)
    
    if success:
        excel_file = FSInputFile(file_name)
        await bot.send_document(
            chat_id=callback_query.message.chat.id,
            document=excel_file,
            caption="Statistika ma'lumotlari Excel fayl shaklida."
        )

        os.remove(file_name)
        await callback_query.message.answer("Kerakli xizmatni tanlang", reply_markup=serving_options())
        await state.clear()
        return
    else:
        await callback_query.message.answer("Excel faylni yaratishda xatolik yuz berdi.")
        await callback_query.message.answer("Kerakli xizmatni tanlang", reply_markup=serving_options())
        await state.clear()
        
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
