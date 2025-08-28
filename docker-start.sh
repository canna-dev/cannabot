#!/bin/bash
# CannaBot Docker Quick Start Script

set -e

echo "🌿 CannaBot Docker Setup"
echo "========================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose found"

# Check if .env file exists
if [ ! -f ".env" ]; then
    if [ -f ".env.docker" ]; then
        echo "📋 Copying Docker environment template..."
        cp .env.docker .env
        echo "⚠️  Please edit .env and add your Discord bot token!"
        echo "   DISCORD_TOKEN=your_bot_token_here"
        echo ""
        echo "   Then run: ./docker-start.sh"
        exit 0
    else
        echo "❌ No .env file found. Please create one with your Discord bot token."
        exit 1
    fi
fi

# Check if Discord token is set
if ! grep -q "DISCORD_TOKEN=.*[^=]" .env; then
    echo "❌ DISCORD_TOKEN not set in .env file!"
    echo "   Please edit .env and add: DISCORD_TOKEN=your_bot_token_here"
    exit 1
fi

echo "✅ Environment configuration found"

# Create necessary directories
echo "📁 Creating data directories..."
mkdir -p data logs

# Build and start services
echo "🐳 Building and starting CannaBot..."

if [ "$1" = "prod" ]; then
    echo "🚀 Starting in production mode..."
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
elif [ "$1" = "dev" ]; then
    echo "🛠️  Starting in development mode..."
    docker-compose up --build
else
    echo "🏃 Starting in standard mode..."
    docker-compose up --build -d
fi

echo ""
echo "✅ CannaBot Docker setup complete!"
echo ""
echo "📊 To check status: docker-compose ps"
echo "📋 To view logs:    docker-compose logs -f cannabot"
echo "🛑 To stop:         docker-compose down"
echo "🔄 To restart:      docker-compose restart"
echo ""
echo "🌿 CannaBot should now be online in your Discord server!"
