import os
import pandas as pd
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
import mlflow
import mlflow.sklearn

# 1. Load & normalize MNIST (784 features: pixel_0 .. pixel_783)
mnist = fetch_openml("mnist_784", version=1, as_frame=False, parser="auto")
X = mnist.data.astype("float32") / 255.0
y = mnist.target.astype(int)

columns = [f"pixel_{i}" for i in range(X.shape[1])]
X_df = pd.DataFrame(X, columns=columns)

# Subset rakhein taake CPU par jaldi run ho jaye
X_sub = X_df.iloc[:10000]
y_sub = y[:10000]

X_train, X_test, y_train, y_test = train_test_split(
    X_sub, y_sub, test_size=0.2, random_state=42, stratify=y_sub
)

# 2. Train & evaluate
clf = LogisticRegression(max_iter=200, n_jobs=-1)
clf.fit(X_train, y_train)
preds = clf.predict(X_test)

acc = float(accuracy_score(y_test, preds))
f1 = float(f1_score(y_test, preds, average="macro"))

# 3. Log to a separate MLflow experiment & registered model name
mlflow.set_tracking_uri(os.environ["MLFLOW_TRACKING_URI"])
mlflow.set_experiment("mnist-classification")

with mlflow.start_run(run_name="mnist-logreg-sample"):
    mlflow.set_tag("dataset", "MNIST")
    mlflow.log_param("model_type", "LogisticRegression")
    mlflow.log_param("samples_used", len(X_sub))
    mlflow.log_metric("accuracy", acc)
    mlflow.log_metric("f1_macro", f1)
    mlflow.sklearn.log_model(
        sk_model=clf,
        artifact_path="model",
        registered_model_name="mnist-logreg-model",
    )

print(f"Done -> accuracy: {acc:.4f}, f1_macro: {f1:.4f}")
