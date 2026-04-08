# Stage 1: Build the React Application
FROM node:20-alpine AS build

WORKDIR /app

# Install dependencies
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

# Copy source and build
COPY frontend/ ./
RUN npm run build

# Stage 2: Serve with Nginx Proxy
FROM nginx:alpine

# Copy the custom Reverse Proxy configuration
COPY deploy/nginx/smart-commerce.conf /etc/nginx/conf.d/default.conf

# Copy the built Vite static files into Nginx document root
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
EXPOSE 443

# Nginx automatically starts when running the alpine image
CMD ["nginx", "-g", "daemon off;"]
