"""Shared utilities for bevcost analysis scripts."""

from copy import deepcopy

import pandas as pd


def deep_merge(base, overrides):
    """Recursively merge overrides into base dict."""
    result = deepcopy(base)
    for key, value in overrides.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def df_to_serializable(df):
    """Convert a pandas DataFrame or Series to a JSON-serializable dict."""
    if df is None:
        return None
    if isinstance(df, pd.Series):
        index = df.index.tolist()
        if len(index) > 0 and hasattr(index[0], 'isoformat'):
            index = [d.isoformat() for d in index]
        return {'values': df.tolist(), '_index': index}
    result = {}
    for col in df.columns:
        values = df[col].tolist()
        result[col] = values
    index = df.index.tolist()
    if len(index) > 0 and hasattr(index[0], 'isoformat'):
        index = [d.isoformat() for d in index]
    result['_index'] = index
    return result
