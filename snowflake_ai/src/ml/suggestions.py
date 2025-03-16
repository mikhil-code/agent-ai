import pandas as pd
import numpy as np
from typing import Dict, List

class MLSuggestionEngine:
    def analyze_data(self, df: pd.DataFrame) -> Dict:
        suggestions = {}
        
        # Get column information
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
        date_cols.extend([col for col in df.columns if 'date' in col.lower()])
        
        # Check for regression potential
        if len(numeric_cols) >= 2:
            suggestions['Regression'] = {
                'algorithms': ['Linear Regression', 'Random Forest'],
                'reason': 'Multiple numeric columns available for prediction',
                'suggested_columns': numeric_cols,
                'example_target': numeric_cols[0],
                'example_features': numeric_cols[1:min(4, len(numeric_cols))]
            }
        
        # Check for clustering potential
        if len(numeric_cols) >= 2:
            suggestions['Clustering'] = {
                'algorithms': ['K-Means'],
                'reason': 'Multiple numeric features available for pattern discovery',
                'suggested_columns': numeric_cols,
                'example_features': numeric_cols[:2]
            }
        
        # Check for time series potential
        if date_cols and numeric_cols:
            suggestions['Time Series'] = {
                'algorithms': ['Prophet', 'ARIMA', 'LSTM'],
                'reason': 'Time-based patterns detected with numeric values',
                'suggested_columns': {
                    'time_columns': date_cols,
                    'value_columns': numeric_cols
                }
            }

        return suggestions

    def get_example_usage(self, df: pd.DataFrame, suggestion_type: str) -> str:
        """Returns example usage text for the suggested analysis"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        examples = {
            'Regression': f"Try predicting {numeric_cols[0]} using {', '.join(numeric_cols[1:3])}",
            'Clustering': f"Find patterns by clustering based on {' and '.join(numeric_cols[:2])}",
            'Time Series': "Analyze trends and make predictions over time"
        }
        
        return examples.get(suggestion_type, "Select columns and algorithm to begin analysis")

    def validate_columns(self, df: pd.DataFrame) -> bool:
        """Validate if dataframe has sufficient columns for analysis"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        return len(numeric_cols) >= 2 and len(df) >= 10
