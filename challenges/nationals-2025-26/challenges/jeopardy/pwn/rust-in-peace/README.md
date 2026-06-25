# Rust In Peace

**Author:** Willem Gooderham

**Category:** PWN

## Description

A post-apocalyptic disk management terminal running on legacy FreeDOS hardware. Players connect via telnet to a QEMU-emulated DOS system and must exploit three sequential vulnerabilities: reverse engineering an obfuscated password, triggering a buffer overflow to leak a security token, and injecting shell metacharacters to read a protected file.

The binary is a no_std Rust application compiled for i586 real-mode DOS.

### Files

- `release_files/PEACE.COM` -- DOS executable (debug-symbols build for RE analysis)
- `release_files/README.md` -- Player-facing challenge description

### Host

```
telnet <host> 7000
```

## Part 1

**CTFd name:** Rust In Peace - Vault Access

### CTFd Description

After the Great Collapse of 2087, you've discovered an abandoned Vault Overseer terminal in the wasteland. The system requires administrator credentials to access restricted areas. The authentication mechanism uses an old obfuscation technique to protect the password. Analyze the binary to recover it.

Connect: `telnet <host> 7000`

Download: `PEACE.COM`

### Depends on

None (first challenge in chain)

### Flag

<details>
<summary>(expand to read)</summary><br>

`CyberSci{SHELTER9_ADMIN_ACCESS}`

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

1. Open `PEACE.COM` in Ghidra.
2. Locate the `check_auth` function and the `process_data` XOR routine.
3. Extract the obfuscated password bytes: `[0x8D, 0xE5, 0xFB, 0xA3, 0x8A, 0xE8, 0xEC, 0xD6]`
4. Extract the XOR key: `[0xDE, 0xAD, 0xBE, 0xEF]` (repeating)
5. XOR to recover plaintext: `SHELTER9`
6. Select option 4 (Admin Login) and enter the password.

</details>

## Part 2

**CTFd name:** Rust In Peace - Classified Archives

### CTFd Description

With admin access, you can reach the classified data drives. But the most sensitive information is protected by an additional security token. The archive search function has a memory safety issue. Find a way to extract the token from the system.

### Depends on

Rust In Peace - Vault Access

### Flag

<details>
<summary>(expand to read)</summary><br>

`CyberSci{WASTELANDS_ADMIN_TOKEN}`

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

1. After admin login, select option 1 (Select Drive), then 5 (Drive F:).
2. In the F:\ directory browser, select S (Search files).
3. Enter 50+ characters (e.g., 50 A's) at the search prompt.
4. The echo function reads past the 16-byte search buffer into the adjacent flag buffer, leaking the admin token.

</details>

## Part 3

**CTFd name:** Rust In Peace - Core Memory

### CTFd Description

Armed with the admin token, you gain access to the Wasteland Command Console -- a restricted shell with limited commands. One of these commands has a flaw in how it processes user input before passing it to the system shell. Exploit it to recover the final piece of data buried deep in the file structure.

### Depends on

Rust In Peace - Classified Archives

### Flag

<details>
<summary>(expand to read)</summary><br>

`CyberSci{CORE_MEMORY_FRAGMENT_RECOVERED}`

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

1. Return to main menu, select option 5 (Command Console).
2. Enter the token from Part 2: `CyberSci{WASTELANDS_ADMIN_TOKEN}`
3. At the `WASTELAND:\>` prompt, enter: `VERIFY x | TYPE F:\SYSTEM\LOGS\CORE.DAT`
4. The VERIFY command passes unsanitized input to `COMMAND.COM /C DIR`, and the pipe metacharacter chains a TYPE command that reads the flag file.
5. Note: FreeDOS only supports `|` (pipe), not `&` for command chaining.

</details>

## Setup instructions

### Requirements

- `qemu-system-i386` (QEMU x86 emulator)
- All disk images from `server_files/`

### Quick Start

```bash
cd server_files/
qemu-system-i386 \
  -drive file=freedos.img,format=raw,if=ide,bus=0,unit=0 \
  -drive file=floppy-a.img,if=floppy,index=0,format=raw \
  -drive file=floppy-b.img,if=floppy,index=1,format=raw \
  -drive file=drive-d.img,if=ide,bus=0,unit=1,format=raw \
  -drive file=drive-e.img,if=ide,bus=1,unit=0,format=raw \
  -drive file=drive-f.img,if=ide,bus=1,unit=1,format=raw \
  -nographic \
  -serial telnet:0.0.0.0:7000,server,nowait \
  -boot c
```

### Systemd Service (Production)

1. Copy disk images to the service user's home directory.
2. Copy `rust-in-peace.service` to `~/.config/systemd/user/` (or `/etc/systemd/system/`).
3. Update image paths in the service file if needed (`%h` expands to the service user's home).
4. Enable and start:

```bash
systemctl --user enable rust-in-peace
systemctl --user start rust-in-peace
```

### Connection

```bash
telnet <host> 7000
```

The platform auto-launches on boot via FDAUTO.BAT. The system reboots automatically when a player exits, resetting state for the next session.

### Source Code

The Rust source for PEACE.EXE is in `src/`. Build requires Rust nightly with a custom i586 target. See the development repo for full build instructions.
