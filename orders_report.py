import json
import pandas as pd
import os
from sys import platform
import xlsxwriter
import datetime
import utility_functions



def generate_order_report(start_date,end_date):
    start_date_obj = datetime.datetime.strptime(start_date, '%Y/%m/%d')
    end_date_obj = datetime.datetime.strptime(end_date, '%Y/%m/%d')


    start_date_shopify = start_date_obj.strftime('%Y/%m/%d')
    end_date_shopify = end_date_obj.strftime('%Y/%m/%d')

    bulk_operation_data = '''
    {
      orders(query: "created_at:>=%s"){
        edges {
          node {
            id
            name
            createdAt
            cancelledAt
            edited
            customer {
              lastName
            }
            lineItems {
              edges {
                node {
                  id
                  sku
                  quantity
                  fulfillmentStatus
                  fulfillableQuantity
                  unfulfilledQuantity
                  refundableQuantity
                  originalUnitPriceSet {
                    presentmentMoney {
                      amount
                    }
                  }
                  originalTotalSet {
                    presentmentMoney {
                      amount
                    }
                  }
                  totalDiscountSet {
                    presentmentMoney {
                      amount
                    }
                  }
                  discountedTotalSet {
                    presentmentMoney {
                      amount
                    }
                  }
                }
              }
            }
            taxLines {
              title
              priceSet {
                presentmentMoney {
                  amount
                }
              }
            }
            cartDiscountAmountSet {
              presentmentMoney {
                amount
              }
            }
            shippingLine {
              originalPriceSet {
                presentmentMoney {
                  amount
                }
              }
            }
            totalDiscountsSet {
              presentmentMoney {
                amount
              }
            }
            netPaymentSet {
              presentmentMoney {
                amount
              }
            }
            totalPriceSet {
              presentmentMoney {
                amount
              }
            }
            transactions {
              id
              createdAt
              authorizationCode
              gateway
              kind
              status
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
    ''' % start_date_shopify

    # **************GET DATA FROM SHOPIFY AND WRITE INTO FLATTENED JSON LINE FILE*********************
    main_file_status = False
    message = []
    while not main_file_status:
        try:
            with open('cache/shopify_order_data.jsonl') as file:
                print('Order Data File Has Been Generated! :)')
                read_data_json = []
                order_details = []
                sku_details = []
                for line in file:
                    read_data_json.append(json.loads(line))
                for obj in read_data_json:
                    if list(obj.keys())[1] == 'sku':
                        sku_details.append(obj)
                    elif list(obj.keys())[0] == 'id':
                        order_details.append(obj)
            main_file_status = True
        except FileNotFoundError:
            print("Order Data File Not Generated Yet")
            bulk_query = utility_functions.bulk_operation_query(bulk_operation_data)
            query_output = utility_functions.run_query(bulk_query)
            check_problem = query_output["data"]["bulkOperationRunQuery"]["bulkOperation"]

            if check_problem is None:
                message = [item["message"] for item in query_output["data"]["bulkOperationRunQuery"]["userErrors"]]
                for i in range(len(message)):
                    print(message[i])
                break
            else:
                utility_functions.download_url(utility_functions.poll_bulk_query_status_download(), 'shopify_order_data')
                print("File Is Generated Now")


    try:
        with open('cache/shopify_transactions.csv') as file:
            print('Transaction File Has Already Been Generated! :)')
    except FileNotFoundError:
        print("Transaction File Not Generated Yet")
        utility_functions.transactions_to_csv()
        print("Transaction File Is Generated Now")


    try:
        with open('cache/paypal_transactions.csv') as file:
            print('Paypal Transactions File Has Already Been Generated! :)')
    except FileNotFoundError:
        print("Paypal Transaction File Not Generated Yet")
        utility_functions.paypal_transactions_to_csv(start_date, end_date)
        print("Paypal Transaction File Is Generated Now")

    # **************SHOPIFY GRAPH QUERY -> PANDAS DATAFRAME*********************
    if not message:
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', None)


        df = pd.json_normalize(order_details, sep='_')
        df = df.drop(columns=['taxLines','transactions', 'cartDiscountAmountSet'])
        df = df.rename(columns={'name': 'ORDER#',
                                'createdAt': 'order_createdAt',
                                'customer_lastName': 'CUSTOMER NAME',
                                'cartDiscountAmountSet_presentmentMoney_amount' : 'ORDER DISCOUNT',
                                'shippingLine_originalPriceSet_presentmentMoney_amount': 'FREIGHT',
                                'totalDiscountsSet_presentmentMoney_amount': 'TOTAL DISCOUNTS',
                                'totalPriceSet_presentmentMoney_amount': 'TOTAL PRICE',
                                'netPaymentSet_presentmentMoney_amount' : 'NET PAYMENT'
                                })
        df['CUSTOMER NAME'] = df['CUSTOMER NAME'].str.upper() # Make Customer Last Names All UpperCase

        if 'ORDER DISCOUNT' in df:
            df[['ORDER DISCOUNT', 'FREIGHT', 'TOTAL DISCOUNTS', 'NET PAYMENT', 'TOTAL PRICE']] = \
                df[['ORDER DISCOUNT',  'FREIGHT', 'TOTAL DISCOUNTS', 'NET PAYMENT', 'TOTAL PRICE']].apply(pd.to_numeric)
        else:
            df[['FREIGHT', 'TOTAL DISCOUNTS', 'NET PAYMENT', 'TOTAL PRICE']] = \
                df[['FREIGHT', 'TOTAL DISCOUNTS', 'NET PAYMENT', 'TOTAL PRICE']].apply(pd.to_numeric)

        tax_lines = pd.json_normalize(order_details, record_path='taxLines', meta='id',sep='_')
        tax_lines = tax_lines.rename(columns={'priceSet_presentmentMoney_amount': 'amount'})
        tax_lines = tax_lines.pivot(index='id', columns='title', values='amount')
        tax_lines = tax_lines.reset_index()

        if 'CA State Tax' in tax_lines:
            tax_lines.loc[(tax_lines['CA State Tax'].notna()), ['California State Tax']] = tax_lines['CA State Tax']
            tax_lines = tax_lines.drop(columns='CA State Tax')

        tax_lines[['Los Angeles County Tax', 'California State Tax']] = tax_lines[['Los Angeles County Tax', 'California State Tax']].apply(pd.to_numeric)

        if 'Pasadena Municipal Tax' in tax_lines:
            tax_lines[['Pasadena Municipal Tax']] = tax_lines[['Pasadena Municipal Tax']].apply(pd.to_numeric)
            tax_lines.loc[(tax_lines['Pasadena Municipal Tax'].notna()), ['Los Angeles County Tax']] = (tax_lines['Los Angeles County Tax'] + tax_lines['Pasadena Municipal Tax'])
            tax_lines = tax_lines.drop(columns='Pasadena Municipal Tax')

        tax_lines = tax_lines.rename(columns={'California State Tax': 'CA TAX', 'Los Angeles County Tax': 'LA TAX'})
        df = pd.merge(df, tax_lines, how='left', on='id')

        transactions = pd.json_normalize(order_details, record_path='transactions', record_prefix='trans_', meta='id', sep='_')
        transactions['trans_id'] = transactions['trans_id'].astype(str).replace('\D', '', regex=True)
        transactions = transactions[(transactions['trans_status'] == 'SUCCESS') & (transactions['trans_kind'] == 'SALE')]
        transactions = transactions.drop(columns=['trans_kind','trans_status'])
        transactions = transactions.rename(columns={'trans_amountSet_presentmentMoney_amount' : 'trans_amount'})
        df = pd.merge(df, transactions, how='left', on='id')
        sku_details = pd.json_normalize(sku_details)
        sku_details = sku_details.rename(columns={'id': 'line_id',
                                                  'quantity': 'QTY',
                                                  'originalUnitPriceSet.presentmentMoney.amount' : 'SHOE PRICE',
                                                  'originalTotalSet.presentmentMoney.amount': 'SUBTOTAL',
                                                  'totalDiscountSet.presentmentMoney.amount': 'LINE DISC.',
                                                  'discountedTotalSet.presentmentMoney.amount': 'LINE SUBTOTAL'})
        sku_details[['SHOE PRICE', 'SUBTOTAL', 'LINE DISC.', 'LINE SUBTOTAL']] = \
            sku_details[['SHOE PRICE', 'SUBTOTAL', 'LINE DISC.', 'LINE SUBTOTAL']].apply(pd.to_numeric)
        sku_details['ORDER LINES TOTAL'] = sku_details.groupby('__parentId', as_index=False)['LINE SUBTOTAL'].transform('sum')
        sku_details['ORDER LINES TOTAL'] = sku_details['ORDER LINES TOTAL'].mask(sku_details['__parentId'].shift(1) == sku_details['__parentId'])
        df = pd.merge(df, sku_details, how='left', left_on='id', right_on='__parentId')

        # SHOW ORDER INFORMATION ONCE
        df_order = df.iloc[:, 1:16].mask(df['id'].shift(1) == df['id'])
        df_id = df.iloc[:, 0:1]
        df_sku = df.iloc[:, 16:]
        df = pd.concat([df_id, df_order, df_sku], axis=1)

        # CHECK FOR ANY DISCREPENCIES
        if 'ORDER DISCOUNT' in df:
            df['check'] = df['ORDER LINES TOTAL'] + df['CA TAX'].fillna(0) + df['LA TAX'].fillna(0) +\
                                                             df['FREIGHT'].fillna(0) - df['ORDER DISCOUNT'].fillna(0)
        else:
            df['check'] = df['ORDER LINES TOTAL'] + df['CA TAX'].fillna(0) + df['LA TAX'].fillna(0) + \
                          df['FREIGHT'].fillna(0)
        df[['trans_amount']]=df[['trans_amount']].apply(pd.to_numeric)
        df['dif'] = (df['check'] - df['trans_amount']).round(2)


        df_shopify_trans_detail = pd.read_csv('cache/shopify_transactions.csv', index_col=0)  # Shopify Payout Transaction Data
        df_shopify_trans_detail['source_order_id'] = df_shopify_trans_detail['source_order_id'].astype(str).replace('\.0', '', regex=True)
        df_shopify_trans_detail['source_order_transaction_id'] = df_shopify_trans_detail['source_order_transaction_id'].astype(str).replace(
            '\.0', '', regex=True)

        # New Dataframe to find last Transaction ID
        last_trans_id_df = df_shopify_trans_detail
        last_trans_id_df = last_trans_id_df[
            last_trans_id_df['processed_at'] == last_trans_id_df['processed_at'].max()]
        last_trans_id = str(last_trans_id_df['id'].values[0])
        utility_functions.latest_transaction_id(last_trans_id)



        df_shopify_trans_detail = df_shopify_trans_detail.drop(['id', 'test', 'payout_id', 'payout_status', 'currency'], axis=1)
        df_shopify_trans_detail['processed_at'] = pd.to_datetime(df_shopify_trans_detail['processed_at'], utc=True)  # Change Column to Pandas DateTime Object
        df_shopify_trans_detail['processed_at'] = df_shopify_trans_detail['processed_at'].dt.tz_convert('america/los_angeles')  # Convert Datetime Object to local Timezone UTC-8:00
        df_shopify_trans_detail['processed_at'] = df_shopify_trans_detail['processed_at'].dt.strftime('%Y/%m/%d')  # Change format
        df_shopify_trans_detail = df_shopify_trans_detail.drop(df_shopify_trans_detail[(df_shopify_trans_detail['type'] == 'payout')].index)
        df_shopify_trans_detail['fee'] = df_shopify_trans_detail['fee'] * -1
        df_shopify_trans_detail = df_shopify_trans_detail.rename(columns={'fee': 'FEES', 'net': 'BANK'})
        df_shopify_trans_detail.loc[(df_shopify_trans_detail['type'] == 'adjustment'), ['FEES']] = df_shopify_trans_detail['amount']
        df_shopify_trans_detail.loc[(df_shopify_trans_detail['type'] == 'adjustment'), ['BANK']] = 0
        df_shopify_trans_detail.loc[(df_shopify_trans_detail['type'] == 'adjustment'), ['type']] = 'refund' # Change all adjustment rows to refund so we can group together and combine refybd rows with Fee's Returned by Shopify
        df_shopify_trans_detail = df_shopify_trans_detail.groupby(['type', 'source_order_id', 'processed_at'], as_index=False).agg({'source_id': 'first',
                                                                                                                   'source_type': 'last',
                                                                                                                   'FEES': 'sum',
                                                                                                                   'BANK': 'sum',
                                                                                                                   'source_order_transaction_id': 'last'})

        df = pd.merge(df, df_shopify_trans_detail, how='left', left_on='trans_id', right_on='source_order_transaction_id')

        # Get Data stored from Paypal Rest API call and select only relevant columns
        df_paypal_trans_detail = pd.read_csv('cache/paypal_transactions.csv', index_col=0)
        df_paypal_trans_detail = df_paypal_trans_detail[['paypal_transaction_id',
                                                         'paypal_transaction_amount_value',
                                                         'paypal_fee_amount_value']]
        # Create Missing Bank Deposit Column
        df_paypal_trans_detail['paypal_BANK'] = df_paypal_trans_detail['paypal_transaction_amount_value']+df_paypal_trans_detail['paypal_fee_amount_value']

        df = pd.merge(df, df_paypal_trans_detail, how='left', left_on=['trans_authorizationCode','trans_amount'], right_on=['paypal_transaction_id', 'paypal_transaction_amount_value'])
        # Copy missing Paypal values into Fees, Bank column
        df.loc[df['trans_gateway'] == 'paypal', 'FEES'] = df['paypal_fee_amount_value']
        df.loc[df['trans_gateway'] == 'paypal', 'BANK'] = df['paypal_BANK']



        df[['STYLE', 'COLOR', 'SIZE']] = df.sku.str.rsplit("-", n=2, expand=True)
        df = df.drop(['order_createdAt',
                      'sku',
                      'edited',
                      'line_id',
                      'fulfillableQuantity',
                      'unfulfilledQuantity',
                      'refundableQuantity',
                      'fulfillmentStatus',
                      'source_order_id',
                      'source_id',
                      'source_type',
                      'type',
                      'processed_at',
                      'NET PAYMENT',
                      'TOTAL PRICE',
                      'source_order_transaction_id',
                      'trans_authorizationCode',
                      'paypal_transaction_id',
                      'paypal_transaction_amount_value',
                      'paypal_fee_amount_value',
                      'paypal_BANK'], axis=1)

        df['trans_createdAt'] = pd.to_datetime(df['trans_createdAt'])  # Change Column to Pandas DateTime Object
        df['trans_createdAt'] = df['trans_createdAt'].dt.tz_convert('america/los_angeles')  # Convert Datetime Object to local Timezone UTC-8:00

        most_earliest_datetime = df['trans_createdAt'].min()
        most_latest_datetime = df['trans_createdAt'].max()


        print('Most Earliest Date & Time Loaded in Cache: ', most_earliest_datetime)
        print('Most Recent Date & Time Loaded in Cache: ', most_latest_datetime)
        most_earliest_date = most_earliest_datetime.strftime('%Y/%m/%d')
        most_latest_date = most_latest_datetime.strftime('%Y/%m/%d')
        utility_functions.save_dates_to_cache(transactions_earliest_date = most_earliest_date, transactions_latest_date = most_latest_date)

        df['DATE'] = df['trans_createdAt']  # Copy New Column as Created_At used to filter orders by Date
        df['DATE'] = df['DATE'].dt.strftime('%m/%d') # Change Format
        df['trans_createdAt'] = df['trans_createdAt'].dt.strftime('%Y/%m/%d')   # Change format
        df['trans_createdAt'] = df['trans_createdAt'].ffill()



        mask = (df['trans_createdAt'] >= start_date) & (df['trans_createdAt'] <= end_date)
        df = df.loc[mask]  # Filter Orders by Date


    # IF ORDER IS CANCELED AND THERE WAS NO TRANSACTION THEN MAKE ALL LINE ITEMS CANCELED AS WELL
        df_cancelled = df.loc[:, ['cancelledAt', '__parentId']]
        df_cancelled = df_cancelled[df_cancelled['cancelledAt'].notna()]
        df_cancelled = df_cancelled.drop_duplicates()
        df = df.drop(['cancelledAt'], axis=1)
        df = pd.merge(df, df_cancelled, how='left', on='__parentId')
        df.loc[(df['cancelledAt'].notna()) & (df['trans_amount'].isna()), ['CUSTOMER NAME',
                                                                           'QTY',
                                                                           'LA TAX',
                                                                           'CA TAX',
                                                                           'FREIGHT',
                                                                           'TOTAL DISCOUNTS',
                                                                           'FEES','BANK']] = 'VOID', 0, 0, 0, 0, 0, 0, 0

        df = df.rename(columns={'trans_amount': 'TOTAL', 'trans_gateway': 'gateway'})
        df .loc[df['gateway'] == 'paypal', 'gateway'] = 'P'
        df .loc[df['gateway'] == 'shopify_payments', 'gateway'] = 'S'

        # Delete All Duplicate repeating rows per column
        df['TOTAL'] = df['TOTAL'].mask(df['id'].shift(1) == df['id'])
        df['gateway'] = df['gateway'].mask(df['id'].shift(1) == df['id'])
        df['BANK'] = df['BANK'].mask(df['id'].shift(1) == df['id'])
        df['FEES'] = df['FEES'].mask(df['id'].shift(1) == df['id'])



        # Rearrange columns
        df = df[['ORDER#',
                 'DATE',
                 'CUSTOMER NAME',
                 'STYLE',
                 'COLOR',
                 'SIZE',
                 'SHOE PRICE',
                 'QTY',
                 'SUBTOTAL',
                 'LINE DISC.',
                 'LINE SUBTOTAL',
                 'LA TAX',
                 'CA TAX',
                 'FREIGHT',
                 utility_functions.check_column_exists('ORDER DISCOUNT',df),
                 'TOTAL DISCOUNTS',
                 'TOTAL',
                 'FEES',
                 'BANK',
                 'dif',
                 'gateway']]



        # NEGATE DISCOUNTS
        df['LINE DISC.'] = df['LINE DISC.'] * -1

        if 'ORDER DISCOUNT' in df:
            df['ORDER DISCOUNT'] = df['ORDER DISCOUNT'] * -1

        df['TOTAL DISCOUNTS'] = df['TOTAL DISCOUNTS'] * -1


        # **************PANDAS -> EXCEL*********************
        writer = pd.ExcelWriter('cache/orders_report.xlsx', engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Sheet1', index=False, startrow=1, header=False)
        workbook = writer.book
        worksheet = writer.sheets['Sheet1']

        header_format = workbook.add_format({
            'bold': True,
            'border': 5,
            'border_color': '#000000'})

        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value)

        number_rows = len(df.index) + 1
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
        worksheet.set_column('D:D', 12, bold_format)
        worksheet.set_column('E:F', 4.50, bold_format)
        worksheet.set_column('G:G', 10.50, money)
        worksheet.set_column('H:H', 5, bold_format)
        worksheet.set_column('I:T', 10.50, money)
        worksheet.set_column('U:U', 6.75, bold_format)


        worksheet.conditional_format("$A$1:$P$%d" % number_rows,
                                     {"type": "formula",
                                      "criteria": '=INDIRECT("D"&ROW())="unfulfilled"',
                                      "format": yellow_highlight
                                      })

        worksheet.conditional_format("$A$1:$P$%d" % number_rows,
                                     {"type": "formula",
                                      "criteria": '=INDIRECT("C"&ROW())="VOID"',
                                      "format": red_highlight
                                      })

        worksheet.conditional_format(f'H2:H{number_rows}',
                                     {'type': 'cell', 'criteria': 'greater than', 'value': 1, 'format': green_highlight})

        worksheet.conditional_format(f'A2:U{number_rows}', {'type': 'blanks', 'format': add_border})
        worksheet.conditional_format(f'A2:U{number_rows}', {'type': 'no_blanks', 'format': add_border})
        worksheet.conditional_format('A1:U2', {'type': 'blanks', 'format': header_format})
        worksheet.conditional_format('A1:U1', {'type': 'no_blanks', 'format': header_format})
        worksheet.conditional_format(f'H{footer_row}:T{footer_row}', {'type': 'blanks', 'format': header_format})
        worksheet.conditional_format(f'H{footer_row}:T{footer_row}', {'type': 'no_blanks', 'format': header_format})

        worksheet.write_formula(f'H{footer_row}', f'=SUM(H2:H{number_rows})')
        worksheet.write_formula(f'I{footer_row}', f'=SUM(I2:I{number_rows})')
        worksheet.write_formula(f'J{footer_row}', f'=SUM(J2:J{number_rows})')
        worksheet.write_formula(f'K{footer_row}', f'=SUM(K2:K{number_rows})')
        worksheet.write_formula(f'L{footer_row}', f'=SUM(L2:L{number_rows})')
        worksheet.write_formula(f'M{footer_row}', f'=SUM(M2:M{number_rows})')
        worksheet.write_formula(f'N{footer_row}', f'=SUM(N2:N{number_rows})')
        worksheet.write_formula(f'O{footer_row}', f'=SUM(O2:O{number_rows})')
        worksheet.write_formula(f'Q{footer_row}', f'=SUM(Q2:Q{number_rows})')
        worksheet.write_formula(f'R{footer_row}', f'=SUM(R2:R{number_rows})')
        worksheet.write_formula(f'S{footer_row}', f'=SUM(S2:S{number_rows})')
        worksheet.write_formula(f'T{footer_row}', f'=SUM(T2:T{number_rows})')

        start_date_excel = start_date_obj.strftime('%m/%d/%Y')
        end_date_excel = end_date_obj.strftime('%m/%d/%Y')

        worksheet.set_header(f'&C&18&"Calibri ,Bold" DIRECT {start_date_excel} -> {end_date_excel}&RPage &P of &N')
        worksheet.repeat_rows(0)
        worksheet.set_landscape()
        worksheet.set_margins(left=0.25, right=0.25, top=0.75, bottom=0.75)
        worksheet.fit_to_pages(1, 0)


        if platform == 'darwin':
            writer.save()
            os.system("open cache/orders_report.xlsx -a '/Applications/Microsoft Excel.app' ")
        else:
                try:
                    writer.save()
                    os.system("start EXCEL.EXE cache/orders_report.xlsx")
                except xlsxwriter.exceptions.FileCreateError:
                    print('\n' * 3) # Print Empty Lines
                    print('Please Close Generated Excel File first before generating a new one!')


if __name__ == '__main__':
    generate_order_report('2020/04/01','2020/04/29')