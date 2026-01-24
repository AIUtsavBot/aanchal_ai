# Frontend Dockerfile (Development)
FROM node:20-alpine

# Install dependencies required
RUN apk add --no-cache libc6-compat

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies (use ci for deterministic installs)
RUN npm ci

# Copy application code
COPY . .

RUN npm run build

# Expose Vite's default port
EXPOSE 5173

# Start Vite dev server with host set to allow external connections
CMD ["npm", "run", "start"]
