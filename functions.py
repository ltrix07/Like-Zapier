import sp_api.base.exceptions
from sp_api.base import Marketplaces
from sp_api.api import Orders
import os.path
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials
import time
from google.oauth2 import service_account
import json
from params import creds_google_path


class WorkWithAmazonAPI:
    def __init__(self, refresh_token, lwa_app_id, lwa_client_secret):
        self.refresh_token = refresh_token
        self.lwa_app_id = lwa_app_id
        self.lwa_client_secret = lwa_client_secret
        self.credentials = {
            "refresh_token": self.refresh_token,
            "lwa_app_id": self.lwa_app_id,
            "lwa_client_secret": self.lwa_client_secret
        }

    def get_all_orders(self, created_after, orders_status):
        res = Orders(credentials=self.credentials, marketplace=Marketplaces.US)
        try:
            orders = res.get_orders(CreatedAfter=created_after.isoformat(),
                                    OrderStatuses=orders_status)
        except sp_api.base.exceptions.SellingApiRequestThrottledException:
            time.sleep(60)
            self.get_all_orders(created_after, orders_status)
        else:
            return orders.payload["Orders"]

    def get_one_order_items(self, order_id):
        res = Orders(credentials=self.credentials, marketplace=Marketplaces.US)
        try:
            order = res.get_order_items(order_id=order_id)
        except sp_api.base.exceptions.SellingApiRequestThrottledException:
            time.sleep(60)
            self.get_one_order_items(order_id)
        else:
            return order.payload


class WorkWithTable:
    def __init__(self, table_id):
        self.table_id = table_id
        self.req_count = 0
        creds = Credentials.from_service_account_file(creds_google_path,
                                                      scopes=['https://www.googleapis.com/auth/spreadsheets'])
        self.service = build('sheets', 'v4', credentials=creds)

    def get_headers(self, worksheet):
        request = self.service.spreadsheets().values().get(
            spreadsheetId=self.table_id,
            range=f'{worksheet}!1:1'
        ).execute()

        return request['values'][0]

    def get_all_info(self, worksheet):
        request = self.service.spreadsheets().values().get(
            spreadsheetId=self.table_id,
            range=worksheet
        ).execute()

        return request['values']

    def get_index_of_column(self, worksheet, columns_names):
        all_columns = self.get_headers(worksheet)
        indices = {}
        for header, col_name in columns_names.items():
            index = all_columns.index(col_name)
            indices[header] = index

        return indices

    def add_to_table(self, worksheet, data, table_range, value_input_options):
        

class ProcessingData:
    def __init__(self):
        pass

    @staticmethod
    def from_json(file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)

        return data

    @staticmethod
    def look_columns(table_data, *args):
        indices = {}

        for arg in args:
            try:
                index = table_data.index(arg)
                indices[arg] = index
            except ValueError:
                indices[arg] = None

        return indices
