#include <cstdlib>
#include <stdio.h>
#include <stdint.h>
#include <stack>
#include <functional>
#include <iostream>

typedef unsigned int uint;

uint16_t r[4] = { 0, 0, 0, 0 };
bool zero_flag = 0;
std::stack<uint16_t> stack;

union {
    uint16_t full;
    struct {
        uint8_t first;
        uint8_t second;
    } parts;
} conv;

void state() {
    for (int i = 0; i < 4; ++i) {
        conv.full = r[i];
        fprintf(stderr, "r%1d = %02x %02x, ", i, conv.parts.first, conv.parts.second);
    }
    fprintf(stderr, "ZF = %d\n", zero_flag);
}

struct {
    uint code : 8;
    uint mod : 4;
    uint dest_reg : 2;
    uint src_reg : 2;
    uint imm : 16;
} inst;

void print_registers() {
    for (int i = 0; i < 4; ++i) {
        conv.full = r[i];
        printf("%02x%02x ", conv.parts.first, conv.parts.second);
        // printf("%04x ", conv.full);
    }
    puts("");
}

uint16_t pop() {
    if (stack.empty()) {
        puts("Empty stack!");
        // exit(1);
    }
    uint16_t val = stack.top();
    stack.pop();
    return val;
}

void push(uint16_t val) {
    stack.push(val);
}

void one_arg_op(std::function<uint16_t(uint16_t)> f) {
    uint16_t result;
    switch(inst.mod) {
        case 0x0:
            result = f(inst.imm);
            break;
        case 0x1:
            result = f(r[inst.dest_reg]);
            r[inst.dest_reg] = result;
            break;
        default:
            std::cerr << __FUNCTION__
                      << ": That was unexpected!\n";
            // print_registers();
            // exit(1);
    }
    zero_flag = (result == 0);
}

void two_args_op(std::function<uint16_t(uint16_t, uint16_t)> f) {
    uint16_t second;
    switch(inst.mod) {
        case 0x2:
            second = inst.imm;
            break;
        case 0x3:
            second = r[inst.src_reg];
            break;
        default:
            std::cerr << __FUNCTION__
                      << ": That was unexpected!\n";
            // print_registers();
            // exit(1);
    }
    r[inst.dest_reg] = f(r[inst.dest_reg], second);
    zero_flag = (r[inst.dest_reg] == 0);
}

FILE *f;

void jmp(int new_inst) {
    int new_pos = new_inst * sizeof(inst);
    if (new_pos == (ftell(f) - sizeof(inst))) {
        std::cerr << "jump to same destination, exiting\n";
        // exit(1);
    }
    fseek(f, new_pos, SEEK_SET);
}

int main(int argc, char const *argv[]) {
    f = fopen("test.bin", "rb");
    if (f == NULL) {
        puts("Error opening file.");
        return 1;
    }

    while (fread(&inst, sizeof(inst), 1, f)) {
        fprintf(stderr, "%04x | code: %02x | mod: %01x | "
                        "dest_reg: %01x | src_reg: %01x | "
                        "imm: %04x\n",
               ftell(f) - sizeof(inst),
               inst.code,
               inst.mod,
               inst.dest_reg,
               inst.src_reg,
               inst.imm);
        switch (inst.code) {
            case 0x00: // move
                two_args_op([](uint16_t _, uint16_t v){return v;});
                break;
            case 0x01: // bitwise or
                two_args_op(std::bit_or<uint16_t>());
                break;
            case 0x02: // bitwise xor
                two_args_op(std::bit_xor<uint16_t>());
                break;
            case 0x03: // bitwise and
                two_args_op(std::bit_and<uint16_t>());
                break;
            case 0x04: // bitwise negation
                one_arg_op(std::bit_not<uint16_t>());
                break;
            case 0x05: // addition
                two_args_op(std::plus<uint16_t>());
                break;
            case 0x06: // subtraction
                two_args_op(std::minus<uint16_t>());
                break;
            case 0x07: // multiplication
                two_args_op(std::multiplies<uint16_t>());
                break;
            case 0x08: // shift left
                two_args_op([](uint16_t a, uint16_t b){return a << b;});
                break;
            case 0x09: // shift right
                two_args_op([](uint16_t a, uint16_t b){return a >> b;});
                break;
            case 0x0a: // increment
                one_arg_op([](uint16_t v){return v + 1;});
                break;
            case 0x0b: // decrement
                one_arg_op([](uint16_t v){return v - 1;});
                break;
            // case 0x0c: // push on stack
            //     push(other_operand());
            //     break;
            // case 0x0d: // pop from stack
            //     *dest_reg = pop();
            //     break;
            // case 0x0e: // compare
            //     {
            //         uint16_t val = *dest_reg - other_operand();
            //         zero_flag = (val == 0);
            //     }
            //     break;
            // case 0x0f: // jnz
            //     if (!zero_flag) {
            //         uint16_t new_inst = other_operand();
            //         jmp(new_inst);
            //     }
            //     break;
            // case 0x10: // jz
            //     if (zero_flag) {
            //         uint16_t new_inst = other_operand();
            //         jmp(new_inst);
            //     }
            //     break;
            default:
                // print_registers();
                std::cerr << "unexpected opcode\n";
                // exit(1);

        }
        state();
    }
    fclose(f);
    print_registers();
    return 0;
}
