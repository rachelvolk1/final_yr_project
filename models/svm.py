import joblib
import numpy as np
from sklearn.svm import OneClassSVM
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)


def train_one_class_svm(X_train, X_test=None, hyperparameters=None, save_path=None):
    """
    Train a One-Class SVM model.

    Args:
        X_train (pd.DataFrame or np.ndarray): Training features.
        X_test (pd.DataFrame or np.ndarray, optional): Optional test features for evaluation.
        hyperparameters (dict, optional): Hyperparameters for OneClassSVM (e.g., {'kernel': 'rbf', 'nu': 0.1}).
        save_path (str, optional): Path to save the trained model.

    Returns:
        dict: A dictionary containing the trained model and evaluation results.
    """
    hyperparameters = hyperparameters or {}
    logging.info("Training One-Class SVM with hyperparameters: %s", hyperparameters)

    # Initialize the One-Class SVM model with the provided hyperparameters
    model = OneClassSVM(**hyperparameters)

    # Train the model
    model.fit(X_train)
    logging.info("Model training completed.")

    # Save the model if a save path is provided
    if save_path:
        joblib.dump(model, save_path)
        logging.info("Model saved to %s", save_path)

    # Initialize metrics dictionary to hold evaluation results
    metrics = {}

    # Evaluate on test data if available
    if X_test is not None:
        try:
            y_pred = model.predict(X_test)  # Predict outliers (1 for inliers, -1 for outliers)
            metrics = {
                'message': 'One-Class SVM evaluation metrics are limited.',
                'outlier_labels': list(y_pred)  # Labels for outliers and inliers
            }
            logging.info("Evaluation metrics: %s", metrics)

        except Exception as e:
            metrics['message'] = f"Error during evaluation: {e}"
            logging.error(metrics['message'], exc_info=True)

    # Calculate proportion of outliers in the training set
    train_labels = model.predict(X_train)
    proportion_outliers_train = np.mean(train_labels == -1)
    metrics['proportion_outliers_train'] = proportion_outliers_train
    logging.info("Proportion of outliers in training data: %.2f", proportion_outliers_train)

    return {'model': model, 'metrics': metrics}
