# Lab 1 - Bake a Docker Image with Packer

## Goal

Build your first image with Packer. We'll use Docker because it's local and free.

You will end up with a Docker image called `my-nginx:packer-built` on your laptop.

## Theory

### Why Docker for Lab 1?

- **Free** - no AWS bill.
- **Fast** - builds in 30 seconds.
- **Local** - no network needed.

It's the perfect way to learn Packer without spending money.

### The Plugin Concept

Packer doesn't know about Docker, AWS, Azure, etc. out of the box. It uses **plugins** for each platform.

The `docker` plugin tells Packer how to:
- Start a Docker container.
- Run setup inside it.
- Save the container as a new image.

You declare which plugins you need at the top of your file. `packer init` downloads them.

### `source` vs `build`

- **`source`** = WHERE Packer builds (which platform, base image, region, etc.)
- **`build`** = WHAT Packer does inside (install packages, copy files).

You can have one `source` and many `build` steps.

## Prerequisites

- Packer installed (`packer version`).
- Docker installed and running (`docker ps`).

## Steps

### Step 1: Look at the Packer File

Open `docker-nginx.pkr.hcl`. Read each block.

### Step 2: Initialize (Download Plugins)

```bash
cd lab1
packer init .
```

This downloads the `docker` plugin. You only do this once per folder.

### Step 3: Validate

Always validate before building:
```bash
packer validate docker-nginx.pkr.hcl
```

Should print "The configuration is valid."

### Step 4: Build

```bash
packer build docker-nginx.pkr.hcl
```

You will see Packer:
1. Pull the `ubuntu:22.04` base image.
2. Start a temp container.
3. Run `apt-get install nginx` inside.
4. Commit the container as a new image.
5. Tag it as `my-nginx:packer-built`.

### Step 5: Verify

```bash
docker images | grep my-nginx
```

You should see your image.

### Step 6: Run Your Image

```bash
docker run -d -p 8080:80 --name test-nginx my-nginx:packer-built nginx -g 'daemon off;'
```

Open http://localhost:8080 in a browser. You should see the nginx welcome page.

Cleanup when done:
```bash
docker stop test-nginx && docker rm test-nginx
```

## What Just Happened

You wrote ONE file. Packer turned it into a reusable image. The exact same `.pkr.hcl` file, with a different `source` block, can build an AWS AMI. That's the power of Packer.

## Try This

1. Edit the playbook to also install `curl` and `git`.
2. Change the image tag to `my-nginx:v2`. Rebuild.
3. Add a `provisioner "file"` block to copy a custom `index.html` into the image.

## Common Mistakes

- **"Cannot connect to the Docker daemon"** - Docker is not running. Start Docker Desktop.
- **"plugin not found"** - You forgot `packer init .`
- **HCL syntax errors** - Run `packer fmt .` to auto-format, and `packer validate` to spot mistakes.

## Next

Go to `lab2/` to bake an AWS AMI.
