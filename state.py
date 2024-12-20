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
    new_product_name = State()
    description_for_qarzdorlik = State()
    contract_number = State()
    enterprise_name = State()

class OtkazState(StatesGroup):
    product_id = State()

class BorrowingState(StatesGroup):
    product_id = State()
    product_temp_id = State()
    product_price_borrowing = State()
    product_edit_id = State()

class EditingZakazState(StatesGroup):
    product_name = State()
    product_description = State()
    product_per_price = State()
    product_count = State()
    product_field = State()

    product_temp_id = State()