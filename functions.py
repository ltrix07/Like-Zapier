import re
import json
import time
import os
from tqdm import tqdm
from typing import Any
from datetime import datetime
from datetime import time as tm


def string_conversion(string: str, methods=None) -> str:
    if methods is None or methods == 'lower&split':
        return re.sub(r'\s+', '', string.lower())
    if methods == 'lower':
        return string.lower()


def read_json(file_path: str) -> dict | list:
    if os.path.isfile(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    return []


def write_json(file_path: str, data_to_write: list | dict):
    with open(file_path, 'w') as file:
        return json.dump(data_to_write, file, indent=4)


def months_get() -> tuple:
    month_now = datetime.now().month
    if month_now == 1:
        month_prev = 12
    else:
        month_prev = month_now - 1

    return str(month_now), str(month_prev)


def get_index_of_column(headers: list, columns_names: dict) -> dict:
    indices = {}
    for header, col_name in columns_names.items():
        index = None
        try:
            index = headers.index(string_conversion(col_name))
        except ValueError:
            pass
        indices[header] = index
    return indices


def filter_by_index(data: list, index: int) -> list:
    result = []
    if index is not None:
        for row in data[1:]:
            try:
                result.append(row[index])
            except IndexError:
                result.append('')
    else:
        return []

    return result


def list_get(my_list: list, index: int, default=None) -> Any:
    try:
        return my_list[index]
    except IndexError:
        return default


def get_next_number(numbers: list) -> int:
    if list_get(numbers, -1) != '':
        try:
            return int(list_get(numbers, -1)) + 1
        except ValueError:
            return 1
        except TypeError:
            return 1
    else:
        return 1


def in_prev_month_or_not(date: str, month: str) -> bool:
    if '_' in month:
        month = int(month.split('_')[1])
    else:
        month = int(month)
    less_10_mor = datetime.fromisoformat(date.replace("Z", "+00:00")).time() < tm(10, 0, 0)
    first_day_or_not = datetime.fromisoformat(date.replace("Z", "+00:00")).day == 1
    now_month_or_not = datetime.fromisoformat(date.replace("Z", "+00:00")).month == month

    if less_10_mor and first_day_or_not and month == datetime.now().month - 1:
        return True

    if less_10_mor and first_day_or_not and now_month_or_not:
        return False

    if now_month_or_not is False:
        return False

    return True


def filter_orders(
        orders: list, order_ids_in_table: list, amz_handler: object, shop_name: str,
        worksheet: str, timeout_btw_req=1
) -> list:
    main = []

    if orders is None:
        orders = []

    for i, order in enumerate(tqdm(orders, desc=f'Processing orders on {shop_name} in worksheet "{worksheet}"')):
        what_month = in_prev_month_or_not(order.get('PurchaseDate'), worksheet)
        if what_month and order.get('AmazonOrderId') not in order_ids_in_table:
            order_item_inf = amz_handler.get_one_order_items(order.get('AmazonOrderId'))

            for item in order_item_inf.get('OrderItems'):
                prep_name = 'no_prep'
                if 'azat' in item.get('SellerSKU').lower():
                    prep_name = 'azat'
                elif 'bro' in item.get('SellerSKU').lower():
                    prep_name = 'bro'

                order_data = {
                    'number': 0,
                    'business_customer': order.get('IsBusinessOrder'),
                    'phone_number': order.get('ShippingAddress', {}).get('Phone'),
                    'state': order.get('ShippingAddress', {}).get('StateOrRegion'),
                    'latest_delivery_date': order.get('LatestDeliveryDate'),
                    'purchase_date': order.get('PurchaseDate'),
                    'quantity': order.get('NumberOfItemsUnshipped'),
                    'amazon_id': order.get('AmazonOrderId'),
                    'selling_price': item.get('ItemPrice', {}).get('Amount'),
                    'shipping_price': item.get('ShippingPrice', {}).get('Amount'),
                    'asin': item.get('ASIN'),
                    'sku': item.get('SellerSKU'),
                    '__prep_name__': prep_name
                }
                main.append(order_data)

            time.sleep(timeout_btw_req)
    return main


def collect_data_for_append(
        data_list: list, indices: dict, len_headers_list: int, number_list: list,
        prep_case: str = 'no_prep'
) -> list:
    result = []
    number = get_next_number(number_list)
    for data_dict in data_list:
        if data_dict.get('__prep_name__') == prep_case:
            row = [''] * len_headers_list
            for key, col in indices.items():
                if col is not None and key in data_dict:
                    if key == 'number':
                        row[col] = number
                    else:
                        row[col] = data_dict[key]

            result.append(row)
            number += 1

    return result
