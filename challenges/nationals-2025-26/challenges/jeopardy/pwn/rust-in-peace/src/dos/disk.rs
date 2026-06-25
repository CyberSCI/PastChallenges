use core::arch::asm;
use crate::dos::error_code::ErrorCode;

extern crate rlibc;

/// Static DTA (Disk Transfer Area) buffer for directory operations.
/// 43 bytes as required by DOS INT 21h AH=4Eh/4Fh.
/// Static allocation ensures linker alignment and prevents segment boundary crossing.
static mut DTA_BUFFER: [u8; 43] = [0u8; 43];

/// Directory entry structure parsed from DTA buffer.
#[derive(Debug, Clone)]
pub struct DirEntry {
    /// ASCIIZ filename in 8.3 format (max 12 chars + null terminator)
    pub name: [u8; 13],
    /// True if this entry is a directory (attribute byte & 0x10)
    pub is_dir: bool,
}

/// Set the default drive.
///
/// DOS INT 21h AH=0Eh - Set Default Drive
///
/// # Arguments
/// * `drive` - Drive code (0=A:, 1=B:, 2=C:, etc.)
///
/// # Returns
/// * `Ok(num_drives)` - Number of logical drives in the system
/// * `Err(ErrorCode)` - InvalidDrive (15) if drive code invalid, DriveNotReady (21) if floppy not attached
///
/// # Example
/// ```
/// // Switch to A: drive
/// match set_drive(0) {
///     Ok(_) => println!("Switched to A:"),
///     Err(ErrorCode::DriveNotReady) => println!("Drive not ready - insert floppy"),
///     Err(e) => println!("Error: {:?}", e),
/// }
/// ```
pub fn set_drive(drive: u8) -> Result<u8, ErrorCode> {
    let num_drives: u16;
    unsafe {
        asm!(
            "mov ah, 0x0e",
            "int 0x21",
            in("dl") drive,
            lateout("ax") num_drives
        );
    }
    // INT 21h/0Eh always succeeds — verify the drive actually changed
    let actual = get_drive();
    if actual != drive {
        return Err(ErrorCode::DriveNotReady);
    }
    Ok(num_drives as u8)
}

/// Get the current default drive.
///
/// DOS INT 21h AH=19h - Get Current Default Drive
///
/// # Returns
/// Drive code (0=A:, 1=B:, 2=C:, etc.)
///
/// This function cannot fail - DOS always returns a valid drive code.
pub fn get_drive() -> u8 {
    let drive_code: u8;
    unsafe {
        asm!(
            "mov ah, 0x19",      // Function: Get current drive
            "int 0x21",          // DOS interrupt
            lateout("al") drive_code
        );
    }
    drive_code
}

/// Set the Disk Transfer Area (DTA) address.
///
/// DOS INT 21h AH=1Ah - Set Disk Transfer Area
///
/// CRITICAL: This MUST be called before find_first(). The DTA buffer is where DOS
/// writes directory entry data during find_first/find_next operations.
///
/// # Arguments
/// * `buffer` - Pointer to 43-byte buffer. MUST NOT cross 64KB segment boundary.
///
/// # Returns
/// * `Ok(())` - DTA successfully set
/// * `Err(ErrorCode)` - Error setting DTA (rare)
///
/// # Safety
/// Caller must ensure buffer is at least 43 bytes and does not cross segment boundary.
/// Use get_dta_buffer() for a safe static buffer.
pub fn set_dta(buffer: *mut u8) -> Result<(), ErrorCode> {
    let mut is_success: u16 = 1;
    let mut error_code: u16 = 0;
    unsafe {
        asm!(
            "mov ah, 0x1a",      // Function: Set DTA
            "int 0x21",          // DOS interrupt
            "setc dl",           // Set DL=1 if carry flag set (error)
            "movzx cx, dl",
            in("dx") buffer as u16,  // DTA address (offset)
            lateout("cx") is_success,
            lateout("ax") error_code
        );
    }
    if is_success == 1 {
        return Err(ErrorCode::from_u8(error_code as u8)
            .unwrap_or(ErrorCode::UnknownError));
    }
    Ok(())
}

/// Find first file matching pattern.
///
/// DOS INT 21h AH=4Eh - Find First Matching File
///
/// CRITICAL: set_dta() MUST be called before this function.
///
/// # Arguments
/// * `pattern` - File pattern (e.g., "*.*", "*.TXT", "README.*")
/// * `attributes` - File attribute mask (0x10 = include directories, 0x00 = files only)
///
/// # Returns
/// * `Ok(())` - First file found, DTA populated with entry data
/// * `Err(FileNotFound)` - No files match pattern
/// * `Err(PathNotFound)` - Invalid path in pattern
///
/// After success, call parse_dta() to extract filename and attributes from DTA buffer.
/// Call find_next() repeatedly to get remaining entries.
///
/// # Example
/// ```
/// set_dta(get_dta_buffer())?;
/// find_first("*.*", 0x10)?;  // Include directories
/// let entry = parse_dta(unsafe { &DTA_BUFFER });
/// ```
pub fn find_first(pattern: &str, attributes: u8) -> Result<(), ErrorCode> {
    // Validate pattern length (DOS PATH limit is 66 bytes, use 69 to leave room for null terminator)
    if pattern.len() >= 70 {
        return Err(ErrorCode::InvalidParameter);
    }

    // Validate no embedded null bytes (would truncate path in DOS)
    if pattern.as_bytes().contains(&0) {
        return Err(ErrorCode::InvalidParameter);
    }

    // DOS PATH length limit is 66 bytes. Use 70-byte array to ensure segment safety.
    let mut pattern_array: [u8; 70] = [0; 70];
    pattern_array[..pattern.len()].copy_from_slice(pattern.as_bytes());
    let pattern_ptr = pattern_array.as_ptr();

    let mut is_success: u16 = 1;
    let mut error_code: u16 = 0;
    unsafe {
        asm!(
            "mov ah, 0x4e",      // Function: Find first file
            "int 0x21",          // DOS interrupt
            "setc dl",           // Set DL=1 if carry flag set (error)
            "movzx cx, dl",
            in("dx") pattern_ptr as u16,      // DS:DX = ASCIIZ pattern
            in("cx") attributes as u16,       // CX = file attributes
            lateout("cx") is_success,
            lateout("ax") error_code
        );
    }
    if is_success == 1 {
        return Err(ErrorCode::from_u8(error_code as u8)
            .unwrap_or(ErrorCode::UnknownError));
    }
    Ok(())
}

/// Find next file matching previous find_first pattern.
///
/// DOS INT 21h AH=4Fh - Find Next Matching File
///
/// CRITICAL: find_first() MUST be called before this function. DOS uses search state
/// stored in DTA reserved bytes (0-20) from the previous find_first call.
///
/// # Returns
/// * `Ok(())` - Next file found, DTA populated with entry data
/// * `Err(NoMoreFiles)` - No more files match pattern (directory exhausted)
///
/// After success, call parse_dta() to extract filename and attributes from DTA buffer.
///
/// # Example
/// ```
/// loop {
///     let entry = parse_dta(unsafe { &DTA_BUFFER });
///     println!("{}", entry.name);
///
///     match find_next() {
///         Ok(_) => continue,
///         Err(ErrorCode::NoMoreFiles) => break,
///         Err(e) => return Err(e),
///     }
/// }
/// ```
pub fn find_next() -> Result<(), ErrorCode> {
    let mut is_success: u16 = 1;
    let mut error_code: u16 = 0;
    unsafe {
        asm!(
            "mov ah, 0x4f",      // Function: Find next file
            "int 0x21",          // DOS interrupt
            "setc dl",           // Set DL=1 if carry flag set (error)
            "movzx cx, dl",
            lateout("cx") is_success,
            lateout("ax") error_code
        );
    }
    if is_success == 1 {
        return Err(ErrorCode::from_u8(error_code as u8)
            .unwrap_or(ErrorCode::UnknownError));
    }
    Ok(())
}

/// Change current directory.
///
/// DOS INT 21h AH=3Bh - Set Current Directory
///
/// # Arguments
/// * `path` - Directory path (e.g., "SUBDIR", "..", "\\ROOT", "A:\\DOCS")
///
/// # Returns
/// * `Ok(())` - Directory changed successfully
/// * `Err(PathNotFound)` - Directory does not exist
///
/// NOTE: DOS silently ignores chdir("..") at root directory (stays at root, no error).
/// Each drive maintains its own current directory - changing directory on A: does not
/// affect the current directory on C:.
///
/// # Example
/// ```
/// chdir("DOCS")?;       // Enter subdirectory
/// chdir("..")?;         // Go up one level (silent no-op at root)
/// chdir("\\ROOT")?;     // Absolute path from root
/// ```
pub fn chdir(path: &str) -> Result<(), ErrorCode> {
    // Validate path length (DOS PATH limit is 66 bytes, use 69 to leave room for null terminator)
    if path.len() >= 70 {
        return Err(ErrorCode::InvalidParameter);
    }

    // Validate no embedded null bytes (would truncate path in DOS)
    if path.as_bytes().contains(&0) {
        return Err(ErrorCode::InvalidParameter);
    }

    let mut path_array: [u8; 70] = [0; 70];
    path_array[..path.len()].copy_from_slice(path.as_bytes());
    let path_ptr = path_array.as_ptr();

    let mut is_success: u16 = 1;
    let mut error_code: u16 = 0;
    unsafe {
        asm!(
            "mov ah, 0x3b",      // Function: Change directory
            "int 0x21",          // DOS interrupt
            "setc dl",           // Set DL=1 if carry flag set (error)
            "movzx cx, dl",
            in("dx") path_ptr as u16,  // DS:DX = ASCIIZ path
            lateout("cx") is_success,
            lateout("ax") error_code
        );
    }
    if is_success == 1 {
        return Err(ErrorCode::from_u8(error_code as u8)
            .unwrap_or(ErrorCode::UnknownError));
    }
    Ok(())
}

/// Parse DTA buffer into DirEntry structure.
///
/// NOT a DOS interrupt - pure Rust function to extract data from DTA.
///
/// # DTA Layout (43 bytes)
/// * Bytes 0-20: Reserved for DOS (search state - DO NOT MODIFY)
/// * Byte 21: File attributes (0x10 = directory, 0x20 = archive, etc.)
/// * Bytes 22-25: File time/date (ignored)
/// * Bytes 26-29: File size (ignored)
/// * Bytes 30-42: ASCIIZ filename (null-terminated 8.3 format, max 12 chars)
///
/// # Arguments
/// * `dta` - Reference to 43-byte DTA buffer populated by find_first/find_next
///
/// # Returns
/// DirEntry with filename and directory flag extracted from DTA
///
/// # Example
/// ```
/// find_first("*.*", 0x10)?;
/// let entry = parse_dta(unsafe { &DTA_BUFFER });
/// if entry.is_dir {
///     println!("{} <DIR>", core::str::from_utf8(&entry.name).unwrap());
/// }
/// ```
pub fn parse_dta(dta: &[u8; 43]) -> DirEntry {
    let attr = dta[21];
    let is_dir = (attr & 0x10) != 0; // Directory bit

    let mut name = [0u8; 13];
    for i in 0..13 {
        let byte = dta[30 + i];
        if byte == 0 { break; } // Null terminator
        name[i] = byte;
    }

    DirEntry { name, is_dir }
}

/// Get pointer to static DTA buffer.
///
/// Returns a pointer to the static DTA_BUFFER for use with set_dta().
/// This buffer is linker-aligned and guaranteed not to cross segment boundaries.
///
/// # Returns
/// Raw mutable pointer to 43-byte static DTA buffer
///
/// # Safety
/// Caller must not create multiple mutable references to the buffer.
/// Use only with set_dta() and parse_dta().
///
/// # Example
/// ```
/// set_dta(get_dta_buffer())?;
/// find_first("*.*", 0x10)?;
/// let entry = parse_dta(unsafe { &DTA_BUFFER });
/// ```
pub fn get_dta_buffer() -> *mut u8 {
    unsafe { DTA_BUFFER.as_mut_ptr() }
}

/// Get safe reference to static DTA buffer.
///
/// Returns a reference to the static DTA_BUFFER for safe parsing after
/// find_first/find_next operations. This eliminates unsafe slice creation
/// from raw pointers.
///
/// # Returns
/// Static reference to 43-byte DTA buffer
///
/// # Safety
/// Safe to call. Caller must ensure DTA has been populated by a successful
/// find_first/find_next call before parsing.
///
/// # Example
/// ```
/// set_dta(get_dta_buffer())?;
/// find_first("*.*", 0x10)?;
/// let entry = parse_dta(get_dta_buffer_ref());
/// ```
pub fn get_dta_buffer_ref() -> &'static [u8; 43] {
    unsafe { &DTA_BUFFER }
}
