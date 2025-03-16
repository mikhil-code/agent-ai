import snowflake.connector
import pandas as pd
from typing import Dict, List
import os

class SnowflakeConnection:
    def __init__(self):
        self.conn = snowflake.connector.connect(
            user=os.getenv('SNOWFLAKE_USER'),
            password=os.getenv('SNOWFLAKE_PASSWORD'),
            account=os.getenv('SNOWFLAKE_ACCOUNT'),
            warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
            database=os.getenv('SNOWFLAKE_DATABASE'),
            schema=os.getenv('SNOWFLAKE_SCHEMA', 'PUBLIC')
        )
        self.cursor = self.conn.cursor()

    def get_schema_info(self) -> Dict:
        schema_info = {}
        try:
            # Get list of views/tables
            self.cursor.execute("""
                SELECT table_name, table_type 
                FROM information_schema.tables 
                WHERE table_schema = CURRENT_SCHEMA()
            """)
            objects = self.cursor.fetchall()

            for obj_name, obj_type in objects:
                # Get column information
                self.cursor.execute(f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = '{obj_name}'
                    AND table_schema = CURRENT_SCHEMA()
                    ORDER BY ordinal_position
                """)
                columns = self.cursor.fetchall()

                # Get sample data
                self.cursor.execute(f"SELECT * FROM {obj_name} LIMIT 5")
                sample_data = self.cursor.fetchall()
                sample_columns = [desc[0] for desc in self.cursor.description]

                schema_info[obj_name] = {
                    'type': obj_type,
                    'columns': [
                        {
                            'name': col[0],
                            'type': col[1],
                            'nullable': col[2]
                        } for col in columns
                    ],
                    'sample_data': [
                        dict(zip(sample_columns, row)) 
                        for row in sample_data
                    ]
                }

            return schema_info
        except Exception as e:
            raise Exception(f"Failed to get schema info: {str(e)}")

    def execute_query(self, query: str) -> pd.DataFrame:
        try:
            self.cursor.execute(query)
            result = self.cursor.fetchall()
            columns = [desc[0] for desc in self.cursor.description]
            return pd.DataFrame(result, columns=columns)
        except Exception as e:
            raise Exception(f"Query execution failed: {str(e)}")

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
