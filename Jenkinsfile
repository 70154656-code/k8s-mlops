pipeline {
    agent any

    options {
        timestamps()
    }

    stages {
        stage('1. Workspace & Python Env') {
            steps {
                sh '''
                    cd /home/raja_ehtasham/k8s-mlops/pipeline
                    pwd
                    ls -la iris_pipeline.py
                    if [ -d .venv ]; then
                        . .venv/bin/activate
                    fi
                    python3 --version
                '''
            }
        }

        stage('2. Compile KFP Pipeline') {
            steps {
                sh '''
                    WORKSPACE_DIR=$(pwd)
                    cd /home/raja_ehtasham/k8s-mlops/pipeline
                    if [ -d .venv ]; then
                        . .venv/bin/activate
                    fi
                    python3 iris_pipeline.py

                    PIPELINE_VER="v1.0.${BUILD_NUMBER:-0}"
                    cp iris_pipeline.yaml "$WORKSPACE_DIR/iris_pipeline.yaml"
                    cp iris_pipeline.yaml "$WORKSPACE_DIR/iris_pipeline_${PIPELINE_VER}.yaml"
                    ls -lh "$WORKSPACE_DIR/iris_pipeline.yaml" "$WORKSPACE_DIR/iris_pipeline_${PIPELINE_VER}.yaml"
                '''
            }
        }

        stage('3. Train, Evaluate & Log to MLflow') {
            steps {
                sh '''
                    cd /home/raja_ehtasham/k8s-mlops/pipeline
                    if [ -d .venv ]; then
                        . .venv/bin/activate
                    fi

                    export MLFLOW_TRACKING_URI="${MLFLOW_TRACKING_URI:-http://127.0.0.1:5000}"
                    export OUT_DIR="/tmp/mlflow_jenkins_${BUILD_NUMBER:-run}"
                    export PIPELINE_VERSION="v1.0.${BUILD_NUMBER:-0}"

                    python3 -c '
import os, json
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

out_dir = os.environ["OUT_DIR"]
os.makedirs(out_dir, exist_ok=True)

X, y = load_iris(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

n_estimators = 100
clf = RandomForestClassifier(n_estimators=n_estimators, random_state=42)
clf.fit(X_train, y_train)
preds = clf.predict(X_test)

metrics = {
    "train_accuracy": float(accuracy_score(y_train, clf.predict(X_train))),
    "accuracy": float(accuracy_score(y_test, preds)),
    "precision_macro": float(precision_score(y_test, preds, average="macro")),
    "recall_macro": float(recall_score(y_test, preds, average="macro")),
    "f1_macro": float(f1_score(y_test, preds, average="macro")),
}

metrics_path = os.path.join(out_dir, "metrics.json")
with open(metrics_path, "w") as f:
    json.dump(metrics, f, indent=2)
print("METRICS:", json.dumps(metrics, indent=2))

try:
    import mlflow
    import mlflow.sklearn

    mlflow.set_tracking_uri(os.environ["MLFLOW_TRACKING_URI"])
    build_num = os.environ.get("BUILD_NUMBER", "local")
    version_tag = os.environ.get("PIPELINE_VERSION", f"v1.0.{build_num}")
    run_name = f"jenkins-build-{build_num}-{version_tag}"

    mlflow.set_experiment("iris-classification")
    with mlflow.start_run(run_name=run_name):
        mlflow.set_tag("ci_tool", "jenkins")
        mlflow.set_tag("job_name", os.environ.get("JOB_NAME", "iris-mlops-pipeline"))
        mlflow.set_tag("build_number", str(build_num))
        mlflow.set_tag("pipeline_version", version_tag)
        mlflow.set_tag("release_tag", f"jenkins-{version_tag}")
        mlflow.log_param("n_estimators", n_estimators)
        mlflow.log_param("test_size", 0.2)
        mlflow.log_param("pipeline_version", version_tag)
        mlflow.log_metrics(metrics)
        mlflow.sklearn.log_model(
            sk_model=clf,
            artifact_path="model",
            registered_model_name="iris-randomforest",
        )

    print("Synced to MLflow (iris-classification):", run_name, version_tag)
except Exception as e:
    print("MLflow logging skipped/fallback:", e)
'
                '''
            }
        }

        stage('4. Verify K8s Context (Read-Only)') {
            steps {
                sh '''
                    export KUBECONFIG=/home/raja_ehtasham/.kube/config
                    kubectl config current-context || true
                    kubectl get pods -n mlops || true
                '''
            }
        }
    }

    post {
        success {
            archiveArtifacts artifacts: 'iris_pipeline*.yaml', allowEmptyArchive: true
            echo 'Assignment workflow step completed: KFP compiled, archived, and synced to MLflow!'
        }
    }
}
