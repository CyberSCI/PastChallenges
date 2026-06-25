#![no_std]
#![no_main]

extern crate alloc;

use rust_dos::*;
use alloc::string::String;
use alloc::vec::Vec;
use rust_dos::dos::error_code::ErrorCode;
use rust_dos::dos::disk::DirEntry;

entry!(main);

struct DiskState {
    current_drive: Option<u8>,  // 0=A:, 1=B:, 2=C:, None=default (C:)
    is_admin: bool,
}

static mut DISK_STATE: DiskState = DiskState {
    current_drive: None,  // Start at C: drive (DOS default)
    is_admin: false,
};

const DISK_BUFFER_SIZE: usize = 2048;
static mut DISK_BUFFER_POOL: [u8; DISK_BUFFER_SIZE] = [0u8; DISK_BUFFER_SIZE];
static mut BUFFER_IN_USE: bool = false;

const CODEC_SEED: [u8; 4] = [0xDE, 0xAD, 0xBE, 0xEF];
const AUTH_SIZE: usize = 8;

const STORED_KEY: [u8; AUTH_SIZE] = [
    0x8D, 0xE5, 0xFB, 0xA3, 0x8A, 0xE8, 0xEC, 0xD6
];

#[repr(C)]
struct DataBlock {
    search_buffer: [u8; 16],
    archive_data: [u8; 64],
    padding: [u8; 176],
}


#[inline(always)]
fn get_state() -> &'static mut DiskState {
    unsafe { &mut DISK_STATE }
}

#[inline(never)]
fn acquire_disk_buffer() -> Option<&'static mut [u8]> {
    unsafe {
        if BUFFER_IN_USE {
            return None;
        }
        BUFFER_IN_USE = true;
        Some(&mut DISK_BUFFER_POOL)
    }
}

#[inline(never)]
fn release_disk_buffer() {
    unsafe {
        debug_assert!(BUFFER_IN_USE, "Attempted to release buffer that wasn't acquired");
        DISK_BUFFER_POOL.fill(0);
        BUFFER_IN_USE = false;
    }
}


fn main() {
    dos::console::disable_ctrl_break();
    
    show_intro();
    main_menu_loop();
}

fn show_intro() {
    clear_screen();
    println!("===========================================================");
    println!("|                    RUST IN PEACE                       |");
    println!("|             Post-Apocalyptic Disk Manager              |");
    println!("===========================================================");
    println!("");
    println!("After the Great Collapse of 2087, only legacy systems");
    println!("remain functional. You are the Last Archivist, keeper");
    println!("of humanity's digital remnants stored on ancient disks.");
    println!("");
    println!("Your mission: Explore floppy disks and recover data");
    println!("from the wasteland's forgotten archives.");
    println!("");
    println!("");
    println!("Press any key to enter the main terminal...");
    dos::console::readc();
}

fn clear_screen() {
    for _ in 0..25 {
        println!("");
    }
}

fn main_menu_loop() {
    loop {
        show_main_menu();
        let choice = get_user_input();
        
        if choice.is_empty() {
            continue; // Redraw menu on empty input
        }
        
        match choice.as_str() {
            "1" => drive_select_menu(),
            "2" => unmount_drive(),
            "3" => show_system_status(),
            "4" => admin_login(),
            "5" => command_console(),
            _ => {
                println!("");
                println!("ERROR: Invalid command detected.");
                println!("The system recognizes only commands 1, 2, 3, 4, or 5.");
                println!("");
                println!("Press any key to continue...");
                dos::console::readc();
            }
        }
    }
}

fn show_main_menu() {
    clear_screen();
    println!("+-----------------------------------------------------------+");
    println!("|              RUST IN PEACE - MAIN TERMINAL             |");
    println!("+-----------------------------------------------------------+");
    
    let state = get_state();
    match state.current_drive {
        Some(drive) => {
            let drive_letter = (b'A' + drive) as char;
            println!("| STATUS: DRIVE {}: ACTIVE", drive_letter);
        }
        None => {
            println!("| STATUS: DRIVE C: ACTIVE (DEFAULT)");
        }
    }
    
    if state.is_admin {
        println!("| ACCESS LEVEL: ADMINISTRATOR");
    } else {
        println!("| ACCESS LEVEL: STANDARD USER");
    }
    
    println!("+-----------------------------------------------------------+");
    println!("|                                                         |");
    println!("|  [1] SELECT DRIVE - Browse floppy disk contents        |");
    println!("|  [2] UNMOUNT DRIVE - Return to C: drive                |");
    println!("|  [3] SYSTEM INFO  - View terminal diagnostics          |");
    println!("|  [4] ADMIN LOGIN  - Authenticate as administrator      |");
    println!("|  [5] COMMAND CONSOLE - Administrative command shell      |");
    println!("|                                                         |");
    println!("+-----------------------------------------------------------+");
    println!("");
    print!("ARCHIVIST> Enter command: ");
}

fn drive_select_menu() {
    loop {
        clear_screen();
        println!("===========================================================");
        println!("                    SELECT DRIVE");
        println!("===========================================================");
        println!("");
        println!("[1] Drive A: (Floppy 1)");
        println!("[2] Drive B: (Floppy 2)");
        println!("[3] Drive D: (IDE Drive 1)");
        println!("[4] Drive E: (IDE Drive 2)");
        if get_state().is_admin {
            println!("[5] Drive F: (IDE Drive 3)");
        }
        println!("[0] Cancel - Return to main menu");
        println!("");
        print!("ARCHIVIST> Select drive: ");

        let choice = get_user_input();

        match choice.as_str() {
            "1" => {
                if try_mount_drive(0) {  // 0 = A:
                    browse_directory(0);
                }
            }
            "2" => {
                if try_mount_drive(1) {  // 1 = B:
                    browse_directory(1);
                }
            }
            "3" => {
                if try_mount_drive(3) {  // 3 = D:
                    browse_directory(3);
                }
            }
            "4" => {
                if try_mount_drive(4) {  // 4 = E:
                    browse_directory(4);
                }
            }
            "5" => {
                if !get_state().is_admin {
                    println!("");
                    println!("===========================================================");
                    println!("|                    ACCESS DENIED                       |");
                    println!("|         RESTRICTED AREA - ADMIN CLEARANCE REQUIRED    |");
                    println!("===========================================================");
                    println!("");
                    println!("Press any key to continue...");
                    dos::console::readc();
                    continue;  // Return to drive selection menu
                }

                if try_mount_drive(5) {  // 5 = F:
                    browse_directory(5);
                }
            }
            "0" => return,
            _ => {
                println!("");
                println!("ERROR: Invalid selection. Choose 1-5 or 0.");
                println!("Press any key to continue...");
                dos::console::readc();
            }
        }
    }
}

fn try_mount_drive(drive: u8) -> bool {
    loop {
        match dos::disk::set_drive(drive) {
            Ok(_) => {
                // Initialize DTA before any find operations
                unsafe {
                    if let Err(e) = dos::disk::set_dta(dos::disk::get_dta_buffer()) {
                        println!("");
                        println!("Error initializing DTA: {}", e.as_str());
                        println!("Press any key to continue...");
                        dos::console::readc();
                        return false;
                    }
                }
                let state = get_state();
                state.current_drive = Some(drive);
                return true;  // Success
            }
            Err(ErrorCode::DriveNotReady) => {
                let drive_letter = (b'A' + drive) as char;
                println!("");
                println!("Drive {}: not ready", drive_letter);
                println!("Ensure floppy image is attached via QEMU.");
                println!("");
                println!("[R] Retry / [Q] Cancel");
                print!("Your choice: ");

                let choice = dos::console::readc();
                println!("");  // Newline after single-char input

                if choice == b'Q' || choice == b'q' {
                    return false;  // User cancelled
                }
                // Loop continues for retry
            }
            Err(e) => {
                println!("");
                println!("Error accessing drive: {}", e.as_str());
                println!("Press any key to continue...");
                dos::console::readc();
                return false;
            }
        }
    }
}

fn browse_directory(drive: u8) {
    let drive_letter = (b'A' + drive) as char;

    loop {
        clear_screen();

        println!("===========================================================");
        println!("                 DIRECTORY LISTING");
        println!("===========================================================");
        println!("");
        println!("Current location: {}:\\", drive_letter);
        println!("");

        // Collect directory entries (find_first + find_next loop)
        let mut entries: Vec<DirEntry> = Vec::new();

        match dos::disk::find_first("*.*", 0x10) {  // 0x10 = include directories
            Ok(_) => {
                // Parse first entry using safe accessor
                let dta_array = *dos::disk::get_dta_buffer_ref();
                entries.push(dos::disk::parse_dta(&dta_array));

                // Continue with find_next
                loop {
                    match dos::disk::find_next() {
                        Ok(_) => {
                            let dta_array = *dos::disk::get_dta_buffer_ref();
                            entries.push(dos::disk::parse_dta(&dta_array));
                        }
                        Err(ErrorCode::NoMoreFiles) => break,
                        Err(e) => {
                            println!("Error reading directory: {}", e.as_str());
                            dos::console::readc();
                            return;
                        }
                    }
                }
            }
            Err(ErrorCode::FileNotFound) => {
                // Empty directory
            }
            Err(e) => {
                println!("Error accessing directory: {}", e.as_str());
                println!("Press any key to return...");
                dos::console::readc();
                return;
            }
        }

        const ENTRIES_PER_PAGE: usize = 15;
        let total_entries = entries.len();
        let mut page_offset = 0;

        loop {
            clear_screen();
            println!("===========================================================");
            println!("            {}:\\ - DIRECTORY BROWSER", drive_letter);
            println!("===========================================================");
            println!("");

            println!("[..]  Parent Directory");
            println!("");

            let page_end = core::cmp::min(page_offset + ENTRIES_PER_PAGE, total_entries);
            for i in page_offset..page_end {
                let entry = &entries[i];
                let entry_num = i + 1;

                // Convert name bytes to string (stop at null terminator)
                let mut name_str = String::new();
                for &byte in &entry.name {
                    if byte == 0 { break; }
                    if byte >= 32 && byte <= 126 {
                        name_str.push(byte as char);
                    }
                }

                if entry.is_dir {
                    println!("[{}]  {}\\          <DIR>", entry_num, name_str);
                } else {
                    println!("[{}]  {}", entry_num, name_str);
                }
            }

            println!("");
            println!("[0]   Return to C: drive");
            println!("");

            if page_end < total_entries {
                println!("[C] Continue to next page ({} more entries)", total_entries - page_end);
                println!("[Q] Back to entry selection");
            } else {
                println!("--- End of directory ---");
            }

            println!("");

            if get_state().is_admin {
                println!("[S]   Search files");
            }

            print!("{}:\\> ", drive_letter);

            let choice = get_user_input();

            // Handle [..] parent directory
            if choice == ".." {
                match dos::disk::chdir("..") {
                    Ok(_) => break,  // Re-list current directory
                    Err(e) => {
                        println!("Error: {}", e.as_str());
                        dos::console::readc();
                    }
                }
                continue;
            }

            // Handle [0] return to C:
            if choice == "0" {
                dos::disk::set_drive(2).ok();  // Switch to C: (2 = C:)
                let state = get_state();
                state.current_drive = None;  // Back to default
                return;
            }

            // Handle [S] search (admin only)
            if (choice.as_str() == "S" || choice.as_str() == "s") && get_state().is_admin {
                handle_input(drive);
                break;  // Re-list directory after search completes
            }

            // Handle pagination
            if choice.as_str() == "C" || choice.as_str() == "c" {
                if page_end < total_entries {
                    page_offset = page_end;
                    continue;
                }
            }

            // Handle numbered entry selection
            if let Ok(num) = choice.parse::<usize>() {
                if num >= 1 && num <= total_entries {
                    let entry = &entries[num - 1];

                    // Convert name to string
                    let mut name_str = String::new();
                    for &byte in &entry.name {
                        if byte == 0 { break; }
                        if byte >= 32 && byte <= 126 {
                            name_str.push(byte as char);
                        }
                    }

                    if entry.is_dir {
                        match dos::disk::chdir(&name_str) {
                            Ok(_) => break,  // Re-list new directory
                            Err(e) => {
                                println!("");
                                println!("Error entering directory: {}", e.as_str());
                                dos::console::readc();
                            }
                        }
                    } else {
                        file_view_menu(&name_str, drive);
                    }
                } else {
                    println!("");
                    println!("Invalid entry number.");
                    dos::console::readc();
                }
            }
        }
    }
}

fn file_view_menu(filename: &str, drive: u8) {
    let drive_letter = (b'A' + drive) as char;

    loop {
        clear_screen();
        println!("===========================================================");
        println!("                    FILE VIEWER");
        println!("===========================================================");
        println!("");
        println!("File: {}", filename);
        println!("Location: {}:\\", drive_letter);
        println!("");
        println!("[1] View as text");
        println!("[2] Hex dump");
        println!("[3] Back to directory listing");
        println!("");
        print!("ARCHIVIST> Select view mode: ");

        let choice = get_user_input();

        match choice.as_str() {
            "1" => view_file_streaming(filename),
            "2" => hex_dump_file_streaming(filename),
            "3" => return,
            _ => {
                println!("");
                println!("ERROR: Invalid selection. Choose 1, 2, or 3.");
                println!("Press any key to continue...");
                dos::console::readc();
            }
        }
    }
}

fn view_file_streaming(filename: &str) {
    // Open file
    let file = match dos::file::File::open(filename) {
        Ok(f) => f,
        Err(e) => {
            clear_screen();
            println!("Error opening file: {}", e.as_str());
            println!("Press any key to continue...");
            dos::console::readc();
            return;
        }
    };

    // Acquire buffer for streaming
    let buffer = match acquire_disk_buffer() {
        Some(buf) => buf,
        None => {
            clear_screen();
            println!("Error: Buffer already in use.");
            println!("Press any key to continue...");
            dos::console::readc();
            if let Err(e) = file.close() {
                println!("Warning: Error closing file: {}", e.as_str());
            }
            return;
        }
    };

    loop {
        clear_screen();
        println!("===========================================================");
        println!("                   FILE CONTENT (TEXT)");
        println!("===========================================================");
        println!("");
        println!("File: {}", filename);
        println!("");

        let bytes_read = match file.read(buffer) {
            Ok(n) => n,
            Err(e) => {
                println!("Error reading file: {}", e.as_str());
                dos::console::readc();
                break;
            }
        };

        if bytes_read == 0 {
            println!("--- End of file ---");
            println!("");
            println!("Press any key to return...");
            dos::console::readc();
            break;
        }

        for i in 0..bytes_read {
            let byte = buffer[i];
            if byte >= 32 && byte <= 126 {
                print!("{}", byte as char);
            } else if byte == 10 {
                println!("");
            } else if byte == 13 {
                // Skip carriage return
            } else {
                print!(".");
            }
        }

        println!("");
        println!("");
        println!("[C] Continue to next chunk");
        println!("[Q] Return to file menu");
        println!("");
        print!("Your choice: ");

        let choice = dos::console::readc();
        println!("");  // Newline after single-char input

        if choice != b'C' && choice != b'c' {
            break;  // User quit
        }
        // Loop continues to read next chunk
    }

    // Cleanup
    if let Err(e) = file.close() {
        println!("Warning: Error closing file: {}", e.as_str());
    }
    release_disk_buffer();
}

fn hex_dump_file_streaming(filename: &str) {
    // Open file
    let file = match dos::file::File::open(filename) {
        Ok(f) => f,
        Err(e) => {
            clear_screen();
            println!("Error opening file: {}", e.as_str());
            println!("Press any key to continue...");
            dos::console::readc();
            return;
        }
    };

    // Acquire buffer for streaming
    let buffer = match acquire_disk_buffer() {
        Some(buf) => buf,
        None => {
            clear_screen();
            println!("Error: Buffer already in use.");
            println!("Press any key to continue...");
            dos::console::readc();
            if let Err(e) = file.close() {
                println!("Warning: Error closing file: {}", e.as_str());
            }
            return;
        }
    };

    let mut file_offset: usize = 0;

    // Stream file in chunks
    loop {
        clear_screen();
        println!("===========================================================");
        println!("                 FILE CONTENT (HEX DUMP)");
        println!("===========================================================");
        println!("");
        println!("File: {}", filename);
        println!("");

        let bytes_read = match file.read(buffer) {
            Ok(n) => n,
            Err(e) => {
                println!("Error reading file: {}", e.as_str());
                dos::console::readc();
                break;
            }
        };

        if bytes_read == 0 {
            println!("--- End of file ---");
            println!("");
            println!("Press any key to return...");
            dos::console::readc();
            break;
        }

        println!("Offset   00 01 02 03 04 05 06 07  08 09 0A 0B 0C 0D 0E 0F");
        println!("-----------------------------------------------------------");

        let rows = (bytes_read + 15) / 16;
        for row in 0..rows {
            let row_offset = file_offset + (row * 16);
            print!("{:08X} ", row_offset);

            // Hex bytes
            for col in 0..16 {
                let pos = row * 16 + col;
                if pos < bytes_read {
                    print!("{:02X} ", buffer[pos]);
                } else {
                    print!("   ");
                }

                if col == 7 {
                    print!(" ");  // Extra space between byte groups
                }
            }

            println!("");
        }

        file_offset += bytes_read;

        println!("");
        println!("[C] Continue to next chunk");
        println!("[Q] Return to file menu");
        println!("");
        print!("Your choice: ");

        let choice = dos::console::readc();
        println!("");  // Newline after single-char input

        if choice != b'C' && choice != b'c' {
            break;  // User quit
        }
        // Loop continues to read next chunk
    }

    // Cleanup
    if let Err(e) = file.close() {
        println!("Warning: Error closing file: {}", e.as_str());
    }
    release_disk_buffer();
}

#[inline(never)]
fn process_data(input: &[u8; AUTH_SIZE]) -> [u8; AUTH_SIZE] {
    let mut result = [0u8; AUTH_SIZE];
    for i in 0..AUTH_SIZE {
        let key_byte = CODEC_SEED[i % CODEC_SEED.len()];
        result[i] = input[i] ^ key_byte;
    }
    result
}

#[inline(never)]
fn check_auth(password: &str) -> bool {
    if password.len() != AUTH_SIZE {
        return false;
    }

    let mut input_bytes = [0u8; AUTH_SIZE];
    for (i, b) in password.bytes().enumerate() {
        input_bytes[i] = b;
    }

    let transformed = process_data(&input_bytes);

    for i in 0..AUTH_SIZE {
        if transformed[i] != STORED_KEY[i] {
            return false;
        }
    }

    true
}

fn read_password_masked() -> String {
    const MAX_AUTH_SIZE: usize = 32;
    let mut buffer = [0u8; MAX_AUTH_SIZE];
    let mut len = 0;

    loop {
        let ch = dos::console::readc_no_echo();

        if ch == b'\r' {  // Enter key
            println!("");
            break;
        }

        if ch == 8 {  // Backspace
            if len > 0 {
                len -= 1;
                print!("\x08 \x08");  // Move back, print space, move back again
            }
            continue;
        }

        // Accept printable ASCII characters (space through tilde)
        if len < MAX_AUTH_SIZE && ch >= 32 && ch <= 126 {
            buffer[len] = ch;
            len += 1;
            print!("*");  // Print asterisk after storing character
        }
    }

    // Convert buffer to String
    let mut result = String::new();
    for i in 0..len {
        result.push(buffer[i] as char);
    }

    result
}

#[inline(never)]
fn load_system_data() -> Result<String, ErrorCode> {
    let file = dos::file::File::open("C:\\flag.txt")?;

    let mut buffer = [0u8; 256];
    let bytes_read = file.read(&mut buffer)?;

    // Convert to String (filter to printable ASCII + newlines)
    let mut content = String::new();
    for i in 0..bytes_read {
        if (buffer[i] >= 32 && buffer[i] <= 126) || buffer[i] == b'\r' || buffer[i] == b'\n' {
            content.push(buffer[i] as char);
        }
    }

    file.close()?;

    Ok(content)
}

#[inline(never)]
fn read_auth_data() -> Result<String, ErrorCode> {
    // Save current drive before switching to F:
    let saved_drive = get_state().current_drive;

    // Switch to F: drive (5 = F:)
    dos::disk::set_drive(5)?;

    let file = dos::file::File::open("F:\\flag.txt")?;

    let mut buffer = [0u8; 256];
    let bytes_read = file.read(&mut buffer)?;

    let mut token = String::new();
    for i in 0..bytes_read {
        if (buffer[i] >= 32 && buffer[i] <= 126) || buffer[i] == b'\r' || buffer[i] == b'\n' {
            token.push(buffer[i] as char);
        }
    }

    file.close()?;

    // Restore original drive
    if let Some(drive) = saved_drive {
        dos::disk::set_drive(drive)?;
    } else {
        dos::disk::set_drive(2)?;  // Back to C: if no drive was mounted
    }

    Ok(token)
}

fn admin_login() {
    println!("");
    println!("===========================================================");
    println!("|                 VAULT ACCESS TERMINAL                  |");
    println!("|               Enter Security Credentials               |");
    println!("===========================================================");
    println!("");
    print!("Password: ");

    let password = read_password_masked();

    if check_auth(&password) {
        let state = get_state();
        state.is_admin = true;

        println!("");
        println!("===========================================================");
        println!("|                    ACCESS GRANTED                      |");
        println!("|         VAULT CLEARANCE LEVEL: ADMINISTRATOR           |");
        println!("|              Welcome, Vault Overseer                   |");
        println!("===========================================================");

        match load_system_data() {
            Ok(data) => {
                println!("");
                println!("{}", data);
                println!("");
            }
            Err(e) => {
                println!("");
                println!("Warning: Could not read system data: {}", e.as_str());
                println!("");
            }
        }
    } else {
        println!("");
        println!("===========================================================");
        println!("|                    ACCESS DENIED                       |");
        println!("|             Invalid credentials provided              |");
        println!("===========================================================");
        println!("");
    }

    println!("Press any key to return to main terminal...");
    dos::console::readc();
}

#[inline(never)]
fn command_console() {
    loop {
        println!("");
        println!("===========================================================");
        println!("|            WASTELAND COMMAND CONSOLE                   |");
        println!("|          Enter Admin Token for Access                 |");
        println!("===========================================================");
        println!("");
        println!("Type EXIT to return to main terminal.");
        println!("");
        print!("ADMIN TOKEN> ");

        let token_input = get_user_input();

        if token_input.trim().eq_ignore_ascii_case("EXIT") {
            return;
        }

        let expected_token = match read_auth_data() {
            Ok(token) => token,
            Err(e) => {
                println!("");
                println!("===========================================================");
                println!("|                    SYSTEM ERROR                        |");
                println!("|         Cannot access authentication file             |");
                println!("|                 Error: {}                   ", e.as_str());
                println!("===========================================================");
                println!("");
                println!("Press any key to return to main terminal...");
                dos::console::readc();
                return;  // Exit to main menu on fatal error
            }
        };

        if token_input.trim() == expected_token.trim() {
            // SUCCESS - enter restricted shell
            println!("");
            println!("===========================================================");
            println!("|                    ACCESS GRANTED                      |");
            println!("|         WASTELAND CONSOLE ACCESS AUTHORIZED            |");
            println!("===========================================================");
            println!("");

            // Enter restricted shell
            command_console_shell();

            return;  // Exit to main menu after shell session
        } else {
            println!("");
            println!("===========================================================");
            println!("|                    ACCESS DENIED                       |");
            println!("|              Invalid token provided                   |");
            println!("===========================================================");
            println!("");
        }
    }
}



fn command_console_shell() {
    loop {
        print!("WASTELAND:\\> ");

        let input = get_user_input();

        // Skip empty input
        if input.is_empty() {
            continue;
        }

        // Parse command and arguments
        let mut parts = input.split_whitespace();
        let command = match parts.next() {
            Some(cmd) => cmd,
            None => continue,  // Empty after trim
        };

        // Route to command handlers (case-insensitive)
        match command.to_uppercase().as_str() {
            "DIR" => cmd_dir(),
            "TYPE" => {
                let filename = parts.next();
                cmd_type(filename);
            },
            "VER" => cmd_ver(),
            "VERIFY" => {
                let args: Vec<&str> = parts.collect();
                if args.is_empty() {
                    cmd_verify(None);
                } else {
                    let search_term = args.join(" ");
                    cmd_verify(Some(&search_term));
                }
            },
            "HELP" => cmd_help(),
            "CLS" => cmd_cls(),
            "EXIT" => {
                println!("Exiting command console...");
                return;
            },
            _ => {
                println!("COMMAND NOT RECOGNIZED - ACCESS RESTRICTED");
            }
        }
    }
}

fn cmd_dir() {
    println!("");
    println!(" Volume in drive WASTELAND has no label");
    println!(" Volume Serial Number is 1337-BEEF");
    println!("");
    println!(" Directory of WASTELAND:\\");
    println!("");
    println!("VAULT      DAT      4,096  05-10-26  9:42a");
    println!("CORE_DUMP  SYS     16,384  03-15-87  2:13p");
    println!("REACTOR    LOG      8,192  11-22-77  11:59p");
    println!("MANIFEST   TXT      2,048  01-01-88  12:00a");
    println!("             4 file(s)     30,720 bytes");
    println!("                          609,280 bytes free");
    println!("");
}

fn cmd_type(filename: Option<&str>) {
    let filename = match filename {
        Some(name) => name.to_uppercase(),
        None => {
            println!("Required parameter missing");
            return;
        }
    };

    match filename.as_str() {
        "VAULT.DAT" => {
            println!("VAULT ACCESS LOG - RESTRICTED");
            println!("Last access: 2087-03-15 14:23:17");
            println!("Security clearance: LEVEL 9 REQUIRED");
            println!("Status: SEALED");
        },
        "CORE_DUMP.SYS" => {
            println!("REACTOR CORE DIAGNOSTIC DUMP");
            println!("Timestamp: 2087-03-15 14:13:42");
            println!("Core temperature: 2847 C (CRITICAL)");
            println!("Containment breach detected at sector 7G");
        },
        "REACTOR.LOG" => {
            println!("REACTOR MONITORING LOG");
            println!("Last entry: 2077-11-22 23:59:58");
            println!("All systems nominal before event");
            println!("[REMAINING LOG ENTRIES CORRUPTED]");
        },
        "MANIFEST.TXT" => {
            println!("WASTELAND SUPPLY MANIFEST");
            println!("Vault supplies: 47% depleted");
            println!("Food rations: 23 days remaining");
            println!("Water purification: OPERATIONAL");
        },
        _ => {
            println!("File not found");
        }
    }
}

fn cmd_ver() {
    println!("");
    println!("WASTELAND OS v2.087 [Vault Terminal Build 1337]");
    println!("Post-Collapse Computing Systems");
    println!("Copyright (C) 2087 Vault-Tec Industries");
    println!("");
}

fn cmd_help() {
    println!("");
    println!("Available commands:");
    println!("  DIR        - List directory contents");
    println!("  TYPE       - Display file contents");
    println!("  VER        - Show system version");
    println!("  VERIFY     - Verify system integrity");
    println!("  HELP       - Display this help");
    println!("  CLS        - Clear screen");
    println!("  EXIT       - Exit command console");
    println!("");
}

fn cmd_cls() {
    clear_screen();
}

#[inline(never)]
fn cmd_verify(search_term: Option<&str>) {
    let term = match search_term {
        Some(t) => t,
        None => "",  // Empty search runs bare DIR
    };
    let mut command_args = String::from("/C DIR ");
    command_args.push_str(term);

    match rust_dos::dos::exec::exec_with_args("C:\\COMMAND.COM", &command_args) {
        Ok(()) => {
        },
        Err(ErrorCode::InvalidParameter) => {
            println!("Search term too long");
        },
        Err(_) => {
            println!("VERIFY failed - system error");
        }
    }
}


fn unmount_drive() {
    let state = get_state();

    match state.current_drive {
        Some(drive) => {
            let drive_letter = (b'A' + drive) as char;

            match dos::disk::set_drive(2) {  // 2 = C:
                Ok(_) => {
                    state.current_drive = None;

                    clear_screen();
                    println!("===========================================================");
                    println!("                   DRIVE UNMOUNTED");
                    println!("===========================================================");
                    println!("");
                    println!("Drive {}: has been unmounted.", drive_letter);
                    println!("Current drive: C:");
                    println!("");
                    println!("Press any key to continue...");
                    dos::console::readc();
                }
                Err(e) => {
                    clear_screen();
                    println!("Error switching to C: drive: {}", e.as_str());
                    println!("Press any key to continue...");
                    dos::console::readc();
                }
            }
        }
        None => {
            clear_screen();
            println!("No drive currently mounted (already on C:).");
            println!("Press any key to continue...");
            dos::console::readc();
        }
    }
}






fn show_system_status() {
    clear_screen();
    println!("===========================================================");
    println!("                   SYSTEM DIAGNOSTICS");
    println!("===========================================================");
    println!("");
    
    println!("System: RUST IN PEACE v1.0");
    println!("Platform: MS-DOS Compatible Terminal");
    println!("Operator: The Last Archivist");
    println!("");
    
    let state = get_state();
    match state.current_drive {
        Some(drive) => {
            let drive_letter = (b'A' + drive) as char;
            println!("Drive Status: ACTIVE - Drive {}: mounted", drive_letter);
            println!("Data Buffer: Available for streaming");
            println!("Buffer Usage: Dynamic (2048 byte chunks)");
        }
        None => {
            println!("Drive Status: C: DRIVE (DEFAULT)");
            println!("Data Buffer: 0 / 2048 bytes used");
            println!("Buffer Usage: 0.0%");
        }
    }
    
    println!("");
    println!("Platform Status: MULTI-DRIVE SUPPORT ENABLED");
    println!("Available Drives: A: B: (Floppy) | D: E: F: (IDE)");
    println!("Mission: Preserve and explore archived data across 5 disk images");
    println!("");
    println!("Memory Status: STABLE");
    println!("Terminal Status: OPERATIONAL");
    println!("Archive Mission: IN PROGRESS");
    
    println!("");
    println!("===========================================================");
    println!("");
    println!("Remember: You are humanity's last hope for preserving");
    println!("the knowledge of the old world. Guard these disks well.");
    println!("");
    println!("Press any key to return to main terminal...");
    dos::console::readc();
}

fn get_user_input() -> String {
    let mut input_buffer = [0u8; 256];
    let len = dos::console::read_line(&mut input_buffer);

    let mut result = String::new();
    for i in 0..len {
        if input_buffer[i] >= 32 && input_buffer[i] <= 126 {
            result.push(input_buffer[i] as char);
        }
    }

    result
}

#[inline(never)]
fn handle_input(drive: u8) {
    // Route to appropriate search implementation based on drive
    if drive != 5 {  // 5 = Drive F:
        scan_entries(drive);  // Standard search path
        return;
    }

    process_query(drive);
}

#[inline(never)]
fn scan_entries(drive: u8) {
    clear_screen();
    println!("===========================================================");
    println!("|                  ARCHIVE SEARCH                        |");
    println!("|          Scanning Data Repository Records             |");
    println!("===========================================================");
    println!("");
    print!("SEARCH TERM> ");

    // Standard input buffer (256 bytes, safe)
    let search_term = get_user_input();

    println!("");
    println!("Searching for: {}", search_term);
    println!("");

    let mut found_count = 0;

    // Scan directory entries
    match dos::disk::find_first("*.*", 0x10) {  // 0x10 = include directories
        Ok(_) => {
            loop {
                let dta_array = *dos::disk::get_dta_buffer_ref();
                let entry = dos::disk::parse_dta(&dta_array);

                // Convert filename to string
                let mut name_str = String::new();
                for &byte in &entry.name {
                    if byte == 0 { break; }
                    if byte >= 32 && byte <= 126 {
                        name_str.push(byte as char);
                    }
                }

                // Substring match (case-insensitive)
                if name_str.to_lowercase().contains(&search_term.to_lowercase()) {
                    println!("  [MATCH] {}", name_str);
                    found_count += 1;
                }

                // Continue to next entry
                match dos::disk::find_next() {
                    Ok(_) => continue,
                    Err(ErrorCode::NoMoreFiles) => break,
                    Err(_) => break,
                }
            }
        }
        Err(_) => {}
    }

    if found_count == 0 {
        println!("No matching archives found.");
    }

    println!("");
    println!("Press any key to continue...");
    dos::console::readc();
}

#[inline(never)]
fn process_query(drive: u8) {
    clear_screen();
    println!("===========================================================");
    println!("|                  ARCHIVE SEARCH                        |");
    println!("|          Scanning Classified Data Repository          |");
    println!("===========================================================");
    println!("");

    // Allocate data block on stack (256 bytes)
    let mut data_block = DataBlock {
        search_buffer: [0u8; 16],
        archive_data: [0u8; 64],
        padding: [0u8; 176],
    };

    if let Ok(file) = dos::file::File::open("F:\\flag.txt") {
        let _ = file.read(&mut data_block.archive_data);
        let _ = file.close();
    }

    print!("SEARCH TERM> ");

    // Read search input
    let mut input_buffer = [0u8; 256];
    let len = dos::console::read_line(&mut input_buffer);

    // Copy input into search buffer (bounded to buffer capacity)
    unsafe {
        let src = input_buffer.as_ptr();
        let dst = data_block.search_buffer.as_mut_ptr();
        let copy_len = core::cmp::min(len, data_block.search_buffer.len());
        core::ptr::copy_nonoverlapping(src, dst, copy_len);
    }

    println!("");

    print!("Searching for: ");
    let echo_len = core::cmp::min(len, 254);
    for i in 0..echo_len {
        let byte = unsafe { *data_block.search_buffer.as_ptr().add(i) };
        if byte >= 32 && byte <= 126 {
            print!("{}", byte as char);
        } else {
            print!(".");
        }
    }
    println!("");
    println!("");

    let mut found_count = 0;

    // Extract search term from input_buffer for matching
    let mut search_term = String::new();
    for i in 0..core::cmp::min(len, 16) {  // Use first 16 bytes as intended search term
        if input_buffer[i] >= 32 && input_buffer[i] <= 126 {
            search_term.push(input_buffer[i] as char);
        }
    }

    match dos::disk::find_first("*.*", 0x10) {
        Ok(_) => {
            loop {
                let dta_array = *dos::disk::get_dta_buffer_ref();
                let entry = dos::disk::parse_dta(&dta_array);

                let mut name_str = String::new();
                for &byte in &entry.name {
                    if byte == 0 { break; }
                    if byte >= 32 && byte <= 126 {
                        name_str.push(byte as char);
                    }
                }

                if name_str.to_lowercase().contains(&search_term.to_lowercase()) {
                    println!("  [MATCH] {}", name_str);
                    found_count += 1;
                }

                match dos::disk::find_next() {
                    Ok(_) => continue,
                    Err(ErrorCode::NoMoreFiles) => break,
                    Err(_) => break,
                }
            }
        }
        Err(_) => {}
    }

    if found_count == 0 {
        println!("No matching archives found.");
    }

    println!("");
    println!("Press any key to continue...");
    dos::console::readc();
}
