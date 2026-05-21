# al2023-nginx-docker.pkr.hcl

packer {
  required_plugins {
    amazon = {
      version = ">= 1.2.0"
      source  = "github.com/hashicorp/amazon"
    }
  }
}

# ---------- Variables ----------

variable "region" {
  type    = string
  default = "ap-south-1"
}

variable "instance_type" {
  type    = string
  default = "t3.micro"
}

variable "kms_key_id" {
  type        = string
  description = "KMS key ARN (or ID/alias) used to encrypt the AMI snapshots"
  # e.g. "arn:aws:kms:ap-south-1:123456789012:key/abcd1234-..."
}

variable "share_account_ids" {
  type        = list(string)
  default     = []
  description = "AWS account IDs to share the encrypted AMI + snapshots with"
}

# ---------- Source ----------

source "amazon-ebs" "al2023" {
  ami_name      = "al2023-nginx-docker-{{timestamp}}"
  instance_type = var.instance_type
  region        = var.region

  # --- Latest Amazon Linux 2023 x86_64 base AMI ---
  source_ami_filter {
    filters = {
      name                = "al2023-ami-2023.*-x86_64"
      virtualization-type = "hvm"
      root-device-type    = "ebs"
    }
    most_recent = true
    owners      = ["137112412989"] # Amazon
  }

  ssh_username = "ec2-user"

  # --- Encryption ---
  # Encrypt the resulting AMI's snapshots with your KMS key.
  encrypt_boot = true
  kms_key_id   = var.kms_key_id

  # --- Sharing ---
  # Grant launch permission on the AMI...
  ami_users = var.share_account_ids
  # ...and share the underlying encrypted snapshots...
  snapshot_users = var.share_account_ids
  # NOTE: the target accounts ALSO need kms:Decrypt etc. on var.kms_key_id.
  # That is granted on the KMS key policy, not here (see notes below).

  tags = {
    Name      = "al2023-nginx-docker"
    Builder   = "packer"
    OS        = "Amazon Linux 2023"
    Encrypted = "true"
  }
}

# ---------- Build ----------

build {
  name    = "al2023-nginx-docker"
  sources = ["source.amazon-ebs.al2023"]

  provisioner "shell" {
    inline = [
      "echo 'Waiting for cloud-init...'",
      "cloud-init status --wait || true",

      "sudo dnf update -y",

      # ---- nginx ----
      "sudo dnf install -y nginx",
      "sudo systemctl enable nginx",

      # ---- Docker ----
      "sudo dnf install -y docker",
      "sudo systemctl enable docker",
      "sudo usermod -aG docker ec2-user",

      # ---- Docker Compose v2 plugin ----
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