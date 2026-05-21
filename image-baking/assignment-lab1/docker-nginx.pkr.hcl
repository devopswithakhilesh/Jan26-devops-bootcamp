// Lab 1: Bake a Docker image with nginx pre-installed.

packer {
  required_plugins {
    docker = {
      source  = "github.com/hashicorp/docker"
      version = "~> 1"
    }
  }
}

// SOURCE: where we build (a temporary Docker container)
source "docker" "ubuntu" {
  image  = "ubuntu:22.04"
  commit = true

  changes = [
    "EXPOSE 80",
    "CMD [\"nginx\", \"-g\", \"daemon off;\"]"
  ]
}

// BUILD: what we do inside the temporary container
build {
  name    = "my-nginx-image"
  sources = ["source.docker.ubuntu"]

  // Step 1: update apt and install nginx
  provisioner "shell" {
    inline = [
      "apt-get update -y",
      "DEBIAN_FRONTEND=noninteractive apt-get install -y nginx",
      "apt-get clean",
      "rm -rf /var/lib/apt/lists/*"
    ]
  }

  // Step 2: drop a custom index.html into the image
  provisioner "shell" {
    inline = [
      "echo '<h1>Baked by Packer</h1>' > /var/www/html/index.html"
    ]
  }

  // POST: tag the resulting image
  post-processor "docker-tag" {
    repository = "my-nginx"
    tags       = ["packer-built", "latest"]
  }
}
