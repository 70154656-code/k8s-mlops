from kfp import dsl, compiler
from kfp.dsl import Input, Output, Dataset, Model, Metrics

BASE = "python:3.11-slim"
PKGS = [
    "--default-timeout=600",
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


@dsl.pipeline(name="iris-classification-pipeline")
def iris_pipeline(n_estimators: int = 100):
    prep = load_and_preprocess()
    train = train_model(
        train_data=prep.outputs["train_data"], n_estimators=n_estimators
    )
    evaluate_model(
        test_data=prep.outputs["test_data"], model=train.outputs["model"]
    )


if __name__ == "__main__":
    compiler.Compiler().compile(iris_pipeline, "iris_pipeline.yaml")
    print("compiled to iris_pipeline.yaml")
PKGS = [
    "--default-timeout=600",
    "scikit-learn==1.5.2",
    "pandas==2.2.3",
]
