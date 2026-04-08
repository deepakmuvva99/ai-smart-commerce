# Smart Commerce AI Architecture

This is a local-ready monorepo containing the Smart Commerce system—a multi-layered application consisting of a React Frontend, a FastAPI Core Backend, and a Python AI Service engine using Deep Learning and Reinforcement Learning for dynamic pricing optimization.

## Requirements
To run this application locally, you **do not** need to install Python, Node.js, or any massive dependencies. You just need:
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed on your machine.
- Git.

## Quick Start
Once you have cloned this repository, simply open a terminal at the root of this folder and type:

```bash
docker-compose up -d --build
```

Docker will automatically:
1. Build the AI Python Environment and load the ML Models (`ai_service`)
2. Build the Core Backend Python Environment (`core_backend`)
3. Compile the Vite React Application into Nginx (`frontend`)
4. Link them all into a secure internal container network and expose the frontend on Port `80`.

## Accessing the Application
Once the containers spin up successfully, you can access the full platform directly from your browser:

- **Frontend Application:** `http://localhost`
- **Admin Dashboard Login:** `admin@smartcommerce.com`
- **Admin Password:** `admin123`

The database (`sql_app.db`) comes pre-seeded in this repository with dozens of products, testing users, and historical ML logs. The repository will mount this seeded data inside the containers during build, so you can test live ML predictions and API calls out of the box!

**To shut down the architecture when finished:**
```bash
docker-compose down
```
