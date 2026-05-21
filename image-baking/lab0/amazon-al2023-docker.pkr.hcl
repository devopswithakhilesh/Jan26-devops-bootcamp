# nginx-docker-al2023.pkr.hcl

packer {
  required_plugins {
    amazon = {
      version = ">= 1.2.0"
      source  = "github.com/hashicorp/amazon"
    }
  }
}

# Optional: make region/instance type easy to override
variable "region" {
  type    = string
  default = "ap-south-1"
}

variable "instance_type" {
  type    = string
  default = "t3.micro"
}

source "amazon-ebs" "al2023" {
  ami_name      = "al2023-nginx-docker-{{timestamp}}"
  instance_type = var.instance_type
  region        = var.region

  # Always pull the latest Amazon Linux 2023 x86_64 AMI
  source_ami_filter {
    filters = {
      name                = "al2023-ami-2023.*-x86_64"
      virtualization-type = "hvm"
      root-device-type    = "ebs"
    }
    most_recent = true
    owners      = ["amazon"]
  }

  ssh_username = "ec2-user"

  tags = {
    Name    = "al2023-nginx-docker"
    Builder = "packer"
    OS      = "Amazon Linux 2023"
  }
}

build {
  name    = "al2023-nginx-docker"
  sources = ["source.amazon-ebs.al2023"]

  provisioner "shell" {
    inline = [
      # Wait for cloud-init so dnf isn't locked on first boot
      "echo 'Waiting for cloud-init...'",
      "cloud-init status --wait || true",

      # Update base packages
      "sudo dnf update -y",

      # ---- Install nginx ----
      "sudo dnf install -y nginx",
      "sudo systemctl enable nginx",

      # ---- Install Docker ----
      "sudo dnf install -y docker",
      "sudo systemctl enable docker",

      # Let ec2-user run docker without sudo
      "sudo usermod -aG docker ec2-user",

      # ---- Install Docker Compose v2 plugin ----
      "sudo mkdir -p /usr/local/lib/docker/cli-plugins",
      "sudo curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 -o /usr/local/lib/docker/cli-plugins/docker-compose",
      "sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose",

      # ---- Verify ----
      "nginx -v",
      "docker --version",
      "docker compose version"
    ]
  }
}