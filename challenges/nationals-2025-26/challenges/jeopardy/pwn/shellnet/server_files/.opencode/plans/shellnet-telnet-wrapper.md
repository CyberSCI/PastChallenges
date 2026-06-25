# ShellNet — Rust Telnet Client Wrapper (CTF Pwn Challenge)

## Goal

Rust binary wraps busybox `telnet` client. Sanitizes `-f root` but intentionally uses `sh -c` for invocation, leaving IFS-based command injection exploitable.

## Architecture

```
User → shellnet (Rust binary) → sh -c "busybox telnet <args>" → busybox telnet → remote host
```

## Implementation (`src/main.rs`)

1. **Parse CLI args** — Collect all args passed to wrapper (`std::env::args().skip(1)`)
2. **Sanitize `-f root`** — Scan args for `-f` followed by `root`; reject/strip if found. Only block `root`, allow other users.
3. **Build shell command string** — Join args into single string (this is the intentional vuln — no proper escaping)
4. **Invoke via `sh -c`** — Use `std::process::Command::new("sh").args(["-c", &format!("busybox telnet {}", args_string)])`
5. **Forward exit code** — Propagate child process exit status

## Key Details

- **Busybox path:** Use `busybox telnet` (busybox in PATH via nix)
- **Sanitization flaw:** Only checks literal string `-f root` in args. IFS manipulation (e.g., setting `IFS` in env or using `$IFS` in arg) bypasses the check since shell splits differently than Rust string matching
- **No deps needed** — stdlib only (`std::process`, `std::env`)

## Code Sketch

```rust
use std::env;
use std::process::{Command, exit};

fn main() {
    let args: Vec<String> = env::args().skip(1).collect();

    // Sanitize: block -f root
    let mut i = 0;
    while i < args.len() {
        if args[i] == "-f" {
            if let Some(user) = args.get(i + 1) {
                if user == "root" {
                    eprintln!("Error: -f root is not allowed");
                    exit(1);
                }
            }
            i += 2;
        } else {
            i += 1;
        }
    }

    // Intentionally vulnerable: join args and pass through shell
    let args_string = args.join(" ");
    let cmd = format!("telnet {}", args_string);

    let status = Command::new("sh")
        .arg("-c")
        .arg(&cmd)
        .status()
        .expect("Failed to execute shell");

    exit(status.code().unwrap_or(1));
}
```

## Exploit Path (CTF Context)

Player can inject commands via IFS manipulation in arguments since wrapper passes raw args through `sh -c` without proper escaping. The `-f root` check only matches literal string comparison in Rust, easily bypassed by shell tricks.
