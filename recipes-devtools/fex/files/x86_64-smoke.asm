; SPDX-License-Identifier: MIT
; Static, sectionless ELF64: NASM emits both headers and code, so no x86
; cross-linker, guest libc, prebuilt binary or network download is required.
BITS 64
ORG 0x400000

ehdr:
    db 0x7f, "ELF", 2, 1, 1, 0
    times 8 db 0
    dw 2, 62
    dd 1
    dq entry
    dq phdr - $$
    dq 0
    dd 0
    dw 64, 56, 1, 0, 0, 0
phdr:
    dd 1, 5                 ; PT_LOAD, read/execute
    dq 0, $$, $$
    dq file_end - $$, file_end - $$
    dq 0x1000

entry:
    xor eax, eax
    mov ecx, 10000
.sum:
    add rax, rcx
    dec ecx
    jnz .sum
    cmp rax, 50005000
    jne .fail

    ; Exercise SSE2 (baseline x86-64), then check the computed result.
    mov eax, 21
    movd xmm0, eax
    paddd xmm0, xmm0
    movd eax, xmm0
    cmp eax, 42
    jne .fail

    mov eax, 1              ; Linux x86-64 write(1, message, length)
    mov edi, 1
    lea rsi, [rel message]
    mov edx, message_end - message
    syscall
    cmp rax, message_end - message
    jne .fail
    xor edi, edi
    jmp .exit
.fail:
    mov edi, 1
.exit:
    mov eax, 60             ; Linux x86-64 exit(status)
    syscall
message:
    db "FEX x86-64 integer/SSE2/syscall smoke: PASS", 10
message_end:
file_end:
