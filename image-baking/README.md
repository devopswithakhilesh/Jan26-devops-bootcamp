# Image Baking with HashiCorp Packer

Build golden images for AWS, Docker, and more — using one tool: Packer.

## What is Packer?

**Packer** is a tool from HashiCorp that builds machine images.

Give it a config file. It will:

1. Spin up a temporary VM (or container).
2. Run your setup steps inside it (install packages, copy files).
3. Save the result as an **image** (AMI, Docker image, VHD, etc.).
4. Throw away the temporary VM.

The output is a ready-to-launch image. Boot it and your software is already installed.

## Why Bake Images?

The "old" way:
- Launch a fresh EC2 instance.
- SSH in. Install nginx. Copy files. Configure.
- Every new server repeats this. Takes minutes per boot.

The "baked" way:
- Bake an AMI once, with everything pre-installed.
- Launch new instances FROM the AMI. Boots in seconds, ready to serve.

Benefits:
- **Fast boots** - no setup at runtime.
- **Consistency** - every server is identical.
- **Immutable infrastructure** - don't patch live servers, bake a new AMI and replace them.
- **Rollback** - keep old AMIs. Roll back is one launch away.

## How Packer Compares to Ansible

| | Packer | Ansible |
|--|--------|---------|
| When does it run? | At **build time** (once) | At **deploy/runtime** (every time) |
| What does it produce? | An image | A configured running server |
| Use case | Bake the OS + base software | Push config to running servers |

They work together. A common pattern:
- **Packer** bakes the AMI (OS + nginx + base config).
- **Ansible** deploys app-specific config on top after boot.

Even better: Packer can **call Ansible** to do the baking. That's Lab 3.

## Lab Order

| Lab | What you build | Needs |
|-----|----------------|-------|
| lab1 | A custom Docker image | Docker installed locally |
| lab2 | A baked AWS AMI (Ubuntu + nginx) | AWS account + AWS CLI |
| lab3 | A baked AWS AMI using an Ansible playbook | AWS account + Ansible |

## Install Packer

**macOS:**
```bash
brew tap hashicorp/tap
brew install hashicorp/tap/packer
```

**Linux:**
```bash
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install packer -y
```

**Windows:**
```bash
choco install packer
```

Verify:
```bash
packer version
```

## Packer Config File Anatomy

Packer files use **HCL2** syntax (the same as Terraform). They end with `.pkr.hcl`.

A config has three main blocks:

```hcl
# 1. Plugins - which platforms Packer talks to
packer {
  required_plugins {
    amazon = {
      source  = "github.com/hashicorp/amazon"
      version = "~> 1"
    }
  }
}

# 2. Source - what kind of image to build, and where from
source "amazon-ebs" "ubuntu" {
  region        = "us-east-1"
  instance_type = "t3.micro"
  ami_name      = "my-baked-image-{{timestamp}}"
  # ... more settings
}

# 3. Build - what to do inside the temp VM
build {
  sources = ["source.amazon-ebs.ubuntu"]

  provisioner "shell" {
    inline = ["sudo apt-get update", "sudo apt-get install -y nginx"]
  }
}
```

## Common Packer Commands

```bash
packer init .                  # download plugins
packer fmt .                   # format HCL files
packer validate template.pkr.hcl   # check for errors
packer build template.pkr.hcl      # build the image
```

## Next

Go to `lab1/` for the quickest win — a Packer-built Docker image.
