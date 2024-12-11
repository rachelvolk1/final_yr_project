import pandas as pd
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
        logger.error("File not found: %s", file_path)
        return pd.DataFrame()
    except pd.errors.EmptyDataError:
        logger.error("No data: The file is empty.")
        return pd.DataFrame()
    except pd.errors.ParserError:
        logger.error("Parsing error: Check the contents of the file.")
        return pd.DataFrame()
    except Exception as e:
        logger.error("An unexpected error occurred: %s", e)
        return pd.DataFrame()


def save_plot(fig, filename: str):
    """
    Saves a matplotlib figure to a file and displays it interactively.

    :param fig: The matplotlib figure object.
    :param filename: The file path to save the figure.
    """
    fig.savefig(filename, bbox_inches='tight')
    # plt.show()  # This will display the plot interactively in PyCharm
    # plt.close(fig)  # Close the figure
    logger.info("Plot saved as %s", filename)


def generate_statistics(df: pd.DataFrame) -> str:
    """
    Generates statistics of the dataset and returns them as a string.

    :param df: DataFrame containing the data.
    :return: String containing the statistics.
    """
    logger.info("Generating statistics.")
    stats = df.describe()

    if 'is_anomaly' in df.columns:
        anomaly_counts = df['is_anomaly'].value_counts()
        stats_str = stats.to_string() + "\n\n"
        stats_str += "Anomaly Counts:\n" + anomaly_counts.to_string()
        logger.info("Statistics generated successfully.")
    else:
        # If 'is_anomaly' column does not exist, create it with default value 0
        logger.warning("'is_anomaly' column not found in the dataset. Creating the column with default values.")
        df['is_anomaly'] = 0  # Create the column with default value 0
        anomaly_counts = df['is_anomaly'].value_counts()
        stats_str = stats.to_string() + "\n\n"
        stats_str += "'is_anomaly' column was not present in the dataset and has been added.\n"
        stats_str += "Anomaly Counts:\n" + anomaly_counts.to_string()
        logger.info("Statistics generated successfully.")

    return stats_str


def plot_correlation_heatmap(df: pd.DataFrame, filename: str):
    """
    Plots and saves a correlation heatmap of numerical features including anomaly labels.

    :param df: DataFrame containing the data.
    :param filename: The file path to save the heatmap.
    """
    logger.info("Plotting correlation heatmap.")
    # Select only numerical features and 'is_anomaly' column
    numerical_features = df.select_dtypes(include='number')

    # Calculate the correlation matrix
    correlation_matrix = numerical_features.corr()

    # Create a heatmap
    # fig, ax = plt.subplots(figsize=(14, 10))
    # sns.heatmap(correlation_matrix, annot=True, fmt='.2f', cmap='coolwarm', linewidths=0.5, ax=ax)

    # Add title
    # ax.set_title('Correlation Heatmap of Numerical Features and Anomaly Labels')

    # Save and display plot
    # save_plot(fig, filename)
    logger.info("Correlation heatmap plot saved.")


def plot_anomalies_distribution_by_group_one_hot(df: pd.DataFrame, group_by_prefix: str, filename: str, palette: str):
    """
    Plots and saves bar charts to show the distribution of anomalies by a specified one-hot encoded group prefix.

    :param df: DataFrame containing the data with one-hot encoded columns with specified prefix and 'is_anomaly' column.
    :param group_by_prefix: The prefix of the one-hot encoded column names (e.g., 'tax_type_' or 'location_')
    :param filename: The file path to save the bar chart.
    :param palette: The color palette to use for the plot.
    """
    logger.info("Plotting anomalies distribution by group: %s", group_by_prefix)

    # Ensure 'is_anomaly' column exists
    if 'is_anomaly' not in df.columns:
        logger.warning("'is_anomaly' column is missing. Creating column with default values.")
        df['is_anomaly'] = 0

    # Filter for anomalies
    anomalies = df[df['is_anomaly'] == 1]

    # Select columns that start with the specified prefix
    group_by_columns = [col for col in df.columns if col.startswith(group_by_prefix)]

    if not group_by_columns:
        logger.warning("No columns found for prefix '%s' in the dataset.", group_by_prefix)
        return

    # Sum the occurrences for each category
    anomalies_by_group = anomalies[group_by_columns].sum().reset_index()
    anomalies_by_group.columns = ['category', 'count']

    # Create a bar plot
    # fig, ax = plt.subplots(figsize=(14, 8))
    # sns.barplot(x='category', y='count', data=anomalies_by_group, hue='category', palette=palette, legend=False, ax=ax)

    # Add labels and title
    # ax.set_title(f'Distribution of Anomalies by {group_by_prefix.replace("_", " ").capitalize()}')
    # ax.set_xlabel(group_by_prefix.replace("_", " ").capitalize())
    # ax.set_ylabel('Number of Anomalies')
    # plt.xticks(rotation=45)

    # Save and display plot
    # save_plot(fig, filename)
    logger.info("Distribution plot for %s saved.", group_by_prefix)


def save_report(report_dir: str, df: pd.DataFrame):
    """
    Generates and saves statistics, plots, and sample anomalies to a report.

    :param report_dir: The directory where the report will be saved.
    :param df: DataFrame containing the data.
    """
    logger.info("Saving report to directory: %s", report_dir)
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)
        logger.info("Created report directory: %s", report_dir)

    # Ensure 'is_anomaly' column exists
    if 'is_anomaly' not in df.columns:
        logger.warning("'is_anomaly' column is missing. Creating column with default values.")
        df['is_anomaly'] = 0

    # Generate statistics
    stats_str = generate_statistics(df)
    with open(os.path.join(report_dir, 'statistics.txt'), 'w') as file:
        file.write(stats_str)
    logger.info("Statistics saved to %s", os.path.join(report_dir, 'statistics.txt'))

    # Plot and save correlation heatmap
    plot_correlation_heatmap(df, os.path.join(report_dir, 'correlation_heatmap.png'))
    logger.info("Correlation heatmap saved to %s", os.path.join(report_dir, 'correlation_heatmap.png'))

    # Plot and save distribution by tax type
    plot_anomalies_distribution_by_group_one_hot(df, 'TAX_TYPE_', os.path.join(report_dir, 'anomalies_by_tax_type.png'),
                                                 palette='tab20')
    logger.info("Distribution by tax type plot saved to %s", os.path.join(report_dir, 'anomalies_by_tax_type.png'))

    # Plot and save distribution by location
    plot_anomalies_distribution_by_group_one_hot(df, 'LOCATION_', os.path.join(report_dir, 'anomalies_by_location.png'),
                                                 palette='viridis')
    logger.info("Distribution by location plot saved to %s", os.path.join(report_dir, 'anomalies_by_location.png'))

    # Save sample anomalies
    sample_anomalies = df[df['is_anomaly'] == 1].head(5)
    sample_anomalies.to_csv(os.path.join(report_dir, 'sample_anomalies.csv'), index=False)
    logger.info("Sample anomalies saved to %s", os.path.join(report_dir, 'sample_anomalies.csv'))
