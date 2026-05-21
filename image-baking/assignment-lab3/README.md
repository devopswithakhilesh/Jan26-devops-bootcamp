# Lab 3 - Bake an AMI Using Ansible

## Goal

Same outcome as Lab 2 (a nginx AMI) — but instead of shell scripts, **Packer uses Ansible** to provision the temp instance. The Ansible playbook is the same kind you wrote in `ansible-labs/lab2`.

This is how real teams do it. Configuration is in version-controlled Ansible playbooks, and Packer just wraps the build.

## Theory

### Why Combine Packer + Ansible?

| Tool | Job |
|------|-----|
| **Packer** | Spin up temp instance → snapshot it as an image |
| **Ansible** | The "what to install / configure" logic |

Packer handles the lifecycle (launch, build, snapshot, terminate). Ansible handles the configuration. Each tool does what it's best at.

The same Ansible playbook can:
- Bake an AMI (via Packer) — once.
- Update a fleet of running servers — many times.

One source of truth.

### The `ansible` Provisioner

Packer has a built-in provisioner called `ansible` (technically `ansible-local` and `ansible`). The remote `ansible` runs Ansible **from your laptop** AGAINST the temp instance over SSH — exactly like a normal Ansible run.

```hcl
provisioner "ansible" {
  playbook_file = "./playbooks/nginx.yml"
}
```

That's the whole integration. Packer handles SSH, gives Ansible the inventory automatically, and runs your playbook.

### Why Not `ansible-local`?

`ansible-local` would COPY Ansible onto the temp instance and run it there. Possible, but heavier and slower. The `ansible` provisioner (remote) is the default choice.

## Prerequisites

- Everything from Lab 2 (AWS CLI configured, Packer installed).
- **Ansible installed on your laptop** (`ansible --version`).

## Steps

### Step 1: Look at the Playbook

Open `playbooks/nginx.yml`. It's a normal Ansible playbook. Nothing Packer-specific. You could reuse this same file with `ansible-playbook` against any host.

### Step 2: Look at the Packer File

Open `aws-ansible.pkr.hcl`. Notice how short the `build` block is — all the logic moved into Ansible.

### Step 3: Initialize

```bash
cd lab3
packer init .
```

This downloads the `amazon` AND `ansible` plugins.

### Step 4: Validate

```bash
packer validate aws-ansible.pkr.hcl
```

### Step 5: Build

```bash
packer build aws-ansible.pkr.hcl
```

You'll see:
1. Packer launches a temp EC2 instance.
2. Packer waits for SSH.
3. **Packer runs `ansible-playbook` against the instance** — you'll see real Ansible output (`TASK [Install nginx] changed: [default]`, etc.).
4. Packer snapshots the instance into an AMI.
5. Packer terminates the temp instance.

### Step 6: Verify

Same as Lab 2 — find the AMI in the EC2 console, launch an instance from it, hit port 80.

## Why This is Powerful

Imagine you have these Ansible playbooks already:
- `nginx.yml` — installs and configures nginx
- `app.yml` — deploys your app
- `monitoring.yml` — installs CloudWatch agent

You can bake an AMI with ALL of them by listing them as extra plays. Or have different Packer templates for "web AMI" vs "worker AMI", each picking the playbooks they need.

Same playbooks work for:
- **Baking AMIs** (via Packer)
- **Configuring live servers** (via Ansible directly)
- **Local testing on Multipass VMs** (like ansible-labs)

One playbook. Three jobs.

## Try This

1. Use one of the playbooks from `../../ansible-labs/lab6/` (the templates lab). Adapt the variables.
2. Pass variables to Ansible from Packer: add `extra_arguments = ["-e", "http_port=8080"]` in the provisioner block.
3. Add a SECOND `provisioner "ansible"` block that runs a different playbook. Both run in order.

## Common Mistakes

- **"ansible-playbook: command not found"** — Ansible isn't installed on your laptop. Install it.
- **SSH errors during the Ansible step** — Packer normally handles SSH. Make sure `ssh_username = "ubuntu"` is set in the source block.
- **Playbook errors** — Test your playbook FIRST against a Multipass VM. Only then plug it into Packer.

## Where to Go From Here

You now have all the pieces:
- **Ansible** to describe configuration.
- **Packer** to bake images.
- **Multipass** for free local testing.
- **AWS** for production.

Real production setups usually layer **Terraform** on top to launch fleets from these AMIs. That's a topic for another day, but the foundation is here.
