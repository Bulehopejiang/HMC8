module decoder (
    clk,res,PROM_out,alu_op,en,sext,imm,a_addr,b_addr,c_addr,d_addr,L_c,
   A_sel,B_sel,L,E,ADDR_bus,g,SFR_wr,L_d
);

    input clk,res;
    input [23:0] PROM_out;
    input en;
    input L_d;
    input [15:0] g;
    output reg [15:0] ADDR_bus;
    output reg sext;//符号扩展
    output reg [9:0] imm;
    output [3:0] a_addr,b_addr,c_addr,d_addr;
    output reg [1:0] L_c;
    output reg  [5:0] alu_op;
    output reg A_sel;
    output reg B_sel;
    output reg L,E;
    output reg SFR_wr;

    reg [3:0] a_ADDR,b_ADDR,c_ADDR,d_ADDR;

    // 【时序优化】把乘除法写回所需的寄存器字段"冻结在源头"，取代原来的地址旁路 mux。
    //
    // 原来的做法：a_bypass..d_bypass 再存一份字段，写回那一拍用 L_d 把地址切到旁路寄存器。
    // 问题：L_d 由 finish 组合产生，于是 finish → 地址 mux → 寄存器堆读 mux → ALU → 写 mux
    //       被串成一条 18ns 的长路径（实测就是最差路径）。
    // 现在改成：译码结果本身是乘/除（alu_op==27/28）的那一拍，不推进这四个地址寄存器，
    //       它们自然保持"乘除法指令自己"的字段直到写回结束，与旁路寄存器取值完全一致，
    //       但地址通路上再也没有 L_d / finish 的组合依赖。
    wire md_op    = (alu_op==6'd27)||(alu_op==6'd28);
    wire addr_upd = en & (~md_op);

    assign a_addr=a_ADDR;
    assign b_addr=b_ADDR;
    assign c_addr=c_ADDR;
    assign d_addr=d_ADDR;

    always @(posedge clk or negedge res) begin//地址信号生成
        if(!res)
            SFR_wr<=1'b0;
        else if(en)
            SFR_wr<=(PROM_out[23:18]==6'd23||PROM_out[23:18]==6'd24);        
    end

    //【优化】原来的 assign g_addr=b_addr 与配套的 g 读口已删除：
    //       g 与 b 恒等，寄存器堆不再单独开这个读口，HMC8.v 直接把 b 接到这里的 g 输入。
    always @(posedge clk or negedge res) begin//地址信号生成
        if(!res)
            ADDR_bus<=16'b0;
        else if(en)
            ADDR_bus<=(PROM_out[23:18]==6'd23||PROM_out[23:18]==6'd24) ? PROM_out[17:8]:g;        
    end

    always @(posedge clk or negedge res) begin//内存输出信号生成
        if(!res)
            E<=1'b0;
        else if(en)
            E<=(PROM_out[23:18]==6'd25||PROM_out[23:18]==6'd24);        
    end

    always @(posedge clk or negedge res) begin//内存加载信号生成
        if(!res)
            L<=1'b0;
        else if(en)
            L<=(PROM_out[23:18]==6'd26||PROM_out[23:18]==6'd23);        
    end

    always @(posedge clk or negedge res) begin//A信号生成
        if(!res)
            A_sel<=1'b0;
        else if(en)
            case (PROM_out[23:18])
                6'd14,6'd15,6'd24,6'd25:A_sel<=1'b0; 
                default:A_sel<=1'b1;
            endcase    
    end

    always @(posedge clk or negedge res) begin//B信号生成
        if(!res)
            B_sel<=1'b0;
        else if(en)
            case (PROM_out[23:18])
                6'd1,6'd2,6'd3,6'd4,6'd14,6'd15,6'd23,6'd22
                ,6'd24,6'd29,6'd30,6'd31,6'd32,6'd24:B_sel<=1'b0; 
                default:B_sel<=1'b1;
            endcase    
    end

    always @(posedge clk or negedge res) begin//寄存器加载信号生成
        if(!res)
            L_c<=2'b0;
        else if(en)
            case (PROM_out[23:18])
                6'd15,6'd23,6'd26,6'd0,6'd27,6'd28,6'd14:L_c<=2'b0;
                6'd22:L_c<=(PROM_out[4]) ? 2'b10:2'b01; 
                default:L_c<=2'b11;
            endcase 
    end

    always @(posedge clk or negedge res) begin//d信号生成
        if(!res)
            d_ADDR<=4'b0;
        else if(addr_upd)
            d_ADDR<=PROM_out[15:12];        
    end

    always @(posedge clk or negedge res) begin//c信号生成
        if(!res)
            c_ADDR<=4'b0;
        else if(addr_upd)
            c_ADDR<=PROM_out[3:0];        
    end

    always @(posedge clk or negedge res) begin//a信号生成
        if(!res)
            a_ADDR<=4'b0;
        else if(addr_upd)
            a_ADDR<=PROM_out[7:4];        
    end

    always @(posedge clk or negedge res) begin//b信号生成
        if(!res)
            b_ADDR<=4'b0;
        else if(addr_upd)
            b_ADDR<=PROM_out[11:8];        
    end

    always @(posedge clk or negedge res) begin//ALU信号生成
        if(!res)
            alu_op<=6'b0;
        else if(en)
            alu_op<=PROM_out[23:18];        
    end

    always @(posedge clk or negedge res) begin//符号扩展信号生成
        if(!res)
            sext<=1'b0;
        else if(en)
            case (PROM_out[23:18])
                6'd1,6'd2,6'd14,6'd29,6'd30,6'd31:sext<=1'b1; 
                default:sext<=0;
            endcase        
    end

    always @(posedge clk or negedge res) begin//立即数信号生成
        if(!res)
            imm<=10'b0;
        else if(en)
            case (PROM_out[23:18])
                6'd1,6'd2,6'd3,6'd4,6'd29,6'd30,6'd31,6'd32,6'd22
                ,6'd23,6'd24:imm<=PROM_out[17:8];
                default:imm<=0;
            endcase        
    end

endmodule