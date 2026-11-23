provider "kubernetes" {
  config_path    = "~/.kube/config"
  config_context = var.profile_name
}

resource "kubernetes_namespace_v1" "mlops" {
  metadata {
    name = "mlops"
  }
}
