import os
import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
MODEL_NAME = os.getenv("MODEL_NAME", "iris-randomforest")
EXPERIMENT_NAME = os.getenv("EXPERIMENT_NAME", "iris-classification")

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
mlflow.set_experiment(EXPERIMENT_NAME)


def train_and_register():
    iris = load_iris(as_frame=True)
    X = iris.data
    y = iris.target

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Pipeline bundles preprocessing + tuned estimator together
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("model", RandomForestClassifier(
            n_estimators=200,
            max_depth=6,
            min_samples_split=2,
            min_samples_leaf=1,
            random_state=42,
        )),
    ])

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(pipeline, X_train, y_train, cv=cv, scoring="accuracy")

    with mlflow.start_run(run_name="rf-tuned-v2") as run:
        pipeline.fit(X_train, y_train)
        preds = pipeline.predict(X_test)

        test_acc = accuracy_score(y_test, preds)
        test_f1 = f1_score(y_test, preds, average="weighted")

        mlflow.log_params({
            "n_estimators": 200,
            "max_depth": 6,
            "min_samples_split": 2,
            "min_samples_leaf": 1,
            "scaler": "StandardScaler",
        })
        mlflow.log_metrics({
            "cv_mean_accuracy": float(cv_scores.mean()),
            "cv_std_accuracy": float(cv_scores.std()),
            "test_accuracy": float(test_acc),
            "test_f1_weighted": float(test_f1),
        })

        signature = infer_signature(X_test, preds)
        model_info = mlflow.sklearn.log_model(
            sk_model=pipeline,
            artifact_path="model",
            signature=signature,
            input_example=X_test.head(3),
            registered_model_name=MODEL_NAME,
        )

        print(f"Run ID: {run.info.run_id}")
        print(f"CV Accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
        print(f"Test Accuracy: {test_acc:.4f} | Test F1: {test_f1:.4f}")
        print(f"Registered as {MODEL_NAME} version: {model_info.registered_model_version}")


if __name__ == "__main__":
    train_and_register()
