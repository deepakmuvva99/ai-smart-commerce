import lightgbm as lgb


def train_lightgbm(X_train, y_train):

    params = {
        "objective": "regression",
        "metric": "rmse",
        "learning_rate": 0.03,
        "num_leaves": 64,
        "feature_fraction": 0.8,
        "bagging_fraction": 0.8,
        "bagging_freq": 5
    }

    dataset = lgb.Dataset(X_train, label=y_train)

    model = lgb.train(
        params,
        dataset,
        num_boost_round=500
    )

    return model