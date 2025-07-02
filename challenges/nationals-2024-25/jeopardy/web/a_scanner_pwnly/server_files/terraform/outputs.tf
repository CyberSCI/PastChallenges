output "main_db_password" {
  value = local.main_db_password
}

output "internal_db_password" {
  value = local.internal_db_password
}

output "db_url" {
  value = local.main_db_url
}

output "object_storage_user" {
  value = var.object_storage_user
}

output "object_storage_password" {
  value = local.object_storage_password
}

output "object_storage_endpoint" {
  value = local.object_storage_endpoint
}
