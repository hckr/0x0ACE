#include <cstdlib>
#include <stdio.h>
#include <stdint.h>
#include <stack>
#include <functional>
#include <iostream>
#include <vector>

struct ProgramInstruction {
    uint8_t code, mod, dest_reg, src_reg;
    uint16_t imm;
};

int read_instruction(FILE *file, ProgramInstruction *inst) {
    struct {
        uint code : 8;
        uint mod : 4;
        uint dest_reg : 2;
        uint src_reg : 2;
    } instruction;
    int ret = fread(&instruction, 2, 1, file);
    inst->code = instruction.code;
    inst->mod = instruction.mod;
    inst->dest_reg = instruction.dest_reg;
    inst->src_reg = instruction.src_reg;
    if (inst->mod == 0 || inst->mod == 2) {
        ret = fread(&inst->imm, 2, 1, file);
    }
    return ret;
}

void print_instruction(ProgramInstruction &inst) {
    static std::vector<std::string> mnemonics = {
        "MOV",
        "OR",
        "XOR",
        "AND",
        "NEG",
        "ADD",
        "SUB",
        "MUL",
        "SHL",
        "SHR",
        "INC",
        "DEC",
        "PUSH",
        "POP",
        "CMP",
        "JNZ",
        "JZ"
    };
    const char *mnemo = mnemonics.at(inst.code).c_str();
    fprintf(stderr, "[%02x] %s ", inst.code, mnemo);
    switch (inst.mod) {
        case 0x0:
            fprintf(stderr, "%04x\n", inst.imm);
            break;
        case 0x1:
            fprintf(stderr, "R%d\n", inst.dest_reg);
            break;
        case 0x2:
            fprintf(stderr, "R%d, %04x\n", inst.dest_reg, inst.imm);
            break;
        case 0x3:
            fprintf(stderr, "R%d, R%d\n", inst.dest_reg, inst.src_reg);
            break;
    }
}

std::vector<ProgramInstruction> load_instructions(const char *file_name) {
    FILE *file = fopen(file_name, "rb");
    if (file == NULL) {
        puts("Error opening file.");
        exit(1);
    }
    std::vector<ProgramInstruction> instructions;
    ProgramInstruction inst;
    while (read_instruction(file, &inst)) {
        instructions.push_back(inst);
    }
    fclose(file);
    return std::move(instructions);
}

int main(int argc, char const *argv[]) {
    uint16_t registers[4] = { 0, 0, 0, 0 };
    bool zero_flag = 0;

    auto print_state = [&](FILE *out = stderr) {
        for (int i = 0; i < 4; ++i) {
            fprintf(out, "r%1d = %04x, ", i, registers[i]);
        }
        fprintf(out, "ZF = %d\n", zero_flag);
    };

    std::vector<ProgramInstruction> instructions = load_instructions("test.bin");

    for (int pc = 0; pc < instructions.size();) {
        fprintf(stderr, "pc: %02x\n", pc);
        print_state();

        ProgramInstruction &inst = instructions[pc];
        print_instruction(instructions[pc]);

        uint8_t &dest_reg = inst.dest_reg;
        uint16_t other_val = 0xffff;
        switch (inst.mod) {
            case 0x2:
                other_val = inst.imm;
                break;
            case 0x3:
                other_val = registers[inst.src_reg];
                break;
        }

        switch (inst.code) {
            case 0x00:
                registers[dest_reg] = other_val;
                break;
            case 0x01:
                registers[dest_reg] |= other_val;
                break;
            case 0x02:
                registers[dest_reg] ^= other_val;
                break;
            case 0x03:
                registers[dest_reg] &= other_val;
                break;
            case 0x04:
                registers[dest_reg] = ~registers[dest_reg];
                break;
            case 0x05:
                registers[dest_reg] += other_val;
                break;
            case 0x06:
                registers[dest_reg] -= other_val;
                break;
            case 0x07:
                registers[dest_reg] *= other_val;
                break;
            case 0x08:
                registers[dest_reg] <<= other_val;
                break;
            case 0x09:
                registers[dest_reg] >>= other_val;
                break;
            case 0x0a:
                registers[dest_reg] += 1;
                break;
            case 0x0b:
                registers[dest_reg] -= 1;
                break;
            case 0x0f:
                if (zero_flag == 0) {
                    pc = inst.imm;
                    continue;
                }
                break;
            case 0x10:
                if (zero_flag == 1) {
                    pc = inst.imm;
                    continue;
                }
                break;
            default:
                fprintf(stderr, "Unsupported opcode: %02x\n", inst.code);
                exit(1);
        }
        zero_flag = (registers[dest_reg] == 0);
        pc += 1;
    }

    union {
        uint16_t full;
        struct {
            uint8_t first;
            uint8_t second;
        } parts;
    } conv;

    printf("%04x %04x %04x %04x\n", registers[0], registers[1], registers[2], registers[3]);

    return 0;
}
