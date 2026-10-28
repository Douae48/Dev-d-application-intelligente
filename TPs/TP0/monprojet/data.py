
"""Chargement et découpage des données."""

import pandas as pd
from sklearn.model_selection import train_test_split

from monprojet import config


def load_data(path=None) -> pd.DataFrame:
    """Lit le CSV, vérifie la cible et retire les cibles manquantes."""

    if path is None:
        path = config.DATA_PATH

    df = pd.read_csv(path)

    if config.TARGET not in df.columns:
        raise ValueError(
            f"La colonne cible '{config.TARGET}' est absente du fichier CSV."
        )

    df = df.dropna(subset=[config.TARGET])

    return df


def feature_columns(df: pd.DataFrame) -> list:
    """Les colonnes d'entrée."""
    if config.FEATURES is not None:
        return list(config.FEATURES)

    excluded = {config.TARGET, config.TIME_COLUMN}
    return [c for c in df.columns if c not in excluded]


def split(df: pd.DataFrame):
    """Renvoie X_train, X_test, y_train, y_test."""

    if config.SPLIT == "random":

        X = df[feature_columns(df)]
        y = df[config.TARGET]

        stratify = y if config.TASK == "classification" else None

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=config.TEST_SIZE,
            random_state=config.SEED,
            stratify=stratify
        )

    elif config.SPLIT == "chronologique":

        if config.TIME_COLUMN is None:
            raise ValueError("TIME_COLUMN doit être définie.")

        df = df.copy()
        df[config.TIME_COLUMN] = pd.to_datetime(df[config.TIME_COLUMN])
        df = df.sort_values(by=config.TIME_COLUMN)

        X = df[feature_columns(df)]
        y = df[config.TARGET]

        n_test = int(len(df) * config.TEST_SIZE)
        n_train = len(df) - n_test

        X_train = X.iloc[:n_train]
        X_test = X.iloc[n_train:]
        y_train = y.iloc[:n_train]
        y_test = y.iloc[n_train:]

    else:
        raise ValueError(f"Type de découpage inconnu : {config.SPLIT}")

    return X_train, X_test, y_train, y_test
