import google.auth.exceptions
import googleapiclient.errors
import sp_api.base.exceptions
import os.path
import time
import json
import socket
import requests
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

    def get_all_orders(self, orders_status: str, created_after: datetime) -> list:
        res = Orders(credentials=self.credentials, marketplace=Marketplaces.US)
        all_orders = []
        next_token = None

        while True:
            try:
                if next_token:
                    response = res.get_orders(CreatedAfter=created_after.isoformat(),
                                              OrderStatuses=[orders_status],
                                              NextToken=next_token)
                else:
                    response = res.get_orders(CreatedAfter=created_after.isoformat(),
                                              OrderStatuses=[orders_status])

                all_orders.extend(response.payload.get("Orders", []))

                # Проверка наличия следующей страницы
                next_token = response.payload.get("NextToken")
                if not next_token:
                    break
            except sp_api.base.exceptions.SellingApiRequestThrottledException:
                time.sleep(60)
            except sp_api.base.exceptions.SellingApiServerException:
                time.sleep(60)
            except requests.exceptions.ConnectionError:
                time.sleep(60)

        return all_orders

    def get_one_order_items(self, order_id: str) -> dict:
        res = Orders(credentials=self.credentials, marketplace=Marketplaces.US)
        try:
            order = res.get_order_items(order_id=order_id)
        except sp_api.base.exceptions.SellingApiRequestThrottledException:
            time.sleep(60)
            return self.get_one_order_items(order_id)
        except sp_api.base.exceptions.SellingApiServerException:
            time.sleep(60)
            return self.get_one_order_items(order_id)
        except requests.exceptions.ConnectionError:
            time.sleep(60)
            return self.get_one_order_items(order_id)
        except HttpError:
            time.sleep(60)
            return self.get_one_order_items(order_id)
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
        )

        while True:
            try:
                response = request.execute()
                return response.get('values')
            except socket.timeout:
                time.sleep(20)
            except googleapiclient.errors.HttpError:
                time.sleep(60)
            except httplib2.error.ServerNotFoundError:
                time.sleep(60)

    def get_sheets_names(self) -> list:
        request = self.service.spreadsheets().get(
            spreadsheetId=self.table_id
        )
        while True:
            try:
                result = []
                response = request.execute()
                sheets = response.get('sheets')
                for sheet in sheets:
                    if sheet.get("properties"):
                        result.append(sheet.get("properties").get('title'))

                return result
            except socket.timeout:
                time.sleep(20)
            except googleapiclient.errors.HttpError:
                time.sleep(60)
            except httplib2.error.ServerNotFoundError:
                time.sleep(60)
            except google.auth.exceptions.TransportError:
                time.sleep(60)

    def append_to_table(self, worksheet: str, data: list,
                        value_input_option: str = 'INPUT_VALUE_OPTION_UNSPECIFIED') -> dict:
        body = {
            'values': data
        }

        request = self.service.spreadsheets().values().append(
            spreadsheetId=self.table_id,
            range=worksheet,
            valueInputOption=value_input_option,
            insertDataOption='INSERT_ROWS',
            body=body
        )
        while True:
            try:
                response = request.execute()
                return response
            except socket.timeout:
                time.sleep(20)
            except googleapiclient.errors.HttpError:
                time.sleep(60)
            except httplib2.error.ServerNotFoundError:
                time.sleep(60)
