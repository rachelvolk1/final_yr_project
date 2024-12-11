# models/evaluation_functions.py

import pandas as pd
import logging
import os
from sklearn.impute import SimpleImputer
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def load_data(filepath):
    """
    Load and clean the data from the specified file path.
    """
    try:
        logging.info(f"Loading data from {filepath}")
        df = pd.read_csv(filepath)

        # Cleaning the data
        expected_columns = ['LOCATION', 'TAX TYPE', 'Transaction ID', 'Payment Date', 'Period From', 'Period To',
                            'Payment Amount', 'TPIN']
        if not all(col in df.columns for col in expected_columns):
            logging.error("Missing one or more expected columns.")
            return None
        logging.info("All expected columns are present.")

        date_cols = ['Payment Date', 'Period From', 'Period To']
        for col in date_cols:
            df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=True)
            logging.info(f"Converted {col} to datetime.")

        df[date_cols] = df[date_cols].fillna(pd.NaT)
        logging.info("Handled missing date values.")

        df.fillna({
            'TPIN': 'Unknown',
            'LOCATION': 'Unknown',
            'TAX TYPE': 'Unknown',
            'Transaction ID': 'Unknown',
            'Payment Amount': df['Payment Amount'].median() if 'Payment Amount' in df.columns else 0
        }, inplace=True)
        logging.info("Filled missing values.")

        df.dropna(subset=['Transaction ID', 'Payment Date', 'Period From', 'Period To'], inplace=True)
        logging.info("Dropped rows with essential missing values.")

        return df
    except Exception as e:
        logging.error(f"An error occurred while loading data: {e}")
        raise e


def ensure_data_types(df):
    """
    Ensure the data types of essential columns are consistent.
    """
    df['TPIN'] = df['TPIN'].astype(str)
    df['Transaction ID'] = df['Transaction ID'].astype(str)
    logging.info("Set TPIN and Transaction ID as strings.")
    if 'Payment Amount' in df.columns:
        df['Payment Amount'] = df['Payment Amount'].astype(float)
        logging.info("Set Payment Amount as float.")
    return df


def remove_duplicates(df):
    """
    Identify and remove duplicate transactions.
    """
    before_count = len(df)
    df = df.drop_duplicates(subset=['Transaction ID', 'Payment Date', 'TPIN', 'Payment Amount'], keep='first')
    after_count = len(df)
    duplicates_removed = before_count - after_count
    logging.info(f"Removed {duplicates_removed} duplicate transactions.")
    return df


def basic_one_hot_encode(df):
    """
    Perform basic one-hot encoding on 'LOCATION' and 'TAX TYPE' columns.
    """
    if 'LOCATION' in df.columns:
        df = pd.get_dummies(df, columns=['LOCATION'], prefix='LOCATION', drop_first=False)
        logging.info("Performed one-hot encoding on 'LOCATION'.")
    if 'TAX TYPE' in df.columns:
        df = pd.get_dummies(df, columns=['TAX TYPE'], prefix='TAX_TYPE', drop_first=False)
        logging.info("Performed one-hot encoding on 'TAX TYPE'.")
    return df


def preprocess_data(df):
    """
    Preprocess the data by converting date columns to numerical features,
    and ensuring all columns (excluding specified ones) are numeric after processing.
    """
    logging.info("Preprocessing data")

    def parse_date(date_str):
        """Attempts to parse a date string in various formats and normalizes to %m/%d/%Y."""
        for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
            try:
                parsed_date = pd.to_datetime(date_str, format=fmt)
                return parsed_date.strftime('%m/%d/%Y')  # Normalize to %m/%d/%Y
            except ValueError:
                pass
        return pd.NaT  # Return NaT (Not a Time) if all formats fail

    # Convert specific date columns to numerical features
    date_columns = ['Payment Date', 'Period From', 'Period To']
    for col in date_columns:
        if col in df.columns:
            df[col] = df[col].apply(parse_date)
            if df[col].isna().any():
                raise ValueError(f"Failed to parse some dates in column {col}")
            # Convert back to datetime to extract features
            df[col] = pd.to_datetime(df[col], format='%m/%d/%Y')
            df[f'{col}_year'] = df[col].dt.year
            df[f'{col}_month'] = df[col].dt.month
            df[f'{col}_day'] = df[col].dt.day
            df.drop(columns=[col], inplace=True)
            logging.info(f"Converted date column {col} to numerical features")
        else:
            logging.info(f"Column {col} not found in the dataset, skipping conversion")

    # Dropping categorical columns processed already as NUMERIC
    categorical_columns = ['LOCATION', 'TAX TYPE']
    for col in categorical_columns:
        if col in df.columns:
            df.drop(columns=[col], inplace=True)
            logging.info(f"Dropped original categorical column {col}")

    # Verify which columns should remain as strings
    string_columns = ['TPIN', 'Transaction ID', 'Payment Method']

    # Ensure all remaining columns are numeric, except for string_columns
    for col in df.columns:
        if col in string_columns:
            logging.info(f"Column {col} is expected to remain as string")
            continue
        if df[col].dtype == 'object':
            raise ValueError(
                f"Column {col} is non-numeric but was expected to be numeric. Check the one-hot encoding process.")
        else:
            logging.info(f"Column {col} is confirmed to be numeric")

    return df

