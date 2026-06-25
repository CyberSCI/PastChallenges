# Task Completion Checklist

After completing a task:
1. `cargo build` — ensure it compiles
2. `cargo fmt --check` — check formatting
3. `cargo clippy` — check lints
4. `cargo test` — run tests (if any exist)

No CI/CD pipeline detected. No pre-commit hooks configured (commented out in devenv.nix).
