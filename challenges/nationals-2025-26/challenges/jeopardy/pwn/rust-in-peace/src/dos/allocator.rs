//! Heap allocator for DOS programs using segment-relative offsets.
//! Heap spans from the linker _heap symbol to below the stack within the current segment.

use core::alloc::{GlobalAlloc, Layout};
use core::arch::asm;
use core::cmp::min;
use core::mem::size_of;

struct AllocatorBlock {
    next: Option<*mut AllocatorBlock>,
    prev: Option<*mut AllocatorBlock>,
    size: usize,
    used: bool,
}

pub struct DosAllocator {
    first_block_ptr: *mut AllocatorBlock,
    heap_end: usize,
}

impl DosAllocator {
    const ALLOCATOR_BLOCK_SIZE: usize = size_of::<AllocatorBlock>();
    const MIN_BLOCK_USEFUL_SIZE: usize = 16;
    const STACK_RESERVE: usize = 4096;

    fn diff_between_blocks_ptr(first_block: *mut AllocatorBlock, second_block: *mut AllocatorBlock) -> usize {
        let first_block_addr = first_block as usize;
        let second_block_addr = second_block as usize;
        assert!(first_block_addr < second_block_addr);
        second_block_addr - first_block_addr
    }

    fn free_space_before_next_block(&self, block: *mut AllocatorBlock) -> usize {
        assert_ne!(block, core::ptr::null_mut());
        assert!((block as usize) < self.heap_end);
        let next_block = unsafe { (*block).next };
        if next_block.is_none() {
            return self.heap_end - block as usize;
        }
        let next_block = next_block.unwrap();
        Self::diff_between_blocks_ptr(block, next_block) - Self::ALLOCATOR_BLOCK_SIZE
    }

    fn block_addr_to_useful_ptr(block: *mut AllocatorBlock) -> *mut u8 {
        assert_ne!(block, core::ptr::null_mut());
        (block as usize + Self::ALLOCATOR_BLOCK_SIZE) as *mut u8
    }
}

unsafe impl GlobalAlloc for DosAllocator {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        // Look for next free block
        let mut current_block_ptr = self.first_block_ptr;
        while (*current_block_ptr).used || (*current_block_ptr).size < layout.size() + Self::ALLOCATOR_BLOCK_SIZE {
            current_block_ptr = match (*current_block_ptr).next {
                Some(ptr) => ptr,
                None => return core::ptr::null_mut(), // No free block found, return null ptr
            };
        }

        let free_space_before_next_block = self.free_space_before_next_block(current_block_ptr);
        if free_space_before_next_block <= Self::MIN_BLOCK_USEFUL_SIZE + Self::ALLOCATOR_BLOCK_SIZE {
            // No space for new block, just use the whole space
            (*current_block_ptr).used = true;
            (*current_block_ptr).size = free_space_before_next_block;
            return Self::block_addr_to_useful_ptr(current_block_ptr);
        }

        // Create a new unused block between current and next

        let current_block_size = layout.size() + Self::ALLOCATOR_BLOCK_SIZE;

        // Create a new block just after current block
        let new_block_ptr = (current_block_size + current_block_ptr as usize) as *mut AllocatorBlock;
        (*new_block_ptr).next = (*current_block_ptr).next;
        (*new_block_ptr).prev = Some(current_block_ptr);
        (*new_block_ptr).size = free_space_before_next_block - current_block_size;
        (*new_block_ptr).used = false;

        (*current_block_ptr).next = Some(new_block_ptr);
        (*current_block_ptr).size = current_block_size;
        (*current_block_ptr).used = true;

        Self::block_addr_to_useful_ptr(current_block_ptr)
    }

    unsafe fn dealloc(&self, ptr: *mut u8, _layout: Layout) {
        // Freeing null pointer is a no-op
        if ptr == core::ptr::null_mut() {
            return;
        }

        let current_block_ptr = (ptr as u32 - Self::ALLOCATOR_BLOCK_SIZE as u32) as *mut AllocatorBlock;
        // Mark block as free
        (*current_block_ptr).used = false;

        // Merge with next block if it's free
        let next_block_ptr = (*current_block_ptr).next;
        if next_block_ptr.is_some() {
            let next_block_ptr = next_block_ptr.unwrap();
            if !(*next_block_ptr).used {
                if (*next_block_ptr).next.is_some() {
                    (*(*next_block_ptr).next.unwrap()).prev = Some(current_block_ptr);
                }
                (*current_block_ptr).size += (*next_block_ptr).size;
                (*current_block_ptr).next = (*next_block_ptr).next;
            }
        }

        // Merge with previous block if it's free
        let prev_block_ptr = (*current_block_ptr).prev;
        if prev_block_ptr.is_some() {
            let prev_block_ptr = prev_block_ptr.unwrap();
            if !(*prev_block_ptr).used {
                if (*current_block_ptr).next.is_some() {
                    (*(*current_block_ptr).next.unwrap()).prev = Some(prev_block_ptr);
                }
                (*prev_block_ptr).size += (*current_block_ptr).size;
                (*prev_block_ptr).next = (*current_block_ptr).next;
            }
        }
    }

    unsafe fn realloc(&self, ptr: *mut u8, layout: Layout, new_size: usize) -> *mut u8 {
        assert_ne!(ptr, core::ptr::null_mut()); // Avoid undefined behavior
        let current_block_ptr = (ptr as u32 - Self::ALLOCATOR_BLOCK_SIZE as u32) as *mut AllocatorBlock;
        if (*current_block_ptr).size >= new_size + Self::ALLOCATOR_BLOCK_SIZE {
            return ptr;
        }
        let new_ptr = self.alloc(Layout::from_size_align(new_size, layout.align()).unwrap());
        new_ptr.copy_from_nonoverlapping(ptr, min(layout.size(), new_size));
        self.dealloc(ptr, layout);
        new_ptr
    }
}

impl DosAllocator {
    pub fn init(&mut self) {
        let heap_start: u32;
        unsafe {
            asm!("movl $_heap, %eax", out("eax") heap_start, options(nostack, preserves_flags, att_syntax));
        }
        let heap_start = heap_start as usize;

        let sp: u16;
        unsafe {
            asm!("mov {0:x}, sp", out(reg) sp, options(nostack, preserves_flags));
        }
        self.heap_end = (sp as usize).saturating_sub(Self::STACK_RESERVE);

        assert!(heap_start < self.heap_end);

        let heap_ptr_as_block = heap_start as *mut AllocatorBlock;
        let first_block_size = self.heap_end - heap_start;
        unsafe {
            core::ptr::write(heap_ptr_as_block, AllocatorBlock {
                next: None,
                prev: None,
                size: first_block_size,
                used: false,
            });
        }
        self.first_block_ptr = heap_ptr_as_block;
    }

    const fn new() -> Self {
        Self {
            first_block_ptr: core::ptr::null_mut(),
            heap_end: 0,
        }
    }
}

#[alloc_error_handler]
fn alloc_error_handler(layout: Layout) -> ! {
    panic!("allocation error: {:?}", layout);
}

#[global_allocator]
pub(crate) static mut GLOBAL_ALLOCATOR: DosAllocator = DosAllocator::new();