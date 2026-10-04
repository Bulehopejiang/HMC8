module Regs (
    clk,res,a,b,c,d,a_addr,b_addr,c_addr,d_addr,L_c,L_d,e,e_addr,f,f_addr
);
    //寄存器组
    input clk,res;
    input [1:0] L_c;
    input L_d;
    output [15:0] a;
    output [15:0] b;
    input [15:0] c;
    input [15:0] d;
    output e;               //【优化】只输出第 0 位
    output [15:0] f;
    input [3:0] a_addr;
    input [3:0] b_addr;
    input [3:0] c_addr;
    input [3:0] d_addr;
    input [3:0] e_addr;
    input [3:0] f_addr;

    reg [15:0] regs [0:15];

    assign a=regs[a_addr];
    assign b=regs[b_addr];
    //【优化】e 原本是 16 位输出，但 jmp_control 的 e 端口本来就是 1 位、只用到 e[0]
    //       （综合器一直在报 "16 bits wider than the 1 bit port"）。
    //       这里直接只读第 0 位，省掉一整套 16:1 × 16bit 读 mux 和它的走线。
    assign e=regs[e_addr][0];
    assign f=regs[f_addr];
    //【优化】原来的 g 读口已删除：decoder 里 assign g_addr=b_addr，
    //       g 与 b 恒等，HMC8.v 直接用 b 充当原先的 g，
    //       省掉一整套 16:1 × 16bit 读 mux，同时把每个寄存器位的读扇出从 5 降到 3。

    /* ==================================================================
       写口：两个写口 + 每寄存器内部优先
       （原实现是 16 个寄存器各自一条 if/else if 优先级链，
         综合后 256 个 FF 各带一套地址比较 + 优先级 mux）

       注意优先级是"按寄存器"判定的，不是全局的 —— 乘除法写回那一拍，
       高位走 L_d/d_addr/d 口、低位走 L_c/c_addr/c 口，同一拍要写两个不同寄存器；
       只有两口指向同一寄存器时 L_d 才优先。

       等价性（与原 if/else if 逐条对应）：
         L_d=1 且 d_addr==i      -> regs[i] <= d            （整字，优先级最高）
         L_c=01 且 c_addr==i     -> regs[i][7:0]  <= c[7:0]
         L_c=10 且 c_addr==i     -> regs[i][15:8] <= c[7:0]
         L_c=11 且 c_addr==i     -> regs[i] <= c
         都不命中                 -> 保持
       ================================================================== */
    // L_c 口的写数据：L_c=10（LB HIGH）写高字节时取的也是 c[7:0]
    wire [15:0] wdata = (L_c == 2'b10) ? {c[7:0], 8'b0} : c;
    wire        b_lo  = (L_c == 2'b01) | (L_c == 2'b11);   // 低字节使能
    wire        b_hi  = (L_c == 2'b10) | (L_c == 2'b11);   // 高字节使能

    genvar i;
    generate
        for(i=0;i<16;i=i+1)begin:regs_gen
            wire we_d = L_d & (d_addr == i[3:0]);
            wire we_c = (L_c != 2'b00) & (c_addr == i[3:0]) & (~we_d);
            always @(posedge clk or negedge res) begin
                if(!res)
                    regs[i]<=16'b0;
                else if(we_d)
                    regs[i]<=d;
                else begin
                    if(we_c & b_lo) regs[i][7:0]  <=wdata[7:0];
                    if(we_c & b_hi) regs[i][15:8] <=wdata[15:8];
                end
            end
        end
    endgenerate
    
endmodule
