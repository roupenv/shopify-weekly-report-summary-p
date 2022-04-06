# shopify_weekly_summary_report
The motivation of this desktop app was to eliminate and automate a time-consuming manual task involved with daily/weekly ecommerce sales reports.
It pulls order and transaction data from Shopify and PayPal and generates and formats a excel file to review, save, and print by date.
Shopify and PayPal transaction credit card fees are not easily accessible for an end user to do manually, and it involves creating several different reports in each website and joining it together with the order detail, this is a time consuming task. The generated excel file's format needed to almost exactly replicate 

The project was done by using Shopify and PayPal's' API's, Python's Pandas, xlsxwriter, and QT5 Libraries 

For Shopify I made use of their newer graphQL API as well as their Rest API.
The motivation for this was that with a single graphQL request, I can request bulk order data by date, check and wait if the file is ready and then download it.
This was important as Shopify has limits on API calls which I did not want to exceed.
The Rest API usage was used due to a limitation on the transaction fee endpoint that was not available on their GraphQl at the time of creating the app in mid 2020.

For Paypal, I use their Rest API and make requests by the order and transaction data pulled from Shopify.

The python Panadas library proccesses, shapes, and merges the Shopify and PayPal json data.
Xlsxwriter library formats and creates a excel file just as the original excel file done manually.

The GUI was made with QT5 for python.

The python app is made into an executable program for both Windows and Mac using pyinstaller.
A special .dotenv file must be added manually to the project folder which contains API secrets.

The App also saves the processed data in cache in order to save time and not have to re-request data for a given time period. If the user makes a request outside of the cached time period it will automatically request that data from Shopify and Payal 

![](https://github.com/roupenv/shopify_weekly_summary_report/blob/master/assets/weekly%20summary%20report%20screenshot.png)
![](https://github.com/roupenv/shopify_weekly_summary_report/blob/master/assets/weekly%20summary%20report%20output%20screenshot.png)
