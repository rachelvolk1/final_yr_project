import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import logging


def train_random_forest(X_train, y_train, X_test=None, y_test=None, hyperparameters=None, save_path=None):
    """
    Train a Random Forest model.

    Args:
        X_train (pd.DataFrame): Training features.
        y_train (pd.Series): Training labels.
        X_test (pd.DataFrame): Optional test features.
        y_test (pd.Series): Optional test labels.
        hyperparameters (dict): Parameters for RandomForestClassifier.
        save_path (str): Path to save the trained model.

    Returns:
        dict: A dictionary containing evaluation metrics.
    """
    hyperparameters = hyperparameters or {}
    logging.info("Training Random Forest with hyperparameters: %s", hyperparameters)

    model = RandomForestClassifier(**hyperparameters)

    # Train the model
    model.fit(X_train, y_train)

    # Save the model
    if save_path:
        joblib.dump(model, save_path)
        logging.info("Model saved to %s", save_path)

    # Evaluate if test data is provided
    metrics = {}
    if X_test is not None and y_test is not None:
        y_pred = model.predict(X_test)
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, average='weighted'),
            'recall': recall_score(y_test, y_pred, average='weighted'),
            'f1_score': f1_score(y_test, y_pred, average='weighted')
        }
        logging.info("Evaluation metrics: %s", metrics)

    return {'model': model, 'metrics': metrics}
