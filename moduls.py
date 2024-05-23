import sp_api.base.exceptions
import os.path
import time
import json
from functions import *
from params import creds_google_path
from sp_api.base import Marketplaces
from sp_api.api import Orders
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials


class WorkWithAmazonAPI:
    def __init__(self, refresh_token: str, lwa_app_id: str, lwa_client_secret: str):
        self.refresh_token = refresh_token
        self.lwa_app_id = lwa_app_id
        self.lwa_client_secret = lwa_client_secret
        self.credentials = {
            "refresh_token": self.refresh_token,
            "lwa_app_id": self.lwa_app_id,
            "lwa_client_secret": self.lwa_client_secret
        }

    def get_all_orders(self, created_after: datetime, orders_status: str) -> dict:
        res = Orders(credentials=self.credentials, marketplace=Marketplaces.US)
        try:
            orders = res.get_orders(CreatedAfter=created_after.isoformat(),
                                    OrderStatuses=orders_status)
        except sp_api.base.exceptions.SellingApiRequestThrottledException:
            time.sleep(60)
            self.get_all_orders(created_after, orders_status)
        else:
            return orders.payload["Orders"]

    def get_one_order_items(self, order_id: str) -> dict:
        res = Orders(credentials=self.credentials, marketplace=Marketplaces.US)
        try:
            order = res.get_order_items(order_id=order_id)
        except sp_api.base.exceptions.SellingApiRequestThrottledException:
            time.sleep(60)
            self.get_one_order_items(order_id)
        else:
            return order.payload


class WorkWithTable:
    def __init__(self, table_id: str):
        self.table_id = table_id
        self.req_count = 0
        creds = Credentials.from_service_account_file(creds_google_path,
                                                      scopes=['https://www.googleapis.com/auth/spreadsheets'])
        self.service = build('sheets', 'v4', credentials=creds)

    def get_headers(self, worksheet: str) -> list:
        request = self.service.spreadsheets().values().get(
            spreadsheetId=self.table_id,
            range=f'{worksheet}!1:1'
        ).execute()

        lower_headers = [string_conversion(elem) for elem in request['values'][0]]

        return lower_headers

    def get_all_info(self, worksheet: str) -> list:
        request = self.service.spreadsheets().values().get(
            spreadsheetId=self.table_id,
            range=worksheet
        ).execute()

        return request['values']

    def append_to_table(self, worksheet: str, data: list) -> dict:
        body = {
            'values': data
        }

        request = self.service.spreadsheets().values().append(
            spreadsheetId=self.table_id,
            range=worksheet,
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body=body
        )
        response = request.execute()

        return response
