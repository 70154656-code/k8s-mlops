terraform {
  required_providers {
    kubernetes = {
      source = "hashicorp/kubernetes"
    }
    null = {
      source = "hashicorp/null"
    }
    minikube = {
      source = "scott-the-programmer/minikube"
    }
  }
}

provider "minikube" {
  kubernetes_version = var.kubernetes_version
}
