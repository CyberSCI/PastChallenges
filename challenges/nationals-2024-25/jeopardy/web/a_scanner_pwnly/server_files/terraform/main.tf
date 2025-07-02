locals {
  project_root            = "${path.module}/.."
  api_hostname            = "api.${var.hostname}"
  object_storage_hostname = "object-storage.${var.hostname}"
  db_hostname             = "db.${var.hostname}"
  internal_db_hostname    = "internal-db.${var.hostname}"
}

resource "docker_image" "backend" {
  name = var.backend_image

  build {
    context = "${local.project_root}/backend"
    tag     = ["${var.backend_image}:latest"]
    label = {
      author : "val-verde"
    }
  }
  triggers = {
    dir_sha1 = sha1(join("", [for f in fileset(path.module, "../backend/**") : filesha1(f)]))
  }
}

resource "docker_image" "frontend" {
  name = var.frontend_image
  build {
    context = "${local.project_root}/frontend"
    tag     = ["${var.frontend_image}:latest"]
    label = {
      author : "val-verde"
    }
    suppress_output = false

    build_arg = {
      "NEXT_PUBLIC_API_URL" : "http://${docker_container.backend.hostname}:8000",
    }
  }
  triggers = {
    dir_sha1 = sha1(join("", [for f in fileset(path.module, "../frontend/**") : filesha1(f)]))
  }
}

data "docker_registry_image" "postgres" {
  name = var.database_image
}

resource "docker_image" "postgres" {
  name          = data.docker_registry_image.postgres.name
  pull_triggers = [data.docker_registry_image.postgres.sha256_digest]
}

data "docker_registry_image" "minio" {
  name = "quay.io/minio/minio"
}

resource "docker_image" "minio" {
  name          = data.docker_registry_image.minio.name
  pull_triggers = [data.docker_registry_image.minio.sha256_digest]
}

data "docker_registry_image" "minio_cli" {
  name = "quay.io/minio/mc"
}

resource "docker_image" "minio_cli" {
  name          = data.docker_registry_image.minio_cli.name
  pull_triggers = [data.docker_registry_image.minio_cli.sha256_digest]
}

resource "docker_network" "vvbs_network" {
  name = "vvbs-network"
}

resource "random_string" "main_db" {
  length  = 32
  special = false
}

resource "random_string" "internal_db" {
  length  = 32
  special = false
}

resource "random_string" "object_storage" {
  length  = 32
  special = false
}

locals {
  main_db_password        = random_string.main_db.result
  internal_db_password    = random_string.internal_db.result
  object_storage_password = random_string.object_storage.result
  main_db_url = format(
    "postgresql+asyncpg://%[1]s:%[2]s@%[3]s:%[4]s/%[5]s",
    var.database_user,
    local.main_db_password,
    docker_container.main_db.hostname,
    var.main_db_port,
    var.main_db_name
  )
}

resource "docker_volume" "main_db_data" {
  name = "vvbs-main-db-data"
}

resource "docker_volume" "internal_db_data" {
  name = "vvbs-internal-db-data"
}

resource "docker_volume" "object_storage_data" {
  name = "vvbs-object-storage-data"
}

resource "docker_container" "main_db" {
  image    = docker_image.postgres.image_id
  name     = "vvbs-main-db"
  must_run = true
  restart  = "unless-stopped"

  hostname = local.db_hostname

  ports {
    internal = 5432
    external = var.main_db_port
  }

  env = [
    "POSTGRES_USER=${var.database_user}",
    "POSTGRES_DB=${var.main_db_name}",
    "POSTGRES_PASSWORD=${local.main_db_password}"
  ]

  network_mode = "bridge"

  networks_advanced {
    name = docker_network.vvbs_network.id
  }

  healthcheck {
    test         = ["CMD-SHELL", "pg_isready -U ${var.database_user} -d ${var.main_db_name}"]
    interval     = "5s"
    retries      = "3"
    start_period = "5s"
    timeout      = "5s"
  }

  volumes {
    volume_name    = docker_volume.main_db_data.name
    container_path = "/var/lib/postgresql/data"
  }
}

resource "docker_container" "internal_db" {
  image    = docker_image.postgres.image_id
  name     = "vvbs-internal-db"
  must_run = true
  restart  = "unless-stopped"

  hostname = local.internal_db_hostname

  env = [
    "POSTGRES_USER=${var.database_user}",
    "POSTGRES_DB=${var.internal_db_name}",
    "POSTGRES_PASSWORD=${local.internal_db_password}"
  ]

  network_mode = "bridge"

  networks_advanced {
    name = docker_network.vvbs_network.id
  }

  volumes {
    volume_name    = docker_volume.internal_db_data.name
    container_path = "/var/lib/postgresql/data"
  }

  mounts {
    target = "/docker-entrypoint-initdb.d"
    type   = "bind"
    source = "${abspath(local.project_root)}/internal_db"
  }
}

resource "docker_container" "object_storage" {
  image    = docker_image.minio.image_id
  name     = "vvbs-object-storage"
  must_run = true
  restart  = "unless-stopped"

  hostname = local.object_storage_hostname

  ports {
    internal = 9000
    external = 9000
  }

  ports {
    internal = 9001
    external = 9001
  }

  env = [
    "MINIO_ROOT_USER=${var.object_storage_user}",
    "MINIO_ROOT_PASSWORD=${local.object_storage_password}"
  ]

  command = ["server", "/data", "--console-address", ":9001"]

  network_mode = "bridge"

  networks_advanced {
    name = docker_network.vvbs_network.id
  }

  volumes {
    volume_name    = docker_volume.object_storage_data.name
    container_path = "/data"
  }

  healthcheck {
    test         = ["CMD", "curl", "http://object-storage.badgescan.vv:9001"]
    interval     = "5s"
    retries      = "3"
    start_period = "5s"
    timeout      = "5s"
  }
}

resource "docker_container" "object_storage_init" {
  image = docker_image.minio_cli.image_id
  name  = "vvbs-object-storage-init"
  tty   = true

  entrypoint = ["/scripts/init_storage.sh"]

  env = [
    "ACCESS_KEY=${var.object_storage_user}",
    "SECRET_KEY=${local.object_storage_password}"
  ]

  network_mode = "bridge"

  networks_advanced {
    name = docker_network.vvbs_network.id
  }

  volumes {
    host_path      = "${abspath(local.project_root)}/scripts"
    container_path = "/scripts"
  }

  depends_on = [docker_container.object_storage]
}

locals {
  object_storage_endpoint = "${docker_container.object_storage.hostname}:9000"
}

resource "docker_container" "backend" {
  image    = docker_image.backend.image_id
  name     = "vvbs-backend"
  must_run = true
  restart  = "unless-stopped"

  hostname = local.api_hostname

  ports {
    internal = 8000
    external = var.backend_port
  }

  env = [
    "DATABASE_URL=${local.main_db_url}",
    "MINIO_ENDPOINT=${local.object_storage_endpoint}",
    "MINIO_ACCESS_KEY=${var.object_storage_user}",
    "MINIO_SECRET_KEY=${local.object_storage_password}",
    "FLAG=${var.flag_1}"
  ]

  network_mode = "bridge"

  networks_advanced {
    name = docker_network.vvbs_network.id
  }

  depends_on = [docker_container.object_storage_init]
}


resource "docker_container" "frontend" {
  image    = docker_image.frontend.image_id
  name     = "vvbs-frontend"
  must_run = true
  restart  = "unless-stopped"

  hostname = var.hostname

  ports {
    internal = 3000
    external = var.frontend_port
  }

  env = [
    "NEXT_PUBLIC_API_URL=http://${docker_container.backend.hostname}:8000",
  ]

  network_mode = "bridge"

  networks_advanced {
    name = docker_network.vvbs_network.id
  }
}
