terraform {
  required_providers {
    forgejo = {
      source  = "svalabs/forgejo"
      version = "1.6.1"
    }
    local = {
      source  = "hashicorp/local"
      version = "2.9.1"
    }
    tls = {
      source = "hashicorp/tls"
    }
  }
}

provider "forgejo" {
  host = "http://${var.forgejo_hostname}:${var.forgejo_port}"
}
