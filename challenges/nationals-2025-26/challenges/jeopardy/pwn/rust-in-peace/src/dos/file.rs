use core::arch::asm;
use core::cmp::min;
use crate::dos::error_code::ErrorCode;

extern crate rlibc;

#[allow(dead_code)]
pub struct File {
    handle: u16,
}
#[allow(dead_code)]
pub enum SeekFrom {
    Start(u32),
    End(u32),
    Current(u32),
}

impl SeekFrom {
    fn to_dos_seek_code(&self) -> u8 {
        match self {
            SeekFrom::Start(_) => 0,
            SeekFrom::End(_) => 2,
            SeekFrom::Current(_) => 1,
        }
    }

    fn to_seek_offset(&self) -> u32 {
        match self {
            SeekFrom::Start(offset) => *offset,
            SeekFrom::End(offset) => *offset,
            SeekFrom::Current(offset) => *offset,
        }
    }
}

#[allow(dead_code)]
#[allow(unused_assignments)]
impl File {
    pub fn open(filename: &str) -> Result<Self, ErrorCode> {
        let mut is_open_success: u16 = 1; // 0: success, 1: fail
        let mut error_code_or_handle: u16 = 0;
        // DOS PATH length limit is 66 bytes.
        let mut filename_array: [u8; 70] = [0; 70]; // To be sure of the segment
        for i in 0..min(filename_array.len(), filename.len()) {
            filename_array[i] = filename.as_bytes()[i];
        }
        let filename_ptr = filename_array.as_ptr();
        unsafe {
            asm!("mov al, 0x40", "mov ah, 0x3d", "int 0x21", "setc  dl", "movzx cx, dl", in("dx") filename_ptr as u16, lateout("cx") is_open_success, lateout("ax") error_code_or_handle);
        }
        if is_open_success == 1 {
            return Err(ErrorCode::from_u8(error_code_or_handle as u8).unwrap_or(ErrorCode::UnknownError));
        }
        Ok(Self {
            handle: error_code_or_handle,
        })
    }

    pub fn read(&self, buffer: &mut [u8]) -> Result<usize, ErrorCode> {
        let mut total_bytes_read: usize = 0;
        for buffer_write_pos in 0..buffer.len() {
            let mut is_read_success: u16 = 1;
            let mut error_code_or_bytes_read: u16 = 0;
            let mut byte_value: u16 = 0;
            let mut tmp_stack_buffer: [u8; 1] = [0; 1];
            let tmp_buffer_ptr = tmp_stack_buffer.as_mut_ptr() as u16;
            unsafe {
                asm!(
                    "mov di, dx",
                    "mov cx, 1",
                    "mov ah, 0x3f",
                    "int 0x21",
                    "setc dl",
                    "movzx cx, dl",
                    "movzx di, byte ptr [di]",
                    in("bx") self.handle,
                    in("dx") tmp_buffer_ptr,
                    lateout("cx") is_read_success,
                    lateout("ax") error_code_or_bytes_read,
                    lateout("di") byte_value
                );
            }
            if is_read_success == 1 {
                return Err(ErrorCode::from_u8(error_code_or_bytes_read as u8).unwrap_or(ErrorCode::UnknownError));
            }
            if error_code_or_bytes_read == 0 {
                break;
            }
            total_bytes_read += 1;
            buffer[buffer_write_pos] = byte_value as u8;
        }

        for buffer_write_pos in total_bytes_read..buffer.len() {
            buffer[buffer_write_pos] = 0;
        }
        Ok(total_bytes_read)
    }

    pub fn write(&self, buffer: &[u8]) -> Result<usize, ErrorCode> {
        let mut total_bytes_written: usize = 0;
        for buffer_read_pos in 0..buffer.len() {
            let mut is_write_success: u16 = 1;
            let mut error_code_or_bytes_written: u16 = 0;
            let mut tmp_stack_buffer: [u8; 1] = [0; 1];
            tmp_stack_buffer[0] = buffer[buffer_read_pos];
            let tmp_buffer_ptr = tmp_stack_buffer.as_ptr();
            unsafe {
                asm!(
                    "mov cx, 1",
                    "mov ah, 0x40",
                    "int 0x21",
                    "setc dl",
                    "movzx cx, dl",
                    in("bx") self.handle,
                    in("dx") tmp_buffer_ptr,
                    lateout("cx") is_write_success,
                    lateout("ax") error_code_or_bytes_written
                );
            }
            if is_write_success == 1 {
                return Err(ErrorCode::from_u8(error_code_or_bytes_written as u8).unwrap_or(ErrorCode::UnknownError));
            }
            total_bytes_written += 1;
        }
        Ok(total_bytes_written)
    }

    pub fn close(self) -> Result<(), ErrorCode> {
        self.close_with_ref()
    }

    fn close_with_ref(&self) -> Result<(), ErrorCode> {
        let mut is_close_success: u16 = 1;
        let mut error_code: u16 = 0;
        unsafe {
            asm!(
                "mov ah, 0x3e",
                "int 0x21",
                "setc dl",
                "movzx cx, dl",
                in("bx") self.handle,
                lateout("cx") is_close_success,
                lateout("ax") error_code,
                lateout("dx") _
            );
        }
        if is_close_success == 1 {
            return Err(ErrorCode::from_u8(error_code as u8).unwrap_or(ErrorCode::UnknownError));
        }
        Ok(())
    }

    /// Seek to an offset, in bytes, in a stream.
    /// Returns number of bytes from the start of the stream if success, or an error code otherwise.
    pub fn seek(&self, pos: SeekFrom) -> Result<u32, ErrorCode> {
        let mut is_seek_success: u16 = 1;
        let mut error_code_or_new_pos_low: u16 = 0;
        let mut new_pos_high: u16 = 0;
        let offset: u32 = pos.to_seek_offset();
        let offset_low = (offset & 0xffff) as u16;
        let offset_high = ((offset >> 16) & 0xffff) as u16;
        let seek_from: u8 = pos.to_dos_seek_code();
        unsafe {
            asm!(
                "mov ah, 0x42",
                "int 0x21",
                "setc bl",
                "movzx cx, bl",
                in("al") seek_from,
                in("bx") self.handle,
                in("cx") offset_high,
                in("dx") offset_low,
                lateout("cx") is_seek_success,
                lateout("ax") error_code_or_new_pos_low,
                lateout("dx") new_pos_high,
                lateout("bx") _
            );
        }
        if is_seek_success == 1 {
            return Err(ErrorCode::from_u8(error_code_or_new_pos_low as u8).unwrap_or(ErrorCode::UnknownError));
        }
        Ok((new_pos_high as u32) << 16 | (error_code_or_new_pos_low as u32))
    }
}

impl Drop for File {
    fn drop(&mut self) {
        let _ = self.close_with_ref();
    }
}