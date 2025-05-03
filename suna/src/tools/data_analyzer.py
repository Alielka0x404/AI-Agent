import logging
import json
import traceback
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)

# Check if pandas is available
try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

class DataAnalyzer:
    """Tools for data analysis and processing."""
    
    def __init__(self, config=None):
        """
        Initialize the data analyzer.
        
        Args:
            config (dict, optional): Configuration for data analysis
        """
        self.config = config or {}
        
        # Check if required packages are available
        if not PANDAS_AVAILABLE:
            logger.warning("Pandas not available. Please install with: pip install pandas numpy")
    
    def analyze_data(self, data: Union[str, Dict, List], analysis_type: str = "basic") -> Dict[str, Any]:
        """
        Perform data analysis on structured data.
        
        Args:
            data (Union[str, Dict, List]): The data to analyze
            analysis_type (str, optional): Type of analysis to perform
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        if not PANDAS_AVAILABLE:
            return {
                "success": False,
                "error": "Pandas not available. Please install with: pip install pandas numpy"
            }
            
        try:
            # Convert data to DataFrame
            df = self._convert_to_dataframe(data)
            if isinstance(df, dict) and "error" in df:
                return {
                    "success": False,
                    "error": df["error"]
                }
            
            # Perform the requested analysis
            if analysis_type == "basic":
                return self._basic_analysis(df)
            elif analysis_type == "correlation":
                return self._correlation_analysis(df)
            elif analysis_type == "timeseries":
                return self._timeseries_analysis(df)
            elif analysis_type == "distribution":
                return self._distribution_analysis(df)
            elif analysis_type == "summary":
                return self._summary_analysis(df)
            else:
                return {
                    "success": False,
                    "error": f"Unknown analysis type: {analysis_type}"
                }
                
        except Exception as e:
            logger.error(f"Error analyzing data: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    def _convert_to_dataframe(self, data: Union[str, Dict, List]) -> Union[pd.DataFrame, Dict]:
        """Convert input data to a pandas DataFrame."""
        try:
            if isinstance(data, str):
                try:
                    # Try to parse as JSON
                    data = json.loads(data)
                except json.JSONDecodeError:
                    return {"error": "Input data is not valid JSON"}
            
            if isinstance(data, dict):
                # Check if it's a dict of lists/arrays (columns)
                if all(isinstance(v, (list, tuple, np.ndarray)) for v in data.values()):
                    return pd.DataFrame.from_dict(data)
                # Check if it's a dict of dicts (records)
                elif all(isinstance(v, dict) for v in data.values()):
                    return pd.DataFrame.from_dict(data, orient='index')
                else:
                    return pd.DataFrame([data])
            elif isinstance(data, list):
                if all(isinstance(item, dict) for item in data):
                    return pd.DataFrame(data)
                else:
                    return pd.DataFrame(data)
            else:
                return {"error": "Input data must be a dictionary, list, or JSON string"}
                
        except Exception as e:
            return {"error": f"Error converting data to DataFrame: {str(e)}"}
    
    def _basic_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Perform basic statistical analysis."""
        try:
            # Get column types
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            datetime_cols = df.select_dtypes(include=['datetime']).columns.tolist()
            bool_cols = df.select_dtypes(include=['bool']).columns.tolist()
            
            # Basic dataframe info
            info = {
                "shape": df.shape,
                "columns": df.columns.tolist(),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "missing_values": df.isnull().sum().to_dict(),
                "missing_percentage": (df.isnull().sum() / len(df) * 100).to_dict()
            }
            
            # Numeric summary
            numeric_summary = {}
            if numeric_cols:
                numeric_summary = df[numeric_cols].describe().to_dict()
                
                # Add additional metrics
                for col in numeric_cols:
                    if col in numeric_summary:
                        numeric_summary[col]["skew"] = float(df[col].skew()) if hasattr(df[col], 'skew') else None
                        numeric_summary[col]["kurtosis"] = float(df[col].kurtosis()) if hasattr(df[col], 'kurtosis') else None
            
            # Categorical summary
            categorical_summary = {}
            for col in categorical_cols[:10]:  # Limit to first 10 categorical columns
                value_counts = df[col].value_counts().head(10).to_dict()  # Top 10 values
                unique_count = df[col].nunique()
                categorical_summary[col] = {
                    "unique_count": unique_count,
                    "top_values": value_counts
                }
            
            # Boolean summary
            boolean_summary = {}
            for col in bool_cols:
                value_counts = df[col].value_counts().to_dict()
                boolean_summary[col] = {
                    "true_count": int(value_counts.get(True, 0)),
                    "false_count": int(value_counts.get(False, 0)),
                    "true_percentage": float(value_counts.get(True, 0) / len(df) * 100) if len(df) > 0 else 0,
                    "false_percentage": float(value_counts.get(False, 0) / len(df) * 100) if len(df) > 0 else 0
                }
            
            # Datetime summary
            datetime_summary = {}
            for col in datetime_cols:
                datetime_summary[col] = {
                    "min": df[col].min().isoformat() if not pd.isna(df[col].min()) else None,
                    "max": df[col].max().isoformat() if not pd.isna(df[col].max()) else None,
                    "range_days": (df[col].max() - df[col].min()).days if not pd.isna(df[col].min()) and not pd.isna(df[col].max()) else None
                }
            
            return {
                "success": True,
                "analysis_type": "basic",
                "info": info,
                "numeric_summary": numeric_summary,
                "categorical_summary": categorical_summary,
                "boolean_summary": boolean_summary,
                "datetime_summary": datetime_summary
            }
            
        except Exception as e:
            logger.error(f"Error in basic analysis: {str(e)}", exc_info=True)
            return {
                "success": False,
                "analysis_type": "basic",
                "error": str(e)
            }
    
    def _correlation_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Perform correlation analysis on numeric columns."""
        try:
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            
            if len(numeric_cols) < 2:
                return {
                    "success": False,
                    "analysis_type": "correlation",
                    "error": "Not enough numeric columns for correlation analysis"
                }
            
            # Calculate correlation matrix
            corr_matrix = df[numeric_cols].corr().to_dict()
            
            # Find highest correlations
            correlations = []
            for i, col1 in enumerate(numeric_cols):
                for col2 in numeric_cols[i+1:]:
                    corr_value = df[col1].corr(df[col2])
                    if not pd.isna(corr_value):
                        correlations.append({
                            "column1": col1,
                            "column2": col2,
                            "correlation": float(corr_value)
                        })
            
            # Sort by absolute correlation value
            correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)
            
            return {
                "success": True,
                "analysis_type": "correlation",
                "correlation_matrix": corr_matrix,
                "top_correlations": correlations[:10]  # Top 10 correlations
            }
            
        except Exception as e:
            logger.error(f"Error in correlation analysis: {str(e)}", exc_info=True)
            return {
                "success": False,
                "analysis_type": "correlation",
                "error": str(e)
            }
    
    def _timeseries_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Perform time series analysis."""
        try:
            # Find datetime columns
            datetime_cols = []
            for col in df.columns:
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    datetime_cols.append(col)
                else:
                    try:
                        # Try to convert to datetime
                        df[f"{col}_dt"] = pd.to_datetime(df[col], errors='coerce')
                        if not df[f"{col}_dt"].isna().all():
                            datetime_cols.append(f"{col}_dt")
                    except:
                        pass
            
            if not datetime_cols:
                return {
                    "success": False,
                    "analysis_type": "timeseries",
                    "error": "No datetime columns found for time series analysis"
                }
            
            # Use the first datetime column for analysis
            date_col = datetime_cols[0]
            
            # Ensure data is sorted by date
            df = df.sort_values(by=date_col)
            
            # Basic time metrics
            time_metrics = {
                "start_date": df[date_col].min().isoformat() if not pd.isna(df[date_col].min()) else None,
                "end_date": df[date_col].max().isoformat() if not pd.isna(df[date_col].max()) else None,
                "time_span_days": (df[date_col].max() - df[date_col].min()).days if not pd.isna(df[date_col].min()) and not pd.isna(df[date_col].max()) else None,
                "record_count": len(df)
            }
            
            # Time-based aggregations
            time_aggregations = {}
            
            # Find numeric columns for aggregation
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            if numeric_cols:
                # Daily aggregation (first 30 days)
                try:
                    daily_df = df.set_index(date_col).resample('D').mean()
                    daily_data = daily_df[numeric_cols].head(30).to_dict()
                    time_aggregations["daily"] = {
                        "aggregation": "mean",
                        "data": daily_data
                    }
                except:
                    pass
                
                # Monthly aggregation
                try:
                    monthly_df = df.set_index(date_col).resample('M').mean()
                    monthly_data = monthly_df[numeric_cols].to_dict()
                    time_aggregations["monthly"] = {
                        "aggregation": "mean",
                        "data": monthly_data
                    }
                except:
                    pass
            
            # Detect seasonality and trends
            seasonality = {}
            for col in numeric_cols[:3]:  # Analyze first 3 numeric columns
                try:
                    # Simple trend detection
                    values = df[col].values
                    if len(values) > 2:
                        trend = "increasing" if values[-1] > values[0] else "decreasing"
                        seasonality[col] = {
                            "trend": trend,
                            "start_value": float(values[0]),
                            "end_value": float(values[-1]),
                            "change_percentage": float((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else None
                        }
                except:
                    pass
            
            return {
                "success": True,
                "analysis_type": "timeseries",
                "date_column": date_col,
                "time_metrics": time_metrics,
                "time_aggregations": time_aggregations,
                "seasonality": seasonality
            }
            
        except Exception as e:
            logger.error(f"Error in time series analysis: {str(e)}", exc_info=True)
            return {
                "success": False,
                "analysis_type": "timeseries",
                "error": str(e)
            }
    
    def _distribution_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze the distribution of numeric columns."""
        try:
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            
            if not numeric_cols:
                return {
                    "success": False,
                    "analysis_type": "distribution",
                    "error": "No numeric columns found for distribution analysis"
                }
            
            distributions = {}
            for col in numeric_cols[:5]:  # Analyze first 5 numeric columns
                try:
                    # Calculate percentiles
                    percentiles = [0, 10, 25, 50, 75, 90, 100]
                    percentile_values = np.percentile(df[col].dropna(), percentiles)
                    
                    # Calculate histogram
                    hist, bin_edges = np.histogram(df[col].dropna(), bins=10)
                    
                    distributions[col] = {
                        "percentiles": {str(p): float(v) for p, v in zip(percentiles, percentile_values)},
                        "histogram": {
                            "counts": [int(x) for x in hist],
                            "bin_edges": [float(x) for x in bin_edges]
                        },
                        "mean": float(df[col].mean()),
                        "median": float(df[col].median()),
                        "std": float(df[col].std()),
                        "skew": float(df[col].skew()) if hasattr(df[col], 'skew') else None,
                        "kurtosis": float(df[col].kurtosis()) if hasattr(df[col], 'kurtosis') else None
                    }
                except:
                    pass
            
            return {
                "success": True,
                "analysis_type": "distribution",
                "distributions": distributions
            }
            
        except Exception as e:
            logger.error(f"Error in distribution analysis: {str(e)}", exc_info=True)
            return {
                "success": False,
                "analysis_type": "distribution",
                "error": str(e)
            }
    
    def _summary_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Provide a comprehensive summary of the dataset."""
        try:
            # Basic info
            info = {
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": df.columns.tolist(),
                "memory_usage": df.memory_usage(deep=True).sum(),
                "duplicated_rows": int(df.duplicated().sum())
            }
            
            # Column types summary
            column_types = df.dtypes.value_counts().to_dict()
            column_types = {str(k): int(v) for k, v in column_types.items()}
            
            # Missing values summary
            missing_values = df.isnull().sum()
            columns_with_missing = missing_values[missing_values > 0].to_dict()
            missing_summary = {
                "total_missing_values": int(missing_values.sum()),
                "columns_with_missing": len(columns_with_missing),
                "columns_missing_data": {k: int(v) for k, v in columns_with_missing.items()}
            }
            
            # Sample data (first 5 rows)
            sample_data = df.head(5).to_dict(orient='records')
            
            return {
                "success": True,
                "analysis_type": "summary",
                "info": info,
                "column_types": column_types,
                "missing_summary": missing_summary,
                "sample_data": sample_data
            }
            
        except Exception as e:
            logger.error(f"Error in summary analysis: {str(e)}", exc_info=True)
            return {
                "success": False,
                "analysis_type": "summary",
                "error": str(e)
            }