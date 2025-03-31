import streamlit as st
from core.snowflake import SnowflakeConnection
import pandas as pd

def generate_sql_suggestions(schema_info):
    suggestions = []
    
    # Find tables with common columns for joins
    tables = list(schema_info.keys())
    for i, table1 in enumerate(tables):
        for table2 in tables[i+1:]:
            cols1 = {col['name'].lower(): col for col in schema_info[table1]['columns']}
            cols2 = {col['name'].lower(): col for col in schema_info[table2]['columns']}
            
            # Find common column names that could be join keys
            common_cols = set(cols1.keys()) & set(cols2.keys())
            
            if common_cols:
                for col in common_cols:
                    suggestions.append({
                        'type': 'Join Analysis',
                        'title': f'Join {table1} and {table2}',
                        'description': f'Analyze relationship between {table1} and {table2} using {col}',
                        'query': f'''
                            SELECT a.*, b.*
                            FROM {table1} a
                            JOIN {table2} b ON a.{col} = b.{col}
                            LIMIT 1000
                        '''
                    })
    
    # Generate aggregation suggestions for numeric columns
    for table, details in schema_info.items():
        numeric_cols = [col['name'] for col in details['columns'] 
                       if any(t in col['type'].upper() for t in ['INT', 'FLOAT', 'NUMBER', 'DECIMAL'])]
        categorical_cols = [col['name'] for col in details['columns'] 
                          if any(t in col['type'].upper() for t in ['VARCHAR', 'STRING', 'CHAR'])]
        date_cols = [col['name'] for col in details['columns'] 
                    if 'DATE' in col['type'].upper() or 'TIMESTAMP' in col['type'].upper()]
        
        # Aggregate functions suggestions
        if numeric_cols and categorical_cols:
            for num_col in numeric_cols[:2]:  # Limit to first 2 numeric columns
                for cat_col in categorical_cols[:2]:  # Limit to first 2 categorical columns
                    suggestions.append({
                        'type': 'Aggregate Analysis',
                        'title': f'Aggregate {num_col} by {cat_col}',
                        'description': f'Calculate summary statistics for {num_col} grouped by {cat_col}',
                        'query': f'''
                            SELECT 
                                {cat_col},
                                COUNT(*) as count,
                                AVG({num_col}) as avg_{num_col},
                                SUM({num_col}) as total_{num_col},
                                MIN({num_col}) as min_{num_col},
                                MAX({num_col}) as max_{num_col}
                            FROM {table}
                            GROUP BY {cat_col}
                            ORDER BY count DESC
                            LIMIT 1000
                        '''
                    })
        
        # Window functions suggestions
        if numeric_cols and (categorical_cols or date_cols):
            partition_col = categorical_cols[0] if categorical_cols else date_cols[0]
            for num_col in numeric_cols[:2]:
                suggestions.append({
                    'type': 'Window Function Analysis',
                    'title': f'Trend Analysis for {num_col}',
                    'description': f'Calculate running totals and rankings for {num_col}',
                    'query': f'''
                        SELECT 
                            {partition_col},
                            {num_col},
                            SUM({num_col}) OVER (ORDER BY {partition_col}) as running_total,
                            AVG({num_col}) OVER (ORDER BY {partition_col} ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) as moving_average,
                            RANK() OVER (ORDER BY {num_col} DESC) as rank
                        FROM {table}
                        ORDER BY {partition_col}
                        LIMIT 1000
                    '''
                })
    
    return suggestions

def render_sql_suggestions_page():
    st.title("AI SQL Query Suggestions")
    
    try:
        snowflake_conn = SnowflakeConnection()
        
        # Get schema info if not cached
        if not st.session_state.get('schema_info'):
            with st.spinner("Loading schema information..."):
                st.session_state.schema_info = snowflake_conn.get_schema_info()
        
        # Generate suggestions
        suggestions = generate_sql_suggestions(st.session_state.schema_info)
        
        # Group suggestions by type
        suggestion_types = list(set(s['type'] for s in suggestions))
        
        # Display suggestions by type
        selected_type = st.selectbox("Select Analysis Type", suggestion_types)
        
        filtered_suggestions = [s for s in suggestions if s['type'] == selected_type]
        
        for idx, suggestion in enumerate(filtered_suggestions):
            with st.expander(f"{suggestion['title']}", expanded=idx == 0):
                st.write(suggestion['description'])
                st.code(suggestion['query'].strip(), language='sql')
                
                if st.button(f"Execute Query {idx + 1}"):
                    try:
                        with st.spinner("Executing query..."):
                            results = snowflake_conn.execute_query(suggestion['query'])
                            st.session_state.generated_sql = suggestion['query']
                            st.session_state.query_results = results
                            
                            st.write("Query Results:")
                            st.dataframe(results)
                            
                            # Add download button
                            if not results.empty:
                                csv = results.to_csv(index=False).encode('utf-8')
                                st.download_button(
                                    "Download Results",
                                    csv,
                                    f"query_results_{idx+1}.csv",
                              ;      "text/csv"
                                )
                    except Exception as e:
                        st.error(f"Query execution failed: {str(e)}")
                        
    except Exception as e:
        st.error(f"Error: {str(e)}")
    finally:
        if 'snowflake_conn' in locals():
            snowflake_conn.close()