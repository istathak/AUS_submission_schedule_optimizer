# Docker Usage Guide for Beginners

## What is Docker?

Docker packages your application and all its dependencies into a "container" - a lightweight, portable package that runs the same way everywhere. Think of it like a shipping container: it works the same whether it's on a ship, truck, or train.

## Prerequisites

1. **Install Docker Desktop** (if not already installed):
   - Mac: Download from https://www.docker.com/products/docker-desktop/
   - Windows: Same link
   - Linux: Follow distribution-specific instructions
   
2. **Verify installation**:
   ```bash
   docker --version
   ```
   You should see something like: `Docker version 24.0.0`

## Quick Start

### Option 1: Using Docker Compose (Easiest)

1. **Build and start the container**:
   ```bash
   docker-compose up --build
   ```
   
   The `--build` flag builds the image first, then starts it.

2. **Access the API**:
   - Open your browser: http://localhost:5001
   - Or test with curl: `curl http://localhost:5001/health`

3. **Stop the container**:
   Press `Ctrl+C` in the terminal, then run:
   ```bash
   docker-compose down
   ```

### Option 2: Using Docker Commands (More Control)

1. **Build the image**:
   ```bash
   docker build -t schedule-api .
   ```
   
   This creates an image named `schedule-api`. The `.` means "current directory".

2. **Run the container**:
   ```bash
   docker run -p 5001:5001 schedule-api
   ```
   
   The `-p 5001:5001` maps port 5001 from the container to port 5001 on your computer.

3. **Stop the container**:
   Press `Ctrl+C` in the terminal

4. **Run in background (detached mode)**:
   ```bash
   docker run -d -p 5001:5001 --name schedule-api schedule-api
   ```
   
   The `-d` flag runs it in the background. `--name` gives it a name.

5. **Stop a background container**:
   ```bash
   docker stop schedule-api
   ```

6. **View running containers**:
   ```bash
   docker ps
   ```

7. **View all containers (including stopped)**:
   ```bash
   docker ps -a
   ```

8. **Remove a container**:
   ```bash
   docker rm schedule-api
   ```

## Common Commands

### Viewing Logs

```bash
# If using docker-compose
docker-compose logs

# If using docker run
docker logs schedule-api

# Follow logs in real-time
docker logs -f schedule-api
```

### Rebuilding After Code Changes

If you change code, rebuild the image:

```bash
# With docker-compose
docker-compose up --build

# With docker commands
docker build -t schedule-api .
docker stop schedule-api  # if running
docker rm schedule-api     # if exists
docker run -p 5001:5001 schedule-api
```

### Cleaning Up

```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove everything (be careful!)
docker system prune -a
```

## Understanding the Files

### Dockerfile
- **What it does**: Instructions for building your container
- **Think of it as**: A recipe for creating your application package

### .dockerignore
- **What it does**: Tells Docker what files to skip when building
- **Think of it as**: Like `.gitignore` but for Docker builds

### docker-compose.yml
- **What it does**: Makes it easier to run containers (optional but helpful)
- **Think of it as**: A shortcut for running docker commands

## Troubleshooting

### "Port already in use"
If port 5001 is already in use:
```bash
# Find what's using it
lsof -ti:5001

# Kill it (replace PID with the number you get)
kill -9 <PID>
```

Or change the port in `docker-compose.yml`:
```yaml
ports:
  - "5002:5001"  # Use 5002 on your computer, 5001 in container
```

### "Cannot connect to Docker daemon"
- Make sure Docker Desktop is running
- On Mac/Windows: Open Docker Desktop application

### "No such file or directory" during build
- Make sure you're in the project root directory
- Check that `data/Schedule_Historical_Data.csv` exists

### Container exits immediately
Check the logs:
```bash
docker logs schedule-api
```

## Testing the API

Once the container is running:

1. **Health check**:
   ```bash
   curl http://localhost:5001/health
   ```
   Should return: `{"status":"healthy"}`

2. **Web interface**:
   Open browser: http://localhost:5001

3. **Test assignment endpoint**:
   ```bash
   curl "http://localhost:5001/assign?schedule_detail_id=8849241&day_num=1"
   ```

## What Happens When You Build?

1. Docker reads `Dockerfile`
2. Downloads Python 3.11 base image
3. Installs dependencies from `requirements.txt`
4. Copies your code and data into the image
5. Creates a runnable container image

## What Happens When You Run?

1. Docker starts a container from the image
2. Runs `python api/app.py` inside the container
3. Flask server starts on port 5001
4. You can access it from your computer at localhost:5001

## Next Steps

- The container is now running your API
- You can access it just like when running locally
- The data file is inside the container (copied during build)
- Everything is self-contained - no need for local Python or dependencies

## Summary: Most Common Workflow

```bash
# Build and start (first time or after code changes)
docker-compose up --build

# Start (if already built)
docker-compose up

# Stop
docker-compose down

# View logs
docker-compose logs
```

That's it! You're now running your API in Docker.
