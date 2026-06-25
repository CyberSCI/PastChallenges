# ShellNet - Project Overview

## Purpose
CTF (Capture The Flag) pwn challenge for CyberSci 2026 NTL competition. "shellnet" is an intentionally vulnerable Rust binary that wraps `telnet` with shell command injection via unsanitized argument joining.

## Tech Stack
- **Language**: Rust (edition 2024)
- **Dependencies**: clap 4.6.1 (CLI parsing with derive feature)
- **Dev Environment**: devenv (Nix-based), direnv
- **Services**: busybox telnetd on port 2333

## Codebase Structure
```
server_files/
├── devenv.nix          # Nix dev environment config (telnetd, rust toolchain)
├── devenv.yaml         # devenv config
├── devenv.lock         # lockfile
├── .envrc              # direnv integration
├── .gitignore
├── secret.txt          # CTF flag file
└── shellnet/
    ├── Cargo.toml      # Rust project manifest
    ├── Cargo.lock
    └── src/
        └── main.rs     # Single source file, ~60 lines
```

## Key Vulnerability
`main.rs` joins CLI args into shell string and executes via `sh -c "telnet ..."`. Only sanitizes `-f root` literally. Susceptible to IFS-based bypass and general command injection.

## How It Works
1. Binary parses args (username, host, port)
2. Checks for `-f root` literally
3. Joins all args into string, executes `sh -c "telnet <args>"`
4. telnetd runs via busybox on port 2333
