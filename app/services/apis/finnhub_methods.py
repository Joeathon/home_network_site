import json
import os
from datetime import date
from datetime import datetime
from io import StringIO
import time

import finnhub
import pandas as pd
import requests

TEMP_FILE_PATH = 'temp/temp'

class FinnhubApi:
    def __init__(self):

        # API Authentication
        api_key = 'd9rt219r01qoo7o5n5k0d9rt219r01qoo7o5n5kg'
        self.finnhub_client = finnhub.Client(api_key=api_key)

        # API Call Limit Parameters  NOTE: This logic does not account for async operations.
        self.limit_1_call_stack = [datetime.now()]
        self.limit_2_call_stack = [datetime.now()]

    # API End Points

    def company_basic_financials(self, symbol:str)->tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:

        # Fetch Data from API
        self.api_call_regulator()
        data = self.finnhub_client.company_basic_financials(symbol, 'all')
        self.limit_1_call_stack.append(datetime.now())

        # PARSE DATA

        # Check for empty sets
        if data.get('metric') == {}:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        # Parse Metric Data.
        metric = data.get('metric')
        df_metric = pd.DataFrame(metric, index=[0])
        df_metric = self.add_meta_data_to_df(df_metric, symbol)
        df_metric = self.add_id_to_df(df_metric, ['symbol'])

        # Parse Annual Data
        annual = data['series']['annual']
        df_annual = pd.DataFrame(columns=['period'])
        for key, value in annual.items():
            df1 = pd.DataFrame(annual[key])
            df1.rename(columns={'v':key}, inplace=True)
            df_annual = pd.merge(df_annual, df1, on='period', how='outer')

        df_annual = self.add_meta_data_to_df(df_annual, symbol)
        df_annual = self.add_id_to_df(df_annual, ['symbol','period'])

        # Parse Quarterly Data
        quarterly = data['series']['quarterly']
        df_quarterly = pd.DataFrame(columns=['period'])
        for key, value in quarterly.items():
            df1 = pd.DataFrame(quarterly[key])
            df1.rename(columns={'v':key}, inplace=True)
            df_quarterly = pd.merge(df_quarterly, df1, on='period', how='outer')

        df_quarterly = self.add_meta_data_to_df(df_quarterly, symbol)
        df_quarterly = self.add_id_to_df(df_quarterly, ['symbol','period'])

        # Return as Data Frames
        return df_metric, df_annual, df_quarterly

    def exchanges(self)->pd.DataFrame:
        # https://docs.google.com/spreadsheets/d/1I3pBxjfXB056-g_JYf_6o3Rns3BV2kMGG1nCatb91ls/edit?gid=0#gid=0
        sheet_id = '1I3pBxjfXB056-g_JYf_6o3Rns3BV2kMGG1nCatb91ls'
        gid = 0

        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

        df = pd.read_csv(url)
        df = self.add_id_to_df(df, ['code'])

        return df

    def stock_symbols(self, exchange:str)->pd.DataFrame:
        data = self.finnhub_client.stock_symbols(exchange)
        df = pd.DataFrame(data)

        df['exchange'] = exchange
        df.insert(0, "exchange", df.pop("exchange"))

        df = self.add_id_to_df(df, ['exchange','symbol'])

        return df

    # API Helper Methods

    def add_meta_data_to_df(self, df:pd.DataFrame, symbol:str)->pd.DataFrame:
        df['symbol'] = symbol
        df.insert(0, "symbol", df.pop("symbol"))

        return df

    def add_id_to_df(self, df:pd.DataFrame, keys:list)->pd.DataFrame:

        df['query_date'] = date.today()
        df.insert(0, "query_date", df.pop("query_date"))

        df['id']=df[keys].astype(str).agg('~'.join, axis=1)
        df.insert(0, 'id', df.pop('id'))

        return df

    def api_call_regulator(self):
        # Limit Criteria as defined by Finnhub API. Documentation
        limit_1 = 30 # Calls per Second      
        limit_2 = 60 # Calls per Minute

        # LIMIT 2 LOGIC
        
        # Remove all calls from list that exceed one minute.
        self.limit_2_call_stack = [call_time for call_time in self.limit_2_call_stack if (datetime.now() - call_time).total_seconds() < 60]

        # Check to see if the stack has more than 60 calls in the last minute.
        if len(self.limit_2_call_stack)>=limit_2:
            # Detemine How much time to wait before making the next call.
            oldest_call_timestamp = min(self.limit_2_call_stack)
            time_to_wait = 60 - (datetime.now() - oldest_call_timestamp).total_seconds()
            print(f"API Call Limit Reached: Waiting {time_to_wait:.2f} seconds before making next call.")
            time.sleep(time_to_wait)
            
# Helper Methods

def load_json():
    with open(TEMP_FILE_PATH, 'r') as file:
        data = json.load(file)
    return data

def pprint(data:dict):
    print(json.dumps(data, indent=4))

def save_file(data, file_extension:str):
    os.makedirs('temp', exist_ok=True)

    if file_extension == 'json':
        with open(f'{TEMP_FILE_PATH}.{file_extension}', "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, sort_keys=True)
    else:
        with open(f'{TEMP_FILE_PATH}.{file_extension}', "w", encoding="utf-8") as file:
            file.write(data)

if __name__ == '__main__':
    F = FinnhubApi()
    df = F.stock_symbols('US')
    print(df)




