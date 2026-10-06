module decoder (
    clk,res,PROM_out,alu_op,en,sext,imm,a_addr,b_addr,c_addr,d_addr,L_c,
   A_sel,B_sel,L,E,ADDR_bus,g,g_addr,SFR_wr,L_d
);
    //译码器
    input clk,res;
    input [23:0] PROM_out;
    input en;
    input L_d;
    input [15:0] g;
    output [3:0] g_addr;
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

    reg [3:0] a_ADDR,b_ADDR,c_ADDR,d_ADDR;//寄存器地址寄存器
    reg [3:0] a_bypass,b_bypass,c_bypass,d_bypass;//专供乘除法的旁路寄存器，用于暂存寄存器地址

    always @(posedge clk or negedge res) begin//旁路寄存器
        if(!res)begin
            a_bypass<=4'b0;
            b_bypass<=4'b0;
            c_bypass<=4'b0;
            d_bypass<=4'b0;
        end
        else if((en==1'b1)&&(alu_op==6'd27||alu_op==6'd28))begin
            a_bypass<=a_ADDR;b_bypass<=b_ADDR;
            c_bypass<=c_ADDR;d_bypass<=d_ADDR;
        end
    end

    assign a_addr=(L_d) ? a_bypass:a_ADDR;/*旁路选择*/
    assign b_addr=(L_d) ? b_bypass:b_ADDR;
    assign c_addr=(L_d) ? c_bypass:c_ADDR;
    assign d_addr=(L_d) ? d_bypass:d_ADDR;

    always @(posedge clk or negedge res) begin//特殊寄存器访存信号生成
        if(!res)
            SFR_wr<=1'b0;
        else if(en)
            SFR_wr<=(PROM_out[23:18]==6'd23||PROM_out[23:18]==6'd24);        
    end

    assign g_addr=b_addr;
    always @(posedge clk or negedge res) begin//内存地址信号生成
        if(!res)
            ADDR_bus<=16'b0;
        else if(en)
            ADDR_bus<=(PROM_out[23:18]==6'd23||PROM_out[23:18]==6'd24) ? PROM_out[17:8]:g;        
    end

    always @(posedge clk or negedge res) begin//内存输出使能信号生成
        if(!res)
            E<=1'b0;
        else if(en)
            E<=(PROM_out[23:18]==6'd25||PROM_out[23:18]==6'd24);        
    end

    always @(posedge clk or negedge res) begin//内存加载使能信号生成
        if(!res)
            L<=1'b0;
        else if(en)
            L<=(PROM_out[23:18]==6'd26||PROM_out[23:18]==6'd23);        
    end

    always @(posedge clk or negedge res) begin//ALU A口选择信号生成
        if(!res)
            A_sel<=1'b0;
        else if(en)
            case (PROM_out[23:18])
                6'd14,6'd15,6'd24,6'd25:A_sel<=1'b0; 
                default:A_sel<=1'b1;
            endcase    
    end

    always @(posedge clk or negedge res) begin//ALU B口选择信号生成
        if(!res)
            B_sel<=1'b0;
        else if(en)
            case (PROM_out[23:18])
                6'd1,6'd2,6'd3,6'd4,6'd14,6'd15,6'd23,6'd22
                ,6'd24,6'd29,6'd30,6'd31,6'd32,6'd24:B_sel<=1'b0; 
                default:B_sel<=1'b1;
            endcase    
    end

    always @(posedge clk or negedge res) begin//寄存器c口加载信号生成
        if(!res)
            L_c<=2'b0;
        else if(en)
            case (PROM_out[23:18])
                6'd15,6'd23,6'd26,6'd0,6'd27,6'd28,6'd14:L_c<=2'b0;
                6'd22:L_c<=(PROM_out[4]) ? 2'b10:2'b01; 
                default:L_c<=2'b11;
            endcase 
    end

    always @(posedge clk or negedge res) begin//寄存器d地址信号生成
        if(!res)
            d_ADDR<=4'b0;
        else if(en)
            d_ADDR<=PROM_out[15:12];        
    end

    always @(posedge clk or negedge res) begin//寄存器c地址信号生成
        if(!res)
            c_ADDR<=4'b0;
        else if(en)
            c_ADDR<=PROM_out[3:0];        
    end

    always @(posedge clk or negedge res) begin//寄存器a地址信号生成
        if(!res)
            a_ADDR<=4'b0;
        else if(en)
            a_ADDR<=PROM_out[7:4];        
    end

    always @(posedge clk or negedge res) begin//寄存器b地址信号生成
        if(!res)
            b_ADDR<=4'b0;
        else if(en)
            b_ADDR<=PROM_out[11:8];        
    end

    always @(posedge clk or negedge res) begin//ALU功能选择信号生成
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