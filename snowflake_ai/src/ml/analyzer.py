import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.cluster import KMeans
import plotly.express as px
import plotly.graph_objects as go
import statsmodels.api as sm
import streamlit as st
from prophet import Prophet
from statsmodels.tsa.arima.model import ARIMA
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense

class MLAnalyzer:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()

    def train_model(self, df: pd.DataFrame, algorithm: str, target_col: str = None, feature_cols: list = None):
        if algorithm in ['Prophet', 'ARIMA', 'LSTM']:
            # Ensure proper DataFrame format for time series
            #st.dataframe(df.head())
            st.write("feat cols: ", feature_cols)
            st.write("target col: ", target_col)
            st.write(df[feature_cols])
            ts_df = pd.DataFrame({
                'ds': pd.to_datetime(df[feature_cols]),  
                'y': df[target_col]
            }).sort_values('ds')
            st.dataframe(ts_df)
            
            if algorithm == 'Prophet':
                self.model = Prophet(
                    daily_seasonality=True,
                    weekly_seasonality=True,
                    yearly_seasonality=True
                )
                self.model.fit(ts_df)
                
                # Make predictions
                future = self.model.make_future_dataframe(periods=30)
                self.forecast = self.model.predict(future)
                return self.forecast
                
            elif algorithm == 'ARIMA':
                self.model = ARIMA(ts_df['y'].values, order=(1,1,1))
                self.model_fit = self.model.fit()
                self.forecast = pd.DataFrame({
                    'ds': ts_df['ds'],
                    'yhat': self.model_fit.fittedvalues
                })
                return self.forecast
                
            elif algorithm == 'LSTM':
                # Prepare data for LSTM
                values = ts_df['y'].values.reshape(-1, 1)
                self.scaler = StandardScaler()
                scaled = self.scaler.fit_transform(values)
                
                # Create sequences
                X, y = [], []
                for i in range(len(scaled) - 1):
                    X.append(scaled[i:i+1])
                    y.append(scaled[i + 1])
                X = np.array(X)
                y = np.array(y)
                
                # Build and train LSTM model
                self.model = Sequential([
                    LSTM(50, input_shape=(1, 1), return_sequences=False),
                    Dense(1)
                ])
                self.model.compile(optimizer='adam', loss='mse')
                self.model.fit(X, y, epochs=100, batch_size=1, verbose=0)
                
                # Make predictions
                predictions = self.model.predict(X)
                self.forecast = pd.DataFrame({
                    'ds': ts_df['ds'],
                    'yhat': self.scaler.inverse_transform(predictions).flatten()
                })
                return self.forecast
        else:
            if not feature_cols:
                raise ValueError("Feature columns must be specified")

            # Ensure feature_cols is a list
            if isinstance(feature_cols, str):
                feature_cols = [feature_cols]

            # Prepare features
            X = df[feature_cols]
            if len(X.shape) == 1:
                X = X.to_frame()

            if algorithm == 'Linear Regression':
                return self._train_linear_regression(X, df[target_col])
            elif algorithm == 'Random Forest':
                return self._train_random_forest(X, df[target_col])
            elif algorithm == 'K-Means':
                return self._train_kmeans(X)

    def _train_linear_regression(self, X, y):
        X_scaled = self.scaler.fit_transform(X)
        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2)
        
        # Add constant for statsmodels
        X_train_sm = sm.add_constant(X_train)
        X_test_sm = sm.add_constant(X_test)
        
        # Fit model
        self.model = sm.OLS(y_train, X_train_sm).fit()
        
        # Calculate R-squared
        return self.model.rsquared

    def _train_random_forest(self, X, y):
        X_scaled = self.scaler.fit_transform(X)
        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2)
        self.model = RandomForestRegressor(n_estimators=100)
        self.model.fit(X_train, y_train)
        return self.model.score(X_test, y_test)

    def _train_kmeans(self, X):
        X_scaled = self.scaler.fit_transform(X)
        self.model = KMeans(n_clusters=3)
        return self.model.fit_predict(X_scaled)

    def _train_time_series(self, df: pd.DataFrame, algorithm: str, target_col: str, date_col: str) -> dict:
        # Convert to datetime
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        
        # Create Prophet DataFrame
        prophet_df = pd.DataFrame({
            'ds': df[date_col],
            'y': df[target_col]
        }).sort_values('ds')
        
        if algorithm == 'Prophet':
            model = Prophet(
                daily_seasonality=True,
                weekly_seasonality=True,
                yearly_seasonality=True
            )
            model.fit(prophet_df)
            
            # Make future predictions
            future_dates = model.make_future_dataframe(periods=30)
            forecast = model.predict(future_dates)
            
            self.model = model
            self.forecast = forecast
            return {
                'model': model,
                'forecast': forecast,
                'train_data': prophet_df
            }

        elif algorithm == 'ARIMA':
            self.model = ARIMA(prophet_df['y'], order=(1,1,1))
            self.model_fit = self.model.fit()
            return self.model_fit.fittedvalues

        elif algorithm == 'LSTM':
            # Prepare data for LSTM
            values = prophet_df['y'].values.reshape(-1, 1)
            scaled = self.scaler.fit_transform(values)
            X, y = self._prepare_lstm_data(scaled, look_back=1)
            
            # Build LSTM model
            self.model = Sequential([
                LSTM(50, input_shape=(1, 1)),
                Dense(1)
            ])
            self.model.compile(optimizer='adam', loss='mse')
            self.model.fit(X, y, epochs=100, batch_size=1, verbose=0)
            return self.model.predict(X)

    def _prepare_lstm_data(self, data, look_back=1):
        X, y = [], []
        for i in range(len(data) - look_back):
            X.append(data[i:(i + look_back)])
            y.append(data[i + look_back])
        return np.array(X).reshape(-1, look_back, 1), np.array(y)

    def plot_results(self, df: pd.DataFrame, algorithm: str, target_col: str = None, feature_cols: list = None):
        if algorithm in ['Prophet', 'ARIMA', 'LSTM']:
            fig = go.Figure()
            
            # Plot actual values
            fig.add_trace(go.Scatter(
                x=df[feature_cols],
                y=df[target_col],
                name='Actual',
                mode='markers+lines'
            ))
            
            # Plot predictions
            fig.add_trace(go.Scatter(
                x=self.forecast['ds'],
                y=self.forecast['yhat'],
                name='Forecast',
                mode='lines',
                line=dict(dash='dash')
            ))
            
            fig.update_layout(
                title=f'{algorithm} Time Series Analysis: {target_col}',
                xaxis_title='Date',
                yaxis_title=target_col,
                showlegend=True
            )
            return fig
        else:
            if not feature_cols:
                raise ValueError("Feature columns must be specified")

            if algorithm == 'Linear Regression':
                return self._plot_regression(df, target_col, feature_cols[0])
            elif algorithm == 'Random Forest':
                return self._plot_feature_importance(feature_cols)
            elif algorithm == 'K-Means':
                return self._plot_clusters(df, feature_cols)

    def _plot_regression(self, df, target_col, feature_col):
        X = df[[feature_col]]
        X_sm = sm.add_constant(self.scaler.transform(X))
        predictions = self.model.predict(X_sm)

        fig = px.scatter(df, x=feature_col, y=target_col, 
                        title=f'{target_col} vs {feature_col}')
        fig.add_traces(
            go.Scatter(
                x=df[feature_col],
                y=predictions,
                name='Regression Line',
                line=dict(color='red')
            )
        )
        
        # Add regression statistics
        stats_text = f"""
        R-squared: {self.model.rsquared:.4f}
        Adj R-squared: {self.model.rsquared_adj:.4f}
        P-value: {self.model.f_pvalue:.4f}
        """
        fig.add_annotation(
            x=0.05, y=0.95,
            xref="paper", yref="paper",
            text=stats_text,
            showarrow=False,
            bgcolor="white",
            bordercolor="black",
            borderwidth=1
        )
        
        return fig

    def _plot_feature_importance(self, feature_cols):
        importances = pd.DataFrame({
            'feature': feature_cols,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        return px.bar(importances, x='feature', y='importance',
                     title='Feature Importance')

    def _plot_clusters(self, df, feature_cols):
        if len(feature_cols) < 2:
            feature_cols = feature_cols * 2  # Duplicate single feature for visualization
        
        df_plot = df.copy()
        df_plot['Cluster'] = self.model.labels_
        
        return px.scatter(
            df_plot, 
            x=feature_cols[0], 
            y=feature_cols[1],
            color='Cluster',
            title='K-Means Clustering Results'
        )

    def _plot_time_series(self, df, algorithm, target_col, date_col):
        fig = go.Figure()
        
        # Plot actual values
        fig.add_trace(go.Scatter(
            x=df[date_col],
            y=df[target_col],
            name='Actual',
            mode='lines+markers'
        ))
        
        # Plot predictions
        if algorithm == 'Prophet':
            date_col = feature_cols[0]
            # Create forecast
            future_dates = pd.date_range(
                start=df[date_col].max(),
                periods=30,
                freq='D'
            )
            future = pd.DataFrame({'ds': future_dates})
            forecast = self.model.predict(future)
            
            # Create plot
            fig = go.Figure()
            
            # Plot actual values
            fig.add_trace(go.Scatter(
                x=df[date_col],
                y=df[target_col],
                name='Actual',
                mode='markers+lines'
            ))
            
            # Plot predictions
            fig.add_trace(go.Scatter(
                x=forecast['ds'],
                y=forecast['yhat'],
                name='Forecast',
                mode='lines',
                line=dict(dash='dash')
            ))
            
            # Add confidence intervals
            fig.add_trace(go.Scatter(
                x=forecast['ds'],
                y=forecast['yhat_upper'],
                fill=None,
                mode='lines',
                line=dict(color='rgba(0,100,80,0.2)'),
                name='Upper Bound'
            ))
            fig.add_trace(go.Scatter(
                x=forecast['ds'],
                y=forecast['yhat_lower'],
                fill='tonexty',
                mode='lines',
                line=dict(color='rgba(0,100,80,0.2)'),
                name='Lower Bound'
            ))
            
            fig.update_layout(
                title=f'Time Series Forecast: {target_col}',
                xaxis_title='Date',
                yaxis_title=target_col,
                hovermode='x unified'
            )
            return fig
            
        elif algorithm in ['ARIMA', 'LSTM']:
            predictions = self.model_fit.fittedvalues if algorithm == 'ARIMA' else self.model.predict(df[target_col].values.reshape(-1,1,1))
            fig.add_trace(go.Scatter(
                x=df[date_col],
                y=predictions,
                name='Forecast',
                mode='lines'
            ))
        
        fig.update_layout(
            title=f'{algorithm} Time Series Analysis: {target_col}',
            xaxis_title=date_col,
            yaxis_title=target_col
        )
        return fig
