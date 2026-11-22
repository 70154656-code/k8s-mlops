variable "kubernetes_version" {
  type    = string
  default = "v1.30.0"
}

variable "cluster_name" {
  type    = string
  default = "mlops-cluster"
}

variable "cpus" {
  type    = number
  default = 3
}

variable "memory" {
  type    = string
  default = "3500mb"
}
