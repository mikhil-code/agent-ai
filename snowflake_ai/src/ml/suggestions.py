import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

class MLSuggestionEngine:
    def _clean_numeric_data(self, df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
        """Clean numeric data by filling nan with 0"""
        df = df.copy()
        for col in columns:
            df[col] = df[col].fillna(0)
        return df

    def _validate_numeric_data(self, df: pd.DataFrame, columns: List[str]) -> Tuple[bool, List[str]]:
        """Validate numeric columns for inf values only"""
        problematic_cols = []
        for col in columns:
            if np.isinf(df[col]).any():
                problematic_cols.append(col)
        return len(problematic_cols) == 0, problematic_cols

    def analyze_data(self, df: pd.DataFrame) -> Dict:
        suggestions = {}
        
        # Get column information
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()   

        # Clean nan values
        df = self._clean_numeric_data(df, numeric_cols)

        # Validate for inf values
        is_valid, problematic_cols = self._validate_numeric_data(df, numeric_cols)
        if not is_valid:
            suggestions['warnings'] = {
                'message': 'Some columns contain infinite values',
                'affected_columns': problematic_cols,
                'recommendation': 'Consider handling infinite values before analysis'
            }
            # Filter out problematic columns
            numeric_cols = [col for col in numeric_cols if col not in problematic_cols]

        date_cols.extend([col for col in df.columns if 'date' in col.lower()])
        date_cols.extend([col for col in df.columns if 'month' in col.lower()])
        date_cols.extend([col for col in df.columns if 'year' in col.lower()])
        
        # Only suggest analysis if we have valid columns
        if len(numeric_cols) >= 2:
            suggestions['Regression'] = {
                'algorithms': ['Linear Regression', 'Random Forest'],
                'reason': 'Multiple numeric columns available for prediction',
                'suggested_columns': numeric_cols,
                'example_target': numeric_cols[0],
                'example_features': numeric_cols[1:min(4, len(numeric_cols))]
            }
        
            suggestions['Clustering'] = {
                'algorithms': ['K-Means'],
                'reason': 'Multiple numeric features available for pattern discovery',
                'suggested_columns': numeric_cols,
                'example_features': numeric_cols[:2]
            }
        
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

    def validate_columns(self, df: pd.DataFrame) -> bool:
        """Validate if dataframe has sufficient columns for analysis"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if len(numeric_cols) < 2 or len(df) < 10:
            return False
            
        # Check for inf/nan values
        is_valid, _ = self._validate_numeric_data(df, numeric_cols)
        return is_valid and len(numeric_cols) >= 2 and len(df) >= 10
