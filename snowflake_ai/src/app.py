from pages.sql_suggestions import render_sql_suggestions_page
import streamlit as st
from core.snowflake import SnowflakeConnection
from core.openai_client import QueryGenerator   
import pandas as pd
from dotenv import load_dotenv
import sqlparse
import traceback
import streamlit.components.v1 as components
from ml.analyzer import MLAnalyzer
from ml.suggestions import MLSuggestionEngine

load_dotenv()

def init_session_state():
    if 'history' not in st.session_state:
        st.session_state.history = []
    if 'schema_info' not in st.session_state:
        st.session_state.schema_info = None
    if 'generated_sql' not in st.session_state:
        st.session_state.generated_sql = None
    if 'query_results' not in st.session_state:
        st.session_state.query_results = None

def is_valid_sql(query: str) -> bool:
    # Basic SQL validation
    if not query or len(query.strip()) == 0:
        return False
    
    # Check for basic SQL structure
    valid_starts = ['SELECT', 'WITH']
    return any(query.strip().upper().startswith(start) for start in valid_starts)

def main():
    init_session_state()
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Choose a page", ["SQL Generator", "ML Analysis", "AI Analysis Suggestions", "SQL Suggestions"])

    if page == "SQL Generator":
        show_sql_generator()
    elif page == "ML Analysis":
        show_ml_analysis()
    elif page == "SQL Suggestions":
        render_sql_suggestions_page()
    else:
        show_ai_suggestions()

    # Add ML suggestions after query execution
    if st.session_state.get('query_results') is not None:
        st.subheader("Machine Learning Suggestions")
        
        suggestion_engine = MLSuggestionEngine()
        ml_suggestions = suggestion_engine.analyze_data(st.session_state.query_results)
        
        if ml_suggestions:
            for category, details in ml_suggestions.items():
                with st.expander(f"{category} Analysis"):
                    st.write("**Suggested Algorithms:**")
                    for algo in details['algorithms']:
                        st.write(f"- {algo}")
                    st.write(f"\n**Why?** {details['reason']}")
                    st.write("\n**Relevant Columns:**")
                    if isinstance(details['suggested_columns'], dict):
                        st.write("Time Columns:", ", ".join(details['suggested_columns']['time_columns']))
                        st.write("Value Columns:", ", ".join(details['suggested_columns']['value_columns']))
                    else:
                        st.write(", ".join(details['suggested_columns']))
        else:
            st.info("No ML suggestions available for current data")

def show_sql_generator():
    st.title("SQL Query Generator")
    
    # Initialize states and connection
    if 'generated_sql' not in st.session_state:
        st.session_state.generated_sql = None
    if 'query_results' not in st.session_state:
        st.session_state.query_results = None

    try:
        snowflake_conn = SnowflakeConnection()
        
        # Get schema info if not cached
        if not st.session_state.schema_info:
            with st.spinner("Loading schema information..."):
                st.session_state.schema_info = snowflake_conn.get_schema_info()
        
        # Show schema information
        with st.expander("Available Tables/Views"):
            for obj_name, details in st.session_state.schema_info.items():
                st.subheader(obj_name)
                for col in details['columns']:
                    st.write(f"- {col['name']} ({col['type']})")
                if details.get('sample_data'):
                    st.write("Sample data:")
                    st.dataframe(pd.DataFrame(details['sample_data'][:2]))

        # Query input and generation
        prompt = st.text_area(
            "Describe your query in natural language:",
            height=100,
            help="Example: Show me treasury yields above 5% in the last quarter"
        )

        if st.button("Generate Query") and prompt:
            result=None
            countr=0
            st.session_state.generated_sql = None
            st.session_state.query_results = None
            try:
                with st.spinner("Generating query..."):
                    while result is None:
                        countr+=1
                        if countr>10:
                            st.error("Failed to generate query")
                            st.session_state.generated_sql = None
                            st.session_state.query_results = None
                            generated_sql = None
                            break
                        st.write(f"Attempt {countr}")
                        query_gen = QueryGenerator()
                        generated_sql = query_gen.generate_sql(prompt, st.session_state.schema_info)
                        generated_sql=generated_sql.replace('```sql', '').replace('```', '').strip()
                        #st.write("Generated SQL: ", generated_sql)
                        generated_sql_limit = query_gen._add_limit_clause(generated_sql)
                        #st.write("Generated SQL limit: ", generated_sql_limit)
                        sqlparse.format(generated_sql_limit, reindent=True, keyword_case='upper')
                        try:
                            print("Executing generated SQL")
                            result = snowflake_conn.execute_query(generated_sql_limit)
                            if not result.empty and result.shape[0]>0:
                                print("adding querry to session state")
                                st.session_state.generated_sql = generated_sql

                            else:
                               # result = None
                                continue
                                
                        except Exception as e:
                            continue
                        
                    #generated_sql = sqlparse.format(generated_sql, reindent=True, keyword_case='upper').strip()
                    
                    
                # Show generated SQL
                st.subheader("Generated SQL")
                st.code(generated_sql, language='sql')
                
            except Exception as e:
                st.error(f"Failed to generate query: {str(e)}")
                st.error(traceback.format_exc())

        # Separate section for query execution
        if st.session_state.generated_sql:
            col1, col2 = st.columns([1, 4])
            with col1:
                execute_button = st.button("Execute Query")
            
            if execute_button:
                try:
                    with st.spinner("Executing query..."):
                        results = None
                        results = snowflake_conn.execute_query(st.session_state.generated_sql)
                        st.session_state.query_results = results
                        
                        st.subheader("Query Results")
                        st.dataframe(results)
                        
                        # Add download button
                        if not results.empty:
                            csv = results.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                "Download Results",
                                csv,
                                "query_results.csv",
                                "text/csv"
                            )
                except Exception as e:
                    st.error(f"Query execution failed: {str(e)}")

    except Exception as e:
        st.error(f"Connection error: {str(e)}")
    finally:
        if 'snowflake_conn' in locals():
            snowflake_conn.close()

def show_ml_analysis():
    st.title("ML Analysis")
    
    if 'query_results' not in st.session_state or st.session_state.query_results is None:
        st.warning("Please execute a query first to get data for ML analysis")
        return
    
    df = st.session_state.query_results
    
    # Initialize analyzers
    suggestion_engine = MLSuggestionEngine()
    analyzer = MLAnalyzer()
    
    ml_suggestions = suggestion_engine.analyze_data(df)
    
    if ml_suggestions:
        st.subheader("Available Analysis Options")
        st.subheader("Generated SQL")
        st.code(st.session_state.generated_sql, language='sql')
        analysis_type = st.selectbox(
            "Select Analysis Type",
            options=list(ml_suggestions.keys())
        )
        
        if analysis_type:
            details = ml_suggestions[analysis_type]
            selected_algo = st.selectbox(
                "Select Algorithm",
                options=details['algorithms']
            )
            
            # Column selection based on analysis type
            if isinstance(details['suggested_columns'], dict):
                time_col = st.selectbox("Select Time Column", 
                                      options=details['suggested_columns']['time_columns'])
                value_col = st.selectbox("Select Value Column", 
                                       options=details['suggested_columns']['value_columns'])
                selected_columns = {'time': time_col, 'value': value_col}
            else:
                selected_columns = st.multiselect(
                    "Select Columns for Analysis",
                    options=details['suggested_columns'],
                    default=details['suggested_columns'][:2]
                )
            
            if st.button("Run Analysis"):
                with st.spinner("Analyzing data..."):
                    try:
                        # Train model
                        result = analyzer.train_model(
                            df=df,
                            algorithm=selected_algo,
                            target_col=selected_columns['value'] if isinstance(selected_columns, dict) else selected_columns[0],
                            feature_cols=selected_columns['time'] if isinstance(selected_columns, dict) else selected_columns[1:]
                        )
                        
                        # Plot results
                        fig = analyzer.plot_results(
                            df=df,
                            algorithm=selected_algo,
                            target_col=selected_columns['value'] if isinstance(selected_columns, dict) else selected_columns[0],
                            feature_cols=selected_columns['time'] if isinstance(selected_columns, dict) else selected_columns[1:]
                        )
                        
                        # Display results
                        if isinstance(result, float):
                            st.write(f"Model Score: {result:.4f}")
                        
                        st.plotly_chart(fig)
                        
                    except Exception as e:
                        st.error(f"Analysis failed: {str(e)}")
                        st.error(traceback.format_exc())

def show_ai_suggestions():
    st.title("AI Analysis Suggestions")
    
    try:
        snowflake_conn = SnowflakeConnection()
        
        # Get schema info if not cached
        if not st.session_state.get('schema_info'):
            with st.spinner("Loading schema information..."):
                st.session_state.schema_info = snowflake_conn.get_schema_info()
        
        suggestion_engine = MLSuggestionEngine()
        
        for table_idx, (table_name, details) in enumerate(st.session_state.schema_info.items()):
            with st.expander(f"Analysis Suggestions for {table_name}", expanded=True):
                # Create sample dataframe from schema info
                df = pd.DataFrame(details['sample_data'])
                if not df.empty:
                    suggestions = suggestion_engine.analyze_data(df)
                    
                    if suggestions:
                        for analysis_idx, (analysis_type, analysis_details) in enumerate(suggestions.items()):
                            if analysis_type != 'warnings':
                                st.subheader(analysis_type)
                                st.write(f"**Why?** {analysis_details['reason']}")
                                st.write("**Suggested Algorithms:**")
                                for algo in analysis_details['algorithms']:
                                    st.write(f"- {algo}")
                                
                                # Generate and show sample query
                                if isinstance(analysis_details['suggested_columns'], dict):
                                    time_cols = analysis_details['suggested_columns']['time_columns']
                                    value_cols = analysis_details['suggested_columns']['value_columns']
                                    sample_query = f"""
                                        SELECT 
                                            {', '.join(time_cols)},
                                            {', '.join(value_cols)}
                                        FROM {table_name}
                                        ORDER BY {time_cols[0]}
                                        LIMIT 1000
                                    """
                                else:
                                    cols = analysis_details['suggested_columns']
                                    sample_query = f"""
                                        SELECT {', '.join(cols)}
                                        FROM {table_name}
                                        LIMIT 1000
                                    """
                                
                                st.write("**Suggested Query:**")
                                st.code(sample_query.strip(), language='sql')
                                
                                # Add unique key to button based on table and analysis type
                                button_key = f"execute_btn_{table_idx}_{analysis_idx}_{table_name}_{analysis_type}"
                                if st.button(f"Execute {analysis_type} Query", key=button_key):
                                    try:
                                        results = snowflake_conn.execute_query(sample_query)
                                        st.write("Query Results:")
                                        st.dataframe(results)
                                        
                                        # Cache results for ML analysis
                                        st.session_state.query_results = results
                                        st.session_state.generated_sql = sample_query
                                        
                                        # Add download button with unique key
                                        if not results.empty:
                                            csv = results.to_csv(index=False).encode('utf-8')
                                            st.download_button(
                                                "Download Results",
                                                csv,
                                                f"{table_name}_{analysis_type.lower()}_results.csv",
                                                "text/csv",
                                                key=f"download_btn_{table_idx}_{analysis_idx}_{table_name}_{analysis_type}"
                                            )
                                    except Exception as e:
                                        st.error(f"Query execution failed: {str(e)}")
                                
                                st.write("**Relevant Columns:**")
                                if isinstance(analysis_details['suggested_columns'], dict):
                                    st.write("Time Columns:", ", ".join(analysis_details['suggested_columns']['time_columns']))
                                    st.write("Value Columns:", ", ".join(analysis_details['suggested_columns']['value_columns']))
                                else:
                                    st.write(", ".join(analysis_details['suggested_columns']))
                    else:
                        continue
                        #st.info("No analysis suggestions available for this table")
                else:
                    st.warning("No sample data available for analysis")
                    
    except Exception as e:
        st.error(f"Error generating suggestions: {str(e)}")
    finally:
        if 'snowflake_conn' in locals():
            snowflake_conn.close()

if __name__ == "__main__":
    main()
