/*
 * CEREBRUM VM - Custom virtual machine for CTF
 * The flag is computed by VM bytecode execution.
 * Bytecode is XOR-encrypted at rest (simpler than AES for CTF portability).
 *
 * VM Architecture:
 *   - 8 registers: R0-R7 (32-bit)
 *   - 256 bytes memory
 *   - 64-entry stack
 *   - PC (program counter)
 *   - ZF (zero flag)
 *
 * Instruction format: [opcode] [operands...]
 *   Variable length depending on opcode.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define NUM_REGS    8
#define MEM_SIZE    256
#define STACK_SIZE  64
#define MAX_PROG    512

/* Opcodes */
#define OP_NOP      0x00
#define OP_MOV_IMM  0x10  /* MOV Rx, imm16 */
#define OP_MOV_REG  0x11  /* MOV Rx, Ry */
#define OP_ADD      0x20  /* ADD Rx, Ry */
#define OP_SUB      0x21  /* SUB Rx, Ry */
#define OP_XOR      0x22  /* XOR Rx, Ry */
#define OP_MUL      0x23  /* MUL Rx, Ry */
#define OP_AND      0x24  /* AND Rx, Ry */
#define OP_OR       0x25  /* OR  Rx, Ry */
#define OP_SHR      0x26  /* SHR Rx, imm8 */
#define OP_SHL      0x27  /* SHL Rx, imm8 */
#define OP_ADD_IMM  0x28  /* ADD Rx, imm8 */
#define OP_XOR_IMM  0x29  /* XOR Rx, imm8 */
#define OP_CMP      0x30  /* CMP Rx, Ry (sets ZF) */
#define OP_CMP_IMM  0x31  /* CMP Rx, imm8 */
#define OP_JMP      0x40  /* JMP addr16 */
#define OP_JZ       0x41  /* JZ  addr16 */
#define OP_JNZ      0x42  /* JNZ addr16 */
#define OP_STORE    0x50  /* STORE [Rx], Ry */
#define OP_LOAD     0x51  /* LOAD Rx, [Ry] */
#define OP_STORE_I  0x52  /* STORE [imm8], Rx */
#define OP_LOAD_I   0x53  /* LOAD Rx, [imm8] */
#define OP_PUSH     0x60  /* PUSH Rx */
#define OP_POP      0x61  /* POP  Rx */
#define OP_PUTC     0x70  /* PUTC Rx (print low byte as char) */
#define OP_HALT     0xFF  /* HALT */

typedef struct {
    uint32_t regs[NUM_REGS];
    uint8_t  mem[MEM_SIZE];
    uint32_t stack[STACK_SIZE];
    int      sp;
    int      pc;
    int      zf;
    uint8_t  prog[MAX_PROG];
    int      prog_len;
} VM;

static void vm_init(VM *vm, uint8_t *bytecode, int len) {
    memset(vm, 0, sizeof(VM));
    memcpy(vm->prog, bytecode, len);
    vm->prog_len = len;
    vm->sp = -1;
}

static uint8_t fetch8(VM *vm) { return vm->prog[vm->pc++]; }
static uint16_t fetch16(VM *vm) {
    uint16_t v = vm->prog[vm->pc] | (vm->prog[vm->pc+1] << 8);
    vm->pc += 2;
    return v;
}

static int vm_run(VM *vm) {
    int cycles = 0;
    while (vm->pc < vm->prog_len && cycles < 100000) {
        uint8_t op = fetch8(vm);
        uint8_t rx, ry, imm8;
        uint16_t imm16;
        cycles++;

        switch (op) {
        case OP_NOP: break;
        case OP_MOV_IMM:
            rx = fetch8(vm); imm16 = fetch16(vm);
            vm->regs[rx & 7] = imm16;
            break;
        case OP_MOV_REG:
            rx = fetch8(vm); ry = fetch8(vm);
            vm->regs[rx & 7] = vm->regs[ry & 7];
            break;
        case OP_ADD:
            rx = fetch8(vm); ry = fetch8(vm);
            vm->regs[rx & 7] += vm->regs[ry & 7];
            break;
        case OP_SUB:
            rx = fetch8(vm); ry = fetch8(vm);
            vm->regs[rx & 7] -= vm->regs[ry & 7];
            break;
        case OP_XOR:
            rx = fetch8(vm); ry = fetch8(vm);
            vm->regs[rx & 7] ^= vm->regs[ry & 7];
            break;
        case OP_MUL:
            rx = fetch8(vm); ry = fetch8(vm);
            vm->regs[rx & 7] *= vm->regs[ry & 7];
            break;
        case OP_AND:
            rx = fetch8(vm); ry = fetch8(vm);
            vm->regs[rx & 7] &= vm->regs[ry & 7];
            break;
        case OP_OR:
            rx = fetch8(vm); ry = fetch8(vm);
            vm->regs[rx & 7] |= vm->regs[ry & 7];
            break;
        case OP_SHR:
            rx = fetch8(vm); imm8 = fetch8(vm);
            vm->regs[rx & 7] >>= imm8;
            break;
        case OP_SHL:
            rx = fetch8(vm); imm8 = fetch8(vm);
            vm->regs[rx & 7] <<= imm8;
            break;
        case OP_ADD_IMM:
            rx = fetch8(vm); imm8 = fetch8(vm);
            vm->regs[rx & 7] += imm8;
            break;
        case OP_XOR_IMM:
            rx = fetch8(vm); imm8 = fetch8(vm);
            vm->regs[rx & 7] ^= imm8;
            break;
        case OP_CMP:
            rx = fetch8(vm); ry = fetch8(vm);
            vm->zf = (vm->regs[rx & 7] == vm->regs[ry & 7]);
            break;
        case OP_CMP_IMM:
            rx = fetch8(vm); imm8 = fetch8(vm);
            vm->zf = (vm->regs[rx & 7] == imm8);
            break;
        case OP_JMP:
            imm16 = fetch16(vm);
            vm->pc = imm16;
            break;
        case OP_JZ:
            imm16 = fetch16(vm);
            if (vm->zf) vm->pc = imm16;
            break;
        case OP_JNZ:
            imm16 = fetch16(vm);
            if (!vm->zf) vm->pc = imm16;
            break;
        case OP_STORE:
            rx = fetch8(vm); ry = fetch8(vm);
            vm->mem[vm->regs[rx & 7] & 0xFF] = (uint8_t)(vm->regs[ry & 7]);
            break;
        case OP_LOAD:
            rx = fetch8(vm); ry = fetch8(vm);
            vm->regs[rx & 7] = vm->mem[vm->regs[ry & 7] & 0xFF];
            break;
        case OP_STORE_I:
            imm8 = fetch8(vm); rx = fetch8(vm);
            vm->mem[imm8] = (uint8_t)(vm->regs[rx & 7]);
            break;
        case OP_LOAD_I:
            rx = fetch8(vm); imm8 = fetch8(vm);
            vm->regs[rx & 7] = vm->mem[imm8];
            break;
        case OP_PUSH:
            rx = fetch8(vm);
            if (vm->sp < STACK_SIZE - 1)
                vm->stack[++vm->sp] = vm->regs[rx & 7];
            break;
        case OP_POP:
            rx = fetch8(vm);
            if (vm->sp >= 0)
                vm->regs[rx & 7] = vm->stack[vm->sp--];
            break;
        case OP_PUTC:
            rx = fetch8(vm);
            putchar((char)(vm->regs[rx & 7] & 0xFF));
            break;
        case OP_HALT:
            return 0;
        default:
            return -1;
        }
    }
    return (cycles >= 100000) ? -2 : 0;
}


#include "bytecode.h"

static void decrypt_bytecode(uint8_t *out, const uint8_t *enc, int len, uint8_t key) {
    for (int i = 0; i < len; i++) {
        out[i] = enc[i] ^ key;
    }
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);

    printf("[ CEREBRUM VM v1.0 ]\n");
    printf("[ Decrypting bytecode... ]\n");

    uint8_t bytecode[MAX_PROG];
    decrypt_bytecode(bytecode, encrypted_bytecode, ENCRYPTED_BYTECODE_LEN, BYTECODE_XOR_KEY);

    printf("[ Executing virtual program ]\n");
    printf("[ Output: ");

    VM vm;
    vm_init(&vm, bytecode, ENCRYPTED_BYTECODE_LEN);
    int result = vm_run(&vm);

    if (result == 0) {
        printf("[ VM halted successfully ]\n");
    } else {
        printf("\n[ VM ERROR: code %d ]\n", result);
    }

    return 0;
}
