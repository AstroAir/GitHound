# GitHound Docker Deployment Guide

This guide covers how to deploy GitHound using Docker for development, staging, and production environments.

## Quick Start

### Prerequisites

- Docker 20.10+ and Docker Compose 2.0+
- Git (for cloning repositories to analyze)
- At least 2GB RAM and 1GB disk space

### Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/AstroAir/GitHound.git
   cd GitHound
   ```

2. **Copy environment configuration**:
   ```bash
   cp .env.example .env
   # Edit .env with your specific configuration
   ```

3. **Start development environment**:
   ```bash
   docker-compose up -d
   ```

4. **Access the services**:
   - Web API: http://localhost:8000
   - MCP Server: http://localhost:3000
   - Redis: localhost:6379

## Architecture Overview

GitHound Docker deployment consists of:

- **githound-web**: FastAPI web server with REST API
- **githound-mcp**: MCP (Model Context Protocol) server
- **redis**: Cache and session storage
- **nginx**: Reverse proxy (production only)

## Environment Configurations

### Development (.env + docker-compose.override.yml)
- Hot reload enabled
- Debug logging
- Source code mounted as volume
- All ports exposed

### Production (docker-compose.prod.yml)
- Optimized for performance
- Resource limits
- Log rotation
- Nginx reverse proxy
- Multiple replicas

## Deployment Commands

### Development
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

### Production
```bash
# Deploy to production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale web service
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale githound-web=3

# Update deployment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml pull
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Configuration

### Environment Variables

Key environment variables for Docker deployment (see `.env.example` for complete list and [Environment Variables Reference](../docs/configuration/environment-variables.md) for comprehensive documentation):

**Core Configuration:**
- `GITHOUND_ENV`: Environment (development/staging/production)
- `GITHOUND_LOG_LEVEL`: Logging level (DEBUG/INFO/WARNING/ERROR)
- `GITHOUND_WEB_PORT`: Web API port (default: 8000)
- `FASTMCP_SERVER_PORT`: MCP server port (default: 3000)

**Security:**
- `SECRET_KEY`: Application secret key (required in production)
- `JWT_SECRET_KEY`: JWT signing key (required for authentication)

**Data Storage:**
- `REDIS_URL`: Redis connection string
- `GITHOUND_DATA_DIR`: Application data directory
- `GITHOUND_CACHE_DIR`: Cache directory

**Authentication (optional):**
- `FASTMCP_SERVER_ENABLE_AUTH`: Enable MCP server authentication
- `FASTMCP_SERVER_AUTH_GITHUB_CLIENT_ID`: GitHub OAuth client ID
- `FASTMCP_SERVER_AUTH_GITHUB_CLIENT_SECRET`: GitHub OAuth client secret

### Volume Mounts

- `githound_data`: Application data and cache
- `githound_logs`: Application logs
- `redis_data`: Redis persistence
- `./repositories`: Git repositories to analyze (read-only)

## Health Checks

All services include health checks:

```bash
# Check service health
docker-compose ps

# Manual health check
curl http://localhost:8000/health
curl http://localhost:3000/health
```

## Monitoring and Logs

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f githound-web

# Last 100 lines
docker-compose logs --tail=100 githound-web
```

### Resource Monitoring
```bash
# Container stats
docker stats

# Service resource usage
docker-compose top
```

## Troubleshooting

### Common Issues

1. **Port conflicts**: Change ports in docker-compose.yml
2. **Permission issues**: Ensure proper file permissions
3. **Memory issues**: Increase Docker memory limits
4. **Redis connection**: Check Redis service status

### Debug Commands
```bash
# Enter container shell
docker-compose exec githound-web bash

# Check container logs
docker logs githound-web

# Inspect container
docker inspect githound-web

# Check network connectivity
docker-compose exec githound-web ping redis
```

## Security Considerations

### Production Security
- Change default secrets in `.env`
- Use HTTPS with proper SSL certificates
- Configure firewall rules
- Regular security updates
- Monitor access logs

### Network Security
- Services communicate via internal Docker network
- Only necessary ports exposed
- Redis not exposed externally in production

## Backup and Recovery

### Data Backup
```bash
# Backup volumes
docker run --rm -v githound_data:/data -v $(pwd):/backup alpine tar czf /backup/githound-data.tar.gz -C /data .
docker run --rm -v redis_data:/data -v $(pwd):/backup alpine tar czf /backup/redis-data.tar.gz -C /data .
```

### Data Restore
```bash
# Restore volumes
docker run --rm -v githound_data:/data -v $(pwd):/backup alpine tar xzf /backup/githound-data.tar.gz -C /data
docker run --rm -v redis_data:/data -v $(pwd):/backup alpine tar xzf /backup/redis-data.tar.gz -C /data
```

## Performance Tuning

### Resource Optimization
- Adjust worker counts based on CPU cores
- Configure Redis memory limits
- Set appropriate cache TTL values
- Monitor and adjust resource limits

### Scaling
```bash
# Scale web service
docker-compose up -d --scale githound-web=3

# Use load balancer for multiple instances
# Configure nginx upstream for load balancing
```

## Integration Examples

### CI/CD Pipeline
```yaml
# Example GitHub Actions workflow
name: Deploy GitHound
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to production
        run: |
          docker-compose -f docker-compose.yml -f docker-compose.prod.yml pull
          docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### External Services
```bash
# Connect to external database
export DATABASE_URL="postgresql://user:pass@host:5432/db"

# Use external Redis
export REDIS_URL="redis://external-redis:6379/0"
```

## Advanced Configuration

### Custom Nginx Configuration

For production deployments with custom domains:

1. **Update nginx configuration**:
   ```bash
   # Edit docker/nginx/conf.d/githound.conf
   # Replace server_name _ with your domain
   server_name yourdomain.com;
   ```

2. **SSL Certificates**:
   ```bash
   # Place SSL certificates in docker/ssl/
   mkdir -p docker/ssl
   cp your-cert.pem docker/ssl/cert.pem
   cp your-key.pem docker/ssl/key.pem
   ```

### Environment-Specific Overrides

Create custom compose files for specific environments:

```yaml
# docker-compose.staging.yml
version: '3.8'
services:
  githound-web:
    environment:
      - GITHOUND_ENV=staging
      - GITHOUND_LOG_LEVEL=info
    deploy:
      replicas: 2
```

### External Database Integration

```yaml
# Add to docker-compose.yml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: githound
      POSTGRES_USER: githound
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

## Deployment Scripts

### Quick Deployment
```bash
# Make scripts executable
chmod +x scripts/docker-deploy.sh

# Deploy development environment
./scripts/docker-deploy.sh deploy

# Deploy production environment
./scripts/docker-deploy.sh -e production deploy

# Windows PowerShell
.\scripts\docker-deploy.ps1 -Environment production deploy
```

### Automated Deployment
```bash
# Set up automated deployment with cron
# Add to crontab for automatic updates
0 2 * * * /path/to/GitHound/scripts/docker-deploy.sh -e production update
```

## Current Features and Capabilities

### MCP Server Integration
- FastMCP 2.0 server with 25+ tools for Git repository analysis
- Support for stdio, HTTP, and SSE transports
- Authentication and authorization providers (GitHub OAuth, JWT, Permit.io, Eunomia)
- Rate limiting and audit logging
- Real-time streaming capabilities

### Web API Features
- Comprehensive REST API with OpenAPI documentation
- WebSocket support for real-time operations
- JWT-based authentication
- Redis-backed rate limiting
- Export capabilities (JSON, YAML, CSV, XML, Excel)

### Search Engine
- Multi-modal search capabilities (content, commit messages, file paths, authors)
- Advanced pattern detection and fuzzy search
- Parallel processing with configurable worker pools
- Intelligent result ranking and caching

### Security Features
- Role-based access control
- Audit logging for all operations
- Secure container configuration with read-only filesystems
- Network isolation and resource limits
- Security headers and CORS configuration

## Support

For issues and questions:
- Check the troubleshooting section
- Review container logs
- Open an issue on GitHub
- Check the main GitHound documentation
- Use the deployment scripts for common operations
- Review the [Environment Variables Reference](../docs/configuration/environment-variables.md) for configuration options
