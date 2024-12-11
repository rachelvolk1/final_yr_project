import joblib
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split
import numpy as np
import logging
import pandas as pd


def train_isolation_forest(data, hyperparameters=None, save_path=None):
    """
    Train an Isolation Forest model and evaluate it.

    Args:
        data (pd.DataFrame): The entire dataset to split into training and test sets.
        hyperparameters (dict, optional): Parameters for IsolationForest.
        save_path (str, optional): Path to save the trained model.

    Returns:
        dict: A dictionary containing the trained model and evaluation results.
    """
    hyperparameters = hyperparameters or {}
    logging.info("Training Isolation Forest with hyperparameters: %s", hyperparameters)

    # Split the data into 80% training and 20% test sets
    X_train, X_test = train_test_split(data, test_size=0.2, random_state=42)

    model = IsolationForest(**hyperparameters)

    # Train the model
    model.fit(X_train)
    logging.info("Model training completed.")

    # Save the model
    if save_path:
        joblib.dump(model, save_path)
        logging.info("Model saved to %s", save_path)

    # Initialize metrics dictionary
    metrics = {
        'proportion_outliers_train': None,
        'proportion_outliers_test': None,
        'outlier_labels_train': None,
        'outlier_labels_test': None,
        'count_1_train': None,
        'count_minus1_train': None,
        'count_1_test': None,
        'count_minus1_test': None
    }

    # Calculate proportion of outliers in the training set
    train_labels = model.predict(X_train)
    metrics['proportion_outliers_train'] = float(np.mean(train_labels == -1))
    metrics['outlier_labels_train'] = list(map(int, train_labels))
    metrics['count_1_train'] = int(np.sum(train_labels == 1))
    metrics['count_minus1_train'] = int(np.sum(train_labels == -1))
    logging.info("Proportion of outliers in training data: %.2f", metrics['proportion_outliers_train'])
    logging.info("Count of 1s (normal) in training data: %d", metrics['count_1_train'])
    logging.info("Count of -1s (outliers) in training data: %d", metrics['count_minus1_train'])

    # Evaluate on test data
    try:
        test_labels = model.predict(X_test)
        metrics.update({
            'proportion_outliers_test': float(np.mean(test_labels == -1)),
            'outlier_labels_test': list(map(int, test_labels)),
            'count_1_test': int(np.sum(test_labels == 1)),
            'count_minus1_test': int(np.sum(test_labels == -1))
        })
        logging.info("Proportion of outliers in test data: %.2f", metrics['proportion_outliers_test'])
        logging.info("Count of 1s (normal) in test data: %d", metrics['count_1_test'])
        logging.info("Count of -1s (outliers) in test data: %d", metrics['count_minus1_test'])
    except Exception as e:
        logging.error(f"Error during evaluation: {e}", exc_info=True)

    return {'model': model, 'metrics': metrics}
