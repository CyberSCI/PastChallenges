section .data

section .text
    global _start

_start:
    ; Allocate 256 bytes on the stack
    ; sub rsp, 256
    mov rax, 0x43800000
    vmovq xmm0, rax
    vcvttps2dq xmm0, xmm0
    vinserti128 ymm0, ymm0, xmm0, 0

    vmovq xmm1, rsp
    vinserti128 ymm1, ymm1, xmm1, 0
    vpsubq ymm1, ymm1, ymm0
    vmovq rsp, xmm1

    ; Allow the current process to be traced by any process
    ; This allows the program to work when `kernel.yama.ptrace_scope` is set to 1
    ; prctl(PR_SET_PTRACER, PR_SET_PTRACER_ANY)
    mov rax, 0x431d0000 ; prctl (157) in float
    vmovq xmm0, rax
    vcvttps2dq xmm0, xmm0
    vpextrq rax, xmm0, 0

    mov rdi, 0x59616d61 ; PR_SET_PTRACER
    mov rsi, 0xffffffffffffffff ; PR_SET_PTRACER_ANY
    vxorps ymm2, ymm2, ymm2
    vmovq rdx, xmm2; arg3
    vmovq r10, xmm2; arg4
    vmovq r9, xmm2; arg5
    syscall

    ; Fork to a new process to run ptrace on the parent
    mov rax, 0x42640000
    vmovq xmm0, rax
    vcvttps2dq xmm0, xmm0
    vmovq rax, xmm0
    syscall
    mov rbx, rax ; rbx in parent contains child PID
    test rbx, rbx
    jne .parent

.child:
    ; Get parent PID
    mov rax, 0x42dc0000 ; PTRACE_GETPPID (110) in float
    vmovq xmm0, rax
    vcvttps2dq xmm0, xmm0
    vpextrq rax, xmm0, 0
    syscall
    mov rbx, rax ; rbx in child contains parent PID

    ; Use ptrace to trace parent to detect if a debugger is attached
    ; mov rax, 101
    mov rax, 0x42ca0000 ; ptrace (101) in float
    vmovq xmm0, rax
    vcvttps2dq xmm0, xmm0
    vpextrq rax, xmm0, 0

    ; mov rdi, 16 ; request
    mov rdi, 0x41800000 ; PTRACE_ATTACH (16) in float
    vmovq xmm0, rdi
    vcvttps2dq xmm0, xmm0
    vpextrq rdi, xmm0, 0
    mov rsi, rbx ; pid
    vpxor ymm2, ymm2, ymm2
    vmovq rdx, xmm2 ; addr
    vmovq r10, xmm2 ; data
    syscall

    ; Check if PTRACE_ATTACH was successful
    vxorps ymm1, ymm1, ymm1
    vcvtsi2ss xmm1, xmm1, rax
    vptest xmm1, xmm1
    jne .exit1

    ; No debugger attached, resume parent process
    ; wait4(ppid, NULL, 0, NULL)
    mov rax, 0x42740000 ; wait4 (61) in float
    vmovq xmm0, rax
    vcvttps2dq xmm0, xmm0
    vpextrq rax, xmm0, 0
    mov rdi, rbx ; upid = ppid
    vmovq rsi, xmm2
    vmovq rdx, xmm2
    vmovq r10, xmm2
    syscall

    ; ptrace(PTRACE_CONT, ppid, NULL, NULL)
    ; mov rax, 101
    mov rax, 0x42ca0000 ; ptrace (101) in float
    vmovq xmm0, rax
    vcvttps2dq xmm0, xmm0
    vpextrq rax, xmm0, 0

    ; mov rdi, 7 ; request
    mov rdi, 0x40e00000 ; PTRACE_CONT (7) in float
    vmovq xmm0, rdi
    vcvttps2dq xmm0, xmm0
    vpextrq rdi, xmm0, 0
    mov rsi, rbx ; pid
    vmovq rdx, xmm2 ; addr
    vmovq r10, xmm2 ; data
    syscall

    ; ptrace(PTRACE_DETACH, ppid, NULL, NULL)
    ; mov rax, 101
    mov rax, 0x42ca0000 ; ptrace (101) in float
    vmovq xmm0, rax
    vcvttps2dq xmm0, xmm0
    vpextrq rax, xmm0, 0

    ; mov rdi, 17 ; request
    mov rdi, 0x41880000 ; PTRACE_DETACH (17) in float
    vmovq xmm0, rdi
    vcvttps2dq xmm0, xmm0
    vpextrq rdi, xmm0, 0
    mov rsi, rbx ; pid
    vmovq rdx, xmm2 ; addr
    vmovq r10, xmm2 ; data
    syscall

    ; exit(0)
    jmp .exit0

.parent:
    ; wait4(pid, [rsp-8], 0, NULL)
    mov rax, 0x42740000 ; wait4 (61) in float
    vmovq xmm0, rax
    vcvttps2dq xmm0, xmm0
    vpextrq rax, xmm0, 0
    mov rdi, rbx ; upid = pid
    lea rsi, [rsp-8] ; status
    vxorps ymm2, ymm2, ymm2
    vmovq rdx, xmm2
    vmovq r10, xmm2
    syscall

    ; Check the exit code of the child process
    ; Jump to an invalid address if debugger is detected
    lea rbx, [rel .name]
    vmovss xmm0, [rsp-8]
    vptest xmm0, xmm0
    cmove rax, rbx
    jmp rax

.name:
    ; Setup for write to stdout
    vpxor ymm0, ymm0, ymm0
    vpcmpeqd ymm0, ymm0, ymm0
    vpsrld ymm0, ymm0, 31
    vpextrq rax, xmm0, 0
    vpextrq rdi, xmm0, 0
    lea rsi, [rsp-28]

    ; mov rdx, 24
    mov rdx, 0x41c00000
    vmovq xmm2, rdx
    vcvttps2dq xmm2, xmm2
    vpextrq rdx, xmm2, 0

    ; "Please enter your name: "
    mov rbx, 0x61656c50
    vmovq xmm3, rbx
    vmovss dword [rsp-28], xmm3
    mov rbx, 0x65206573
    vmovq xmm3, rbx
    vmovss dword [rsp-24], xmm3
    mov rbx, 0x7265746e
    vmovq xmm3, rbx
    vmovss dword [rsp-20], xmm3
    mov rbx, 0x756f7920
    vmovq xmm3, rbx
    vmovss dword [rsp-16], xmm3
    mov rbx, 0x616e2072
    vmovq xmm3, rbx
    vmovss dword [rsp-12], xmm3
    mov rbx, 0x203a656d
    vmovq xmm3, rbx
    vmovss dword [rsp-8], xmm3
    vxorps xmm3, xmm3, xmm3
    vmovss dword [rsp-4], xmm3
    syscall

    ; Read 64 bytes from stdin, although only 33 bytes are needed
    vxorps ymm0, ymm0, ymm0
    vmovdqu [rsp-128], ymm0
    vmovq rax, xmm0
    vmovq rdi, xmm0
    lea rsi, [rsp-128]

    ; Read 64 bytes to [rsp-128]
    mov rdx, 0x42800000
    vmovq xmm2, rdx
    vcvttps2dq xmm2, xmm2
    vpextrq rdx, xmm2, 0
    syscall

    ; Check if the bytes read are less than 32
    vzeroall
    vcvtsi2ss xmm1, xmm1, rax ; xmm1 contains the number of bytes read

    ; Check if the input is empty
    vpxor ymm0, ymm0, ymm0
    vpcmpeqd ymm0, ymm0, ymm0
    vpsrld ymm0, ymm0, 31
    vcvtdq2ps  xmm0, xmm0
    vucomiss xmm1, xmm0
    jbe .nempty

    mov rbx, 0x42040000 ; 33 in float
    vmovq xmm2, rbx

    ; If we read more than 33 bytes, the input is invalid
    vucomiss xmm1, xmm2
    jbe .regcode

    vcvtsi2ss xmm2, xmm2, rdx
    vucomiss xmm1, xmm2
    jb .invlen1

    ; Check if we need to read more bytes
    cmp byte [rsi+rdx-1], 10
    je .invlen1
    jmp .overflow1

.nempty:
    ; Setup for write to stdout
    vpxor ymm0, ymm0, ymm0
    vpcmpeqd ymm0, ymm0, ymm0
    vpsrld ymm0, ymm0, 31
    vpextrq rax, xmm0, 0
    vpextrq rdi, xmm0, 0
    lea rsi, [rsp-28]

    ; mov rdx, 22
    mov rdx, 0x41b00000
    vmovq xmm2, rdx
    vcvttps2dq xmm2, xmm2
    vpextrq rdx, xmm2, 0

    ; "Name cannot be empty.\n"
    mov rbx, 0x656d614e
    vmovq xmm3, rbx
    vmovss dword [rsp-28], xmm3
    mov rbx, 0x6e616320
    vmovq xmm3, rbx
    vmovss dword [rsp-24], xmm3
    mov rbx, 0x20746f6e
    vmovq xmm3, rbx
    vmovss dword [rsp-20], xmm3
    mov rbx, 0x65206562
    vmovq xmm3, rbx
    vmovss dword [rsp-16], xmm3
    mov rbx, 0x7974706d
    vmovq xmm3, rbx
    vmovss dword [rsp-12], xmm3
    mov rbx, 0xa2e
    vmovq xmm3, rbx
    vmovss dword [rsp-8], xmm3
    vxorps xmm3, xmm3, xmm3
    vmovss dword [rsp-4], xmm3
    syscall
    jmp .exit1

; Read and discard the remaining input
.overflow1:
    vxorps ymm0, ymm0, ymm0
    vmovq rax, xmm0
    vmovq rdi, xmm0
    lea rsi, [rsp-16]

    ; mov rdx, 16
    mov rdx, 0x41800000
    vmovq xmm2, rdx
    vcvttps2dq xmm2, xmm2
    vpextrq rdx, xmm2, 0
    syscall

    vxorps ymm1, ymm1, ymm1
    vxorps ymm2, ymm2, ymm2
    vcvtsi2ss xmm1, xmm1, rax
    vcvtsi2ss xmm2, xmm2, rdx

    ; After reading all remaining bytes, print an error message
    vucomiss xmm1, xmm2
    jb .invlen1

    cmp byte [rsi+rdx-1], 10
    jne .overflow1

.invlen1:
    ; Setup for write to stdout
    vpxor ymm0, ymm0, ymm0
    vpcmpeqd ymm0, ymm0, ymm0
    vpsrld ymm0, ymm0, 31
    vpextrq rax, xmm0, 0
    vpextrq rdi, xmm0, 0
    lea rsi, [rsp-48]

    ; mov rdx, 41
    mov rdx, 0x42240000
    vmovq xmm2, rdx
    vcvttps2dq xmm2, xmm2
    vpextrq rdx, xmm2, 0

    ; "Names can contain at most 32 characters.\n"
    mov rbx, 0x656d614e
    vmovq xmm3, rbx
    vmovss dword [rsp-48], xmm3
    mov rbx, 0x61632073
    vmovq xmm3, rbx
    vmovss dword [rsp-44], xmm3
    mov rbx, 0x6f63206e
    vmovq xmm3, rbx
    vmovss dword [rsp-40], xmm3
    mov rbx, 0x6961746e
    vmovq xmm3, rbx
    vmovss dword [rsp-36], xmm3
    mov rbx, 0x7461206e
    vmovq xmm3, rbx
    vmovss dword [rsp-32], xmm3
    mov rbx, 0x736f6d20
    vmovq xmm3, rbx
    vmovss dword [rsp-28], xmm3
    mov rbx, 0x32332074
    vmovq xmm3, rbx
    vmovss dword [rsp-24], xmm3
    mov rbx, 0x61686320
    vmovq xmm3, rbx
    vmovss dword [rsp-20], xmm3
    mov rbx, 0x74636172
    vmovq xmm3, rbx
    vmovss dword [rsp-16], xmm3
    mov rbx, 0x2e737265
    vmovq xmm3, rbx
    vmovss dword [rsp-12], xmm3
    mov rbx, 0xa
    vmovq xmm3, rbx
    vmovss dword [rsp-8], xmm3
    vxorps xmm3, xmm3, xmm3
    vmovss dword [rsp-4], xmm3
    syscall
    jmp .exit1

.regcode:
    ; Remove the newline character
    mov byte [rsi+rax-1], 0

    ; Setup for write to stdout
    vpxor ymm0, ymm0, ymm0
    vpcmpeqd ymm0, ymm0, ymm0
    vpsrld ymm0, ymm0, 31
    vpextrq rax, xmm0, 0
    vpextrq rdi, xmm0, 0
    lea rsi, [rsp-44]

    ; mov rdx, 37
    mov rdx, 0x42140000
    vmovq xmm2, rdx
    vcvttps2dq xmm2, xmm2
    vpextrq rdx, xmm2, 0

    ; "Please enter your registration code: "
    mov rbx, 0x61656c50
    vmovq xmm3, rbx
    vmovss dword [rsp-44], xmm3
    mov rbx, 0x65206573
    vmovq xmm3, rbx
    vmovss dword [rsp-40], xmm3
    mov rbx, 0x7265746e
    vmovq xmm3, rbx
    vmovss dword [rsp-36], xmm3
    mov rbx, 0x756f7920
    vmovq xmm3, rbx
    vmovss dword [rsp-32], xmm3
    mov rbx, 0x65722072
    vmovq xmm3, rbx
    vmovss dword [rsp-28], xmm3
    mov rbx, 0x74736967
    vmovq xmm3, rbx
    vmovss dword [rsp-24], xmm3
    mov rbx, 0x69746172
    vmovq xmm3, rbx
    vmovss dword [rsp-20], xmm3
    mov rbx, 0x63206e6f
    vmovq xmm3, rbx
    vmovss dword [rsp-16], xmm3
    mov rbx, 0x3a65646f
    vmovq xmm3, rbx
    vmovss dword [rsp-12], xmm3
    mov rbx, 0x20
    vmovq xmm3, rbx
    vmovss dword [rsp-8], xmm3
    vxorps xmm3, xmm3, xmm3
    vmovss dword [rsp-4], xmm3
    syscall

    ; Read 64 bytes from stdin, although only 20 bytes are needed
    vxorps ymm0, ymm0, ymm0
    vmovdqu [rsp-192], ymm0
    vmovq rax, xmm0
    vmovq rdi, xmm0
    lea rsi, [rsp-192]

    ; Read 64 bytes to [rsp-192]
    mov rdx, 0x42800000
    vmovq xmm2, rdx
    vcvttps2dq xmm2, xmm2
    vpextrq rdx, xmm2, 0
    syscall

    ; Check if the bytes read are less than 11
    vzeroall
    vcvtsi2ss xmm1, xmm1, rax ; xmm1 contains the number of bytes read

    ; Check if the input is empty
    vpxor ymm0, ymm0, ymm0
    vpcmpeqd ymm0, ymm0, ymm0
    vpsrld ymm0, ymm0, 31
    vcvtdq2ps  xmm0, xmm0
    vucomiss xmm1, xmm0
    jbe .tempty

    mov rbx, 0x41300000 ; 11 in float
    vmovq xmm2, rbx

    ; If we read more than 11 bytes, the input is invalid
    vucomiss xmm1, xmm2
    jbe .atoi

    vcvtsi2ss xmm2, xmm2, rdx
    vucomiss xmm1, xmm2
    jb .invlen2

    ; Check if we need to read more bytes
    cmp byte [rsi+rdx-1], 10
    je .invlen2
    jmp .overflow2

.tempty:
    ; Setup for write to stdout
    vpxor ymm0, ymm0, ymm0
    vpcmpeqd ymm0, ymm0, ymm0
    vpsrld ymm0, ymm0, 31
    vpextrq rax, xmm0, 0
    vpextrq rdi, xmm0, 0
    lea rsi, [rsp-44]

    ; mov rdx, 39
    mov rdx, 0x421c0000
    vmovq xmm2, rdx
    vcvttps2dq xmm2, xmm2
    vpextrq rdx, xmm2, 0

    ; "The registration code cannot be empty.\n"
    mov rbx, 0x20656854
    vmovq xmm3, rbx
    vmovss dword [rsp-44], xmm3
    mov rbx, 0x69676572
    vmovq xmm3, rbx
    vmovss dword [rsp-40], xmm3
    mov rbx, 0x61727473
    vmovq xmm3, rbx
    vmovss dword [rsp-36], xmm3
    mov rbx, 0x6e6f6974
    vmovq xmm3, rbx
    vmovss dword [rsp-32], xmm3
    mov rbx, 0x646f6320
    vmovq xmm3, rbx
    vmovss dword [rsp-28], xmm3
    mov rbx, 0x61632065
    vmovq xmm3, rbx
    vmovss dword [rsp-24], xmm3
    mov rbx, 0x746f6e6e
    vmovq xmm3, rbx
    vmovss dword [rsp-20], xmm3
    mov rbx, 0x20656220
    vmovq xmm3, rbx
    vmovss dword [rsp-16], xmm3
    mov rbx, 0x74706d65
    vmovq xmm3, rbx
    vmovss dword [rsp-12], xmm3
    mov rbx, 0xa2e79
    vmovq xmm3, rbx
    vmovss dword [rsp-8], xmm3
    vxorps xmm3, xmm3, xmm3
    vmovss dword [rsp-4], xmm3
    syscall
    jmp .exit1

; Read and discard the remaining input
.overflow2:
    vxorps ymm0, ymm0, ymm0
    vmovq rax, xmm0
    vmovq rdi, xmm0
    lea rsi, [rsp-16]

    ; mov rdx, 16
    mov rdx, 0x41800000
    vmovq xmm2, rdx
    vcvttps2dq xmm2, xmm2
    vpextrq rdx, xmm2, 0
    syscall

    vxorps ymm1, ymm1, ymm1
    vxorps ymm2, ymm2, ymm2
    vcvtsi2ss xmm1, xmm1, rax
    vcvtsi2ss xmm2, xmm2, rdx

    ; After reading all remaining bytes, print an error message
    vucomiss xmm1, xmm2
    jb .invlen2

    cmp byte [rsi+rdx-1], 10
    jne .overflow2

.invlen2:
    ; Setup for write to stdout
    vpxor ymm0, ymm0, ymm0
    vpcmpeqd ymm0, ymm0, ymm0
    vpsrld ymm0, ymm0, 31
    vpextrq rax, xmm0, 0
    vpextrq rdi, xmm0, 0
    lea rsi, [rsp-60]

    ; mov rdx, 54
    mov rdx, 0x42580000
    vmovq xmm2, rdx
    vcvttps2dq xmm2, xmm2
    vpextrq rdx, xmm2, 0

    ; "Registration codes can contain at most 10 characters.\n"
    mov rbx, 0x69676552
    vmovq xmm3, rbx
    vmovss dword [rsp-60], xmm3
    mov rbx, 0x61727473
    vmovq xmm3, rbx
    vmovss dword [rsp-56], xmm3
    mov rbx, 0x6e6f6974
    vmovq xmm3, rbx
    vmovss dword [rsp-52], xmm3
    mov rbx, 0x646f6320
    vmovq xmm3, rbx
    vmovss dword [rsp-48], xmm3
    mov rbx, 0x63207365
    vmovq xmm3, rbx
    vmovss dword [rsp-44], xmm3
    mov rbx, 0x63206e61
    vmovq xmm3, rbx
    vmovss dword [rsp-40], xmm3
    mov rbx, 0x61746e6f
    vmovq xmm3, rbx
    vmovss dword [rsp-36], xmm3
    mov rbx, 0x61206e69
    vmovq xmm3, rbx
    vmovss dword [rsp-32], xmm3
    mov rbx, 0x6f6d2074
    vmovq xmm3, rbx
    vmovss dword [rsp-28], xmm3
    mov rbx, 0x32207473
    vmovq xmm3, rbx
    vmovss dword [rsp-24], xmm3
    mov rbx, 0x68632030
    vmovq xmm3, rbx
    vmovss dword [rsp-20], xmm3
    mov rbx, 0x63617261
    vmovq xmm3, rbx
    vmovss dword [rsp-16], xmm3
    mov rbx, 0x73726574
    vmovq xmm3, rbx
    vmovss dword [rsp-12], xmm3
    mov rbx, 0xa2e
    vmovq xmm3, rbx
    vmovss dword [rsp-8], xmm3
    vxorps xmm3, xmm3, xmm3
    vmovss dword [rsp-4], xmm3
    syscall
    jmp .exit1

.atoi:
    vpxor ymm5, ymm5, ymm5 ; ymm5 stores the result of the atoi function
    lea rdi, [rsp-192]

.atoiloop:
    movzx rax, byte [rdi]
    vmovq xmm0, rax
    vinserti128 ymm0, ymm0, xmm0, 0

    ; sub rax, '0'
    mov rax, 0x30 ; '0'
    vmovq xmm1, rax
    vinserti128 ymm1, ymm1, xmm1, 0
    vpsubq ymm0, ymm0, ymm1

    ; imul rbx, rbx, 10
    mov rax, 10
    vmovq xmm2, rax
    vinserti128 ymm2, ymm2, xmm2, 0
    vpmulld ymm5, ymm5, ymm2

    ; add rbx, rax
    vpaddd ymm5, ymm5, ymm0

    ; inc rdi
    vpxor ymm1, ymm1, ymm1
    vpcmpeqq ymm0, ymm1, ymm1
    vpsrlq ymm0, ymm0, 63
    vmovq xmm1, rdi
    vinserti128 ymm1, ymm1, xmm1, 0
    vpaddd ymm1, ymm1, ymm0
    vpextrq rdi, xmm1, 0

    ; Check if the next byte is a newline
    cmp byte [rdi], 10
    je .verify

    ; Check if next byte is null
    cmp byte [rdi], 0
    jne .atoiloop

; Verify if the password is correct with FNV-1a and XOR
.verify:
    vmovd xmm0, [rel .fnv1a_offset_basis]
    vmovd xmm1, [rel .fnv1a_prime]
    lea rdi, [rsp-128]

.fnv1a_loop:
    vpxor xmm4, xmm4, xmm4
    vpinsrb xmm4, xmm4, byte [rdi], 0
    vptest xmm4, xmm4
    jz .fnv1a_done
    vpxor xmm2, xmm2, xmm2
    vpinsrb xmm2, xmm2, byte [rdi], 0
    vpxor xmm0, xmm0, xmm2
    vpmulld xmm0, xmm0, xmm1

    ; inc rdi
    vpxor ymm2, ymm2, ymm2
    vpcmpeqq ymm2, ymm2, ymm2
    vpsrlq ymm2, ymm2, 63
    vmovq xmm4, rdi
    vinserti128 ymm4, ymm4, xmm4, 0
    vpaddd ymm4, ymm4, ymm2
    vpextrq rdi, xmm4, 0
    jmp .fnv1a_loop

.fnv1a_done:
    vmovd xmm1, [rel .xor_key]
    vpxor xmm0, xmm0, xmm1
    vpxor xmm0, xmm0, xmm5
    vptest xmm0, xmm0
    jz .correct

.incorrect:
    vpxor ymm0, ymm0, ymm0
    vpcmpeqd ymm0, ymm0, ymm0
    vpsrld ymm0, ymm0, 31
    vpextrq rax, xmm0, 0
    vpextrq rdi, xmm0, 0
    lea rsi, [rsp-44]

    ; mov rdx, 36
    mov rbx, 0x42100000
    vmovq xmm3, rbx
    vcvttps2dq xmm3, xmm3
    vpextrq rdx, xmm3, 0

    ; "Invalid registration code provided.\n"
    mov rbx, 0x61766e49
    vmovq xmm3, rbx
    vmovss dword [rsp-44], xmm3
    mov rbx, 0x2064696c
    vmovq xmm3, rbx
    vmovss dword [rsp-40], xmm3
    mov rbx, 0x69676572
    vmovq xmm3, rbx
    vmovss dword [rsp-36], xmm3
    mov rbx, 0x61727473
    vmovq xmm3, rbx
    vmovss dword [rsp-32], xmm3
    mov rbx, 0x6e6f6974
    vmovq xmm3, rbx
    vmovss dword [rsp-28], xmm3
    mov rbx, 0x646f6320
    vmovq xmm3, rbx
    vmovss dword [rsp-24], xmm3
    mov rbx, 0x72702065
    vmovq xmm3, rbx
    vmovss dword [rsp-20], xmm3
    mov rbx, 0x6469766f
    vmovq xmm3, rbx
    vmovss dword [rsp-16], xmm3
    mov rbx, 0xa2e6465
    vmovq xmm3, rbx
    vmovss dword [rsp-12], xmm3
    vxorps xmm3, xmm3, xmm3
    vmovss dword [rsp-8], xmm3
    syscall

.exit1:
    ; add rsp, 256
    mov rax, 0x43800000
    vmovq xmm0, rax
    vcvttps2dq xmm0, xmm0
    vinserti128 ymm0, ymm0, xmm0, 0

    vmovq xmm1, rsp
    vinserti128 ymm1, ymm1, xmm1, 0
    vpaddq ymm1, ymm1, ymm0
    vmovq rsp, xmm1

    ; exit(1)
    mov rax, 0x42700000
    vmovq xmm1, rax
    vcvttps2dq xmm1, xmm1
    vpextrq rax, xmm1, 0

    vpxor ymm0, ymm0, ymm0
    vpcmpeqd ymm0, ymm0, ymm0
    vpsrld ymm0, ymm0, 31
    vpextrq rdi, xmm0, 0
    syscall

.correct:
    vpxor ymm0, ymm0, ymm0
    vpcmpeqd ymm0, ymm0, ymm0
    vpsrld ymm0, ymm0, 31
    vpextrq rax, xmm0, 0
    vpextrq rdi, xmm0, 0
    lea rsi, [rsp-40]

    ; mov rdx, 34
    mov rbx, 0x42080000
    vmovq xmm3, rbx
    vcvttps2dq xmm3, xmm3
    vpextrq rdx, xmm3, 0

    ; "Your identity has been validated.\n"
    mov rbx, 0x72756f59
    vmovq xmm3, rbx
    vmovss dword [rsp-40], xmm3
    mov rbx, 0x65646920
    vmovq xmm3, rbx
    vmovss dword [rsp-36], xmm3
    mov rbx, 0x7469746e
    vmovq xmm3, rbx
    vmovss dword [rsp-32], xmm3
    mov rbx, 0x61682079
    vmovq xmm3, rbx
    vmovss dword [rsp-28], xmm3
    mov rbx, 0x65622073
    vmovq xmm3, rbx
    vmovss dword [rsp-24], xmm3
    mov rbx, 0x76206e65
    vmovq xmm3, rbx
    vmovss dword [rsp-20], xmm3
    mov rbx, 0x64696c61
    vmovq xmm3, rbx
    vmovss dword [rsp-16], xmm3
    mov rbx, 0x64657461
    vmovq xmm3, rbx
    vmovss dword [rsp-12], xmm3
    mov rbx, 0xa2e
    vmovq xmm3, rbx
    vmovss dword [rsp-8], xmm3
    vxorps xmm3, xmm3, xmm3
    vmovss dword [rsp-4], xmm3
    syscall

.exit0:
    ; add rsp, 256
    mov rax, 0x43800000
    vmovq xmm0, rax
    vcvttps2dq xmm0, xmm0
    vinserti128 ymm0, ymm0, xmm0, 0

    vmovq xmm1, rsp
    vinserti128 ymm1, ymm1, xmm1, 0
    vpaddq ymm1, ymm1, ymm0
    vmovq rsp, xmm1

    ; exit(0)
    mov rax, 0x42700000
    vmovq xmm1, rax
    vcvttps2dq xmm1, xmm1
    vpextrq rax, xmm1, 0
    vxorps xmm1, xmm1, xmm1
    vpextrq rdi, xmm1, 0
    syscall

; Below is used as the .data section to store static data
; RIP will never reach below this point

; If the participants change this byte to 0xC3 (ret)
; IDA will be able to generate a CFG for the code above
.helper_byte:
    db 0
    ; db 0xC3

.xor_key:
    db "CYBERSCI_REGIONALS_2025"

.fnv1a_offset_basis:
    dd 2166136261

.fnv1a_prime:
    dd 16777619

