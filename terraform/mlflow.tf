resource "null_resource" "mlflow_image" {
  triggers = {
    dockerfile = filemd5("${path.module}/../docker/Dockerfile")
    version    = var.mlflow_version
  }
  provisioner "local-exec" {
    command = <<-EOT
      docker build -t ${var.mlflow_image} --build-arg MLFLOW_VERSION=${var.mlflow_version} ${path.module}/../docker
      minikube image load ${var.mlflow_image} -p ${var.profile_name}
    EOT
  }
  depends_on = [minikube_cluster.mlops]
}

resource "kubernetes_persistent_volume_claim_v1" "mlflow" {
  metadata {
    name      = "mlflow-data"
    namespace = kubernetes_namespace_v1.mlops.metadata[0].name
  }
  spec {
    access_modes = ["ReadWriteOnce"]
    resources {
      requests = { storage = "2Gi" }
    }
  }
  wait_until_bound = false
}

resource "kubernetes_deployment_v1" "mlflow" {
  metadata {
    name      = "mlflow"
    namespace = kubernetes_namespace_v1.mlops.metadata[0].name
    labels    = { app = "mlflow" }
  }
  spec {
    replicas = 1
    selector {
      match_labels = { app = "mlflow" }
    }
    template {
      metadata {
        labels = { app = "mlflow" }
      }
      spec {
        security_context {
          fs_group = 10001
        }
        container {
          
  name              = "mlflow"
  image             = var.mlflow_image
  image_pull_policy = "IfNotPresent"

  command = [
  "mlflow",
  "server"
]

  args = [
  "--workers", "1",
  "--host", "0.0.0.0",
  "--port", "5000",
  "--backend-store-uri", "sqlite:////mlflow/data/mlflow.db",
  "--artifacts-destination", "/mlflow/data/artifacts",
  "--serve-artifacts"
]

  port {
    container_port = 5000
  }

  volume_mount {
    name       = "data"
    mount_path = "/mlflow/data"
  }

  resources {
  requests = {
    cpu    = "250m"
    memory = "1Gi"
  }

  limits = {
    cpu    = "1"
    memory = "1536Mi"
  }
}

  readiness_probe {
    http_get {
      path = "/health"
      port = 5000
    }

    initial_delay_seconds = 10
    period_seconds        = 10
  }
}
        
        volume {
          name = "data"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim_v1.mlflow.metadata[0].name
          }
        }
      }
    }
  }
  depends_on = [null_resource.mlflow_image]
}

resource "kubernetes_service_v1" "mlflow" {
  metadata {
    name      = "mlflow"
    namespace = kubernetes_namespace_v1.mlops.metadata[0].name
  }
  spec {
    selector = { app = "mlflow" }
    port {
      port        = 5000
      target_port = 5000
    }
  }
}

