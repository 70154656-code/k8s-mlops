terraform {
  required_providers {
    minikube = {
      source = "scott-the-programmer/minikube"
    }
  }
}

provider "minikube" {
  kubernetes_version = var.kubernetes_version
}
