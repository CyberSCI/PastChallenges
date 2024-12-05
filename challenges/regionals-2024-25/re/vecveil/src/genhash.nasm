section .data
    hex_fmt db 'Hash (%%X): %X', 10, 0
    dword_fmt db 'Hash (%%u): %u', 10, 0
    err_usage db 'Usage: genhash <NAME>', 10, 0
    align 16
    xor_key db "CYBERSCI"

section .bss
    name resb 32

section .text
    global _start
    extern printf

_start:
    ; Get argc from the stack
    mov rax, [rsp] ; argc
    cmp rax, 2
    je proceed

    ; argc < 2, print usage message
    sub rsp, 8
    lea rdi, [rel err_usage]
    xor rax, rax
    call printf
    add rsp, 8

    ; exit(0)
    mov rax, 60
    xor rdi, rdi
    syscall

proceed:
    ; Load argv[1] into rsi
    mov rsi, [rsp + 16]

    ; Zero the 'name' buffer
    vpxor ymm0, ymm0, ymm0
    vmovdqu [rel name], ymm0

    ; Copy argv[1] into 'name' buffer, zero-padded up to 32 bytes
    mov rcx, 32
    lea rdi, [rel name]

copy_loop:
    cmp rcx, 0
    je copy_done
    mov al, byte [rsi]
    mov byte [rdi], al
    cmp al, 0
    je copy_done
    inc rsi
    inc rdi
    dec rcx
    jmp copy_loop

copy_done:
    mov rax, 2166136261
    vmovq xmm0, rax ; xmm0 contains FNV-1a offset basis
    mov rax, 16777619
    vmovq xmm1, rax ; xmm1 contains FNV-1a prime
    vpxor xmm3, xmm3, xmm3
    lea rdi, [rel name]

fnv1a_loop:
    movzx rax, byte [rdi]
    vmovq xmm4, rax
    vptest xmm4, xmm4
    je fnv1a_done
    vmovq xmm2, rax
    vpxor xmm0, xmm0, xmm2
    vpmulld xmm0, xmm0, xmm1
    inc rdi
    jmp fnv1a_loop

fnv1a_done:
    vmovd xmm1, [rel xor_key]
    vpxor xmm0, xmm0, xmm1
    vpextrq rbx, xmm0, 0

    ; Align stack
    sub rsp, 8

    ; Print the hash value as hex
    lea rdi, [rel hex_fmt]
    mov rsi, rbx
    xor rax, rax
    call printf

    ; Print the hash value as qword
    lea rdi, [rel dword_fmt]
    mov rsi, rbx
    xor rax, rax
    call printf

    ; Clean up the stack
    add rsp, 8

    ; exit(0)
    mov rax, 60
    xor rdi, rdi
    syscall

