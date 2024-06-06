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


def processing(orders: list, table_handler: object,
               worksheet: str | int, prep_case: str = 'no_prep') -> dict:
    in_table = table_handler.get_all_info(worksheet)
    indices = get_index_of_column(
        [string_conversion(elem) for elem in in_table[0]],
        columns_names
    )

    if indices.get('amazon_id'):
        number = filter_by_index(in_table, indices.get('number'))
        amazon_id = filter_by_index(in_table, indices.get('amazon_id'))

        to_table = []
        for order_inf in orders:
            if order_inf.get('AmazonOrderId') not in amazon_id:
                to_table.append(order_inf)

        data_to_table = collect_data_for_append(
            data_list=to_table, indices=indices, len_headers_list=len(in_table[0]),
            number_list=number, prep_case=prep_case
        )
        return table_handler.append_to_table(worksheet, data_to_table, 'USER_ENTERED')
    else:
        return {'status': 'error', 'message': f'Not found column "amazon_id" in the table'}


def start_zapier(timeout_btw_shops):
    circle = 1
    while True:
        shops_inf = read_json(spreadsheets_info_path)
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

            created_after = (datetime.now() - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
            orders = amz_worker.get_all_orders(created_after=created_after,
                                               orders_status='Unshipped')
            orders_not_in_table = element_in_sheet_or_not(
                table_handler=table_worker,
                worksheets=[month_now, month_prev, f'azat_{month_now}', f'azat_{month_prev}', f'bro_{month_now}',
                            f'bro_{month_prev}'],
                elements=orders,
                columns_names=columns_names
            )
            print(len(orders_not_in_table))

            # sheets = table_worker.get_sheets_names()
            #
            # result = filter_orders(orders, amz_worker, shop_name)
            # month_now_data = result.get('main_now')
            # month_prev_data = result.get('main_prev')
            # azat_now = result.get('azat_now')
            # azat_prev = result.get('azat_prev')
            # bro_now = result.get('bro_now')
            # bro_prev = result.get('bro_prev')
            #
            # if month_now in sheets:
            #     processing(month_now_data, table_worker, month_now) if month_now_data else None
            # if month_prev in sheets:
            #     processing(month_prev_data, table_worker, month_prev) if month_prev_data else None
            # if f'azat_{month_now}' in sheets:
            #     processing(azat_now, table_worker, f'azat_{month_now}', 'azat') if azat_now else None
            # if f'azat_{month_prev}' in sheets:
            #     processing(azat_prev, table_worker, f'azat_{month_prev}', 'azat') if azat_prev else None
            # if f'bro_{month_now}' in sheets:
            #     processing(bro_now, table_worker, f'bro_{month_now}', 'bro') if bro_now else None
            # if f'bro_{month_prev}' in sheets:
            #     processing(bro_prev, table_worker, f'bro_{month_prev}', 'bro') if bro_prev else None
            # print('')
            # time.sleep(timeout_btw_shops)

        circle += 1


if __name__ == '__main__':
    start_zapier(3)
