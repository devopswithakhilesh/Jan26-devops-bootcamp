# Lab 2 - Bake an AWS AMI

## Goal

Build a custom Amazon Machine Image (AMI). The AMI will have Ubuntu 22.04 + nginx + your custom HTML, all pre-installed.

When you launch an EC2 instance from this AMI, nginx is already running. No setup at boot time.

## Theory

### What is an AMI?

An **AMI** (Amazon Machine Image) is a snapshot of an EC2 instance's disk. Launch an EC2 instance "from an AMI" and you get a copy of that disk.

AWS provides AMIs (Amazon Linux, Ubuntu, Windows). You can also build your own.

### How Packer Builds an AMI

When you run `packer build` for AWS:

1. Packer makes an API call to AWS: "launch a temp EC2 instance from this base AMI".
2. AWS launches the instance.
3. Packer SSHes in.
4. Packer runs your provisioners (shell, ansible, etc.) over SSH.
5. Packer asks AWS: "stop this instance and create an AMI from its disk".
6. AWS creates the AMI.
7. Packer terminates the temp instance.

End result: a new AMI in your AWS account, ready to launch.

### What This Costs

- A `t3.micro` instance for ~5 minutes during the build (cheap, often free tier).
- A small EBS snapshot (the AMI itself) — about $0.05/GB-month while it exists.
- Delete old AMIs when you don't need them: `aws ec2 deregister-image --image-id ami-xxx`.

## Prerequisites

1. **AWS account** with EC2 + AMI permissions.
2. **AWS CLI** installed and configured: `aws configure` (access key, secret, region).
3. **Packer** installed.

Verify your AWS credentials work:
```bash
aws sts get-caller-identity
```

## Steps

### Step 1: Look at the Files

- `variables.pkr.hcl` — region, instance type, etc. (easy to change).
- `aws-nginx.pkr.hcl` — the actual build config.

### Step 2: Set Your AWS Region (Optional)

The default is `us-east-1`. To change, edit `variables.pkr.hcl` or pass `-var`:
```bash
packer build -var "region=ap-south-1" aws-nginx.pkr.hcl
```

### Step 3: Initialize

```bash
cd lab2
packer init .
```

This downloads the `amazon` plugin.

### Step 4: Validate

```bash
packer validate aws-nginx.pkr.hcl
```

### Step 5: Build

```bash
packer build aws-nginx.pkr.hcl
```

You will see:
1. Packer reads your AWS credentials.
2. It launches a temp t3.micro EC2 instance.
3. Connects via SSH (with a temp key Packer creates and destroys).
4. Runs `apt-get update && install nginx`.
5. Stops the instance and creates an AMI.
6. Terminates the temp instance.

At the end you'll see:
```
==> Builds finished. The artifacts of successful builds are:
--> amazon-ebs.ubuntu: AMIs were created:
us-east-1: ami-0abc123def456789
```

**Write down the AMI ID.**

### Step 6: Verify in AWS Console

Go to AWS Console → EC2 → AMIs (in your build region). You'll see your AMI named something like `nginx-baked-1716412345`.

### Step 7: Launch an Instance From Your AMI

```bash
aws ec2 run-instances \
  --image-id ami-0abc123def456789 \
  --instance-type t3.micro \
  --key-name your-key-pair \
  --security-group-ids sg-xxx
```

Or use the console. Open port 80 in the security group, then visit the instance's public IP. Nginx is already serving — zero setup at boot.

### Step 8: Clean Up

When done with the lab, delete the AMI and its snapshot to avoid charges:

```bash
# Find your AMI's snapshot
aws ec2 describe-images --image-ids ami-0abc123def456789 \
  --query 'Images[].BlockDeviceMappings[].Ebs.SnapshotId' --output text

# Deregister the AMI
aws ec2 deregister-image --image-id ami-0abc123def456789

# Delete the snapshot
aws ec2 delete-snapshot --snapshot-id snap-xxxxxxx
```

## What's Happening Behind the Scenes

The `source "amazon-ebs" "ubuntu"` block tells Packer:
- **`region`** — which AWS region to build in.
- **`source_ami_filter`** — find a base AMI matching a pattern (latest Ubuntu 22.04).
- **`instance_type`** — what size temp instance to use.
- **`ssh_username`** — the user to SSH in as (`ubuntu` for Ubuntu AMIs).
- **`ami_name`** — what to call the resulting AMI.

The `source_ami_filter` is powerful — you don't hardcode an AMI ID (which changes constantly). You describe what you want and Packer finds the latest.

## Try This

1. Add a tag to the AMI: `tags = { Project = "bootcamp", Built-by = "packer" }`.
2. Install `htop` and `git` in addition to `nginx`.
3. Bake the same image in TWO regions at once (hint: `ami_regions = ["us-east-1", "ap-south-1"]`).

## Common Mistakes

- **"NoCredentialProviders"** — Run `aws configure` first.
- **"InvalidAMIID.NotFound"** — Your base AMI filter found nothing in that region. Try a different region.
- **VPC/Subnet errors** — If your default VPC was deleted, you must pass `vpc_id` and `subnet_id` in the source block.
- **SSH timeout** — Security group may be blocking SSH. Packer creates one automatically by default — make sure your account allows that.

## Next

Go to `lab3/` — same idea, but Ansible does the provisioning. This is the real-world workflow.
