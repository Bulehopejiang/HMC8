module HMC8 (
    clk,res,R_bus,W_bus,ADDR_bus,L,E,int_addr,out_int,SFR_wr,PC_out,
    L_ch,PC_CH,en
);
    
    input clk,res;
    input out_int;
    input [15:0] R_bus;
    input [15:0] int_addr;
    output [15:0] W_bus;
    output [15:0] ADDR_bus;
    output [15:0] PC_CH;
    output L;
    output E;
    output SFR_wr;
    output [15:0] PC_out;
    output L_ch;
    output en;

    reg [15:0] PC;
    reg [23:0] PROM_out_reg;
    wire [15:0] PC_mux;
    wire [23:0] PROM_out;
    wire [15:0] A;
    wire [15:0] B;
    wire [15:0] a;
    wire [15:0] b;
    wire [15:0] c;
    wire [15:0] d;
    wire [15:0] e;
    wire [15:0] f;
    wire [15:0] g;
    wire [3:0] e_addr;
    wire [3:0] f_addr;
    wire [3:0] a_addr,b_addr,c_addr;
    wire [3:0] d_addr;
    wire [3:0] g_addr;
    wire [15:0] PC_val;
    wire [1:0] PC_add;
    wire sext;
    wire [5:0] alu_op;
    wire finish;
    
    wire [9:0] imm;

    wire L_d;
    wire [1:0] L_cb;
    wire [1:0] L_c;
    wire A_sel,B_sel;
    wire [15:0] out_l,out_h;

    always @(posedge clk or negedge res) begin
        if(!res)
            PROM_out_reg<=24'b0;
        else if(en)
            PROM_out_reg<=PROM_out;
    end

    always @(posedge clk or negedge res) begin
        if(!res)
            PC<=16'b0;
        else if(en)
            PC<=PC_mux;
    end

    assign PC_out=PC+1'b1;
    assign PC_CH=(!en) ? PC:(PC_add==2'b10) ? PC_val:(PC_add==2'b01) ? PC+PC_val:PC+1'b1;

    assign PC_mux=(!en) ? PC:(out_int) ? int_addr:(PC_add==2'b10) ? PC_val:(PC_add==2'b01) ? PC+PC_val:PC+1'b1;

    PROM	PROM_inst (//PROM
	.aclr ( ~res ),
	.address ( PC_mux ),
	.clock ( clk ),
	.q ( PROM_out )
	);

    decoder decoder_uut(//译码器
        .clk(clk),.res(res),.PROM_out(PROM_out_reg),.alu_op(alu_op),
        .en(en),.sext(sext),.imm(imm),.a_addr(a_addr),.b_addr(b_addr),
        .c_addr(c_addr),.d_addr(d_addr),.L_c(L_c),
        .A_sel(A_sel),.B_sel(B_sel),.ADDR_bus(ADDR_bus),
        .L(L),.E(E),.g(g),.g_addr(g_addr),.SFR_wr(SFR_wr),.L_d(L_d)
    );

    jmp_control jmp_control_uut(
        .PROM_out(PROM_out),.e(e),.e_addr(e_addr),.PC_add(PC_add),
        .PC_val(PC_val),.f(f),.f_addr(f_addr),.L_ch(L_ch)
    );

    pip_control pip_control_uut(//流水线控制器
        .clk(clk),.res(res),.en(en),.finish(finish),.alu_op(alu_op),
        .L_d(L_d),.L_cb(L_cb)
    );

    Regs Regs_uut(//寄存器堆
        .clk(clk),.res(res),.a(a),.b(b),.c(c),.d(d),.a_addr(a_addr),
        .b_addr(b_addr),.c_addr(c_addr),.d_addr(d_addr),.L_c(L_c|L_cb),
        .L_d(L_d),.e(e),.e_addr(e_addr),.f(f),.f_addr(f_addr),.g(g),
        .g_addr(g_addr)
    );

    assign A=(A_sel) ? a:R_bus;//运算器端口选择
    assign B=(B_sel) ? b:(!sext) ? {6'b0,imm}:(imm[9]) ? {6'b111_111,imm}:{6'b0,imm};
    assign c=(L_c|L_cb) ? out_l:16'd0;
    assign W_bus=out_l;
    assign d=out_h;

    ALU ALU_uut(//运算器
        .clk(clk),.res(res),.alu_op(alu_op),.out_l(out_l),.out_h(out_h),
        .finish(finish),.A(A),.B(B)
    );

endmodule