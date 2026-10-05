// ============================================================================
//  仅供 RTL 仿真使用的存储器模型（不参与综合）
//
//  为什么需要它：
//    安路 IP 生成出来的 ip/PROM.v / ip/RAM.v 例化的是 EG_LOGIC_BRAM，而那个模型是
//    加密的，并且在本工程里读不到 IP 里写的 INIT_FILE("../al_PROM.mif") ——
//    结果 RTL 仿真时 PROM 输出全是 x，CPU 等于没有程序（跑出来一片 NOP）。
//    这里用行为级模型代替：初始化数据从 rtl_sim.do 自动转出来的 al_PROM.hex 读。
//
//  【重要】仿真时只编译本文件，不要再编译 ip/PROM.v、ip/RAM.v（模块会重名）。
//          端口名和位宽与安路 IP 一致，所以 HMC8_SOC.v 里 ip_sel=0 那一路不用改。
// ============================================================================

// ---------------------------- PROM：1024 × 24 ----------------------------
module PROM (doa, addra, clka);
    output [23:0] doa;
    input  [9:0]  addra;
    input         clka;

    reg [23:0] mem [0:1023];
    reg [23:0] dout;
    integer i;

    initial begin
        for (i = 0; i < 1024; i = i + 1) mem[i] = 24'h000000;   // 未写的地址填 0（NOP）
        $readmemh("al_PROM.hex", mem);
        dout = 24'h000000;
    end

    always @(posedge clka) begin
        // 关键：地址未知时必须给 0（NOP），不能让 mem[x] 读出 x。
        // 复位同步器在头两拍会输出 x，PC_mux 跟着变 x；若这里返回 x，
        // PROM_out → jmp_control → PC_mux 会被 x 锁死，仿真永远跑不起来。
        if (^addra === 1'bx) dout <= 24'h000000;
        else                 dout <= mem[addra];
    end

    assign doa = dout;
endmodule

// ---------------------------- RAM：2048 × 16 -----------------------------
module RAM (doa, dia, addra, clka, wea);
    output [15:0] doa;
    input  [15:0] dia;
    input  [10:0] addra;
    input         clka;
    input         wea;

    reg [15:0] mem [0:2047];
    reg [15:0] dout;
    integer i;

    initial begin
        for (i = 0; i < 2048; i = i + 1) mem[i] = 16'h0000;
        dout = 16'h0000;
    end

    always @(posedge clka) begin
        if (wea) mem[addra] <= dia;
        if (^addra === 1'bx) dout <= 16'h0000;      // 同 PROM：地址未知时给 0
        else                 dout <= mem[addra];
    end

    assign doa = dout;
endmodule
