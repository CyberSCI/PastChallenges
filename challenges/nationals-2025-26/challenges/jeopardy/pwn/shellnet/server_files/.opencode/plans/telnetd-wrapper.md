# Plan: Replace shellnet with telnetd login wrapper

## Goal
Replace current `shellnet` (telnet client wrapper with CLI arg injection) with a telnetd **login program** wrapper that sanitizes the `USER` env var. Literal `-f root` blocked; IFS-encoded bypasses pass through (intended CTF solve).

## Architecture
```
telnetd -b 0.0.0.0:2333 -l /path/to/shellnet
```
Per connection: telnetd execs shellnet → shellnet checks USER env → execs `/bin/sh -l`.

## Changes

### 1. `shellnet/src/main.rs` — Full rewrite

Replace entire file with:

```rust
use std::env;
use std::os::unix::process::CommandExt;
use std::process::{exit, Command};

fn main() {
    if let Ok(user) = env::var("USER") {
        if user.contains("-f root") {
            eprintln!("Error: -f root is not allowed in USER");
            exit(1);
        }
    }

    let err = Command::new("/bin/sh")
        .arg("-l")
        .exec();

    eprintln!("Failed to exec shell: {}", err);
    exit(1);
}
```

Key points:
- `exec()` replaces process (Unix-only, uses `std::os::unix::process::CommandExt`)
- `user.contains("-f root")` — literal substring only, no regex
- IFS bypasses like `-f${IFS}root` pass through because shell hasn't expanded them in env context
- No CLI args, no clap needed

### 2. `shellnet/Cargo.toml` — Remove clap

Replace:
```toml
[dependencies]
clap = { version = "4.6.1", features = ["derive"] }
```
With:
```toml
[dependencies]
```

### 3. `devenv.nix` — Update telnetd to use shellnet as login program

Line 39, change:
```nix
${binary} -b ${bind}:${builtins.toString port} -l bash
```
To:
```nix
${binary} -b ${bind}:${builtins.toString port} -l ${shellnet}/bin/shellnet
```

This makes telnetd exec shellnet per connection instead of bash directly.

## Verification
1. `cargo build` in `shellnet/` — should compile with zero deps
2. `devenv up` — telnetd starts with shellnet as login program
3. `telnet localhost 2333` — should get shell
4. Set `USER="-f root"` → connection rejected
5. Set `USER="-f${IFS}root"` → connection allowed (CTF solve path)
