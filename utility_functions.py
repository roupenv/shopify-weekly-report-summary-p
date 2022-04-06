import config
import time
from datetime import datetime
import calendar
import json
from sys import platform
import pandas as pd
import requests
import os

# LINK TO SHOPIFY CONFIG INFO
shopUrl = config.shopUrl
shopurl_strip = config.shopUrl_strip
api_key = config.api_key
api_secret = config.api_secret
api_version = '2020-04'

# LINK TO PAYPAL CONFIG INFO
paypal_url = config.paypal_url
paypal_clientid = config.paypal_clientid
paypal_secret = config.paypal_secret


# ************************ GLOBAL  **************************

# GENERATE LIST OF MONTHS BETWEEN GIVEN START AND END DATE INCLUSIVE
def monthlist(start_date, end_date):
    start = datetime.strptime(start_date, '%Y/%m/%d')
    end = datetime.strptime(end_date, '%Y/%m/%d')
    total_months = lambda dt: dt.month + 12 * dt.year
    mlist = []
    for tot_m in range(total_months(start) - 1, total_months(end)):
        y, m = divmod(tot_m, 12)
        mlist.append(datetime(y, m + 1, 1).strftime("%Y-%m"))
    return mlist


def clear_cache(file_list, answer='Yes'):
    list_of_files = ['cache/' + file for file in file_list]

    while True:
        if answer == 'Yes':
            for file in list_of_files:
                try:
                    os.remove(file)
                except FileNotFoundError:
                    print(file, ' already deleted')
                    continue
            break
        elif answer == 'No':
            break
        else:
            print('Please input Yes or No')
            break


def create_check_for_directory():
    if not os.path.exists('cache'):
        os.makedirs('cache')


def save_dates_to_cache(transactions_earliest_date='', transactions_latest_date=''):
    create_check_for_directory()
    loaded_dates = {'most_earliest_date': transactions_earliest_date, 'most_recent_date': transactions_latest_date}
    loaded_dates_json = json.dumps(obj=loaded_dates)

    with open('cache/dates.json', 'w') as file:
        file.write(loaded_dates_json)


def latest_transaction_id(transaction_id):
    create_check_for_directory()
    with open('cache/latest_transaction_id.txt', 'w') as file:
        file.write(transaction_id)

def check_column_exists(column_name, dataframe):
    if column_name in dataframe:
        return column_name
    else:
        return None



# ************************ SHOPIFY  **************************


def callShopifyGraphQL(GraphQLString):
    headers = {
        'Content-Type': 'application/json',
        'X-Shopify-Access-Token': api_secret}
    response = requests.post(f'{shopUrl}', json={'query': GraphQLString}, headers=headers)
    if response.status_code == 400:
        raise ValueError('GraphQL error:' + response.text)
    answer = json.loads(response.text)
    throttleStatus = None
    if 'errors' in answer:
        try:
            throttleStatus = answer['errors'][0]['extensions']['code']
        except:
            pass
        if throttleStatus != 'THROTTLED':
            raise ValueError('GraphQL error:' + repr(answer['errors']))
    qlRequired = answer['extensions']['cost']['requestedQueryCost']
    qlLimit = answer['extensions']['cost']['throttleStatus']['maximumAvailable']
    qlAvail = answer['extensions']['cost']['throttleStatus']['currentlyAvailable']
    print('GraphQL throttling status: ' + str(qlAvail) + '/' + str(int(qlLimit)))
    while throttleStatus == 'THROTTLED':
        print('Waiting (GraphQL throttling)... ' + str(qlAvail) + '/' + str(int(qlLimit)) + ' used, requested ' + str(
            qlRequired))
        time.sleep(1)
        response = requests.post(f'{shopUrl}', json={'query': GraphQLString}, headers=headers)
        answer = json.loads(response.text)
        try:
            throttleStatus = answer['errors'][0]['extensions']['code']
        except:
            throttleStatus = None
            pass
    return answer['data']


def payout_transaction_rest_query(page='', since_id=None):
    headers = {"Content-Type": "application/json"}

    if since_id != None:
        response = requests.get(
            f'https://{api_key}:{api_secret}@{shopurl_strip}/{api_version}/shopify_payments/balance/transactions.json?since_id={since_id}',
            headers=headers)
    else:
        response = requests.get(
            f'https://{api_key}:{api_secret}@{shopurl_strip}/{api_version}/shopify_payments/balance/transactions.json?page_info={page}',
            headers=headers)

    return response


def build_json(last_id=None):
    is_next = 'next'
    page = ''
    jsonf = []

    if last_id == None:
        while is_next == 'next':
            link = payout_transaction_rest_query(page).headers.get('Link')
            link = link.split(',')[-1]
            page_info_init = link.split('page_info=', 1)[1]
            next_page_info = page_info_init.split('>', 1)[0]
            is_next = page_info_init.split('rel="')[1]
            is_next = is_next.split('"')[0]
            transactions = payout_transaction_rest_query(page).json().get('transactions')
            jsonf.extend(transactions)
            page = next_page_info
            print('Running')
    elif last_id != None:
        remebered_last_id = ''
        while last_id != '':
            try:
                transactions = payout_transaction_rest_query(since_id=last_id).json().get('transactions')
                last_id = transactions[-1]['id']
                jsonf.extend(transactions)

                remebered_last_id = str(last_id)
                print(remebered_last_id)
                print('Updating')
            except IndexError:
                latest_transaction_id(remebered_last_id)
                break

    return jsonf

def transactions_to_csv(since_id=None):
    df_transactions = pd.DataFrame(build_json(last_id=since_id))
    df_transactions['source_order_id'] = df_transactions['source_order_id'].astype(str).replace('\.0', '', regex=True)
    df_transactions['source_order_transaction_id'] = df_transactions['source_order_transaction_id'].astype(str).replace(
        '\.0', '', regex=True)
    create_check_for_directory()
    if since_id != None:
        with open('cache/shopify_transactions.csv', 'a') as file:
            file.write('\n') # Start New Line, in Csv File
        df_transactions.to_csv('cache/shopify_transactions.csv', mode='a', header=False)
        temp_trans_df = pd.read_csv('cache/shopify_transactions.csv', index_col=0)
        temp_trans_df = temp_trans_df.sort_values(by=['processed_at'], ascending=False)
        temp_trans_df = temp_trans_df.reset_index(drop=True)
        temp_trans_df.to_csv('cache/shopify_transactions.csv', index=False)
        print('Updated')
    else:
        df_transactions.to_csv('cache/shopify_transactions.csv')

    return df_transactions


def csv_to_df(file_location):
    df = pd.read_csv(file_location)
    return df


def run_query(query):  # A simple function to use requests.post to make the API call. Note the json= section.
    headers = {
        'Content-Type': 'application/json',
        'X-Shopify-Access-Token': api_secret}
    response = requests.post(f'{shopUrl}', json={'query': query}, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))


def bulk_operation_query(bulk_query):
    bulk_operation_std = '''
    mutation {
      bulkOperationRunQuery(
       query: """%s"""
      ) {
        bulkOperation {
          id
          status
        }
        userErrors {
          field
          message
        }
      }
    }''' % bulk_query
    return bulk_operation_std


def poll_bulk_query_status_download():
    status = ''''''
    operation_status = "RUNNING"
    poll_output = {}
    while operation_status == "RUNNING":
        status = '''
        {
          currentBulkOperation {
            id
            status
            errorCode
            createdAt
            completedAt
            objectCount
            fileSize
            url
            partialDataUrl
          }
        }
        '''
        poll_output = run_query(status)
        operation_status = poll_output["data"]["currentBulkOperation"]["status"]
        print(operation_status)
        time.sleep(1)
    url = poll_output["data"]["currentBulkOperation"]["url"]
    return url


def download_url(url, file_name):
    url_file = requests.get(url)
    create_check_for_directory()
    with open(f'cache/{file_name}.jsonl', 'w') as file:
        file.write(url_file.text)


def cancel_bulk_operation_query(bulk_query_id):
    bulk_operation_std = '''
    mutation {
      bulkOperationCancel(id: """%s""") {
        bulkOperation {
          status
        }
        userErrors {
          field
          message
        }
      }
    }
    ''' % (bulk_query_id)
    return bulk_operation_std
    # print(bulk_op_q_data)


# ************************ PAYPAL **************************

# GENERATE PAYPAL ACCESS TOKEN
def paypal_access_token():
    headers = {'Accept': 'application/json', 'Accept-Language': 'en_US'}
    data = {'grant_type': 'client_credentials'}
    response = requests.post(f'{paypal_url}/v1/oauth2/token', headers=headers, data=data,
                             auth=(paypal_clientid, paypal_secret))
    response_details = response.json()
    paypal_access_token = response_details['access_token']
    create_check_for_directory()
    with open(f'cache/paypal_access_token.txt', 'w') as file:
        file.write(paypal_access_token)

    time_expire = round(float(response_details['expires_in']) / 3600,
                        2)  # PAYAL RETURNS TIME TO EXPIRE IN SECONDS, CONVERTING TO HOURS
    print('Paypal Access Token Generated with ', time_expire, 'hours to expire')
    return paypal_access_token


# PAYPAL TRANSACTIONS SEARCH REST QUERY
def paypal_transaction_rest_query(year_month, last_day_of_month):
    good_response = False
    while not good_response:

        file_status = False
        while not file_status:
            try:
                with open('cache/paypal_access_token.txt') as file:
                    current_access_token = file.read()
                print('We have an Access Token. Need to Check if Valid.')
                file_status = True
            except FileNotFoundError:
                print("File not Generated Yet")
                paypal_access_token()

        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {current_access_token}'}

        params = (
            ('fields', 'transaction_info'),
            ('start_date', f'{year_month}-01T00:00:00-0700'),
            ('end_date', f'{year_month}-{last_day_of_month}T23:59:59-0700'),
            ('page_size', '500'),  # Maximum Value
            ('page', '1')
        )

        response = requests.get(f'{paypal_url}/v1/reporting/transactions', headers=headers,
                                params=params)

        # print(response.status_code)
        if response.status_code == 401:
            print('Need To Generate New Access Token')
            paypal_access_token()
        else:
            good_response = True
            print('Access Token Is Valid')
    return response


# GENERATE PAYPAL TRANSACTIONS CSV FILE
def paypal_transactions_to_csv(start_date, end_date):
    # GENERATE LIST OF MONTHS BETWEEN GIVEN START AND END DATE INCLUSIVE
    list_of_months = monthlist(start_date, end_date)
    # Initialize Empty DATAFRAME TO APPEND TO
    paypal_transactions = pd.DataFrame()

    for month_info in list_of_months:
        year_month = month_info

        end_date_of_month = datetime.strptime(month_info, '%Y-%m')
        end_date_of_month_year = int(end_date_of_month.strftime("%Y"))
        if platform == 'darwin':
            end_date_of_month_number = int(end_date_of_month.strftime("%-m"))
        else:
            end_date_of_month_number = int(end_date_of_month.strftime("%m"))

        last_day_of_month = calendar.monthrange(end_date_of_month_year, end_date_of_month_number)[1]

        paypal_transaction_data = paypal_transaction_rest_query(year_month, last_day_of_month).json()

        # IF THERE IS AN ERROR, SHOW THE MESSAGE AND BREAK THE LOOP
        if 'message' in paypal_transaction_data.keys():
            print(paypal_transaction_data['message'])
            break

        paypal_transactions_month = pd.json_normalize(paypal_transaction_data, record_path='transaction_details',
                                                      sep='_')
        paypal_transactions = pd.concat([paypal_transactions, paypal_transactions_month], axis=0)

    paypal_transactions = paypal_transactions.reset_index()
    paypal_transactions = paypal_transactions.drop(columns='index')
    paypal_transactions.columns = paypal_transactions.columns.str.replace('^transaction_info_', '', regex=True)
    paypal_transactions.columns = paypal_transactions.columns.str.replace('^paypal_', '', regex=True)
    paypal_transactions = paypal_transactions.add_prefix('paypal_')
    create_check_for_directory()
    paypal_transactions.to_csv('cache/paypal_transactions.csv')
