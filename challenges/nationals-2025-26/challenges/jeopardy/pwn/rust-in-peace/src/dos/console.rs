use core::arch::asm;
use core::fmt::{self, Write};

#[macro_export]
macro_rules! print {
    ($($arg:tt)*) => {
        $crate::dos::console::_print(format_args!($($arg)*))
    };
}

#[macro_export]
macro_rules! println {
    ($fmt:expr) => {
        print!(concat!($fmt, "\r\n"))
    };
    ($fmt:expr, $($arg:tt)*) => {
        print!(concat!($fmt, "\r\n"), $($arg)*)
    };
}

pub fn _print(args: fmt::Arguments) {
    let mut writer = DosWriter {};
    writer.write_fmt(args).unwrap();
}

struct DosWriter;

impl Write for DosWriter {
    fn write_str(&mut self, s: &str) -> fmt::Result {
        for c in s.bytes() {
            printc(c);
        }
        Ok(())
    }
}

fn printc(ch: u8) {
    unsafe { asm!("int 0x21", in("ah") 0x02_u8, in("dl") ch) }
}

static mut OLD_INT23_OFFSET: u16 = 0;
static mut OLD_INT23_SEGMENT: u16 = 0;
static mut OLD_INT1B_OFFSET: u16 = 0;
static mut OLD_INT1B_SEGMENT: u16 = 0;

#[inline(never)]
unsafe extern "C" fn dummy_interrupt_handler() -> ! {
    asm!(
        "iret",  // Interrupt return - does nothing, just returns
        options(noreturn)
    );
}

unsafe fn get_interrupt_vector(interrupt_num: u8) -> (u16, u16) {
    let mut segment: u16;
    let mut offset: u16;
    
    asm!(
        "push es",                  // Save ES
        "int 0x21",
        "mov {segment:x}, es",      // Get segment from ES
        "mov {offset:x}, bx",       // Get offset from BX
        "pop es",                   // Restore ES
        segment = out(reg) segment,
        offset = out(reg) offset,
        in("ah") 0x35_u8,           // Function: Get Interrupt Vector
        in("al") interrupt_num,     // Interrupt number
        out("bx") _,                // BX will be modified
    );
    
    (segment, offset)
}

/// Set interrupt vector using DOS INT 0x21, AH=0x25
unsafe fn set_interrupt_vector(interrupt_num: u8, segment: u16, offset: u16) {
    asm!(
        "push ds",                  // Save DS
        "mov ds, {segment:x}",      // DS = segment of new handler
        "int 0x21",
        "pop ds",                   // Restore DS
        segment = in(reg) segment,
        in("ah") 0x25_u8,           // Function: Set Interrupt Vector
        in("al") interrupt_num,     // Interrupt number
        in("dx") offset,            // DX = offset of new handler
    );
}

pub fn disable_ctrl_break() {
    unsafe {
        let cs: u16;
        asm!("mov {cs:x}, cs", cs = out(reg) cs);
        
        let handler_ptr = dummy_interrupt_handler as *const () as u16;
        
        let (seg, off) = get_interrupt_vector(0x23);
        OLD_INT23_SEGMENT = seg;
        OLD_INT23_OFFSET = off;
        
        let (seg, off) = get_interrupt_vector(0x1B);
        OLD_INT1B_SEGMENT = seg;
        OLD_INT1B_OFFSET = off;
        
        set_interrupt_vector(0x23, cs, handler_ptr);  // CTRL+C
        set_interrupt_vector(0x1B, cs, handler_ptr);  // CTRL+BREAK
        
        asm!(
            "int 0x21",
            in("ah") 0x33_u8,  // Function: Get/Set Ctrl-Break check
            in("al") 0x01_u8,  // Subfunction: Set state
            in("dl") 0x00_u8,  // DL = 0: Disable Ctrl-Break checking
        );
    }
}

pub fn enable_ctrl_break() {
    unsafe {
        if OLD_INT23_SEGMENT != 0 || OLD_INT23_OFFSET != 0 {
            set_interrupt_vector(0x23, OLD_INT23_SEGMENT, OLD_INT23_OFFSET);
        }
        
        if OLD_INT1B_SEGMENT != 0 || OLD_INT1B_OFFSET != 0 {
            set_interrupt_vector(0x1B, OLD_INT1B_SEGMENT, OLD_INT1B_OFFSET);
        }
        
        asm!(
            "int 0x21",
            in("ah") 0x33_u8,  // Function: Get/Set Ctrl-Break check
            in("al") 0x01_u8,  // Subfunction: Set state
            in("dl") 0x01_u8,  // DL = 1: Enable Ctrl-Break checking
        );
    }
}

pub fn readc() -> u8 {
    let ch: u8;
    unsafe {
        asm!("int 0x21", in("ah") 0x01_u8, lateout("al") ch);
    }
    ch
}

/// Read character without echo (DOS INT 21h/08h)
/// Used for password input with asterisk masking
pub fn readc_no_echo() -> u8 {
    let ch: u8;
    unsafe {
        asm!("int 0x21", in("ah") 0x08_u8, lateout("al") ch);
    }
    ch
}

pub fn read_line(buffer: &mut [u8]) -> usize {
    if buffer.len() < 2 {
        return 0;
    }

    
    let max_len = (buffer.len() - 2).min(254) as u8; // Leave room for length bytes
    buffer[0] = max_len;
    
    unsafe {
        let buffer_ptr = buffer.as_mut_ptr();
        asm!("int 0x21", in("ah") 0x0A_u8, in("dx") buffer_ptr);
    }
    
    let actual_len = buffer[1] as usize;
    
    if actual_len > 0 {
        for i in 0..actual_len {
            buffer[i] = buffer[i + 2];
        }
    }
    
    actual_len
}

