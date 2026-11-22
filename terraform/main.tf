resource "minikube_cluster" "mlops" {
  driver       = "docker"
  cluster_name = var.cluster_name
  cpus         = var.cpus
  memory       = var.memory
  addons       = ["default-storageclass", "storage-provisioner"]
}
