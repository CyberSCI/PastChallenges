# Build stage
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache gcc musl-dev

# Copy go mod and sum files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy source code
COPY . .

# Build the application
RUN CGO_ENABLED=1 GOOS=linux go build -o main .

# Final stage
FROM alpine:3.19

WORKDIR /app

# Install runtime dependencies
RUN apk add --no-cache sqlite

# Create a non-root user
RUN adduser -D -g '' appuser

# Copy the binary and schema file from builder
COPY --from=builder /app/main /app/main
COPY --from=builder /app/db/schema.sql /app/db/schema.sql

# Set proper permissions
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

EXPOSE 8080

CMD ["/app/main"] 