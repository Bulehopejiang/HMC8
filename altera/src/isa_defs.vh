// ============================================================================
//  isa_defs.vh —— 由 verify/isa_gen.py 从 verify/isa.json 自动生成，请勿手改
//  作用：RTL 里不再出现 6'd27 这类魔法数字；改 ISA 只改 json 再重新生成
// ============================================================================
`ifndef ISA_DEFS_VH
`define ISA_DEFS_VH

`define ISA_WORD_BITS   24
`define ISA_PROM_DEPTH  1024
`define ISA_GPR_COUNT   16
`define ISA_GPR_BITS    16
`define ISA_RAM_DEPTH   2048
`define ISA_SFR_COUNT   2

`define OP_NOP   6'd0   // 不改变任何状态
`define OP_ADDI  6'd1   // R[c] = R[a] + sext10(imm)
`define OP_SLTI  6'd2   // R[c] = ($signed(R[a]) < $signed(sext10(imm))) ? 1 : 0
`define OP_SLLI  6'd3   // R[c] = R[a] << imm
`define OP_SRLI  6'd4   // R[c] = R[a] >> imm
`define OP_ADD   6'd5   // R[c] = R[a] + R[b]
`define OP_SUB   6'd6   // R[c] = R[a] - R[b]
`define OP_SLL   6'd7   // R[c] = R[a] << R[b]
`define OP_SRL   6'd8   // R[c] = R[a] >> R[b]
`define OP_AND   6'd11  // R[c] = R[a] & R[b]
`define OP_OR    6'd12  // R[c] = R[a] | R[b]
`define OP_XOR   6'd13  // R[c] = R[a] ^ R[b]
`define OP_JAL   6'd14  // if (R[cond][0]) PC = PC + sext14(off) else PC = PC + 1
`define OP_JALR  6'd15  // SFR[1] = PC + 1; PC = R[f]
`define OP_BEQ   6'd16  // R[c] = (R[a] == R[b]) ? 1 : 0
`define OP_BNE   6'd17  // R[c] = (R[a] != R[b]) ? 1 : 0
`define OP_BLT   6'd18  // R[c] = ($signed(R[a]) <  $signed(R[b])) ? 1 : 0
`define OP_BGE   6'd19  // R[c] = ($signed(R[a]) >= $signed(R[b])) ? 1 : 0
`define OP_BLTU  6'd20  // R[c] = (R[a] <  R[b]) ? 1 : 0
`define OP_BGEU  6'd21  // R[c] = (R[a] >= R[b]) ? 1 : 0
`define OP_LB    6'd22  // hi=0: R[r][7:0] = byte;  hi=1: R[r][15:8] = byte
`define OP_LSR   6'd23  // SFR[imm] = R[a]
`define OP_ESR   6'd24  // R[c] = SFR[imm]
`define OP_IN    6'd25  // R[c] = MEM[R[b]]
`define OP_OUT   6'd26  // MEM[R[b]] = R[a]
`define OP_MUL   6'd27  // {R[d],R[c]} = R[a] * R[b]（无符号 32 位，d 高位 c 低位）
`define OP_DIV   6'd28  // R[d] = R[a] % R[b]; R[c] = R[a] / R[b]（无符号）
`define OP_XORI  6'd29  // R[c] = R[a] ^ sext10(imm)
`define OP_ORI   6'd30  // R[c] = R[a] | sext10(imm)
`define OP_ANDI  6'd31  // R[c] = R[a] & sext10(imm)
`define OP_SRAI  6'd32  // R[c] = $signed(R[a]) >>> imm
`define OP_SRA   6'd33  // R[c] = $signed(R[a]) >>> R[b]
`define OP_SLA   6'd34  // R[c] = $signed(R[a]) <<< R[b]

// 常用集合（避免在多处重复写 6'd27||6'd28 这种）
`define IS_MULDIV(op) ((op)==`OP_MUL || (op)==`OP_DIV)

`endif
