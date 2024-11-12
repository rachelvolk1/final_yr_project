import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)


def load_and_clean_data(file_path):
    """
    Load a CSV dataset with specified columns and perform initial cleaning.
    """
    try:
        df = pd.read_csv(file_path)
        logging.info("CSV file loaded successfully.")
    except Exception as e:
        logging.error(f"Error loading CSV file: {e}")
        return None

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
