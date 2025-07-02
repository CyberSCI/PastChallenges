terraform {
  required_version = "~> 1.9"
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "3.0.2"
    }
    random = {
      source  = "hashicorp/random"
      version = "3.7.1"
    }
  }
}

provider "docker" {
  host = "unix:///var/run/docker.sock"
}

provider "random" {
  # Configuration options
}

