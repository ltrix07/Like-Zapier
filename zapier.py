import json
import time as tmd
import sys
from datetime import datetime, time, timedelta
from params import spreadsheets_info_path, columns_names
from random import randrange
from moduls import WorkWithTable, WorkWithAmazonAPI
from functions import *
sys.stdout.reconfigure(encoding='utf-8')

circle_of_check = 1


def processing(table_handler, amz_handler, worksheet, shop_name):
    in_table = table_handler.get_all_info(worksheet)
    indices = get_index_of_column(
        [string_conversion(elem) for elem in in_table[0]],
        columns_names
    )

    number = filter_by_index(in_table, indices.get('number'))
    order_id = filter_by_index(in_table, indices.get('amazon_id'))

    today = datetime.now()
    orders = amz_handler.get_all_orders(created_after=today - timedelta(days=1), orders_status='Unshipped')

    new_orders = filter_orders(orders, order_id, number, amz_handler, shop_name, worksheet)
    data_to_table = collect_data_for_append(new_orders, indices, len(in_table[0]))
    table_handler.append_to_table(worksheet, data_to_table)


def start_zapier(timeout_btw_shops):
    shops_inf = read_json('./creds/spreadsheets_info.json')
    circle = 1
    while True:
        now = datetime.now()
        print(f'--- Circle of check {circle}. {now.day}.{now.month}.{now.year} \
    {now.hour if len(str(now.hour)) > 1 else f"0{now.hour}"}:{now.minute if len(str(now.minute)) > 1 else f"0{now.minute}"} ---')

        for shop_inf in shops_inf:
            month_now, month_prev = months_get()
            shop_name = shop_inf['shop_name']
            spreadsheet_id = shop_inf['table_id']
            refresh_token = shop_inf['credentials']['refresh_token']
            lwa_app_id = shop_inf['credentials']['lwa_app_id']
            lwa_client_secret = shop_inf['credentials']['lwa_client_secret']

            table_worker = WorkWithTable(table_id=spreadsheet_id)
            amz_worker = WorkWithAmazonAPI(
                refresh_token=refresh_token,
                lwa_app_id=lwa_app_id,
                lwa_client_secret=lwa_client_secret
            )

            processing(table_worker, amz_worker, month_now, shop_name)
            processing(table_worker, amz_worker, month_prev, shop_name)
            print('')
            time.sleep(timeout_btw_shops)

        circle += 1


if __name__ == '__main__':
    start_zapier(10)


