from functions import read_json, write_json


def add_shop(google_creds_path, shop_ifo_path):
    while True:
        print('If you want to quite - press "q"')
        google_creds_info = read_json(google_creds_path)
        service_mail = google_creds_info.get('client_email')
        print(f"Before adding a store to the list, make sure the service mail has access to the table - {service_mail}")
        creds = read_json(shop_ifo_path)

        shop_name = input('Input shop name: ').strip()
        if shop_name == 'q':
            break
        for shop in creds:
            if shop.get('shop_name') == shop_name:
                print('This store is already in the data list')
                break

        table_id = input('Input table_id: ').strip()
        if table_id == 'q':
            break
        refresh_token = input('Input refresh_token: ').strip()
        if refresh_token == 'q':
            break
        lwa_app_id = input('Input lwa_app_id: ').strip()
        if lwa_app_id == 'q':
            break
        lwa_client_secret = input('Input lwa_client_secret: ').strip()
        if lwa_client_secret == 'q':
            break

        if shop_name and table_id and refresh_token and lwa_app_id and lwa_client_secret:
            data = {
                'shop_name': shop_name,
                'table_id': table_id,
                'credentials': {
                    'refresh_token': refresh_token,
                    'lwa_app_id': lwa_app_id,
                    'lwa_client_secret': lwa_client_secret
                }
            }

            creds.append(data)
            write_json(shop_ifo_path, creds)

            print('Shop was added successfully!')
            print()
        else:
            print('One of the fields was not filled in or filled in incorrectly, please try again.')
            print()
            return


def delete_table(shop_ifo_path):
    while True:
        print('If you want to quite - press "q"')
        shop_name = input('What shop name to delete (The register is accounted): ').strip()
        if shop_name == 'q':
            break
        creds = read_json(shop_ifo_path)
        for cred in creds:
            if cred.get('shop_name') == shop_name:
                index = creds.index(cred)
                creds.pop(index)
                print('Shop was deleted successfully!')
                break

        write_json(shop_ifo_path, creds)


if __name__ == '__main__':
    google_creds_path = './creds/creds_google.json'
    shop_ifo_path = './creds/spreadsheets_info.json'

    while True:
        print()
        print(
            '1. Add table\n'
            '2. Delete table\n'
        )
        what_to_do = input('Choose action: ').strip()
        if what_to_do == 'q':
            break

        if what_to_do == '1':
            add_shop(google_creds_path, shop_ifo_path)
            print('If you want to quite - press "q"')
        elif what_to_do == '2':
            delete_table(shop_ifo_path)
            print('If you want to quite - press "q"')
