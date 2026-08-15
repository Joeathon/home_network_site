import sqlite3
import pandas as pd

class SQLiteMethods:
    def __init__(self, path='app/services/data_store', database='data.db'):
        self.path = path
        self.database = database
        self.conn = self.__get_connection()

    def __get_connection(self)-> sqlite3.Connection:
        conn = sqlite3.connect(f'{self.path}/{self.database}')
        return conn

    def create_table(self, table_name:str, columns:list[str])->None:
        sql = f"""CREATE TABLE {table_name} ("""

        for column in columns:
            if column == 'id':
                sql += f"""'{column}' TEXT PRIMARY KEY,"""
            else:
                sql += f"""'{column}' TEXT,"""
        sql = sql[:-1]
        sql += ")"

        self.query(sql)

    def drop_table(self, table_name:str):
        sql = f"""DROP TABLE IF EXISTS {table_name}"""
        self.query(sql)

    def upsert(self, df:pd.DataFrame, table_name:str):
        # Ignore if DataFrame has no data in it.
        if df.shape[0] == 0: return

        # Initialize Table if it doesn't exist.
        if not self.table_exists(table_name):
            self.create_table(table_name, df.columns.tolist())

        # Upsert Data
        temp_table_name = f'{table_name}_temp'
        
        df.to_sql(temp_table_name, self.conn, if_exists='replace', index=False)

        columns = df.columns.tolist()
        columns_str = ", ".join([f'"{item}"' for item in columns])

        sql = f"""
            INSERT INTO {table_name} ({columns_str})
            SELECT {columns_str} FROM {temp_table_name}
            WHERE true
            ON CONFLICT(id) DO UPDATE SET 
        """
        for column in columns:
            if column != "id":
                sql += f""""{column}" = excluded."{column}","""
        sql = sql[:-1]
        sql += ';'

        self.conn.execute(sql)
        self.conn.execute(f'DROP TABLE {temp_table_name}')
        self.conn.commit()

    def query(self, sql:str)->None:
        cursor = self.conn.cursor()
        cursor.execute(sql)
        self.conn.commit()
        cursor.close()

    def query_df(self, sql: str) -> pd.DataFrame:
        try:
            df = pd.read_sql_query(sql, self.conn)
            return df
        except Exception as e:
            print(f"Error occurred while querying DataFrame: {e}")
            return pd.DataFrame()

    def table_exists(self, table_name) -> bool:
        sql = f"""SELECT name FROM sqlite_master WHERE type='table' and name='{table_name}'"""

        cursor = self.conn.cursor()
        cursor.execute(sql)
        exists = cursor.fetchone() is not None
        cursor.close()

        if not exists: return False
        else: return True

if __name__ == "__main__":

    # Initialize
    table_name = 'test'
    DB = SQLiteMethods()

    # DB.drop_table(table_name)
    # # DB.drop_table(f'{table_name}_temp')
    # # quit()

    # Insert Table.
    import os, sys
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.append(parent_dir)
    from apis import finnhub_methods
    FH = finnhub_methods.FinnhubApi()
    # df, df2, df3 = FH.company_basic_financials('PG')
    # DB.upsert(df2,table_name)
    # df, df2, df3 = FH.company_basic_financials('AAPL')
    # DB.upsert(df2,table_name)
    df, df2, df3 = FH.company_basic_financials('AAPLxyz')
    DB.upsert(df2,table_name)


