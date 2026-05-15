# Smart Commerce: Azure VM Deployment Guide

This guide will walk you through deploying your microservices (Frontend Proxy, Backend, and AI Service) to an Azure Virtual Machine. 

> [!IMPORTANT]
> Before you start, ensure your code is pushed to a Git repository (like GitHub, GitLab, or Azure DevOps) so you can easily pull it onto the server. 

## Step 1: Create the Azure Virtual Machine
1. Go to the **Azure Portal**.
2. Click **Create a resource** > **Virtual machine**.
3. Configure the VM:
   - **Image:** Ubuntu Server 22.04 LTS
   - **Size:** Ensure it has enough RAM (at least 2-4GB) since you are running AI services and a database. `Standard_B2s` is a good starting point.
   - **Authentication type:** SSH public key (recommended) or Password.
4. Under **Inbound port rules**, allow the following ports:
   - `HTTP (80)`: For the frontend application
   - `HTTPS (443)`: For secure traffic
   - `SSH (22)`: To connect to the machine
5. Click **Review + create** and then **Create**. 
6. Once deployed, note down the **Public IP address**.

## Step 2: Connect to the VM
Open your local terminal and connect to your new VM using SSH:
```bash
ssh username@your_vm_public_ip
```
*(Replace `username` with the admin username you set, and `your_vm_public_ip` with the actual IP).*

## Step 3: Install Docker and Docker Compose
I have created a setup script for you in the repository: `deploy/azure_vm_setup.sh`. 

1. Clone your project onto the VM:
   ```bash
   git clone https://github.com/your-username/your-repo-name.git
   cd your-repo-name/smart-commerce
   ```
2. Make the script executable and run it:
   ```bash
   chmod +x deploy/azure_vm_setup.sh
   ./deploy/azure_vm_setup.sh
   ```
3. **Log out and log back in** (type `exit` and then `ssh` back in) so that you can run Docker commands without typing `sudo`.

## Step 4: Add Environment Variables
Your `.env` files are generally not committed to Git (for security reasons). You must create them on the server:

```bash
cd core_backend
nano .env
```
Paste your production environment variables (database credentials, API keys) into this file and save it (`Ctrl+O`, `Enter`, `Ctrl+X`).

## Step 5: Start the Application
Go back to the `smart-commerce` directory where your `docker-compose.yml` lives, and start everything up:

```bash
cd ~/your-repo-name/smart-commerce
docker compose up -d --build
```

> [!TIP]
> The `-d` flag runs the containers in the background ("detached mode"). The `--build` flag forces Docker to build fresh images with the names we just added.

## Step 6: Verify Deployment
Run this command to ensure all 3 containers (`smart_commerce_proxy`, `smart_commerce_backend`, `smart_commerce_ai`) are running:
```bash
docker ps
```

Finally, open your web browser and go to `http://<your_vm_public_ip>`. You should see your Smart Commerce platform live!
