# Suggested Commands

## Build
```bash
cargo build                  # Debug build
cargo build --release        # Release build
```
Working directory: `shellnet/`

## Run
```bash
cargo run -- --username user --host localhost --port 2333
./target/debug/shellnet --username user --host localhost --port 2333
```

## Dev Environment
```bash
devenv up          # Start telnetd + all processes
devenv shell       # Enter dev shell with rust toolchain
```

## Testing
```bash
cargo test         # Run tests (none currently)
cargo clippy       # Lint
cargo fmt          # Format
cargo fmt --check  # Check formatting
```

## System Utils
```bash
git, ls, grep, find  # Standard Linux utils
```
