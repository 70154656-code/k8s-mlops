variable "profile_name" {
  type    = string
  default = "mlops-cluster"
}
variable "mlflow_version" {
  type = string
}
variable "mlflow_image" {
  type    = string
  default = "mlops/mlflow-iris:1"
}
variable "model_name" {
  type    = string
  default = "iris-randomforest"
}
variable "serving_replicas" {
  type    = number
  default = 0
}
