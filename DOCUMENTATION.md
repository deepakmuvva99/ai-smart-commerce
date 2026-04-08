# Smart Commerce AI Architecture - Complete Documentation

Welcome to the Smart Commerce AI project! This document serves as the complete technical bible for the repository. Whether you are a new developer onboarding, an investor, or a team member trying to run the project, this guide explains exactly what this system is, how to run it, and the deep technical architecture behind every microservice.

---

## 1. Quick Start Guide (How to Clone & Run)

Our goal is to make setting up this massive AI infrastructure as easy as a single command. You do **not** need to install Python, Node.js, or configure environment variables locally. Everything is containerized.

### Prerequisites
1. Install [Git](https://git-scm.com/downloads)
2. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### Step-by-Step Setup
1. **Clone the Repository:**
   ```bash
   git clone https://github.com/deepakmuvva99/ai-smart-commerce.git
   cd ai-smart-commerce
   ```

2. **Launch the Architecture:**
   ```bash
   docker-compose up -d --build
   ```
   *Note: The first build will take several minutes as it downloads PyTorch, Node.js, and builds the isolated Linux environments.*

3. **Access the Platform:**
   - **Main Website / Admin Panel:** Open your browser to `http://localhost`
   - **Admin Login:** `admin@smartcommerce.com`
   - **Admin Password:** `admin123`

4. **Shutdown the Platform:**
   ```bash
   docker-compose down
   ```

---

## 2. Project Overview & "The Why"
At its core, **Smart Commerce** is an autonomous e-commerce engine that dynamically alters product prices based on user traffic, remaining inventory, and global demand. 

Instead of relying on human analysts to manually adjust prices, this project fuses **Deep Learning (DL)** to predict demand and **Reinforcement Learning (RL)** to autonomously take action on the prices. It is built using a modern microservice architecture to ensure scalability.

---

## 3. Microservice Architecture Breakdown
The system uses Docker Compose to orchestrate three completely separate environments. They run independently and communicate over a secure internal Docker network.

### Service A: The Frontend Proxy (`frontend_proxy`)
**Technology:** React, Vite, TailwindCSS, Nginx  
**Role:** The visual interface of the platform.
*   **Why Vite & React?** Vite provides lightning-fast compilation, and React allows us to build complex state-driven components like the real-time AI Analytics dashboard.
*   **Why Nginx?** Nginx acts as our reverse proxy. Instead of the browser trying to find the backend directly, Nginx handles all routing. If a user visits `http://localhost/api/*`, Nginx silently forwards that request to the hidden Backend service. This completely eliminates CORS errors and perfectly mirrors professional enterprise deployments.

### Service B: The Core Backend (`core_backend`)
**Technology:** Python, FastAPI, SQLite, SQLAlchemy, JWT Authentication  
**Role:** The central nervous system of the platform.
*   **Authentication:** Uses standard JSON Web Tokens (JWT) encrypted with bcrypt. It securely hashes passwords and issues bearer tokens validating whether a user is a normal customer or an "Admin".
*   **Database (SQLite via Docker Volume):** We persist user logic, product catalogs, and transaction history. The database is housed safely in a secure Docker Named Volume (`db_data`) so data survives even if the containers crash.
*   **The Scheduler:** A background Python thread runs continuously (e.g., every 60 seconds). It loops through the product catalog and asks the AI service: *"Given what just happened, what should the price be now?"*

### Service C: The AI Engine (`ai_engine`)
**Technology:** Python, PyTorch, FastAPI  
**Role:** The isolated mathematical brain containing our trained models.  
*   **Deep Learning (BiLSTM):** We utilize a Bidirectional Long Short-Term Memory (BiLSTM) network. This neural network looks at historical data and accurately predicts exactly how much "demand" (purchase volume) a specific product will have shortly.
*   **Reinforcement Learning (SAC-RL):** We utilize a Soft-Actor Critic (SAC) agent. Unlike normal AI that just outputs a prediction, RL is an "actor". It takes the predicted demand from the Deep Learning model, evaluates the remaining stock, and outputs a calculated `price_multiplier`. 
    *   *Example:* If demand is soaring and stock is low, the RL agent explores by outputting a `1.05` multiplier, raising the price by 5% to maximize profit automatically. It learns from "Rewards" (sales revenue) sent back to it by the Core Backend every cycle.

---

## 4. Key Platform Features

### Authentication & Authorization Flow
We built custom Pydantic schemas validating all incoming credentials. If a user tries to create an account with a weak password (< 8 chars), the backend returns a `422 Unprocessable Entity` which the Frontend catches and beautifully displays. When validated, the user is given a JWT to access protected endpoints.

### Real-time AI Settings Dashboard
Inside the Admin view, the "Platform Settings" panel allows humans to interact directly with the AI. Because the microservices are distinct, the Core Backend fetches live health checks from the AI engine. An Admin can pause the AI pricing optimizer, change the frequency of its evaluations, and force it to retrain its algorithms in real-time.

### Network Isolation & Security Fortification
To make this project production-ready, security was paramount:
- **No Open Ports:** The AI Engine and Core Backend do NOT expose any ports to the host machine. You cannot hit them directly.
- **Proxy Gatekeeper:** The only container exposed to the outside world is the Nginx load balancer (Port 80/443). If a bad actor attempts to exploit Port 8000 on your machine, the connection will be totally refused.

## 5. Summary
By decoupling the architecture into decoupled microservices, we achieved an enterprise-grade structure. The Machine Learning models can spin up on massive GPU clusters independently, the frontend can be cached globally on CDNs, and the core transactional backend can scale safely. All of this deploys identically whether you are running it on a local Windows laptop via Docker Compose or on a massive set of AWS EC2 instances.
