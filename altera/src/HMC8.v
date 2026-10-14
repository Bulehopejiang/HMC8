module HMC8 (
    clk,res,R_bus,W_bus,ADDR_bus,L,E,int_addr,out_int,SFR_wr,PC_out,
    L_ch,PC_CH,en
);
    parameter ip_sel=0;//1 altera 0 al
    
    input clk,res;
    input out_int;//中断信号
    input [15:0] R_bus;//读总线
    input [15:0] int_addr;//中断复位函数地址
    output [15:0] W_bus;//写总线
    output [15:0] ADDR_bus;//地址总线
    output [15:0] PC_CH;//中断捕获PC信号
    output L;/*内存加载和输出使能*/
    output E;
    output SFR_wr;//特殊寄存器访问信号
    output [15:0] PC_out;//JALR执行时PC由此输出
    output L_ch;//中断PC捕获使能
    output en;//流水线使能

    reg [15:0] PC;//程序计数器
    reg [23:0] PROM_out_reg;//程序存储器输出数据寄存器
    wire [15:0] PC_mux;//PC选择器
    wire [23:0] PROM_out;//PROM输出
    wire [15:0] A;/*运算器端口*/
    wire [15:0] B;
    wire [15:0] a;/*寄存器组端口*/
    wire [15:0] b;
    wire [15:0] c;
    wire [15:0] d;
    wire [15:0] e;
    wire [15:0] f;
    wire [15:0] g;
    wire [3:0] e_addr;/*寄存器组端口选择地址*/
    wire [3:0] f_addr;
    wire [3:0] a_addr,b_addr,c_addr;
    wire [3:0] d_addr;
    wire [3:0] g_addr;
    wire [15:0] PC_val;/*PC装载值选择，跳转时使用*/
    wire [1:0] PC_add;/*PC跳转选择信号，选择加偏移量还是装载新址*/
    wire sext;/*符号扩展*/
    wire [5:0] alu_op;/*运算器功能选择*/
    wire finish;/*乘除法完信号*/
    
    wire [9:0] imm;//立即数

    wire L_d;//寄存器d口加载使能，仅乘除法使用
    wire [1:0] L_cb;//寄存器c口加载使能信号（乘除法指令会接管L_c的职能）
    wire [1:0] L_c;//寄存器c口加载使能信号
    wire A_sel,B_sel;//运算器端口选择
    wire [15:0] out_l,out_h;//运算器高、低16位输出

    always @(posedge clk or negedge res) begin//第一级流水线寄存器
        if(!res)
            PROM_out_reg<=24'b0;
        else if(en)
            PROM_out_reg<=PROM_out;
    end

    always @(posedge clk or negedge res) begin//PC
        if(!res)
            PC<=16'b0;
        else if(en)
            PC<=PC_mux;
    end

    assign PC_out=PC+1'b1;//JALR执行时，会保存PC的下一条地址
    assign PC_CH=(!en) ? PC:(PC_add==2'b10) ? PC_val:(PC_add==2'b01) ? PC+PC_val:PC+1'b1;//中断捕获值

    assign PC_mux=(!en) ? PC:(out_int) ? int_addr:(PC_add==2'b10) ? PC_val:(PC_add==2'b01) ? PC+PC_val:PC+1'b1;//PC选择器

    generate//PROM IP选择
        if(ip_sel)
           PROM	PROM_inst (//PROM
            .aclr ( ~res ),
            .address ( PC_mux ),
            .clock ( clk ),
            .q ( PROM_out )
            ); 
        else
            PROM PROM_uut( .doa(PROM_out), .addra(PC_mux), .clka(clk) );
    endgenerate

    decoder decoder_uut(//译码器
        .clk(clk),.res(res),.PROM_out(PROM_out_reg),.alu_op(alu_op),
        .en(en),.sext(sext),.imm(imm),.a_addr(a_addr),.b_addr(b_addr),
        .c_addr(c_addr),.d_addr(d_addr),.L_c(L_c),
        .A_sel(A_sel),.B_sel(B_sel),.ADDR_bus(ADDR_bus),
        .L(L),.E(E),.g(g),.g_addr(g_addr),.SFR_wr(SFR_wr),.L_d(L_d)
    );

    jmp_control jmp_control_uut(//跳转控制器，位于流水线第一级
        .PROM_out(PROM_out),.e(e!=16'b0),.e_addr(e_addr),.PC_add(PC_add),
        .PC_val(PC_val),.f(f),.f_addr(f_addr),.L_ch(L_ch)
    );

    pip_control pip_control_uut(//流水线控制器，控制流水线停顿
        .clk(clk),.res(res),.en(en),.finish(finish),.alu_op(alu_op),
        .L_d(L_d),.L_cb(L_cb)
    );

    Regs Regs_uut(//寄存器堆
        .clk(clk),.res(res),.a(a),.b(b),.c(c),.d(d),.a_addr(a_addr),
        .b_addr(b_addr),.c_addr(c_addr),.d_addr(d_addr),.L_c(L_c|L_cb),
        .L_d(L_d),.e(e),.e_addr(e_addr),.f(f),.f_addr(f_addr),.g(g),
        .g_addr(g_addr)
    );

    assign A=(A_sel) ? a:R_bus;/*运算器端口选择*/
    assign B=(B_sel) ? b:(!sext) ? {6'b0,imm}:(imm[9]) ? {6'b111_111,imm}:{6'b0,imm};
    assign c=(L_c|L_cb) ? out_l:16'd0;/*运算结果选择*/
    assign W_bus=out_l;
    assign d=out_h;//乘除法的高16位或余数从d口读入

    ALU ALU_uut(//运算器
        .clk(clk),.res(res),.alu_op(alu_op),.out_l(out_l),.out_h(out_h),
        .finish(finish),.A(A),.B(B)
    );

endmodule