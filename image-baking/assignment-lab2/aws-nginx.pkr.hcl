// Lab 2: Bake an AWS AMI with nginx pre-installed.

packer {
  required_plugins {
    amazon = {
      source  = "github.com/hashicorp/amazon"
      version = "~> 1"
    }
  }
}

// Pick a unique-ish AMI name using a timestamp
locals {
  timestamp = formatdate("YYYYMMDD-hhmmss", timestamp())
}

// SOURCE: build a temp EC2 instance from latest Ubuntu 22.04, then snapshot it.
source "amazon-ebs" "ubuntu" {
  region        = var.region
  instance_type = var.instance_type
  ami_name      = "${var.ami_prefix}-${local.timestamp}"

  // Find the latest official Ubuntu 22.04 AMI
  source_ami_filter {
    filters = {
      name                = "ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"
      root-device-type    = "ebs"
      virtualization-type = "hvm"
    }
    most_recent = true
    owners      = ["879381241087"]   // Canonical's AWS account
  }

  ssh_username = "ubuntu"

  tags = {
    Name        = "${var.ami_prefix}-${local.timestamp}"
    Project     = "bootcamp"
    Built-by    = "packer"
    Base        = "ubuntu-22.04"
  }
}

// BUILD: provision the temp instance, then Packer auto-snapshots into an AMI.
build {
  name    = "nginx-ami"
  sources = ["source.amazon-ebs.ubuntu"]

  // Wait for cloud-init to finish before doing anything else
  provisioner "shell" {
    inline = [
      "echo 'Waiting for cloud-init to finish...'",
      "cloud-init status --wait"
    ]
  }

  // Install nginx
  provisioner "shell" {
    inline = [
      "sudo apt-get update -y",
      "sudo DEBIAN_FRONTEND=noninteractive apt-get install -y nginx",
      "sudo systemctl enable nginx",
      "sudo systemctl start nginx"
    ]
  }

  // Drop a custom landing page
  provisioner "shell" {
    inline = [
      "echo '<h1>Baked by Packer + AWS</h1>' | sudo tee /var/www/html/index.html"
    ]
  }

  // Final cleanup (smaller, safer image)
  provisioner "shell" {
    inline = [
      "sudo apt-get clean",
      "sudo rm -rf /var/lib/apt/lists/*",
      "sudo rm -rf /tmp/*"
    ]
  }
}
