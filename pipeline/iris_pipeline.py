import os
from kfp import compiler, dsl
from kfp.dsl import Dataset, Input, Metrics, Model, Output

BASE = "python:3.11-slim"
PKGS = [
    "--default-timeout=600",
    "scikit-learn==1.5.2",
    "pandas==2.2.3",
]
MLFLOW_PKGS = [
    "--default-timeout=600",
    "mlflow==2.17.2",
    "sqlalchemy==2.0.36",
    "scikit-learn==1.5.2",
    "pandas==2.2.3",
]


@dsl.component(base_image=BASE, packages_to_install=PKGS)
def load_and_preprocess(train_data: Output[Dataset], test_data: Output[Dataset]):
    """Component A: load Iris, clean it, split into train/test."""
    from sklearn.datasets import load_iris
    from sklearn.model_selection import train_test_split

    iris = load_iris(as_frame=True)
    df = iris.frame.drop_duplicates().dropna()
    train, test = train_test_split(
        df, test_size=0.2, random_state=42, stratify=df["target"]
    )
    train.to_csv(train_data.path, index=False)
    test.to_csv(test_data.path, index=False)
    print(f"rows: train={len(train)} test={len(test)}")


@dsl.component(base_image=BASE, packages_to_install=PKGS)
def train_model(
    train_data: Input[Dataset],
    model: Output[Model],
    metrics: Output[Metrics],
    n_estimators: int = 100,
):
    """Component B: train a scaler + random forest, save the model file."""
    import joblib
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    df = pd.read_csv(train_data.path)
    X, y = df.drop(columns=["target"]), df["target"]
    clf = make_pipeline(
        StandardScaler(),
        RandomForestClassifier(n_estimators=n_estimators, random_state=42),
    )
    clf.fit(X, y)
    metrics.log_metric("train_accuracy", float(clf.score(X, y)))
    joblib.dump(clf, model.path)


@dsl.component(base_image=BASE, packages_to_install=PKGS)
def evaluate_model(
    test_data: Input[Dataset],
    model: Input[Model],
    metrics: Output[Metrics],
):
    """Component C: evaluate the trained model on the held-out test set."""
    import joblib
    import pandas as pd
    from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

    df = pd.read_csv(test_data.path)
    X, y = df.drop(columns=["target"]), df["target"]
    clf = joblib.load(model.path)
    pred = clf.predict(X)
    metrics.log_metric("accuracy", float(accuracy_score(y, pred)))
    metrics.log_metric("precision_macro", float(precision_score(y, pred, average="macro")))
    metrics.log_metric("recall_macro", float(recall_score(y, pred, average="macro")))
    metrics.log_metric("f1_macro", float(f1_score(y, pred, average="macro")))


@dsl.component(base_image=BASE, packages_to_install=MLFLOW_PKGS)
def register_model_in_mlflow(
    train_data: Input[Dataset],
    model: Input[Model],
    tracking_uri: str = "http://mlflow.mlops.svc.cluster.local:5000",
    registered_model_name: str = "iris-randomforest",
    alias: str = "production",
):
    """Component D: log model & metrics to MLflow and assign @production alias."""
    import joblib
    import mlflow
    import mlflow.sklearn
    import pandas as pd
    from mlflow.tracking import MlflowClient

    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment("iris-classification")

    clf = joblib.load(model.path)
    sample_df = pd.read_csv(train_data.path).drop(columns=["target"]).head(5)

    with mlflow.start_run(run_name="iris-rf-pipeline") as run:
        mlflow.log_param("model_type", "StandardScaler+RandomForestClassifier")
        model_info = mlflow.sklearn.log_model(
            sk_model=clf,
            artifact_path="model",
            registered_model_name=registered_model_name,
            input_example=sample_df,
        )
        client = MlflowClient(tracking_uri=tracking_uri)
        version = model_info.registered_model_version
        client.set_registered_model_alias(
            name=registered_model_name,
            alias=alias,
            version=version,
        )
        print(
            f"Logged run={run.info.run_id}, registered {registered_model_name} "
            f"v{version} with alias @{alias}"
        )


@dsl.pipeline(name="iris-classification-pipeline")
def iris_pipeline(
    n_estimators: int = 100,
    mlflow_tracking_uri: str = "http://mlflow.mlops.svc.cluster.local:5000",
    registered_model_name: str = "iris-randomforest",
    alias: str = "production",
):
    prep = load_and_preprocess()
    train = train_model(
        train_data=prep.outputs["train_data"], n_estimators=n_estimators
    )
    evaluate_model(
        test_data=prep.outputs["test_data"], model=train.outputs["model"]
    )
    register_model_in_mlflow(
        train_data=prep.outputs["train_data"],
        model=train.outputs["model"],
        tracking_uri=mlflow_tracking_uri,
        registered_model_name=registered_model_name,
        alias=alias,
    )


if __name__ == "__main__":
    compiler.Compiler().compile(iris_pipeline, "iris_pipeline.yaml")
    print("compiled to iris_pipeline.yaml")
