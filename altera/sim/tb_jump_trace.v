`timescale 1ns/1ps
// ============================================================================
//  HMC8 跳转指令调试 testbench
//
//  用途：把 PC / PC_add / PC_val / L_c / 关键寄存器 逐拍打印出来，
//        用来定位"跳转指令看起来跳了、但过一会儿 PC 又继续数下去"这类问题。
//
//  运行方法（必须先进入 altera/simulation/modelsim，那里有 PROM.mif）：
//      cd altera\simulation\modelsim
//      F:\FPGAIDE\modelsim_ase\win32aloem\vsim.exe -c -do ..\..\sim\run_jump_trace.do
//
//  打印列说明：
//      cyc     仿真拍数
//      PC      当前 PC 值（设计里的 PC 就是"当前正在取指的地址"）
//      PCout   PC+1，JALR 保存返回地址用的就是这个值
//      PCadd   jmp_control 给出的跳转类型：00=不跳 01=JAL(相对) 10=JALR(绝对)
//      PCval   跳转目标/偏移；JAL 条件不成立时是默认值 1
//      op      当前译码出的操作码（14=JAL 15=JALR 0=NOP 22=LB ...）
//      Lc      寄存器堆写使能：00=不写 01/10=写半字 11=写整字
//      Lch     JALR 保存返回地址（写 SFR[1]）的使能
//      R0 R1 R5 SFR1   关键寄存器 / 特殊寄存器现场
//      PROM_out_reg    译码器当前正在处理的指令字（用来对照 MIF 里的地址）
// ============================================================================
module tb_jump_trace;
    reg clk = 1'b0, res_n = 1'b0;
    wire [15:0] out;

    HMC8_SOC uut(.clk(clk), .res_n(res_n), .out(out));

    always #10 clk = ~clk;

    integer i;
    initial begin
        res_n = 1'b0;
        repeat(5) @(posedge clk);
        @(negedge clk); res_n = 1'b1;
    end

    initial begin
        $display("cyc | PC PCout PCadd PCval op Lc Lch | R0   R1  R5  SFR1 | PROM_out_reg");
        for (i = 0; i < 200; i = i + 1) begin
            @(posedge clk); #1;
            $display("%3d | %2d %5d %5b %5d %2d %2b %b | %4d %3d %3d %5d | %0d",
                     i,
                     uut.HMC8_uut.PC,
                     uut.HMC8_uut.PC_out,
                     uut.HMC8_uut.PC_add,
                     uut.HMC8_uut.PC_val,
                     uut.HMC8_uut.alu_op,
                     uut.HMC8_uut.L_c,
                     uut.HMC8_uut.L_ch,
                     uut.HMC8_uut.Regs_uut.regs[0],
                     uut.HMC8_uut.Regs_uut.regs[1],
                     uut.HMC8_uut.Regs_uut.regs[5],
                     uut.SFR[1],
                     uut.HMC8_uut.PROM_out_reg);
        end
        $stop;
    end
endmodule
