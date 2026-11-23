resource "kubernetes_config_map_v1" "nginx" {
  count = var.serving_replicas > 0 ? 1 : 0
  metadata {
    name      = "nginx-lb-conf"
    namespace = kubernetes_namespace_v1.mlops.metadata[0].name
  }
  data = {
    "nginx.conf" = <<-EOT
      events {}
      http {
        upstream model_pods {
          server iris-serving-headless.mlops.svc.cluster.local:5001;
        }
        server {
          listen 80;
          location / {
            proxy_pass http://model_pods;
            add_header X-Served-By $upstream_addr always;
          }
        }
      }
    EOT
  }
}

resource "kubernetes_deployment_v1" "nginx" {
  count = var.serving_replicas > 0 ? 1 : 0
  metadata {
    name      = "nginx-lb"
    namespace = kubernetes_namespace_v1.mlops.metadata[0].name
    labels    = { app = "nginx-lb" }
  }
  spec {
    replicas = 1
    selector {
      match_labels = { app = "nginx-lb" }
    }
    template {
      metadata {
        labels = { app = "nginx-lb" }
      }
      spec {
        container {
          name  = "nginx"
          image = "nginx:1.27-alpine"
          port {
            container_port = 80
          }
          volume_mount {
            name       = "conf"
            mount_path = "/etc/nginx/nginx.conf"
            sub_path   = "nginx.conf"
          }
        }
        volume {
          name = "conf"
          config_map {
            name = kubernetes_config_map_v1.nginx[0].metadata[0].name
          }
        }
      }
    }
  }
  depends_on = [kubernetes_deployment_v1.serving, kubernetes_service_v1.serving_headless]
}

resource "kubernetes_service_v1" "nginx" {
  count = var.serving_replicas > 0 ? 1 : 0
  metadata {
    name      = "nginx-lb"
    namespace = kubernetes_namespace_v1.mlops.metadata[0].name
  }
  spec {
    type     = "NodePort"
    selector = { app = "nginx-lb" }
    port {
      port        = 80
      target_port = 80
    }
  }
}
