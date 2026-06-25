# Project Structure: deployment_hell

## Directory Layout
```
deployment_hell/
├── README.md                  # Challenge README (template/placeholder — not yet filled in)
├── release_files/
│   └── sample.txt             # Files to provide to CTF players (placeholder)
├── server_files/
│   └── secret.txt             # Server-side / setup files, NOT shared with players (placeholder)
├── solve_files/
│   └── solve.txt              # Solve script/instructions for testers (placeholder)
└── .serena/
    ├── project.yml            # Serena config: language=python, encoding=utf-8
    ├── project.local.yml
    └── memories/              # Serena memory files (this directory)
```

## Standard Challenge Template Convention
All challenge directories in this repo follow this structure:
- `README.md` — challenge description, flags, walkthrough, setup instructions
- `release_files/` — artefacts handed to CTF players
- `server_files/` — server config/setup files (private)
- `solve_files/` — solve scripts/hints (for testers/organizers)

## What Needs to Be Built
The challenge itself (Jenkins/CI/CD server with vulnerabilities) still needs to be implemented:
- Docker Compose setup in `server_files/`
- Any player-facing files (e.g., Jenkinsfile, config snippets) in `release_files/`
- Solve script in `solve_files/`
- Completed `README.md` with actual flag(s), description, and setup instructions
