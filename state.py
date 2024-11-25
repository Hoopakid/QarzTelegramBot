from aiogram.fsm.state import State, StatesGroup

class ProductState(StatesGroup):
    product_name = State()
    product_count = State()
    product_price = State()
    client_phone_number = State()
    client_full_name = State()
    payment_choice = State()
    product_description = State()

class GetProductID(StatesGroup):
    temp_data = State()
    product_id = State()

class GetQarzProductID(StatesGroup):
    temp_data = State()
    qarz_product_id = State()

class ProductDetailState(StatesGroup):
    product_count = State()
    product_price = State()
    client_phone_number = State()
    payment_choice = State()
    product_description = State()
    client_full_name = State()