pipeline {
    agent any

    parameters {
        string(name: 'MODEL_NAME', defaultValue: 'iris-randomforest', description: 'Registered MLflow model name')
        string(name: 'EXPERIMENT_NAME', defaultValue: 'iris-classification', description: 'MLflow experiment name')
        string(name: 'MLFLOW_TRACKING_URI', defaultValue: 'http://localhost:5000', description: 'MLflow tracking URI')
        string(name: 'K8S_NAMESPACE', defaultValue: 'mlops', description: 'Target Kubernetes namespace')
        string(name: 'K8S_DEPLOYMENT', defaultValue: 'mlflow-model-serving', description: 'Kubernetes serving deployment name')
        booleanParam(name: 'PROMOTE_TO_STAGING', defaultValue: true, description: 'Assign @staging to the newly registered version')
        booleanParam(name: 'PROMOTE_TO_PRODUCTION', defaultValue: false, description: 'Assign @production and restart Kubernetes serving')
    }

    environment {
        VENV_PYTHON = '/home/raja_ehtasham/k8s-mlops/.venv/bin/python'
    }

    stages {
        stage('Train & Register Model') {
            steps {
                sh """
                    MLFLOW_TRACKING_URI="${params.MLFLOW_TRACKING_URI}" \
                    MODEL_NAME="${params.MODEL_NAME}" \
                    EXPERIMENT_NAME="${params.EXPERIMENT_NAME}" \
                    "${VENV_PYTHON}" pipeline/train_improved_iris.py
                """
            }
        }

        stage('Promote Aliases & Rollout') {
            steps {
                sh """
                    MLFLOW_TRACKING_URI="${params.MLFLOW_TRACKING_URI}" \
                    MODEL_NAME="${params.MODEL_NAME}" \
                    K8S_NAMESPACE="${params.K8S_NAMESPACE}" \
                    K8S_DEPLOYMENT="${params.K8S_DEPLOYMENT}" \
                    PROMOTE_TO_STAGING="${params.PROMOTE_TO_STAGING}" \
                    PROMOTE_TO_PRODUCTION="${params.PROMOTE_TO_PRODUCTION}" \
                    "${VENV_PYTHON}" - << 'EOF'
import os
import subprocess
import mlflow
from mlflow.tracking import MlflowClient

uri = os.environ["MLFLOW_TRACKING_URI"]
model_name = os.environ["MODEL_NAME"]
ns = os.environ["K8S_NAMESPACE"]
deploy = os.environ["K8S_DEPLOYMENT"]
to_staging = os.environ["PROMOTE_TO_STAGING"].lower() == "true"
to_prod = os.environ["PROMOTE_TO_PRODUCTION"].lower() == "true"

mlflow.set_tracking_uri(uri)
client = MlflowClient(tracking_uri=uri)

versions = client.search_registered_models(filter_string=f"name = '{model_name}'")
latest_version = max(int(v.version) for v in versions[0].latest_versions) if versions else None
assert latest_version is not None, f"No versions found for {model_name}"

print(f"Latest registered version for {model_name}: {latest_version}")

if to_staging:
    client.set_registered_model_alias(name=model_name, alias="staging", version=str(latest_version))
    print(f"Set @staging -> v{latest_version}")

if to_prod:
    client.set_registered_model_alias(name=model_name, alias="production", version=str(latest_version))
    print(f"Set @production -> v{latest_version}")
    subprocess.run(["kubectl", "rollout", "restart", f"deployment/{deploy}", "-n", ns], check=True)
    subprocess.run(["kubectl", "rollout", "status", f"deployment/{deploy}", "-n", ns], check=True)
