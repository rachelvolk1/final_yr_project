import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
#import matplotlib.pyplot as plt
#import seaborn as sns
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_csv_to_dataframe(file_path: str) -> pd.DataFrame:
    """
    Loads a CSV file into a pandas DataFrame.

    :param file_path: The file path to the CSV file.
    :return: DataFrame containing the data from the CSV file.
    """
    try:
        df = pd.read_csv(file_path)
        logger.info("File loaded successfully.")
        logger.info("Columns in the dataset: %s", df.columns.tolist())
        return df
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return pd.DataFrame()
    except pd.errors.EmptyDataError:
        logger.error("No data: The file is empty.")
        return pd.DataFrame()
    except pd.errors.ParserError:
        logger.error("Parsing error: Check the contents of the file.")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return pd.DataFrame()


def prepare_for_isolation_forest(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepares the DataFrame for Isolation Forest by adding necessary features.

    :param df: DataFrame containing the data.
    :return: DataFrame with required features added.
    """
    payment_counts = df.groupby(['TPIN', 'Period From', 'Period To']).size().reset_index(name='payment_frequency')
    df = pd.merge(df, payment_counts, on=['TPIN', 'Period From', 'Period To'], how='left')

    df['payment_amount_log'] = np.log1p(df['Payment Amount'])
    df['is_weekend'] = pd.to_datetime(df['Payment Date']).dt.dayofweek >= 5
    df['quarter'] = pd.to_datetime(df['Payment Date']).dt.quarter

    return df


def evaluate_anomalies(df: pd.DataFrame) -> tuple:
    """
    Evaluates the number of anomalies and their percentage in the DataFrame.

    :param df: DataFrame containing the data with 'is_anomaly' column.
    :return: Number of anomalies and their percentage in the dataset.
    """
    num_anomalies = df['is_anomaly'].sum()
    total_records = len(df)
    anomaly_percentage = (num_anomalies / total_records) * 100

    logger.info(f"Total number of records: {total_records}")
    logger.info(f"Number of anomalies detected: {num_anomalies}")
    logger.info(f"Percentage of anomalies detected: {anomaly_percentage:.2f}%")

    return num_anomalies, anomaly_percentage


def perform_anomaly_detection(df: pd.DataFrame) -> pd.DataFrame:
    """
    Performs anomaly detection using Isolation Forest and labels the data with anomalies.

    :param df: DataFrame containing the data.
    :return: DataFrame with a new column 'is_anomaly' indicating anomalies.
    """
    df = prepare_for_isolation_forest(df)
    features = ['Payment Amount', 'payment_frequency', 'payment_amount_log', 'is_weekend', 'quarter']
    X = df[features]

    isolation_forest = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
    df['is_anomaly'] = isolation_forest.fit_predict(X)
    df['is_anomaly'] = df['is_anomaly'].apply(lambda x: 1 if x == -1 else 0)

    num_anomalies, anomaly_percentage = evaluate_anomalies(df)
    return df


def save_labeled_dataframe(df: pd.DataFrame, output_file_path: str):
    """
    Saves the DataFrame with anomaly labels to a CSV file.

    :param df: DataFrame containing the data with 'is_anomaly' column.
    :param output_file_path: The file path to save the labeled data.
    """
    df.to_csv(output_file_path, index=False)
    logger.info(f"Labeled anomalies saved to {output_file_path}")


def plot_visualizations(df: pd.DataFrame, report_dir: str):
    """
    Generates and saves box plots and scatter plots visualizing anomalies.

    :param df: DataFrame containing the data with 'is_anomaly' column.
    :param report_dir: Directory to save the plots.
    """
    anomalies = df[df['is_anomaly'] == 1]
    normal = df[df['is_anomaly'] == 0]

    boxplot_file_path = os.path.join(report_dir, 'boxplot_payment_amount.png')
   # plt.figure(figsize=(12, 6))
   # sns.boxplot(x='is_anomaly', y='Payment Amount', data=df)
   # plt.title('Box Plot of Payment Amount with Anomalies')
  # plt.savefig(boxplot_file_path)
   # plt.close()
    logger.info(f"Box plot saved to {boxplot_file_path}")

    scatterplot_file_path = os.path.join(report_dir, 'scatterplot_payment_frequency.png')
    #plt.figure(figsize=(12, 6))
   # plt.scatter(normal['Payment Amount'], normal['payment_frequency'], label='Normal', alpha=0.5)
   # plt.scatter(anomalies['Payment Amount'], anomalies['payment_frequency'], color='r', label='Anomaly', alpha=0.5)
   # plt.xlabel('Payment Amount')
   # plt.ylabel('Payment Frequency')
   # plt.title('Scatter Plot of Payment Amount vs Payment Frequency')
    #plt.legend()
  #  plt.savefig(scatterplot_file_path)
  #  plt.close()
    logger.info(f"Scatter plot saved to {scatterplot_file_path}")


def save_report(report_dir: str, df: pd.DataFrame):
    """
    Creates a report directory, performs anomaly detection, saves labeled data and visualizations.

    :param report_dir: The directory where the report will be saved.
    :param df: DataFrame containing the data.
    """
    os.makedirs(report_dir, exist_ok=True)

    df = perform_anomaly_detection(df)
    output_file_path = os.path.join(report_dir, 'labeled_anomalies.csv')
    save_labeled_dataframe(df, output_file_path)
    plot_visualizations(df, report_dir)

    logger.info(f"Report created in {report_dir}")
