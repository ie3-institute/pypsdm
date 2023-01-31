import numpy as np
from pandas import Series


def rmse_by_iloc(predictions: Series, targets: Series):
    """
    Calculates the RMSE between two series. Resets the index to calculate by their index (iloc)
    :param predictions: the predictions
    :param targets: the targets to aim for
    :return: the root mean squared error
    """
    if len(predictions) != len(targets):
        raise ValueError("Predictions and targets should have the same length!")
    return np.sqrt(
        (
            (predictions.reset_index(drop=True) - targets.reset_index(drop=True)) ** 2
        ).mean()
    )
