# keep-sorted start block=yes newline_separated=yes
variable "flag" {
  type = list(string)
  default = [
    "CyberSci{found_a_vein}",
    "CyberSci{poisoning_the_well}",
    "CyberSci{who_let_the_packages_out}"
  ]
}

variable "forgejo_hostname" {
  type    = string
  default = "localhost"
}

variable "forgejo_port" {
  type    = number
  default = 3000
}

variable "forgejo_username" {
  type    = string
  default = "Chuck"
}

variable "org_name" {
  type    = string
  default = "BeaverWorks"
}

variable "ssh_public_key" {
  type    = string
  default = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBAJuhBdcjQTcYRFvZx2pP0Pf4P64rQ7sqlwFs7V39w7"
}
# keep-sorted end
