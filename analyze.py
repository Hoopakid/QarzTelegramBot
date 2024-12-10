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


def insert_data_to_products(product_name):
    conn = connection()
    cursor = conn.cursor(cursor_factory=extras.DictCursor)
    try:
        query = "INSERT INTO user_products (product_name) VALUES (%s)"
        cursor.execute(query, (product_name,))
        conn.commit()
        conn.close()
        return {'success': True}
    except Exception:
        return {'success': False}


def delete_data_from_products(product_id):
    conn = connection()
    cursor = conn.cursor(cursor_factory=extras.DictCursor)
    try:
        query = "DELETE FROM user_products WHERE id::integer = %s"
        cursor.execute(query, (product_id,))
        conn.commit()
        conn.close()
        return {'success': True}
    except Exception:
        return {'success': False}


def get_sorted_data():
    conn = connection()
    cursor = conn.cursor(cursor_factory=extras.DictCursor)
    try:
        query = "SELECT * FROM user_products"
        cursor.execute(query)
        datas = cursor.fetchall()
        sorted_ = []
        for data in datas:
            sorted_.append({'product_id': data[0], 'product_name': data[1]})
        conn.close()
        return {'success': True, 'sorted': sorted_}
    except Exception:
        return {'success': False, 'sorted': None}


def insert_data(product_data: dict):
    conn = connection()
    cursor = conn.cursor(cursor_factory=extras.DictCursor)
    returned_id = None
    try:
        if product_data.get('payment_choice') == 'Qarzga berish':
            insert_query = """
                INSERT INTO zakaz_products (product_name, product_count, product_per_price, product_price, product_description, client_phone_number, client_enterprise, payment_choice, qarzdorlik_description, contract_number, enterprise_name, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            cursor.execute(insert_query, (
                product_data.get('product_name'),
                product_data.get('product_count'),
                product_data.get('product_per_price'),
                product_data.get('product_price'),
                product_data.get('product_description'),
                product_data.get('client_phone_number'),
                product_data.get('client_enterprise'),
                product_data.get('payment_choice'),
                product_data.get('qarzdorlik_description'),
                product_data.get('contract_number'),
                product_data.get('enterprise_name'),
                False
            ))
        else:
            insert_query = """
                INSERT INTO zakaz_products (product_name, product_count, product_per_price, product_price, product_description, client_phone_number, client_enterprise, payment_choice, qarzdorlik_description, contract_number, enterprise_name)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            cursor.execute(insert_query, (
                product_data.get('product_name'),
                product_data.get('product_count'),
                product_data.get('product_per_price'),
                product_data.get('product_price'),
                product_data.get('product_description'),
                product_data.get('client_phone_number'),
                product_data.get('client_enterprise'),
                product_data.get('payment_choice'),
                product_data.get('qarzdorlik_description'),
                product_data.get('contract_number'),
                product_data.get('enterprise_name')
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


def get_product_by_id(product_id: int):
    conn = connection()
    cursor = conn.cursor(cursor_factory=extras.DictCursor)
    get_query = "SELECT * FROM zakaz_products WHERE id = %s AND is_active = %s"
    cursor.execute(get_query, (product_id, True))
    product = cursor.fetchone()
    if product is not None:
        return {"success": True, "product": dict(product)}
    return {"success": False}


def get_qarz_product_by_id(product_id: int):
    conn = connection()
    cursor = conn.cursor(cursor_factory=extras.DictCursor)
    get_query = "SELECT * FROM zakaz_products WHERE id = %s AND status = %s"
    cursor.execute(get_query, (product_id, False))
    product = cursor.fetchone()
    if product is not None:
        return {"success": True, "product": dict(product)}
    return {"success": False}


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
    cursor = conn.cursor(cursor_factory=extras.DictCursor)
    try:
        get_query = "SELECT * FROM zakaz_products WHERE status = %s"
        cursor.execute(get_query, (False,))
        temp = cursor.fetchone()
        if temp is not None:
            return {'success': True, 'data': dict(temp)}
    except Exception as e:
        print(f"Error: {e}")
        return {'success': False, 'data': []}


def change_by_section(column_name, product_id, changed_value):
    conn = connection()
    cursor = conn.cursor(cursor_factory=extras.DictCursor)
    try:
        update_query = f"UPDATE zakaz_products SET {column_name} = %s WHERE id = %s"
        cursor.execute(update_query, (changed_value, product_id))
        conn.commit()
        return {'success': True}
    except Exception:
        return {'success': False}


def save_product_detail(product_id, updated_details):
    query = """
    UPDATE zakaz_products
    SET 
        product_name = %s,
        product_count = %s,
        product_per_price = %s,
        product_price = %s,
        product_description = %s,
        updated_at = %s
    WHERE id = %s;
    """
    try:
        conn = connection()
        cursor = conn.cursor()

        cursor.execute(query, (
            updated_details['product_name'],
            updated_details['product_count'],
            updated_details['product_per_price'],
            updated_details['product_price'],
            updated_details['product_description'],
            datetime.now(),
            product_id
        ))
        conn.commit()

        return {'success': True}
    except Exception as e:
        print(f"Database Error: {e}")
        return {'success': False}
    finally:
        conn.close()


def get_only_product(product_id):
    conn = connection()
    cursor = conn.cursor(cursor_factory=extras.DictCursor)
    try:
        get_query = "SELECT * FROM zakaz_products WHERE id = %s"
        cursor.execute(get_query, (product_id,))
        temp = cursor.fetchone()
        if temp is not None:
            return {'success': True, 'data': dict(temp)}
    except Exception as e:
        print(f"Error: {e}")
        return {'success': False, 'data': []}


def insert_to_qarzdorlik(product_id, price):
    conn = connection()
    cursor = conn.cursor(cursor_factory=extras.DictCursor)
    try:
        add_query = "INSERT INTO qarz_statistics (zakaz_id, price) VALUES (%s, %s)"
        cursor.execute(add_query, (product_id, price))
        conn.commit()
        return {'success': True}
    except Exception as e:
        print(f"Error: {e}")
        return {'success': False}


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
                'enterprise_name': row['enterprise_name'],
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


from collections import defaultdict


def get_analyzed_information(is_today=False, is_week=False, is_month=False, start_date=False, starting_date=None):
    conn = connection()
    cursor = conn.cursor(cursor_factory=extras.DictCursor)
    data = []

    if is_today:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        query = """
            SELECT id, product_name, product_count, product_price, payment_choice, is_active, client_phone_number, enterprise_name
            FROM zakaz_products 
            WHERE created_at >= %s
            """
        cursor.execute(query, (today,))
        data = cursor.fetchall()

    elif is_week:
        today = datetime.now()
        monday = (today - timedelta(days=today.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        query = """
            SELECT id, product_name, product_count, product_price, payment_choice, is_active, client_phone_number, enterprise_name
            FROM zakaz_products 
            WHERE created_at >= %s AND created_at <= %s
            """
        cursor.execute(query, (monday, today))
        data = cursor.fetchall()

    elif is_month:
        today = datetime.now()
        first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        query = """
            SELECT id, product_name, product_count, product_price, payment_choice, is_active, client_phone_number, enterprise_name
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
            SELECT id, product_name, product_count, product_price, payment_choice, is_active, client_phone_number, enterprise_name
            FROM zakaz_products 
            WHERE created_at >= %s AND created_at <= %s
        """
        cursor.execute(query, (start_of_day, end_of_day))
        data = cursor.fetchall()

    if not data:
        return {"success": False, 'message': 'No data found for this date range'}

    df = pd.DataFrame(data, columns=[
        'id', 'product_name', 'product_count', 'product_price', 'payment_choice', 'is_active',
        'client_phone_number', 'enterprise_name'])

    df['product_names_split'] = df['product_name'].apply(lambda x: x.split('# '))
    df['product_counts_split'] = df['product_count'].apply(lambda x: list(map(int, x.split('# '))))
    df['product_price_split'] = df['product_price'].apply(lambda x: list(map(int, str(x).split('# '))))

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


import pandas as pd


def export_statistics_to_excel(data, file_name="statistics.xlsx"):
    try:
        if not data.get("success") or "message" not in data:
            print("No valid data available to export.")
            return {'success': False}

        message = data['message']
        product_summary = []
        payment_summary = []

        lines = message.splitlines()
        for line in lines:
            if "📝 Mahsulotlar kesimida:" in line:
                start_index = lines.index(line) + 1
                while start_index < len(lines) and not lines[start_index].startswith("📝 To'lov turlari kesimida:"):
                    product_line = lines[start_index].strip()
                    if product_line:
                        product_name, product_count = map(str.strip, product_line.split(":"))
                        product_summary.append({
                            "Mahsulot nomi": product_name,
                            "Soni": int(product_count.split(" ")[0])
                        })
                    start_index += 1
            if "📝 To'lov turlari kesimida:" in line:
                start_index = lines.index(line) + 1
                while start_index < len(lines):
                    payment_line = lines[start_index].strip()
                    if payment_line:
                        payment_type, payment_count = map(str.strip, payment_line.split(":"))
                        payment_summary.append({
                            "To'lov turi": payment_type,
                            "Soni": int(payment_count.split(" ")[0])
                        })
                    start_index += 1

        df_product_summary = pd.DataFrame(product_summary)
        df_payment_summary = pd.DataFrame(payment_summary)

        absolute_path = os.path.abspath(file_name)
        with pd.ExcelWriter(absolute_path, engine='openpyxl') as writer:
            df_product_summary.to_excel(writer, sheet_name="Mahsulotlar", index=False)
            df_payment_summary.to_excel(writer, sheet_name="To'lovlar", index=False)

        return {'success': True, 'file_path': absolute_path}
    except Exception as e:
        print(f"Error occurred while exporting to Excel: {e}")
        return {'success': False}
