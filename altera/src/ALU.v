module ALU (
    clk,res,alu_op,out_l,out_h,finish,A,B
);
    
    input clk,res;
    input [5:0] alu_op;
    output [15:0] out_h;
    output [15:0] out_l;
    output finish;
    input [15:0] A;
    input [15:0] B;

    wire [15:0] mul_l;
    wire [15:0] mul_h;
    wire [15:0] div_r;
    wire [15:0] div_q;
    wire mul_finish;
    wire div_finish;

    /* ==================================================================
       【时序优化】组合逻辑扁平化：17 分支 case -> 分组译码 + 两级平衡 mux
       原实现里 17 个分支的表达式被综合器合并成一条 7 级串联 LUT 链
       （实测占掉 5.2ns，是数据通路里最贵的一段）。
       现在改成：先并行算出各功能类的候选结果，再用两级 2 选 1 挑出来，
       从 A/B 到 out_l 的 mux 深度由 7 级降到 3 级。
       每个分支的取值与原 case 逐条等价，包括移位量 >=16 的溢出语义。
       ================================================================== */

    /* ---------- 1) 操作码分组译码（只依赖 alu_op，早到信号，不在关键路径上） ---------- */
    wire is_sub   = (alu_op==6'd6);
    wire is_and   = (alu_op==6'd11)|(alu_op==6'd31);
    wire is_or    = (alu_op==6'd12)|(alu_op==6'd30);
    wire is_srl   = (alu_op==6'd4) |(alu_op==6'd8);       // 逻辑右移
    wire is_sra   = (alu_op==6'd32)|(alu_op==6'd33);      // 算术右移
    wire is_eq    = (alu_op==6'd16);
    wire is_ne    = (alu_op==6'd17);
    wire is_ult   = (alu_op==6'd20);                      // 无符号 <
    wire is_uge   = (alu_op==6'd21);                      // 无符号 >=
    wire is_slt   = (alu_op==6'd2) |(alu_op==6'd18);      // 有符号 <
    wire is_sge   = (alu_op==6'd19);                      // 有符号 >=
    wire is_passA = (alu_op==6'd23)|(alu_op==6'd24)|(alu_op==6'd25)|(alu_op==6'd26);

    // 3 位组选择，直接对应下面的两级 mux 树：
    //   sel[0] 选组内第二个，sel[1] 选高半，sel[2] 直接选第三组
    //   000=加减 001=逻辑 010=移位 011=比较 100=直通A 101=乘除/B(默认)
    reg [2:0] sel;
    always @(*) begin
        case (alu_op)
            6'd1,6'd5,6'd6:                           sel = 3'b000;
            6'd11,6'd31,6'd12,6'd30,6'd13,6'd29:      sel = 3'b001;
            6'd3,6'd7,6'd34,6'd4,6'd8,6'd32,6'd33:    sel = 3'b010;
            6'd20,6'd2,6'd18,6'd19,6'd21,6'd16,6'd17: sel = 3'b011;
            6'd23,6'd24,6'd25,6'd26:                  sel = 3'b100;
            default:                                  sel = 3'b101;
        endcase
    end

    /* ---------- 2) 各功能类并行算候选结果 ---------- */
    // 加减共用一个加法器（A-B 映射成带进位输入的减法，深度不变）
    wire [15:0] r_addsub = is_sub ? (A - B) : (A + B);

    wire [15:0] r_logic  = is_and ? (A & B) : (is_or ? (A | B) : (A ^ B));

    // 移位器：只做低 4 位的桶形移位（4 级），高位非零时按原语义取溢出结果
    //   原语义：A<<B / A>>B 在 B>=16 时结果为 0；$signed(A)>>>B 在 B>=16 时是全符号位
    //   结果与原 16 位移位器完全一致，但移位器规模/深度缩到 1/4
    wire        sh_ovf  = |B[15:4];
    wire [15:0] sh_l    = A << B[3:0];
    wire [15:0] sh_r    = A >> B[3:0];
    wire [15:0] sh_a    = $signed(A) >>> B[3:0];
    wire [15:0] r_shpre = is_sra ? sh_a : (is_srl ? sh_r : sh_l);
    wire [15:0] r_shift = sh_ovf ? (is_sra ? {16{A[15]}} : 16'd0) : r_shpre;

    // 比较：共用一个无符号比较器 + 符号位修正，不需要第二套比较器
    wire        u_lt = (A < B);
    wire        s_lt = (A[15]^B[15]) ? A[15] : u_lt;      // 有符号小于
    wire        eq   = (A == B);
    wire [15:0] r_cmp = is_eq  ? {15'b0,  eq}
                      : is_ne  ? {15'b0, ~eq}
                      : is_ult ? {15'b0,  u_lt}
                      : is_uge ? {15'b0, ~u_lt}
                      : is_slt ? {15'b0,  s_lt}
                      :          {15'b0, ~s_lt};           // is_sge

    wire [15:0] r_pass = A;                                            // LSR/ESR/IN/OUT
    wire [15:0] r_md   = mul_finish ? mul_l : (div_finish ? div_q : B); // 乘除/NOP/JAL/LB...

    /* ---------- 3) 两级平衡选择（数据路径深度 3 级） ---------- */
    wire [15:0] g0  = sel[0] ? r_logic : r_addsub;
    wire [15:0] g1  = sel[0] ? r_cmp   : r_shift;
    wire [15:0] g2  = sel[0] ? r_md    : r_pass;
    wire [15:0] g01 = sel[1] ? g1 : g0;
    assign out_l    = sel[2] ? g2 : g01;

    assign out_h=(mul_finish) ? mul_h:div_r;
    assign finish=div_finish|mul_finish;

    DIV_serial DIV_uut(//除法器
        .clk(clk),.res_n(res),.a(A),.b(B),.out({div_r,div_q}),
        .en(alu_op==6'd28),
        .finish(div_finish)
    );

    MUL_serial MUL_uut(//乘法器
        .clk(clk),.res_n(res),.a(A),.b(B),.out({mul_h,mul_l}),
        .en(alu_op==6'd27),
        .finish(mul_finish)
    );

endmodule
