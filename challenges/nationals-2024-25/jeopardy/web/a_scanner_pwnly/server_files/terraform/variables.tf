variable "frontend_image" {
  type    = string
  default = "vvbs-frontend"
}

variable "backend_image" {
  type    = string
  default = "vvbs-backend"
}

variable "database_image" {
  type    = string
  default = "postgres:14"
}

variable "database_user" {
  type    = string
  default = "postgres"
}

variable "object_storage_user" {
  type    = string
  default = "vvbs-admin"
}

variable "hostname" {
  type    = string
  default = "badgescan.valverde.vote"
}

variable "main_db_name" {
  type    = string
  default = "badgescan"
}

variable "internal_db_name" {
  type    = string
  default = "badgescan-internal"
}

variable "backend_port" {
  type    = number
  default = 8000
}

variable "flag_1" {
  type    = string
  default = "FLAG{democracy_in_a_pickle_f2a687abaf0305c4}"
}

variable "frontend_port" {
  type    = number
  default = 1337
}

variable "main_db_port" {
  type    = number
  default = 5432
}

variable "internal_db_port" {
  type    = number
  default = 5433
}
