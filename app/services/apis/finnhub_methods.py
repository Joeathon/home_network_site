import json
import os
from datetime import datetime
from datetime import date

import finnhub
import pandas as pd

TEMP_FILE_PATH = 'temp/temp.json'

class FinnhubApi:
    def __init__(self):

        # API Authentication
        api_key = 'd9rt219r01qoo7o5n5k0d9rt219r01qoo7o5n5kg'
        self.finnhub_client = finnhub.Client(api_key=api_key)

        # API Call Limit Parameters  NOTE: This logic does not account for async operations.
        self.limit_1_call_stack = []
        self.limit_2_call_stack = []

    # API End Points

    def company_basic_financials(self, symbol:str)->tuple[pd.DataFrame, pd.DataFrame]:

        # Fetch Data from API
        data = self.finnhub_client.company_basic_financials(symbol, 'all')

        # PARSE DATA

        # Parse Metric Data.
        metric = data.get('metric')
        df_metric = pd.DataFrame(metric, index=[0])
        df_metric = self.add_meta_data_to_df(df_metric, symbol)

        # Parse Annual Data
        annual = data['series']['annual']
        df_annual = pd.DataFrame(columns=['period'])
        for key, value in annual.items():
            df1 = pd.DataFrame(annual[key])
            df1.rename(columns={'v':key}, inplace=True)
            df_annual = pd.merge(df_annual, df1, on='period', how='outer')

        df_annual = self.add_meta_data_to_df(df_annual, symbol)

        # Parse Quarterly Data
        quarterly = data['series']['quarterly']
        df_quarterly = pd.DataFrame(columns=['period'])
        for key, value in quarterly.items():
            df1 = pd.DataFrame(quarterly[key])
            df1.rename(columns={'v':key}, inplace=True)
            df_quarterly = pd.merge(df_quarterly, df1, on='period', how='outer')

        df_quarterly = self.add_meta_data_to_df(df_quarterly, symbol)

        # Return as Data Frames
        return df_metric, df_annual, df_quarterly

    # API Helper Methods

    def add_meta_data_to_df(self, df:pd.DataFrame, symbol:str)->pd.DataFrame:
        df['symbol'] = symbol
        df.insert(0, "symbol", df.pop("symbol"))

        df['query_date'] = date.today()
        df.insert(1, "query_date", df.pop("query_date"))

        return df

    def api_call_regulator(self):
        # Limit Criteria as defined by Finnhub API. Documentation
        limit_1 = 30 # Calls per Second      
        limit_2 = 60 # Calls per Minute

        # LIMIT 2 LOGIC
        
        # Remove all calls from list that exceed one minute.

        if len(self.limit_2_call_stack)>=limit_2:
            oldest_call = min(self.limit_2_call_stack)
            
        


# Helper Methods

def pprint(data:dict):
    print(json.dumps(data, indent=4))

def save_json(data:dict):
    os.makedirs('temp', exist_ok=True)
    with open(TEMP_FILE_PATH, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, sort_keys=True)

def load_json():
    with open(TEMP_FILE_PATH, 'r') as file:
        data = json.load(file)
    return data

if __name__ == '__main__':
    F = FinnhubApi()
    df = F.company_basic_financials('PG')

    # print(df)



