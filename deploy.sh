#!/bin/bash

# Career Path Recommender System - Deployment Script
# This script provides easy deployment options

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required files exist
check_requirements() {
    print_status "Checking requirements..."
    
    if [ ! -f "main.py" ]; then
        print_error "main.py not found!"
        exit 1
    fi
    
    if [ ! -f "Requirements.txt" ]; then
        print_error "Requirements.txt not found!"
        exit 1
    fi
    
    if [ ! -f "aws_credentials.env" ]; then
        print_warning "aws_credentials.env not found. Please create it with your AWS credentials."
    fi
    
    print_success "Requirements check passed!"
}

# Docker deployment
deploy_docker() {
    print_status "Deploying with Docker..."
    
    # Build Docker image
    print_status "Building Docker image..."
    docker build -t career-path-recommender .
    
    if [ $? -eq 0 ]; then
        print_success "Docker image built successfully!"
    else
        print_error "Docker build failed!"
        exit 1
    fi
    
    # Run container
    print_status "Starting container..."
    docker run -d \
        --name career-path-recommender \
        -p 8501:8501 \
        --env-file aws_credentials.env \
        career-path-recommender
    
    if [ $? -eq 0 ]; then
        print_success "Container started successfully!"
        print_status "Application is running at: http://localhost:8501"
    else
        print_error "Failed to start container!"
        exit 1
    fi
}

# Docker Compose deployment
deploy_docker_compose() {
    print_status "Deploying with Docker Compose..."
    
    # Start services
    docker-compose up -d
    
    if [ $? -eq 0 ]; then
        print_success "Docker Compose deployment successful!"
        print_status "Application is running at: http://localhost:8501"
        print_status "View logs with: docker-compose logs -f"
    else
        print_error "Docker Compose deployment failed!"
        exit 1
    fi
}

# Stop deployment
stop_deployment() {
    print_status "Stopping deployment..."
    
    # Stop Docker Compose
    if [ -f "docker-compose.yml" ]; then
        docker-compose down
    fi
    
    # Stop Docker container
    docker stop career-path-recommender 2>/dev/null || true
    docker rm career-path-recommender 2>/dev/null || true
    
    print_success "Deployment stopped!"
}

# Show logs
show_logs() {
    print_status "Showing logs..."
    
    if docker ps | grep -q career-path-recommender; then
        docker logs -f career-path-recommender
    elif docker-compose ps | grep -q career-app; then
        docker-compose logs -f
    else
        print_error "No running containers found!"
    fi
}

# Health check
health_check() {
    print_status "Performing health check..."
    
    # Wait for application to start
    sleep 10
    
    # Check if application is responding
    if curl -f http://localhost:8501/_stcore/health >/dev/null 2>&1; then
        print_success "Application is healthy!"
    else
        print_error "Health check failed!"
        print_status "Check logs with: ./deploy.sh logs"
    fi
}

# Show help
show_help() {
    echo "Career Path Recommender System - Deployment Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  docker          Deploy using Docker"
    echo "  compose         Deploy using Docker Compose"
    echo "  stop            Stop all deployments"
    echo "  logs            Show application logs"
    echo "  health          Perform health check"
    echo "  help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 docker       # Deploy with Docker"
    echo "  $0 compose      # Deploy with Docker Compose"
    echo "  $0 stop         # Stop deployment"
    echo "  $0 logs         # View logs"
}

# Main script logic
case "${1:-help}" in
    docker)
        check_requirements
        deploy_docker
        health_check
        ;;
    compose)
        check_requirements
        deploy_docker_compose
        health_check
        ;;
    stop)
        stop_deployment
        ;;
    logs)
        show_logs
        ;;
    health)
        health_check
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
