### VERSION WITH TRANSACTIONS ###
import json
import pandas as pd
import flatten_json
import os
from sys import platform
import PySimpleGUI as sg
import datetime
import utility_functions

start_date = '2019/01/01'
end_date = '2020/04/30'

start_date_obj = datetime.datetime.strptime(start_date, '%Y/%m/%d')
end_date_obj = datetime.datetime.strptime(end_date, '%Y/%m/%d')

start_date_shopify = start_date_obj.strftime('%Y/%m/%d')
end_date_shopify = end_date_obj.strftime('%Y/%m/%d')

find_all_refunded_orders = '''
{
  orders(query: "created_at:>=%s AND financial_status:refunded OR financial_status:partially_refunded") {
    edges {
      node {
        id
        name
        customer {
          lastName
        }
        refunds {
          id
        }
      }
    }
  }
}
''' % start_date_shopify

# **************GET DATA FROM SHOPIFY AND WRITE INTO FLATTENED JSON LINE FILE*********************

# Check If Transaction File is present, if not then call function to generate it
def check_transaction_file():
    try:
        with open('cache/transactions.csv') as file:
            print('TRANSACTION FILE HAS ALREADY BEEN GENERATED! :)')
    except FileNotFoundError:
        print("Transaction file not Generated Yet")
        utility_functions.transactions_to_csv()
        print("Transaction file is Generated Now")

# PANDAS visual debugging block see all columns and rows
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

# Get Shopify's Payout Transactions List to use for Dataframe Merges later
check_transaction_file()
df_paytransactions = pd.read_csv('cache/transactions.csv', index_col=0)  # Shopify Payout Transaction Data

df_paytransactions['source_order_id'] = df_paytransactions['source_order_id'].astype(str).replace('\.0', '', regex=True) # Strip excess ID information
df_paytransactions['source_order_transaction_id'] = df_paytransactions['source_order_transaction_id'].astype(
    str).replace('\.0', '', regex=True)

df_paytransactions = df_paytransactions.drop(['id', 'test', 'payout_id', 'payout_status', 'currency'], axis=1) # remove unneccessary columns
df_paytransactions['processed_at'] = pd.to_datetime(df_paytransactions['processed_at'], utc=True)  # Change Column to Pandas DateTime Object
df_paytransactions['processed_at'] = df_paytransactions['processed_at'].dt.tz_convert('america/los_angeles')  # Convert Datetime Object to local Timezone UTC-8:00
df_paytransactions['processed_at'] = df_paytransactions['processed_at'].dt.strftime('%Y/%m/%d')  # Change format

df_paytransactions = df_paytransactions.drop(df_paytransactions[(df_paytransactions['type'] == 'payout')].index) # Drop all rows related to bank payouts
df_paytransactions['fee'] = df_paytransactions['fee'] * -1 # Negate Fees
df_paytransactions = df_paytransactions.rename(columns={'fee': 'FEES', 'net': 'BANK'}) # Rename Columns

df_paytransactions.loc[(df_paytransactions['type'] == 'adjustment'), ['FEES']] = df_paytransactions['amount']   # Shift some data into otner columns conditionally
df_paytransactions.loc[(df_paytransactions['type'] == 'adjustment'), ['BANK']] = 0
df_paytransactions.loc[(df_paytransactions['type'] == 'adjustment'), ['type']] = 'refund' # Change all adjustment rows to refund so we can group together and combine refund rows with Fee's Returned by Shopify
df_paytransactions = df_paytransactions.groupby(['type', 'source_order_id', 'processed_at'], as_index=False).agg({'source_id': 'first',
                                                                                                           'source_type': 'last',
                                                                                                           'FEES': 'sum',
                                                                                                           'BANK': 'sum',
                                                                                                           'source_order_transaction_id': 'last'}) # Aggregate rows to avoid duplicate records when merging
# Run Bulk Query and save to file name
def bulk_query_save_to_jsonf(bulk_query_operation, file_name):
    main_file_status = False
    message = []
    while not main_file_status:
        try:
            with open(f'cache/{file_name}.jsonl') as file:
                print('FILE HAS ALREADY BEEN GENERATED! :)')
                read_data_json = []
                for line in file:
                    read_data_json.append(json.loads(line))
                    json_flattened = (flatten_json.flatten(d, '.') for d in read_data_json)
            main_file_status = True
        except FileNotFoundError:
            print("File not Generated Yet")
            bulk_query = utility_functions.bulk_operation_query(bulk_query_operation)
            query_output = utility_functions.run_query(bulk_query)
            check_problem = query_output["cache"]["bulkOperationRunQuery"]["bulkOperation"]
            if check_problem is None:
                message = [item["message"] for item in query_output["data"]["bulkOperationRunQuery"]["userErrors"]]
                for i in range(len(message)):
                    print(message[i])
                break
            else:
                utility_functions.download_url(utility_functions.poll_bulk_query_status_download(), file_name)
                print("File is Generated Now")
    return json_flattened

# Call this function to Produce List of All Shopify Refunds after specified Date as Bulk GraphQL operation
def refund_function(refund_id):
    refund_detail_bulk_operation_data = '''
    {
      refund(id: "%s") {
        id
        note
        totalRefundedSet {
          presentmentMoney {
            amount
          }
        }
        refundLineItems(first: 10) {
          edges {
            node {
              lineItem {
                id
                sku
                totalDiscountSet {
                  presentmentMoney {
                    amount
                  }
                }
              }
              restockType
              restocked
              quantity
              priceSet {
                shopMoney {
                  amount
                }
              }
              subtotalSet {
                shopMoney {
                  amount
                }
              }
              totalTaxSet {
                shopMoney {
                  amount
                }
              }
            }
          }
        }
        transactions(first: 10) {
          edges {
            node {
              id
              createdAt
              kind
              status
              gateway
              authorizationCode
              amountSet {
                presentmentMoney {
                  amount
                }
              }
            }
          }
        }
      }
    }
    ''' % refund_id
    return refund_detail_bulk_operation_data



# Get List Of All Refund Id's to Iterate and find details, Prep Block
all_refund_ids = pd.DataFrame(bulk_query_save_to_jsonf(find_all_refunded_orders, 'refunds'))
all_refund_ids = all_refund_ids.melt(id_vars=['id', 'name', 'customer.lastName']) # Make dataframe from wide to narrow to simplify merge matching
all_refund_ids = all_refund_ids.sort_values(by='name')
all_refund_ids = all_refund_ids[all_refund_ids['value'].notna()] #Filter all rows that contain values only

# Using list of all refunds from Bulk Query, find all refund details, preprocess them, and make bulk refund detail table
def get_refund_data():
    refunds = pd.DataFrame() # Blank Dataframe to Append to
    for refund_id in all_refund_ids['value']: # Iterate through all refund Id's
        refund_data = utility_functions.callShopifyGraphQL(refund_function(refund_id))  # Call and return Details per Refund ID
        # Block to drill down and normalize nested Json response
        refund_main_df = pd.json_normalize(refund_data)
        refund_main_df = refund_main_df.rename(columns={'refund.id': 'id', 'refund.totalRefundedSet.presentmentMoney.amount': 'TOTAL REFUND'})
        refund_main_df = refund_main_df.drop(columns=['refund.refundLineItems.edges', 'refund.transactions.edges'])
        refund_lines_df = pd.json_normalize(refund_data['refund'], record_path=['refundLineItems', 'edges'], record_prefix='lines_', sep='_')
        refund_transactions_df = pd.json_normalize(refund_data['refund'], record_path=['transactions', 'edges'], record_prefix='transaction_', sep='_')
        # Merge all drilled down and normalized cache together
        refund_merge = pd.concat([refund_main_df, refund_lines_df, refund_transactions_df], axis=1)
        refund_merge = refund_merge.ffill() # Foward fill all NaN values
        refund_merge = refund_merge.rename(columns={'lines_node_priceSet_shopMoney_amount': 'lineitem_amount',
                                                    'lines_node_quantity': 'linesitem_quantity',
                                                    'lines_node_restockType': 'lineitem_restockType',
                                                    'lines_node_restocked': 'lineitem_restocked',
                                                    'lines_node_subtotalSet_shopMoney_amount': 'linesitem_subtotal',
                                                    'lines_node_totalTaxSet_shopMoney_amount': 'linesitem_tax',
                                                    'lines_node_lineItem_id': 'linesitem_id',
                                                    'lines_node_lineItem_sku': 'linesitem_sku',
                                                    'lines_node_lineItem_totalDiscountSet_presentmentMoney_amount' : 'lineItem_Discount',
                                                    'transaction_node_id': 'transaction_id',
                                                    'transaction_node_gateway': 'transaction_gateway',
                                                    'transaction_node_authorizationCode': 'transaction_authorizationCode',
                                                    'transaction_node_createdAt': 'transaction_createdAt',
                                                    'transaction_node_kind': 'transaction_kind',
                                                    'transaction_node_status': 'transaction_status',
                                                    'transaction_node_amountSet_presentmentMoney_amount': 'transaction_amount',
                                                    'id': 'refund_id'
                                                    })

        refunds = pd.concat([refunds, refund_merge], axis=0) # Append to initially empty Refund Dataframe to build Bulk Table
        print('working on it')
    refunds = refunds.reset_index()
    refunds['refund_id'] = refunds['refund_id'].ffill()
    refunds = pd.merge(all_refund_ids, refunds, how='left', left_on='value', right_on='refund_id') # Merge all Data Togteher
    refunds.to_csv('cache/refunds.csv')  # Save into CSV file for later use

get_refund_data() # Generate Refund Data Bulk Dataframe and save into CSV

refund_df = pd.read_csv('cache/refunds.csv', index_col=0)
pending_paypal = refund_df.loc[(refund_df['transaction_status'] == 'PENDING')]
pending_paypal = pending_paypal.iloc[:, 7:25]
pending_paypal = pending_paypal.add_suffix('_pending')
refund_df = refund_df.loc[(refund_df['transaction_status'] != 'PENDING')]
refund_df = pd.merge(refund_df, pending_paypal, how='left', left_on='transaction_authorizationCode', right_on='transaction_authorizationCode_pending')
refund_df.loc[(refund_df['transaction_status_pending'] == 'PENDING'), ['lineitem_amount']] = refund_df['lineitem_amount_pending']
refund_df.loc[(refund_df['transaction_status_pending'] == 'PENDING'), ['lineItem_Discount']] = refund_df['lineItem_Discount_pending']
refund_df.loc[(refund_df['transaction_status_pending'] == 'PENDING'), ['lineitem_restockType']] = refund_df['lineitem_restockType_pending']
refund_df.loc[(refund_df['transaction_status_pending'] == 'PENDING'), ['lineitem_restocked']] = refund_df['lineitem_restocked_pending']
refund_df.loc[(refund_df['transaction_status_pending'] == 'PENDING'), ['linesitem_quantity']] = refund_df['linesitem_quantity_pending']
refund_df.loc[(refund_df['transaction_status_pending'] == 'PENDING'), ['linesitem_subtotal']] = refund_df['linesitem_subtotal_pending']
refund_df.loc[(refund_df['transaction_status_pending'] == 'PENDING'), ['linesitem_tax']] = refund_df['linesitem_tax_pending']
refund_df.loc[(refund_df['transaction_status_pending'] == 'PENDING'), ['linesitem_id']] = refund_df['linesitem_id_pending']
refund_df.loc[(refund_df['transaction_status_pending'] == 'PENDING'), ['linesitem_sku']] = refund_df['linesitem_sku_pending']
refund_df.loc[(refund_df['transaction_status_pending'] == 'PENDING'), ['transaction_id']] = refund_df['transaction_id_pending'] # NOT SURE IF SHOULD USE PENDING OR CLEARED TRANSACTION ID
refund_df= refund_df.loc[refund_df['refund.note'].str.contains('Exchanged', na=False) == False]
refund_df= refund_df.loc[refund_df['transaction_createdAt'].notna()]


exchange_df = refund_df.loc[refund_df['refund.note'].str.contains('Exchanged', na=False)]

refund_df = refund_df.rename(columns={'transaction_createdAt_pending': 'paypal_clearedAt'})
refund_df = refund_df.drop(refund_df.columns[refund_df.columns.str.endswith('_pending')], axis=1)
refund_df.loc[(refund_df['paypal_clearedAt'].notnull()), ['transaction_createdAt', 'paypal_clearedAt']] = \
    refund_df.loc[(refund_df['paypal_clearedAt'].notnull()), ['paypal_clearedAt', 'transaction_createdAt']].values # Swap Paypal Date created and cleared at values

refund_df = refund_df.sort_values(by=['transaction_createdAt','id', 'index'])
refund_df = refund_df.reset_index()

refund_df[['STYLE', 'COLOR', 'SIZE']] = refund_df['linesitem_sku'].str.rsplit("-", n=2, expand=True)


refund_df['lineitem_subtotal_w/tax'] = refund_df['linesitem_subtotal'] + refund_df['linesitem_tax']
refund_df['refund_subtotal'] = refund_df.groupby('refund_id')['lineitem_subtotal_w/tax'].transform('sum')
refund_df['transaction_amount'] = refund_df['transaction_amount'].mask(refund_df['name'].shift(1) == refund_df['name'])
refund_df['refund_subtotal'] = refund_df['refund_subtotal'].mask(refund_df['name'].shift(1) == refund_df['name']) # Set Consecutive Duplicate Values in column to NaN
refund_df['refund_withheld'] = None
refund_df.loc[(refund_df['lineitem_subtotal_w/tax'].notnull()), ['refund_withheld']] = (refund_df['refund_subtotal'] - refund_df['transaction_amount']).round(2)

refund_df['transaction_id'] = refund_df['transaction_id'].str.rsplit('/', 1).str[-1]
refund_df = pd.merge(refund_df, df_paytransactions, how='left', left_on='transaction_id', right_on='source_order_transaction_id')

refund_df = refund_df.rename(columns={'name': 'ORDER #',
                                      'transaction_createdAt': 'DATE',
                                      'customer.lastName': 'CUSTOMER NAME',
                                      'lineitem_restockType': 'TYPE',
                                      'lineitem_restocked': 'RESTOCKED',
                                      'lineitem_amount': 'SHOE PRICE',
                                      'linesitem_quantity': 'QTY',
                                      'lineItem_Discount': 'DISC.',
                                      'linesitem_tax' : 'TAX',
                                      'linesitem_subtotal': 'LINE SUBTOTAL',
                                      'transaction_gateway': 'PROCESSOR',
                                      'refund_withheld' : 'WITHHELD',
                                      'paypal_clearedAt' : 'PAYPAL CLEARED'
                                      })


refund_df.loc[(refund_df['PROCESSOR'] == 'shopify_payments'), ['PROCESSOR']] = 'SHOPIFY'
refund_df.loc[(refund_df['PROCESSOR'] == 'paypal'), ['PROCESSOR']] ='PAYPAL'

refund_df['SHOE PRICE'] = refund_df['SHOE PRICE'] * -1
refund_df['QTY'] = refund_df['QTY'] * -1
refund_df['LINE SUBTOTAL'] = refund_df['LINE SUBTOTAL'] * -1
refund_df['DISC.'] = refund_df['DISC.'] * -1
refund_df['TAX'] = refund_df['TAX'] * -1
refund_df['TOTAL REFUND'] = refund_df['TOTAL REFUND'] * -1


refund_df = refund_df[['ORDER #', 'DATE', 'CUSTOMER NAME', 'TYPE', 'RESTOCKED', 'STYLE', 'COLOR', 'SIZE', 'SHOE PRICE',
                       'QTY', 'LINE SUBTOTAL', 'DISC.', 'TAX','WITHHELD', 'TOTAL REFUND','PROCESSOR', 'FEES', 'BANK',  'PAYPAL CLEARED']]

refund_df['CUSTOMER NAME'] = refund_df['CUSTOMER NAME'].mask(refund_df['CUSTOMER NAME'].shift(1) == refund_df['CUSTOMER NAME'])# Set Consecutive Duplicate Values in column to NaN
refund_df['TYPE'] = refund_df['TYPE'].mask(refund_df['ORDER #'].shift(1) == refund_df['ORDER #'])
refund_df['PROCESSOR'] = refund_df['PROCESSOR'].mask(refund_df['ORDER #'].shift(1) == refund_df['ORDER #'])
refund_df['TOTAL REFUND'] = refund_df['TOTAL REFUND'].mask(refund_df['ORDER #'].shift(1) == refund_df['ORDER #'])
refund_df['DATE'] = refund_df['DATE'].mask(refund_df['ORDER #'].shift(1) == refund_df['ORDER #'])
refund_df['FEES'] = refund_df['FEES'].mask(refund_df['ORDER #'].shift(1) == refund_df['ORDER #'])
refund_df['BANK'] = refund_df['BANK'].mask(refund_df['ORDER #'].shift(1) == refund_df['ORDER #'])

refund_df['ORDER #'] = refund_df['ORDER #'].mask(refund_df['ORDER #'].shift(1) == refund_df['ORDER #']) # Do this row low last as everything depends on it

refund_df['CUSTOMER NAME'] = refund_df['CUSTOMER NAME'].str.upper()
refund_df['DATE'] = pd.to_datetime(refund_df['DATE'])  # Change Column to Pandas DateTime Object
refund_df['DATE'] = refund_df['DATE'].dt.tz_convert('america/los_angeles')
refund_df['DATE'] = refund_df['DATE'].dt.strftime('%m/%d')

refund_df['PAYPAL CLEARED'] = pd.to_datetime(refund_df['PAYPAL CLEARED'])  # Change Column to Pandas DateTime Object
refund_df['PAYPAL CLEARED'] = refund_df['PAYPAL CLEARED'].dt.tz_convert('america/los_angeles')
refund_df['PAYPAL CLEARED'] = refund_df['PAYPAL CLEARED'].dt.strftime('%m/%d')


# **************PANDAS -> EXCEL*********************
writer = pd.ExcelWriter('cache/refunds.xlsx', engine='xlsxwriter')
refund_df.to_excel(writer, sheet_name='Sheet1', index=False, startrow=1, header=False)
workbook = writer.book
worksheet = writer.sheets['Sheet1']

header_format = workbook.add_format({
    'bold': True,
    'border': 5,
    'border_color': '#000000'})

for col_num, value in enumerate(refund_df.columns.values):
    worksheet.write(0, col_num, value)

number_rows = len(refund_df.index) + 1
footer_row = number_rows + 1

bold_format = workbook.add_format({'bold': True})
money = workbook.add_format(
    {'bold': True, 'num_format': '_($* #,##0.00_);_($* (#,##0.00);_($* "-"??_);_(@_)'})
add_border = workbook.add_format({'border': 1, 'border_color': '#000000'})

green_highlight = workbook.add_format({'bg_color': '#C6EFCE',
                                       'font_color': '#006100'})
red_highlight = workbook.add_format({'bg_color': '#FFC7CE',
                                     'font_color': '#9C0006'})
yellow_highlight = workbook.add_format({'bg_color': '#FFEB9C', 'font_color': '#9C6500'})

worksheet.set_column('A:B', None, bold_format)
worksheet.set_column('C:C', 16, bold_format)
worksheet.set_column('D:D', None, None, {'hidden': True})
worksheet.set_column('E:E', 9, bold_format)
worksheet.set_column('F:F', 12, bold_format)
worksheet.set_column('G:H', 5, bold_format)
worksheet.set_column('I:I', 10, money)
worksheet.set_column('J:J', 4, bold_format)
worksheet.set_column('K:O', 12, money)
worksheet.set_column('P:P', 10.25, bold_format)
worksheet.set_column('Q:R', 12, money)
worksheet.set_column('S:S', 13.50, bold_format)


worksheet.conditional_format("$A$1:$S$%d" % number_rows,
                             {"type": "formula",
                              "criteria": '=INDIRECT("D"&ROW())="NO_RESTOCK"',
                              "format": yellow_highlight
                              })

worksheet.conditional_format("$A$1:$S$%d" % number_rows,
                             {"type": "formula",
                              "criteria": '=INDIRECT("D"&ROW())="CANCEL"',
                              "format": red_highlight
                              })

worksheet.conditional_format(f'J2:J{number_rows}',
                             {'type': 'cell', 'criteria': 'less than', 'value': -1, 'format': green_highlight})

worksheet.conditional_format(f'A2:S{number_rows}', {'type': 'blanks', 'format': add_border})
worksheet.conditional_format(f'A2:S{number_rows}', {'type': 'no_blanks', 'format': add_border})
worksheet.conditional_format('A1:S2', {'type': 'blanks', 'format': header_format})
worksheet.conditional_format('A1:S1', {'type': 'no_blanks', 'format': header_format})
worksheet.conditional_format(f'J{footer_row}:R{footer_row}', {'type': 'blanks', 'format': header_format})
worksheet.conditional_format(f'J{footer_row}:R{footer_row}', {'type': 'no_blanks', 'format': header_format})

worksheet.write_formula(f'J{footer_row}', f'=SUM(J2:J{number_rows})')
worksheet.write_formula(f'K{footer_row}', f'=SUM(K2:K{number_rows})')
worksheet.write_formula(f'L{footer_row}', f'=SUM(L2:L{number_rows})')
worksheet.write_formula(f'M{footer_row}', f'=SUM(M2:M{number_rows})')
worksheet.write_formula(f'N{footer_row}', f'=SUM(N2:N{number_rows})')
worksheet.write_formula(f'O{footer_row}', f'=SUM(O2:O{number_rows})')
worksheet.write_formula(f'Q{footer_row}', f'=SUM(Q2:Q{number_rows})')
worksheet.write_formula(f'R{footer_row}', f'=SUM(R2:R{number_rows})')



writer.save()

if platform == 'darwin':
    os.system("open cache/refunds.xlsx -a '/Applications/Microsoft Excel.app' ")
else:
    os.system("start EXCEL.EXE cache/refunds.xlsx")
    print(platform)
