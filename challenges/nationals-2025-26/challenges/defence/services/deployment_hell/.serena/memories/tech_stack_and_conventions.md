# Tech Stack & Conventions: deployment_hell

## Planned Tech Stack
- **CI/CD server:** Jenkins (likely)
- **Infrastructure:** Docker Compose on Ubuntu VM
- **Challenge type:** Defence (find and patch/exploit vulnerabilities in a deployed service)

## Serena Project Config
- **Languages:** Python (as configured in `.serena/project.yml`)
- **Encoding:** UTF-8
- **Line endings:** not specified (platform default)

## Repository Conventions (from challenge_template and sibling challenges)
- README follows a fixed template: challenge name, author, category, description, files, host, flag(s), walkthrough, setup instructions
- Flags are hidden in `<details>` collapsible blocks in README
- Multiple flags/parts are each a separate CTFd challenge entry
- Docker Compose is the standard deployment mechanism for server-side challenges

## Code Style Notes
- No Python source code exists yet; once written, follow PEP 8
- No explicit linting/formatting tools configured at this time
