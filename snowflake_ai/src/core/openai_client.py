import openai
import os
import json
from typing import Dict

class QueryGenerator:
    def __init__(self):
        openai.api_key = os.getenv('OPENAI_API_KEY')
        self.model = "gpt-3.5-turbo"

    def generate_sql(self, prompt: str, schema_info: Dict) -> str:
        schema_context = self._format_schema_context(schema_info)
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"""You are a SQL expert. 
                    Use this schema information:
                    {schema_context}
                    Rules:
                    1. Strictly Use the schema as reference no column or table outside of the schema.
                    2. Include WHERE clauses where appropriate
                    3. Include joins, aggregations, and subqueries as needed
                    4. Include window functions as needed
                    5. Try to generate sql where on resultset machine learning model can be applied
                    6. Generate only SQL, no explanations"""},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            return response.choices[0].message['content'].strip()
        except Exception as e:
            raise Exception(f"Query generation failed: {str(e)}")

    def _add_limit_clause(self, sql: str) -> str:
        """Add LIMIT 1 to query for validation"""
        sql = sql.strip().rstrip(';')
        sql =sql.replace('```sql', '').replace('```', '').strip()
        if 'LIMIT' not in sql.upper():
            return f"{sql} LIMIT 2"
        return sql
    

    def _format_schema_context(self, schema_info: Dict) -> str:
        context = []
        for table_name, details in schema_info.items():
            context.append(f"\n{table_name}:")
            for col in details['columns']:
                col_info = [f"- {col['name']} ({col['type']})"]
                if 'description' in col and col['description']:
                    col_info.append(f"  Description: {col['description']}")
                context.append("\n".join(col_info))
            
            if details.get('sample_data'):
                context.append("\nSample Data:")
                for row in details['sample_data'][:2]:
                    context.append(json.dumps(row, default=str))
            context.append("-" * 40)
        
        return "\n".join(context)
