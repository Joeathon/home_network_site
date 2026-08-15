import os, sys
from datetime import datetime
from datetime import date
# Get the absolute path to the parent directory (my_project)
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)

from services.apis import finnhub_methods
from services.data_store import sqlite_methods

# Finnhub API Class
FH = finnhub_methods.FinnhubApi()

# Database Class
DB = sqlite_methods.SQLiteMethods()

# Table Names
EXCHANGES = 'finnhub_stock_exchanges'
SYMBOLS = 'finnhub_stock_symbols'

def main():
    update_exchanges(days=30)
    update_symbols(days=30)

# Database Update Methods

def update_exchanges(days:int)->None:
    table_name = EXCHANGES
    if updated_needed(table_name, days):
        df = FH.exchanges()
        DB.upsert(df, table_name)

def update_symbols(days:int)->None:
    table_name = SYMBOLS
    exchanges = ['US']

    for exchange in exchanges:
        if updated_needed(table_name, days, where_clause=f"""WHERE exchange = '{exchange}'"""):
            df = FH.stock_symbols(exchange)
            print(df)
            DB.upsert(df, table_name)

# Helper Methods

def updated_needed(table_name:str, days:int, where_clause:str=None)->bool:
    if not where_clause:
        sql = f"""SELECT max(query_date) AS max_query_date FROM {table_name}"""
    else:
        sql = f"""SELECT max(query_date) AS max_query_date FROM {table_name} {where_clause}"""

    df_db = DB.query_df(sql)

    # Check to see if the DataFrame has data.
    if df_db.shape[0]>0:
        # If the max query date is None, then refresh needed
        if df_db.at[0,'max_query_date'] == None:
            return True

        # Determine the last time the database was updated.
        max_date = df_db.at[0,'max_query_date']
        max_date = datetime.strptime(max_date, "%Y-%m-%d").date()
        today = date.today()
        delta = (today-max_date).days

        # If within update frequency, the don't update.
        if delta < days: 
            return False

    return True



# FH = finnhub_methods.FinnhubApi()
# df, df2, df3 = FH.company_basic_financials('PG')
# conn = sqlite_methods.get_connection()
# # df.to_sql('finnhub_company_metrics', conn, if_exists='append', index=False)
# sqlite_methods.update_table_from_dataframe(df, 'finnhub_company_metrics', ['symbol'])

# df, df2, df3 = FH.company_basic_financials('AAPL')
# df.to_sql('finnhub_company_metrics', conn, if_exists='append', index=False)

if __name__ == '__main__':
    main()

