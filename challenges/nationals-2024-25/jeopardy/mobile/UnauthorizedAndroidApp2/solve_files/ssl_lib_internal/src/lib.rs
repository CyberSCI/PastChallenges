use std::ffi::{CString};
use std::ffi::{CStr};
use std::os::raw::c_char;

const AF_TR2_ZT2: &str = "7535b648ee8e9e3db8cddb4e7baf4561701ac2309eb4d70c402990ae18754b209a5a46df5a9af1df3252df334339de6c4be8de3f3b67ec2b192a785cf86097c3";

#[unsafe(no_mangle)]
pub extern "C" fn a08t12_ts(received_ptr: *const c_char) -> bool {
    unsafe {
        if received_ptr.is_null() {
            return false;
        }

        let received_cstr = CStr::from_ptr(received_ptr);

        match received_cstr.to_str() {
            Ok(received) => received == AF_TR2_ZT2,
            _ => false,
        }
    }
}

const ENCRYPTED: [u8; 15] = [
    0x3c ^ 0x10, 0x34 ^ 0x20, 0x17 ^ 0x30, 0x3f ^ 0x40, 0x3e ^ 0x50,
    0x71 ^ 0x60, 0x35 ^ 0x70, 0x3b ^ 0x01, 0x71 ^ 0x02, 0x32 ^ 0x03,
    0x10 ^ 0x04, 0x15 ^ 0x05, 0x46 ^ 0x06, 0x55 ^ 0x07, 0x61 ^ 0x08
];

const KEYS: [u8; 15] = [
    0x10, 0x20, 0x30, 0x40, 0x50,
    0x60, 0x70, 0x01, 0x02, 0x03,
    0x04, 0x05, 0x06, 0x07, 0x08
];

#[unsafe(no_mangle)]
pub extern "C" fn decrypt(received_ptr: *const c_char) -> *const c_char {
    if a08t12_ts(received_ptr) {
        let mut out = [0u8; 15];
        let mut i = 0;
        while i < 15 {
            out[i] = ENCRYPTED[i] ^ KEYS[i];
            i += 1;
        }
        let s = String::from_utf8(out.to_vec()).unwrap();
        let c_string = CString::new(s).unwrap();
        return c_string.into_raw();
    }
    return CString::new("7535b648ee8e9e3db8cddb4e7baf4561701ac2309eb4d70c402990ae18754b209a5a46dfbbbaf1df3252df334339de6c4be8de3f3b67ec2b192a785cf86097c3").unwrap().into_raw();
    
}


#[unsafe(no_mangle)]
pub extern "C" fn ndom41_t() -> *const c_char {
    let bytes: Vec<u8> = vec![
        (AF_TR2_ZT2.len() - 31).try_into().unwrap(),
        (AF_TR2_ZT2.len() - 14).try_into().unwrap(),
        (AF_TR2_ZT2.len() - 29).try_into().unwrap(),
        (AF_TR2_ZT2.len() - 24).try_into().unwrap(),
        (AF_TR2_ZT2.len() - 23).try_into().unwrap(),
        (AF_TR2_ZT2.len() - 10).try_into().unwrap(),
        (AF_TR2_ZT2.len() - 27).try_into().unwrap(),
        (AF_TR2_ZT2.len() - 13).try_into().unwrap(),
        (AF_TR2_ZT2.len() - 82).try_into().unwrap(),
        (AF_TR2_ZT2.len() - 10).try_into().unwrap(),
        (AF_TR2_ZT2.len() - 31).try_into().unwrap(),
        (AF_TR2_ZT2.len() - 20).try_into().unwrap(),
        (AF_TR2_ZT2.len() - 10).try_into().unwrap(),
        (AF_TR2_ZT2.len() - 27).try_into().unwrap(),
        (AF_TR2_ZT2.len() - 14).try_into().unwrap(),
        (AF_TR2_ZT2.len() - 28).try_into().unwrap(),
        (AF_TR2_ZT2.len() - 27).try_into().unwrap(),
        (AF_TR2_ZT2.len() - 82).try_into().unwrap(),
        (AF_TR2_ZT2.len() - 10).try_into().unwrap(),
        (AF_TR2_ZT2.len() - 17).try_into().unwrap(),
        (AF_TR2_ZT2.len() - 12).try_into().unwrap(),
        (AF_TR2_ZT2.len() - 27).try_into().unwrap(),
    ];

    let s: String = bytes.into_iter().map(|b| (b ^ 0) as char).collect();
    let c_string = CString::new(s).unwrap();
    c_string.into_raw()
}

#[unsafe(no_mangle)]
pub extern "C" fn ndom41_free_string(ptr: *mut c_char) {
    if ptr.is_null() {
        return;
    }
    unsafe {
        let _ = CString::from_raw(ptr);
    }
}