// Lab 3: Bake an AWS AMI. Provisioning is delegated to Ansible.

packer {
  required_plugins {
    amazon = {
      source  = "github.com/hashicorp/amazon"
      version = "~> 1"
    }
    ansible = {
      source  = "github.com/hashicorp/ansible"
      version = "~> 1"
    }
  }
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "instance_type" {
  type    = string
  default = "t3.micro"
}

locals {
  timestamp = formatdate("YYYYMMDD-hhmmss", timestamp())
}

source "amazon-ebs" "ubuntu" {
  region        = var.region
  instance_type = var.instance_type
  ami_name      = "nginx-ansible-${local.timestamp}"

  source_ami_filter {
    filters = {
      name                = "ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"
      root-device-type    = "ebs"
      virtualization-type = "hvm"
    }
    most_recent = true
    owners      = ["099720109477"]
  }

  ssh_username = "ubuntu"

  tags = {
    Name         = "nginx-ansible-${local.timestamp}"
    Project      = "bootcamp"
    Built-by     = "packer+ansible"
    Base         = "ubuntu-22.04"
  }
}

build {
  name    = "nginx-ami-via-ansible"
  sources = ["source.amazon-ebs.ubuntu"]

  // Wait for cloud-init so apt isn't fighting another process
  provisioner "shell" {
    inline = [
      "echo 'Waiting for cloud-init...'",
      "cloud-init status --wait"
    ]
  }

  // Hand over to Ansible.
  // Packer creates a one-host inventory and runs ansible-playbook over SSH.
  provisioner "ansible" {
    playbook_file = "./playbooks/nginx.yml"
    user          = "ubuntu"

    // Pass any extra args to ansible-playbook
    extra_arguments = [
      "--scp-extra-args", "'-O'"   // works around scp issues on newer OpenSSH
    ]
  }
}
