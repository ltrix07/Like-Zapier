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


def main():
    global circle_of_check
    spreadsheets_info = ProcessingData.from_json(spreadsheets_info_path)
    now = datetime.now()

    print(f"--- {circle_of_check} круг проверки данных. \
{now.day}.{now.month}.{now.year} {now.hour}:{now.minute if len(str(now.minute > 1)) else f'0{now.minute}'} ---")
    print("")

    for table_info in spreadsheets_info:
        table_worker = WorkWithTable(table_id=table_info["table_id"])
        amazon_api_worker = WorkWithAmazonAPI(refresh_token=table_info["credentials"]["refresh_token"],
                                              lwa_app_id=table_info["credentials"]["lwa_app_id"],
                                              lwa_client_secret=table_info["credentials"]["lwa_client_secret"])

        all_to_table_now = []
        all_to_table_previous = []

        info_in_table_now = table_worker.get_all_info(datetime.now().month)
        info_in_table_previous = table_worker.get_all_info(datetime.now().month - 1)
        orders_list = amazon_api_worker.get_all_orders(created_after=datetime.now() - timedelta(days=1),
                                                       orders_status="Unshipped")

        col_names = ("ID заказа амазона", "№")
        indices_now = ProcessingData.look_columns(info_in_table_now[0], *col_names)
        indices_previous = ProcessingData.look_columns(info_in_table_previous[0], *col_names)

        order_column_index_now, number_index_now = indices_now.values()
        order_column_index_previous, number_index_previous = indices_previous.values()

        if info_in_table_previous[-1][number_index_previous] != "№" and \
                info_in_table_previous[-1][number_index_previous] != "":
            lust_number_previous = int(info_in_table_previous[-1][number_index_previous]) + 1
        else:
            lust_number_previous = 1

        if info_in_table_now[-1][number_index_now] != "№" and info_in_table_now[-1][number_index_now] != "":
            lust_number_now = int(info_in_table_now[-1][number_index_now]) + 1
        else:
            lust_number_now = 1

        orders_in_table_now = [sublist[order_column_index_now] for sublist in info_in_table_now]
        orders_in_table_previous = [sublist[order_column_index_previous] for sublist in info_in_table_previous]

        for order in tqdm(orders_list, desc=f"Обрабатываем {table_info['shop_name']}", ascii=True):
            if order["AmazonOrderId"] not in orders_in_table_now and order["AmazonOrderId"]\
                    not in orders_in_table_previous:

                iso_purchase_date = order["PurchaseDate"]

                if iso_purchase_date is not None:
                    if datetime.fromisoformat(iso_purchase_date.replace("Z", "+00:00")).time() < time(10, 0, 0) \
                            and datetime.fromisoformat(iso_purchase_date.replace("Z", "+00:00")).day == 1:

                        order_info = [""] * len(info_in_table_previous[0])
                        asins = []

                        col_names = ("№", "Business customer", "STATE", "Lastest\nDelivery\nDate",
                                     "Дата заказа", "Q", "ID заказа амазона", "Цена\nпродажи", "ASIN")

                        indices = ProcessingData.look_columns(info_in_table_previous[0], *col_names)
                        number_index, business_customer_index, state_index, latest_date_index, purchase_date_index, \
                            quantity_index, amz_order_id_index, total_amount_index, asin_index = indices.values()

                        item_data_by_order = amazon_api_worker.get_one_order_items(order["AmazonOrderId"])

                        for item in item_data_by_order["OrderItems"]:
                            asins.append(item["ASIN"])

                        order_info[number_index] = lust_number_previous
                        order_info[business_customer_index] = order["IsBusinessOrder"]
                        order_info[state_index] = order["ShippingAddress"]["StateOrRegion"]
                        iso_latest_date = order["LatestShipDate"]
                        order_info[latest_date_index] = datetime.fromisoformat(
                            iso_latest_date.replace("Z", "+00:00")).strftime("%d.%m.%Y %H:%M:%S")
                        order_info[purchase_date_index] = datetime.fromisoformat(
                            iso_purchase_date.replace("Z", "+00:00")).strftime("%d.%m.%Y %H:%M:%S")
                        order_info[quantity_index] = order["NumberOfItemsUnshipped"]
                        order_info[amz_order_id_index] = order["AmazonOrderId"]
                        try:
                            order_info[total_amount_index] = item_data_by_order["OrderItems"][0]["ItemPrice"][
                                "Amount"]
                        except KeyError:
                            order_info[total_amont_index] = 0
                        order_info[asin_index] = u' '.join(asins)

                        all_to_table_previous.append(order_info)
                        lust_number_previous += 1

                    else:
                        order_info = [''] * len(info_in_table_now[0])
                        asins = []

                        col_names = ("№", "Business customer", "STATE", "Lastest\nDelivery\nDate",
                                     "Дата заказа", "Q", "ID заказа амазона", "Цена\nпродажи", "ASIN")

                        indices = ProcessingData.look_columns(info_in_table_now[0], *col_names)
                        number_index, business_customer_index, state_index, latest_date_index, purchase_date_index, \
                            quantity_index, amz_order_id_index, total_amount_index, asin_index = indices.values()

                        item_data_by_order = amazon_api_worker.get_one_order_items(order["AmazonOrderId"])

                        for item in item_data_by_order["OrderItems"]:
                            asins.append(item["ASIN"])

                        order_info[number_index] = lust_number_previous
                        order_info[business_customer_index] = order["IsBusinessOrder"]
                        order_info[state_index] = order["ShippingAddress"]["StateOrRegion"]
                        iso_latest_date = order["LatestShipDate"]
                        order_info[latest_date_index] = datetime.fromisoformat(
                            iso_latest_date.replace("Z", "+00:00")).strftime("%d.%m.%Y %H:%M:%S")
                        order_info[purchase_date_index] = datetime.fromisoformat(
                            iso_purchase_date.replace("Z", "+00:00")).strftime("%d.%m.%Y %H:%M:%S")
                        order_info[quantity_index] = order["NumberOfItemsUnshipped"]
                        order_info[amz_order_id_index] = order["AmazonOrderId"]
                        try:
                            order_info[total_amount_index] = item_data_by_order["OrderItems"][0]["ItemPrice"]["Amount"]
                        except KeyError:
                            order_info[total_amount_index] = 0
                        order_info[asin_index] = ' '.join(asins)

                        all_to_table_now.append(order_info)
                        lust_number_now += 1

        table_worker.add_to_table(worksheet=datetime.now().month, data=all_to_table_now, table_range="A:A",
                                  value_input_options="USER_ENTERED")

        table_worker.add_to_table(worksheet=datetime.now().month - 1, data=all_to_table_previous, table_range="A:A",
                                  value_input_options="USER_ENTERED")

        print(f"Все данные занесены в таблицу {table_info['shop_name']}")
    print("")
    circle_of_check += 1


if __name__ == '__main__':
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

        circle += 1


