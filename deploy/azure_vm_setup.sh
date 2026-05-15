#!/bin/bash
# Azure VM Initial Setup Script for Ubuntu 22.04 LTS
# This script installs Docker and Docker Compose.

set -e

echo "================================================="
echo "Starting VM Setup for Smart Commerce Platform..."
echo "================================================="

# 1. Update the system
echo "Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y

# 2. Install prerequisites
echo "Installing prerequisite packages..."
sudo apt-get install -y ca-certificates curl gnupg lsb-release git

# 3. Add Docker's official GPG key
echo "Adding Docker GPG key..."
sudo mkdir -m 0755 -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 4. Set up the stable Docker repository
echo "Setting up Docker repository..."
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 5. Install Docker Engine and Docker Compose
echo "Installing Docker Engine and Docker Compose..."
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 6. Add current user to the docker group
# This allows running docker commands without 'sudo'
echo "Adding user to docker group..."
sudo usermod -aG docker $USER

echo "================================================="
echo "Setup Complete!"
echo "IMPORTANT: You must log out and log back in for the 'docker' group changes to take effect."
echo "Verify installation by running: docker --version && docker compose version"
echo "================================================="
