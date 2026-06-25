# Task Completion Checklist: deployment_hell

## When completing any coding task, do the following:

1. **Check files are in the right directories:**
   - Player-facing files → `release_files/`
   - Server/setup files → `server_files/`
   - Solve scripts/hints → `solve_files/`

2. **Keep README.md updated:**
   - Fill in challenge name, author, category, description
   - Document files to attach
   - Document host/connection info
   - Add flag(s) in `<details>` blocks
   - Write walkthrough
   - Write complete setup instructions

3. **Docker Compose validation (once implemented):**
   ```bash
   docker compose config   # validate config syntax
   docker compose up --build -d  # verify it starts clean
   docker compose logs     # check for errors
   docker compose down     # clean up
   ```

4. **Git:**
   ```bash
   git status
   git diff
   git add .
   git commit -m "descriptive message"
   ```

5. **No automated linting/testing pipeline exists yet.**
   Add this section when a build system is introduced.
