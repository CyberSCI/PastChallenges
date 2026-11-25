locals {
  ssh_key_name = "beaverops"
}

data "forgejo_user" "admin" {
  login = var.forgejo_username
}

resource "tls_private_key" "admin" {
  algorithm = "ED25519"
}

resource "local_sensitive_file" "admin_private_key" {
  content         = tls_private_key.admin.private_key_openssh
  filename        = "/home/vpcadmin/.ssh/${local.ssh_key_name}"
  file_permission = "0600"
}

resource "local_file" "ssh_config" {
  content = templatefile("${path.module}/templates/ssh-config.tftpl", {
    hostname = var.forgejo_hostname
    keyname  = local.ssh_key_name
  })
  filename        = "/home/vpcadmin/.ssh/config"
  file_permission = "0600"
}

resource "forgejo_ssh_key" "beaverops_key" {
  user  = data.forgejo_user.admin.login
  key   = trimspace(tls_private_key.admin.public_key_openssh)
  title = "BeaverOps Key"
}

resource "forgejo_personal_access_token" "npm_package_token" {
  user = data.forgejo_user.admin.login
  name = "NPM Package Token"
  scopes = [
    "read:repository",
    "read:user",
    "write:package"
  ]
}

resource "forgejo_organization" "beaverworks" {
  name = var.org_name
}

resource "forgejo_team" "beaverworks_devs" {
  organization_id           = forgejo_organization.beaverworks.id
  name                      = "Devs"
  includes_all_repositories = true

  units_map = {
    "repo.code"    = "write"
    "repo.pulls"   = "write"
    "repo.actions" = "write"
  }
}

resource "forgejo_user" "challenger" {
  login    = "frank-beaverton"
  email    = "frank-beaverton@damoverflow.com"
  password = "1fb6da0397a123e2e622bc2eca5d24e9"
}

resource "forgejo_team_member" "challenger" {
  team_id = forgejo_team.beaverworks_devs.id
  user    = forgejo_user.challenger.login
}

resource "forgejo_repository" "dam_builder" {
  owner     = forgejo_organization.beaverworks.name
  name      = "dam-builder"
  private   = false
  template  = false
  auto_init = false
}

resource "forgejo_repository_action_secret" "owner_npm_token" {
  repository_id = forgejo_repository.dam_builder.id
  name          = "OWNER_TOKEN"
  data          = forgejo_personal_access_token.npm_package_token.token
}

resource "forgejo_repository_action_secret" "flag" {
  count         = length(var.flag)
  repository_id = forgejo_repository.dam_builder.id
  name          = "FLAG_${count.index + 1}"
  data          = var.flag[count.index]
}
