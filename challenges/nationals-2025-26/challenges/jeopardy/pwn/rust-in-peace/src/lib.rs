#![no_std]
#![feature(alloc_error_handler)]

#[macro_use]
pub mod dos;
pub mod dpkey;
extern crate rlibc;
extern crate alloc;

use core::arch::asm;
use crate::dos::allocator::GLOBAL_ALLOCATOR;
use crate::dos::cooperative_multitasking::TASKING;

#[link_section = ".startup"]
#[no_mangle]
fn _start() -> ! {
    unsafe {
        let bss_start: u32;
        let bss_end: u32;
        asm!("movl $_bss_start, %eax", out("eax") bss_start, options(nostack, preserves_flags, att_syntax));
        asm!("movl $_bss_end, %eax", out("eax") bss_end, options(nostack, preserves_flags, att_syntax));
        let len = (bss_end - bss_start) as usize;
        core::ptr::write_bytes(bss_start as *mut u8, 0, len);
    }
    unsafe {
        GLOBAL_ALLOCATOR.init();
        TASKING.init();
    }
    extern "Rust" {
        fn main() -> ();
    }
    unsafe {
        main();
    }
    dos::exit(0);
}

#[macro_export]
macro_rules! entry {
    ($path:path) => {
        #[export_name = "main"]
        pub fn __main() -> () {
            // type check the given path
            let f: fn() -> () = $path;
            f()
        }
    };
}