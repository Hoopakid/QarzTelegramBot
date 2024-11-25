import os
import psycopg2
import pandas as pd
from psycopg2 import extras
from dotenv import load_dotenv
from psycopg2 import extras
from datetime import datetime, timedelta

load_dotenv()

DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_USER = os.environ.get('DB_USERNAME')
DB_NAME = os.environ.get('DB_NAME')

def connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        password=DB_PASSWORD,
        user=DB_USER
    )
    return conn

def insert_data(product_data: dict):
    conn = connection()
    cursor = conn.cursor(cursor_factory=extras.DictCursor)
    returned_id = None
    try:
        if product_data.get('payment_choice') == 'Qarzga berish':
            insert_query = """
                INSERT INTO zakaz_products (product_name, product_count, product_price, client_phone_number, client_full_name, payment_choice, product_description, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            cursor.execute(insert_query, (
                product_data.get('product_name'),
                product_data.get('product_count'),
                product_data.get('product_price'),
                product_data.get('client_phone_number'),
                product_data.get('client_full_name'),
                product_data.get('payment_choice'),
                product_data.get('product_description'),
                False
            ))
        else:
            insert_query = """
                INSERT INTO zakaz_products (product_name, product_count, product_price, client_phone_number, client_full_name, payment_choice, product_description)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            cursor.execute(insert_query, (
                product_data.get('product_name'),
                product_data.get('product_count'),
                product_data.get('product_price'),
                product_data.get('client_phone_number'),
                product_data.get('client_full_name'),
                product_data.get('payment_choice'),
                product_data.get('product_description')
            ))
        returned_id = cursor.fetchone()['id']
        conn.commit() 
    except Exception as e:
        conn.rollback()
        print(f"Error inserting data: {e}")
        return {"success": False}
    finally:
        cursor.close()
        conn.close()
    return {"success": True, "returned_id": returned_id}
    

def get_products():
    conn = connection()
    cursor = conn.cursor(cursor_factory=extras.DictCursor)
    get_query = "SELECT product_name FROM user_products"
    cursor.execute(get_query)
    products = cursor.fetchall()
    data = [product[0] for product in products]
    return data

def read_qarz_data():
    conn = connection()
    data = []
    cursor = conn.cursor(cursor_factory=extras.DictCursor)
    try:
        get_query = "SELECT * FROM zakaz_products WHERE status = %s"
        cursor.execute(get_query, (False,))
        temp = cursor.fetchall()

        for k, row in enumerate(temp):
            data.append({
                'product_id': row['id'],
                'product_name': row['product_name'],
                'product_count': row['product_count'],
                'product_price': row['product_price'],
                'client_full_name': row['client_full_name'],
                'client_phone_number': row['client_phone_number'],
                'payment_choice': row['payment_choice'],
                'product_description': row['product_description'],
                'status': row['status'],
            })
    except Exception as e:
        print(f"Error: {e}")
        return {'success': False, 'data': []}
    finally:
        cursor.close()
        conn.close()

    return {'success': True, 'data': data}

def change_status_qarz(product_id):
    conn = connection()
    cursor = conn.cursor(cursor_factory=extras.DictCursor)
    try:
        change_query = "UPDATE zakaz_products SET status = %s WHERE id = %s"
        cursor.execute(change_query, (True, product_id))
        conn.commit()
    except Exception:
        return {'success': False}
    finally:
        conn.close()
        return {'success': True}

def read_all_data():
    conn = connection()
    data = []
    cursor = conn.cursor(cursor_factory=extras.DictCursor)
    try:
        get_query = "SELECT * FROM zakaz_products WHERE is_active = %s"
        cursor.execute(get_query, (True,))
        temp = cursor.fetchall()

        for k, row in enumerate(temp):
            data.append({
                'product_id': row['id'],
                'product_name': row['product_name'],
                'product_count': row['product_count'],
                'product_price': row['product_price'],
                'client_full_name': row['client_full_name'],
                'client_phone_number': row['client_phone_number'],
                'payment_choice': row['payment_choice'],
                'product_description': row['product_description'],
                'status': row['status'],
            })
    except Exception as e:
        print(f"Error: {e}")
        return {'success': False, 'data': []}
    finally:
        cursor.close()
        conn.close()

    return {'success': True, 'data': data}

def change_status_otkaz(product_id):
    conn = connection()
    cursor = conn.cursor(cursor_factory=extras.DictCursor)
    try:
        change_query = "UPDATE zakaz_products SET is_active = %s WHERE id = %s"
        cursor.execute(change_query, (False, product_id))
        conn.commit()
    except Exception:
        return {'success': False}
    finally:
        conn.close()
        return {'success': True}

def get_analyzed_information(is_today=False, is_week=False, is_month=False, start_date=False, starting_date=None):
    conn = connection()
    cursor = conn.cursor(cursor_factory=extras.DictCursor)
    data = []

    if is_today:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        query = """
            SELECT id, product_name, product_count, product_price, payment_choice, is_active, client_phone_number, client_full_name, product_description
            FROM zakaz_products 
            WHERE created_at >= %s
            """
        cursor.execute(query, (today,))
        data = cursor.fetchall()

    elif is_week:
        today = datetime.now()
        monday = (today - timedelta(days=today.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        query = """
            SELECT id, product_name, product_count, product_price, payment_choice, is_active, client_phone_number, client_full_name, product_description
            FROM zakaz_products 
            WHERE created_at >= %s AND created_at <= %s
            """
        cursor.execute(query, (monday, today))
        data = cursor.fetchall()

    elif is_month:
        today = datetime.now()
        first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        query = """
            SELECT id, product_name, product_count, product_price, payment_choice, is_active, client_phone_number, client_full_name, product_description
            FROM zakaz_products 
            WHERE created_at >= %s AND created_at <= %s
            """
        cursor.execute(query, (first_day_of_month, today))
        data = cursor.fetchall()

    elif start_date is True and starting_date:
        try:
            start_date = datetime.strptime(starting_date, '%Y-%m-%d')
        except ValueError as e:
            return {"success": False, "message": "Invalid date format"}
        
        start_of_day = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        query = """
            SELECT id, product_name, product_count, product_price, payment_choice, is_active, client_phone_number, client_full_name, product_description
            FROM zakaz_products 
            WHERE created_at >= %s AND created_at <= %s
        """
        cursor.execute(query, (start_of_day, end_of_day))
        data = cursor.fetchall()

    if not data:
        return {"success": False, 'message': 'No data found for this date range'}
    
    # Convert data to DataFrame
    df = pd.DataFrame(data, columns=[
        'id', 'product_name', 'product_count', 'product_price', 'payment_choice', 'is_active', 'client_phone_number', 'client_full_name', 'product_description'])

    # Create a new column with a list of products by splitting the product names
    df['product_names_split'] = df['product_name'].apply(lambda x: x.split(', '))

    # Create a new column with a list of counts by splitting the product counts
    df['product_counts_split'] = df['product_count'].apply(lambda x: list(map(int, x.split(', '))))

    # Flatten the lists for product names and their corresponding counts
    flattened_products = []
    for i, row in df.iterrows():
        product_names = row['product_names_split']
        product_counts = row['product_counts_split']
        for product, count in zip(product_names, product_counts):
            flattened_products.append((product, count))

    # Aggregate product counts across all rows
    from collections import defaultdict
    product_summary = defaultdict(int)
    for product, count in flattened_products:
        product_summary[product] += count

    # Collect other data for the message
    payment_counts = df['payment_choice'].value_counts().to_dict()
    client_phone = df['client_phone_number'].iloc[0]  # Assuming all records have the same phone number
    client_name = df['client_full_name'].iloc[0]  # Assuming all records have the same client name
    product_description = df['product_description'].iloc[0]  # Assuming all records have the same description

    # Summing up the total price for all products
    total_price = (df['product_price'] * df['product_count']).sum()

    # Create the message with total product counts and other information
    message = f"📅 Period Summary:\n\n💰 Jami Narx: {total_price}\n📦 Zakazlar soni: {len(df)}\n❎ Bekor qilingan: {(df['is_active'] == False).sum()}\n\n📝 Mahsulotlar kesimida:"
    
    for product, total_count in product_summary.items():
        message += f"\n\t\t{product}: {total_count} ta"
    
    message += "\n\n📝 To'lov turlari kesimida:"
    
    for payment, count in payment_counts.items():
        message += f"\n\t\t{payment}: {count} ta"
    
    message += f"\n\n📱 Telefon raqam: {client_phone}\n🤵 Mijoz: {client_name}\n📝 Izoh: {product_description}"

    return {"success": True, "message": message}


from collections import defaultdict

def get_analyzed_information(is_today=False, is_week=False, is_month=False, start_date=False, starting_date=None):
    conn = connection()  # Assuming `connection` is defined elsewhere
    cursor = conn.cursor(cursor_factory=extras.DictCursor)
    data = []

    if is_today:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        query = """
            SELECT id, product_name, product_count, product_price, payment_choice, is_active, client_phone_number, client_full_name, product_description
            FROM zakaz_products 
            WHERE created_at >= %s
            """
        cursor.execute(query, (today,))
        data = cursor.fetchall()

    elif is_week:
        today = datetime.now()
        monday = (today - timedelta(days=today.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        query = """
            SELECT id, product_name, product_count, product_price, payment_choice, is_active, client_phone_number, client_full_name, product_description
            FROM zakaz_products 
            WHERE created_at >= %s AND created_at <= %s
            """
        cursor.execute(query, (monday, today))
        data = cursor.fetchall()

    elif is_month:
        today = datetime.now()
        first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        query = """
            SELECT id, product_name, product_count, product_price, payment_choice, is_active, client_phone_number, client_full_name, product_description
            FROM zakaz_products 
            WHERE created_at >= %s AND created_at <= %s
            """
        cursor.execute(query, (first_day_of_month, today))
        data = cursor.fetchall()

    elif start_date is True and starting_date:
        try:
            start_date = datetime.strptime(starting_date, '%Y-%m-%d')
        except ValueError as e:
            return {"success": False, "message": "Invalid date format"}
        
        start_of_day = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        query = """
            SELECT id, product_name, product_count, product_price, payment_choice, is_active, client_phone_number, client_full_name, product_description
            FROM zakaz_products 
            WHERE created_at >= %s AND created_at <= %s
        """
        cursor.execute(query, (start_of_day, end_of_day))
        data = cursor.fetchall()

    if not data:
        return {"success": False, 'message': 'No data found for this date range'}
    
    df = pd.DataFrame(data, columns=[
        'id', 'product_name', 'product_count', 'product_price', 'payment_choice', 'is_active', 
        'client_phone_number', 'client_full_name', 'product_description'])

    df['product_names_split'] = df['product_name'].apply(lambda x: x.split(', '))
    df['product_counts_split'] = df['product_count'].apply(lambda x: list(map(int, x.split(', '))))
    df['product_price_split'] = df['product_price'].apply(lambda x: list(map(int, str(x).split(', '))))

    flattened_products = []
    for i, row in df.iterrows():
        product_names = row['product_names_split']
        product_counts = row['product_counts_split']
        product_prices = row['product_price_split']
        
        for product, count, price in zip(product_names, product_counts, product_prices):
            flattened_products.append((product, count, price))

    # Product summary
    product_summary = defaultdict(int)
    total_price = 0
    for product, count, price in flattened_products:
        product_summary[product] += count
        total_price += count * price

    payment_counts = df['payment_choice'].value_counts().to_dict()

    if is_today:
        period_label = f"Kunlik {datetime.today().date()}"
    elif is_week:
        period_label = f"Haftalik {monday.date()} dan {datetime.today().date()} gacha"
    elif is_month:
        period_label = f"Oylik {first_day_of_month.date()} dan {datetime.today().date()} gacha"
    else:
        period_label = f"Kunlik {starting_date}"

    message = f"📅 {period_label}\n\n💰 Jami Narx: {total_price}\n📦 Zakazlar soni: {len(df)}\n❎ Bekor qilingan: {(df['is_active'] == False).sum()}\n\n📝 Mahsulotlar kesimida:"

    for product, total_count in product_summary.items():
        message += f"\n\t\t{product}: {total_count} ta"

    message += "\n\n📝 To'lov turlari kesimida:"

    for payment, count in payment_counts.items():
        message += f"\n\t\t{payment}: {count} ta"

    return {"success": True, "message": message}
