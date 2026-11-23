resource "kubernetes_deployment_v1" "serving" {
  metadata {
    name      = "iris-serving"
    namespace = kubernetes_namespace_v1.mlops.metadata[0].name
    labels    = { app = "iris-serving" }
  }
  spec {
    replicas = var.serving_replicas
    selector {
      match_labels = { app = "iris-serving" }
    }
    template {
      metadata {
        labels = { app = "iris-serving" }
      }
      spec {
        container {
          name              = "model"
          image             = var.mlflow_image
          image_pull_policy = "IfNotPresent"
          command           = ["mlflow", "models", "serve"]
          args = [
            "-m", "models:/${var.model_name}@production",
            "--host", "0.0.0.0", "--port", "5001", "--env-manager", "local",
          ]
          env {
            name  = "MLFLOW_TRACKING_URI"
            value = "http://mlflow.mlops.svc.cluster.local:5000"
          }
          port {
            container_port = 5001
          }
          resources {
            requests = {
              cpu    = "250m"
              memory = "512Mi"
            }

            limits = {
              cpu    = "1"
              memory = "1Gi"
            }
          }
          readiness_probe {
            http_get {
              path = "/ping"
              port = 5001
            }
            initial_delay_seconds = 40
            period_seconds        = 10
          }
        }
      }
    }
  }
  depends_on = [kubernetes_service_v1.mlflow]
}

resource "kubernetes_service_v1" "serving_headless" {
  metadata {
    name      = "iris-serving-headless"
    namespace = kubernetes_namespace_v1.mlops.metadata[0].name
  }
  spec {
    cluster_ip = "None"
    selector   = { app = "iris-serving" }
    port {
      port        = 5001
      target_port = 5001
    }
  }
}
