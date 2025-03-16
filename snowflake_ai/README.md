# Snowflake AI Query Generator

An intelligent natural language to SQL query generator for Snowflake using OpenAI and Streamlit.

## Project Structure
```
snowflake_ai/
├── src/
│   ├── core/                # Core functionality
│   │   ├── __init__.py
│   │   ├── snowflake.py    # Snowflake connection handling
│   │   └── openai_client.py # OpenAI integration
│   ├── utils/              # Utility functions
│   │   ├── __init__.py
│   │   ├── query_helper.py # SQL query utilities
│   │   └── validator.py    # Input validation
│   └── app.py             # Streamlit application
├── config/                # Configuration files
│   ├── snowflake_conf.yaml
│   └── model_conf.yaml
├── tests/                # Test files
├── .env.template         # Environment variables template
├── requirements.txt      # Project dependencies
└── README.md            # Project documentation
```

## Features
- Natural language to SQL query conversion
- Interactive query building and execution
- Query history and management
- Schema visualization
- Query optimization suggestions
- Export results to various formats

## Requirements
- Python 3.8+
- Snowflake account
- OpenAI API key
- Streamlit
