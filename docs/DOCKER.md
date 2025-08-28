# 🐳 CannaBot Docker Deployment Guide

Complete Docker containerization for easy deployment and scalability.

## 🚀 Quick Start

### Prerequisites
- Docker Engine 20.10+
- Docker Compose 2.0+
- Discord Bot Token

### 1. Clone and Setup
```bash
git clone https://github.com/yourusername/CannaBot.git
cd CannaBot
```

### 2. Configure Environment
```bash
# Copy Docker environment template
cp .env.docker .env

# Edit .env and add your Discord bot token
DISCORD_TOKEN=your_discord_bot_token_here
```

### 3. Start with Docker Compose

**Windows:**
```cmd
docker-start.bat
```

**Linux/macOS:**
```bash
chmod +x docker-start.sh
./docker-start.sh
```

**Manual:**
```bash
docker-compose up --build -d
```

## 📋 Available Docker Configurations

### 🏠 Standard Mode (Recommended)
- **SQLite database** - Simple setup, perfect for small servers
- **Automatic restarts** - Bot stays online
- **Volume persistence** - Data survives container restarts

```bash
docker-compose up -d
```

### 🚀 Production Mode
- **PostgreSQL database** - Better performance and reliability
- **Resource limits** - Optimized memory usage
- **Enhanced logging** - Structured log management
- **Multi-stage builds** - Smaller image size

```bash
./docker-start.sh prod
# OR
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 🛠️ Development Mode
- **Live code reloading** - Changes reflected immediately
- **Debug logging** - Detailed development information
- **Database admin panel** - Adminer on port 8080
- **Interactive terminal** - For debugging

```bash
./docker-start.sh dev
# OR
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

## 🗂️ Docker Files Overview

```
CannaBot/
├── Dockerfile                 # Main Docker image (SQLite)
├── Dockerfile.production      # Optimized production image
├── docker-compose.yml         # Main compose configuration
├── docker-compose.prod.yml    # Production overrides
├── docker-compose.dev.yml     # Development overrides
├── .env.docker               # Docker environment template
├── docker-start.sh           # Linux/macOS startup script
└── docker-start.bat          # Windows startup script
```

## ⚙️ Environment Configuration

### Required Variables
```env
# Discord Bot Token (Required)
DISCORD_TOKEN=your_discord_bot_token_here
```

### Database Options

**SQLite (Default - Simple Setup):**
```env
DATABASE_URL=sqlite:///data/cannabot.db
```

**PostgreSQL (Production Recommended):**
```env
DATABASE_URL=postgresql://cannabot:password@postgres:5432/cannabot
POSTGRES_DB=cannabot
POSTGRES_USER=cannabot
POSTGRES_PASSWORD=your_secure_password
```

### Feature Flags
```env
ENABLE_SHARING=true
ENABLE_LEADERBOARDS=true
MAX_DAILY_THC_DEFAULT=100
```

## 🐳 Docker Commands Reference

### Basic Operations
```bash
# Start services
docker-compose up -d

# Stop services  
docker-compose down

# Restart bot only
docker-compose restart cannabot

# View logs
docker-compose logs -f cannabot

# Check status
docker-compose ps
```

### Database Operations
```bash
# Access PostgreSQL
docker-compose exec postgres psql -U cannabot -d cannabot

# Backup database
docker-compose exec postgres pg_dump -U cannabot cannabot > backup.sql

# Restore database
docker-compose exec -T postgres psql -U cannabot -d cannabot < backup.sql
```

### Maintenance
```bash
# Update images
docker-compose pull
docker-compose up -d

# Clean up unused images
docker image prune -f

# View resource usage
docker stats cannabot
```

## 📊 Monitoring and Health Checks

### Built-in Health Checks
- **Bot health**: Configuration validation every 30s
- **Database health**: PostgreSQL connection check every 10s
- **Redis health**: Cache availability check every 10s

### View Health Status
```bash
# Check all services
docker-compose ps

# Detailed health information
docker inspect cannabot --format='{{.State.Health.Status}}'
```

### Logs and Debugging
```bash
# Real-time logs
docker-compose logs -f cannabot

# Specific time range
docker-compose logs --since="2h" cannabot

# Container shell access
docker-compose exec cannabot /bin/bash
```

## 🔧 Customization

### Custom Dockerfile
```dockerfile
FROM cannabot:latest

# Add custom packages
USER root
RUN apt-get update && apt-get install -y your-package
USER cannabot

# Copy custom configuration
COPY custom-config.py /app/
```

### Environment Overrides
Create `docker-compose.override.yml`:
```yaml
version: '3.8'
services:
  cannabot:
    environment:
      - CUSTOM_SETTING=value
    ports:
      - "8080:8080"  # Expose health check port
```

## 🚢 Production Deployment

### 1. Server Setup
```bash
# Install Docker on Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Production Configuration
```bash
# Clone repository
git clone https://github.com/yourusername/CannaBot.git
cd CannaBot

# Setup environment
cp .env.docker .env
nano .env  # Add your Discord token and database settings

# Start in production mode
./docker-start.sh prod
```

### 3. Process Management
```bash
# Auto-start on boot
sudo systemctl enable docker

# Create systemd service (optional)
sudo tee /etc/systemd/system/cannabot.service > /dev/null <<EOF
[Unit]
Description=CannaBot Discord Bot
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/path/to/CannaBot
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable cannabot
sudo systemctl start cannabot
```

## 🔐 Security Best Practices

### Environment Security
- Never commit `.env` files
- Use strong database passwords
- Limit container resources
- Run as non-root user (implemented)

### Network Security
```yaml
# docker-compose.yml
networks:
  cannabot-network:
    driver: bridge
    internal: true  # No internet access for database
```

### Container Security
```bash
# Scan for vulnerabilities
docker scan cannabot:latest

# Update base images regularly
docker-compose pull
docker-compose up -d
```

## 🆘 Troubleshooting

### Common Issues

**Bot won't start:**
```bash
# Check logs
docker-compose logs cannabot

# Verify environment
docker-compose exec cannabot env | grep DISCORD_TOKEN
```

**Database connection issues:**
```bash
# Check database status
docker-compose ps postgres

# Test connection
docker-compose exec cannabot python -c "from bot.database.connection import db; print('DB OK')"
```

**Permission errors:**
```bash
# Fix volume permissions
sudo chown -R 999:999 data/ logs/
```

### Performance Issues
```bash
# Monitor resource usage
docker stats

# Check container limits
docker inspect cannabot | grep -A 5 "Memory"
```

## 📈 Scaling and Load Balancing

### Horizontal Scaling
```yaml
# docker-compose.yml
services:
  cannabot:
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
```

### Load Balancer Setup
```yaml
# nginx.conf
upstream cannabot {
    server cannabot_1:8080;
    server cannabot_2:8080;
    server cannabot_3:8080;
}
```

---

**🌿 Your CannaBot is now fully containerized and ready for any deployment scenario!**
