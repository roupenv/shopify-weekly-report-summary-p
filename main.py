import sys
import os
import json
from PySide2.QtWidgets import QApplication, QMainWindow, QDialog
# from PySide2.QtCore import QFile  # Not sure where this is needed maybe need to remove
from main_gui import Ui_MainWindow
import datetime
import utility_functions
import orders_report



class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.run_orders.clicked.connect(self.run_orders_click)
        self.ui.exit.clicked.connect(self.onclose)
        self.ui.clear_cache.clicked.connect(self.clear_cache)
        self.ui.clear_transactions.clicked.connect(self.clear_transactions)
        self.ui.update_transaction.clicked.connect(self.update_transaction)


    def run_orders_click(self):
        start_date_input_obj = self.ui.start_date.selectedDate()
        start_date_input = start_date_input_obj.toString('yyyy/MM/dd')

        end_date_input_obj = self.ui.end_date.selectedDate()
        end_date_input = end_date_input_obj.toString('yyyy/MM/dd')

        if end_date_input_obj < start_date_input_obj:
            print('End Date Cannot Be Before Start Date!!!')
        else:
            utility_functions.create_check_for_directory()
            try:
                with open('cache/dates.json') as dates:
                    saved_dates = json.load(dates)
                    stored_earliest_date = datetime.datetime.strptime(saved_dates.get('most_earliest_date'), '%Y/%m/%d')
                    stored_recent_date = datetime.datetime.strptime(saved_dates.get('most_recent_date'), '%Y/%m/%d')

                    if (start_date_input_obj < stored_earliest_date) or (end_date_input_obj > stored_recent_date):
                        file_list = ['shopify_order_data.jsonl', 'paypal_transactions.csv']
                        utility_functions.clear_cache(file_list)
            except FileNotFoundError:
                pass

            orders_report.generate_order_report(start_date_input, end_date_input)

    def onclose(self):
       self.close()

    def clear_cache(self):
        file_list =  ['shopify_order_data.jsonl', 'dates.json', 'orders_report.xlsx', 'paypal_transactions.csv']
        utility_functions.clear_cache(file_list)

    def clear_transactions(self):
        file_list = ['shopify_transactions.csv']
        utility_functions.clear_cache(file_list)

    def update_transaction(self):
        try:
            with open('cache/latest_transaction_id.txt') as file:
                last_trans_id = file.read()
        except FileNotFoundError:
            print("Transaction File Not Generated Yet")
            utility_functions.transactions_to_csv()
            print("Transaction File Is Generated Now")
        utility_functions.transactions_to_csv(last_trans_id)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

# Run this only when imported as module , ignore if run directly so it works in IDE
if __name__ != "__main__":

    def run_gui():
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()

        if getattr(sys, 'frozen') and hasattr(sys, '_MEIPASS'):
            print('running in a PyInstaller bundle')
            # print(sys._MEIPASS)  # PyInstaller Stored absolute path to executable directory
            # print(sys.argv[0])   # Absolute path to Executable File or if using symbolic link, path to symbolic link
            # print(sys.executable) # Absolute path to Executable file
            # print(os.getcwd())  # Cuurent working directory (Probably Home)
            # print(os.path.dirname(sys.executable))  # This returns the parent directory of the executable file
            executable_dir = os.path.dirname(sys.executable) # Set variable to absolute path of executable file's parent directory
            os.chdir(executable_dir) # Change Pythons Working Directory to that of the Executable file to save Cache files
            print('Changed Directory to: ', os.getcwd())

        else:
            print('running in a normal Python process')

        sys.exit(app.exec_()) # PySide2 exit App Quit Process
