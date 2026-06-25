# Suggested Commands: deployment_hell

## Git
```bash
git status
git diff
git log --oneline -20
git add .
git commit -m "message"
git push
```

## Docker Compose (once implemented)
```bash
# Build and start the challenge environment
docker compose up --build -d

# Stop the challenge environment
docker compose down

# View logs
docker compose logs -f
```

## File Navigation
```bash
ls -la
find . -type f
cat README.md
```

## No build/test/lint commands exist yet
The challenge has no source code yet. Commands will be added once Jenkins/Docker setup is implemented.

## Running the Challenge (planned)
Once the Docker Compose setup is complete:
```bash
cd server_files/
docker compose up --build -d
```

## Notes
- Ubuntu VM required with sufficient compute for Docker Compose
- Jenkins will be the primary service, likely exposed on port 8080
