@echo off
REM CannaBot Docker Quick Start Script for Windows

echo 🌿 CannaBot Docker Setup
echo =========================

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    echo    Visit: https://docs.docker.com/desktop/windows/
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose first.
    echo    Visit: https://docs.docker.com/compose/install/
    pause
    exit /b 1
)

echo ✅ Docker and Docker Compose found

REM Check if .env file exists
if not exist ".env" (
    if exist ".env.docker" (
        echo 📋 Copying Docker environment template...
        copy ".env.docker" ".env"
        echo ⚠️  Please edit .env and add your Discord bot token!
        echo    DISCORD_TOKEN=your_bot_token_here
        echo.
        echo    Then run: docker-start.bat
        pause
        exit /b 0
    ) else (
        echo ❌ No .env file found. Please create one with your Discord bot token.
        pause
        exit /b 1
    )
)

REM Check if Discord token is set
findstr /C:"DISCORD_TOKEN=" .env | findstr /V /C:"DISCORD_TOKEN=$" >nul
if %errorlevel% neq 0 (
    echo ❌ DISCORD_TOKEN not set in .env file!
    echo    Please edit .env and add: DISCORD_TOKEN=your_bot_token_here
    pause
    exit /b 1
)

echo ✅ Environment configuration found

REM Create necessary directories
echo 📁 Creating data directories...
if not exist "data" mkdir data
if not exist "logs" mkdir logs

REM Build and start services
echo 🐳 Building and starting CannaBot...

if "%1"=="prod" (
    echo 🚀 Starting in production mode...
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
) else if "%1"=="dev" (
    echo 🛠️  Starting in development mode...
    docker-compose up --build
) else (
    echo 🏃 Starting in standard mode...
    docker-compose up --build -d
)

echo.
echo ✅ CannaBot Docker setup complete!
echo.
echo 📊 To check status: docker-compose ps
echo 📋 To view logs:    docker-compose logs -f cannabot
echo 🛑 To stop:         docker-compose down
echo 🔄 To restart:      docker-compose restart
echo.
echo 🌿 CannaBot should now be online in your Discord server!
pause
