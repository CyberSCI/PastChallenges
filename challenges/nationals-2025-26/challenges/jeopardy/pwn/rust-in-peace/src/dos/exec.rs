use core::arch::asm;
use crate::dos::error_code::ErrorCode;

extern crate rlibc;

/// Saved stack segment register. DOS EXEC destroys SS:SP, must restore after return.
/// Static storage in code segment ensures this memory is never deallocated.
static mut STK_SEG: u16 = 0;

/// Saved stack pointer register. DOS EXEC destroys SS:SP, must restore after return.
static mut STK_PTR: u16 = 0;

/// Parameter block for INT 21h/AH=4Bh/AL=00h (Load and Execute Program).
/// Must be in C layout for DOS compatibility.
#[repr(C)]
struct ExecParamBlock {
    env_seg: u16,        // +00h: Environment segment (0 = copy parent)
    cmd_offset: u16,     // +02h: Command line offset
    cmd_seg: u16,        // +04h: Command line segment
    fcb1_offset: u16,    // +06h: First FCB offset (use 0xFFFF = unused)
    fcb1_seg: u16,       // +08h: First FCB segment (use 0xFFFF)
    fcb2_offset: u16,    // +0Ah: Second FCB offset (use 0xFFFF = unused)
    fcb2_seg: u16,       // +0Ch: Second FCB segment (use 0xFFFF)
}

/// Execute a DOS program via INT 21h/AH=4Bh (EXEC/Load and Execute).
///
/// Spawns the program at `program_path`, gives it control, and returns when it exits.
/// DOS destroys all registers including SS:SP during EXEC — this function saves and
/// restores the stack to ensure safe return-to-caller.
///
/// # Arguments
/// * `program_path` - DOS path to executable (e.g., "C:\\COMMAND.COM"). Must be < 70 bytes.
///
/// # Returns
/// * `Ok(())` if program executed and exited normally
/// * `Err(ErrorCode)` if EXEC failed (file not found, insufficient memory, etc.)
///
/// # Safety
/// This function uses unsafe inline assembly to invoke DOS interrupts and manipulate
/// stack registers (SS:SP). Stack restoration uses CLI/STI to prevent interrupt-driven
/// corruption during the multi-instruction restore sequence.
///
/// # DOS Interrupt
/// INT 21h/AH=4Bh/AL=00h (Load and Execute Program)
/// * DS:DX = ASCIIZ program path
/// * ES:BX = Parameter block pointer
/// * Returns: CF=1 on error (AX=error code), CF=0 on success
///
/// # Example
/// ```
/// // Spawn COMMAND.COM and wait for user to exit
/// match dos::exec::exec("C:\\COMMAND.COM") {
///     Ok(()) => println!("Shell exited normally"),
///     Err(ErrorCode::FileNotFound) => println!("COMMAND.COM not found"),
///     Err(ErrorCode::InsufficientMemory) => println!("Not enough memory to spawn process"),
///     Err(e) => println!("EXEC failed: {:?}", e),
/// }
/// ```
pub fn exec(program_path: &str) -> Result<(), ErrorCode> {
    // Validate path length (DOS PATH limit is 66 bytes, use 70 for null terminator + safety)
    if program_path.len() >= 70 {
        return Err(ErrorCode::InvalidParameter);
    }

    // Validate no embedded null bytes (would truncate path in DOS ASCIIZ format)
    if program_path.as_bytes().contains(&0) {
        return Err(ErrorCode::InvalidParameter);
    }

    // Convert Rust string to DOS ASCIIZ format (null-terminated)
    let mut path_buf: [u8; 70] = [0; 70];
    let path_bytes = program_path.as_bytes();
    let copy_len = core::cmp::min(path_bytes.len(), 69);
    path_buf[..copy_len].copy_from_slice(&path_bytes[..copy_len]);
    // path_buf[copy_len] is already 0 (null terminator)

    // DOS command line format: [count][space][args...][CR]
    // For no arguments: count=1, space=0x20, CR=0x0D
    let mut cmd_line: [u8; 128] = [0; 128];
    cmd_line[0] = 1;      // Length: 1 (just the space)
    cmd_line[1] = b' ';   // Required space for COMMAND.COM compatibility
    cmd_line[2] = 0x0D;   // Carriage return

    // Get current data segment — cmd_line is stack-allocated, SS=DS in COM model
    let cmd_ds: u16;
    unsafe {
        asm!("mov {0}, ds", out(reg) cmd_ds, options(nostack, nomem));
    }

    // Setup parameter block for AL=00h (load and execute)
    let params = ExecParamBlock {
        env_seg: 0,                          // 0 = copy parent environment
        cmd_offset: cmd_line.as_ptr() as u16,
        cmd_seg: cmd_ds,                     // Actual DS — segment 0 would point to IVT
        fcb1_offset: 0xFFFF,                 // Unused FCB
        fcb1_seg: 0xFFFF,
        fcb2_offset: 0xFFFF,                 // Unused FCB
        fcb2_seg: 0xFFFF,
    };

    let mut error_code: u16 = 0;
    let mut is_error: u16 = 0;

    unsafe {
        // Save stack registers to statics BEFORE INT 21h (DOS destroys SS:SP!)
        asm!("mov word ptr [{0}], ss", in(reg) &STK_SEG as *const _ as u16, options(nostack));
        asm!("mov word ptr [{0}], sp", in(reg) &STK_PTR as *const _ as u16, options(nostack));

        // Call DOS EXEC (AL=00h: load and execute)
        asm!(
            "mov ax, 0x4B00",    // AH=4Bh (EXEC), AL=00h (load and execute)
            "int 0x21",          // DOS interrupt
            "setc dl",           // Capture carry flag (error indicator)
            "movzx cx, dl",      // Zero-extend to CX for lateout
            in("dx") path_buf.as_ptr() as u16,     // DS:DX = program path
            in("bx") &params as *const _ as u16,   // ES:BX = param block
            lateout("cx") is_error,
            lateout("ax") error_code,
            options(nostack)
        );

        // Restore stack (with interrupts disabled during restoration)
        // CLI/STI sequence prevents interrupt between SS and SP loads (critical!)
        asm!("cli", options(nostack));                                              // Disable interrupts
        asm!("mov ss, word ptr [{0}]", in(reg) &STK_SEG as *const _ as u16, options(nostack));  // Restore SS
        asm!("mov sp, word ptr [{0}]", in(reg) &STK_PTR as *const _ as u16, options(nostack));  // Restore SP
        asm!("sti", options(nostack));                                              // Re-enable interrupts
    }

    if is_error == 1 {
        return Err(ErrorCode::from_u8(error_code as u8)
            .unwrap_or(ErrorCode::UnknownError));
    }

    Ok(())
}

/// Execute a DOS program with arguments via INT 21h/AH=4Bh (EXEC/Load and Execute).
///
/// Spawns the program at `program_path` with command-line arguments, gives it control,
/// and returns when it exits. Arguments are passed via DOS command tail at PSP offset 80h.
/// DOS destroys all registers including SS:SP during EXEC — this function saves and
/// restores the stack to ensure safe return-to-caller.
///
/// # Arguments
/// * `program_path` - DOS path to executable (e.g., "C:\\COMMAND.COM"). Must be < 70 bytes.
/// * `args` - Command-line arguments (e.g., "/C VER"). Must be < 126 bytes.
///
/// # Returns
/// * `Ok(())` if program executed and exited normally
/// * `Err(ErrorCode::InvalidParameter)` if path > 70 bytes or args > 125 bytes
/// * `Err(ErrorCode)` if EXEC failed (file not found, insufficient memory, etc.)
///
/// # Safety
/// This function uses unsafe inline assembly to invoke DOS interrupts and manipulate
/// stack registers (SS:SP). Stack restoration uses CLI/STI to prevent interrupt-driven
/// corruption during the multi-instruction restore sequence.
///
/// # DOS Command Tail Format
/// [count_byte][space][args...][CR]
/// - count_byte = 1 (space) + args.len() — includes space, EXCLUDES CR
/// - CR terminator at position count + 1, NOT count
/// - Maximum safe args length: 125 characters
///
/// # Example
/// ```
/// // Spawn COMMAND.COM to execute VER command
/// match dos::exec::exec_with_args("C:\\COMMAND.COM", "/C VER") {
///     Ok(()) => println!("Command executed"),
///     Err(ErrorCode::InvalidParameter) => println!("Arguments too long"),
///     Err(e) => println!("EXEC failed: {:?}", e),
/// }
/// ```
pub fn exec_with_args(program_path: &str, args: &str) -> Result<(), ErrorCode> {
    // Validate path length (DOS PATH limit is 66 bytes, use 70 for null terminator + safety)
    if program_path.len() >= 70 {
        return Err(ErrorCode::InvalidParameter);
    }

    // Validate no embedded null bytes (would truncate path in DOS ASCIIZ format)
    if program_path.as_bytes().contains(&0) {
        return Err(ErrorCode::InvalidParameter);
    }

    // Validate argument length: max 125 chars (1 space + 125 args + 1 CR = 127 bytes total)
    if args.len() > 125 {
        return Err(ErrorCode::InvalidParameter);
    }

    // Convert Rust string to DOS ASCIIZ format (null-terminated)
    let mut path_buf: [u8; 70] = [0; 70];
    let path_bytes = program_path.as_bytes();
    let copy_len = core::cmp::min(path_bytes.len(), 69);
    path_buf[..copy_len].copy_from_slice(&path_bytes[..copy_len]);
    // path_buf[copy_len] is already 0 (null terminator)

    // DOS command line format: [count][space][args...][CR]
    // Count includes space, excludes CR
    let mut cmd_line: [u8; 128] = [0; 128];

    if args.is_empty() {
        // No arguments case
        cmd_line[0] = 1;      // Count: 1 (just the space)
        cmd_line[1] = b' ';   // Mandatory space
        cmd_line[2] = 0x0D;   // CR
    } else {
        // Arguments provided
        let count = 1 + args.len();  // Space + args length
        cmd_line[0] = count as u8;
        cmd_line[1] = b' ';

        // Copy argument string
        let args_bytes = args.as_bytes();
        cmd_line[2..(2 + args.len())].copy_from_slice(args_bytes);

        // Terminate with CR at position count + 1 (NOT count!)
        cmd_line[count + 1] = 0x0D;
    }

    // Get current data segment — cmd_line is stack-allocated, SS=DS in COM model
    let cmd_ds: u16;
    unsafe {
        asm!("mov {0}, ds", out(reg) cmd_ds, options(nostack, nomem));
    }

    // Setup parameter block for AL=00h (load and execute)
    let params = ExecParamBlock {
        env_seg: 0,                          // 0 = copy parent environment
        cmd_offset: cmd_line.as_ptr() as u16,
        cmd_seg: cmd_ds,                     // Actual DS — segment 0 would point to IVT
        fcb1_offset: 0xFFFF,                 // Unused FCB
        fcb1_seg: 0xFFFF,
        fcb2_offset: 0xFFFF,                 // Unused FCB
        fcb2_seg: 0xFFFF,
    };

    let mut error_code: u16 = 0;
    let mut is_error: u16 = 0;

    unsafe {
        // Save stack registers to statics BEFORE INT 21h (DOS destroys SS:SP!)
        asm!("mov word ptr [{0}], ss", in(reg) &STK_SEG as *const _ as u16, options(nostack));
        asm!("mov word ptr [{0}], sp", in(reg) &STK_PTR as *const _ as u16, options(nostack));

        // Call DOS EXEC (AL=00h: load and execute)
        asm!(
            "mov ax, 0x4B00",    // AH=4Bh (EXEC), AL=00h (load and execute)
            "int 0x21",          // DOS interrupt
            "setc dl",           // Capture carry flag (error indicator)
            "movzx cx, dl",      // Zero-extend to CX for lateout
            in("dx") path_buf.as_ptr() as u16,     // DS:DX = program path
            in("bx") &params as *const _ as u16,   // ES:BX = param block
            lateout("cx") is_error,
            lateout("ax") error_code,
            options(nostack)
        );

        // Restore stack (with interrupts disabled during restoration)
        // CLI/STI sequence prevents interrupt between SS and SP loads (critical!)
        asm!("cli", options(nostack));                                              // Disable interrupts
        asm!("mov ss, word ptr [{0}]", in(reg) &STK_SEG as *const _ as u16, options(nostack));  // Restore SS
        asm!("mov sp, word ptr [{0}]", in(reg) &STK_PTR as *const _ as u16, options(nostack));  // Restore SP
        asm!("sti", options(nostack));                                              // Re-enable interrupts
    }

    if is_error == 1 {
        return Err(ErrorCode::from_u8(error_code as u8)
            .unwrap_or(ErrorCode::UnknownError));
    }

    Ok(())
}
