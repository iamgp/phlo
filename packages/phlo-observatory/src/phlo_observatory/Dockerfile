# Build stage
FROM node:24-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source files
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM node:24-alpine AS runner

WORKDIR /app

# Copy built application
COPY --from=builder /app/.output /app/.output
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules /app/node_modules

# Set environment
ENV NODE_ENV=production
ENV HOST=0.0.0.0
ENV PORT=3001

# Expose port
EXPOSE 3001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3001/ || exit 1

# Run the application
CMD ["node", ".output/server/index.mjs"]
