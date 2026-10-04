module DIV_serial (
    clk,res_n,a,b,out,en,finish
);

    // 【时序优化】端口上不再加 keep/preserve/noextract（原因见 MUL_serial.v 同位置注释）
    input clk;
    input res_n;
    input en;

    input [15:0] a;
    input [15:0] b;

    output reg [31:0] out/* synthesis keep, preserve, noextract */;
    output reg finish/* synthesis keep, preserve, noextract */;

    reg [15:0] b_reg/* synthesis keep, preserve, noextract */;
    wire out_l/* synthesis keep, preserve, noextract */;
    reg [31:0] mid/* synthesis keep, preserve, noextract */;
    reg [3:0] state/* synthesis keep, preserve, noextract */;
    reg [3:0] state_next/* synthesis keep, preserve, noextract */;

    always @(posedge clk or negedge res_n) begin //除数寄存器
        if(!res_n)
            b_reg<=16'b0;
        else if(en)
            b_reg<=b;
    end

    always @(posedge clk or negedge res_n) begin //输出寄存器
        if(!res_n)
            out<=32'b0;
        else if(en)
            out<={16'b0,a};
        else if(out_l)
            out<=mid;
    end

    always @(posedge clk or negedge res_n) begin //状态寄存器
        if(!res_n)
            state<=4'b0;
        else 
            state<=state_next;
    end

    always @(*) begin //状态转移电路
        case (state)
           4'b0000:state_next=(en) ? 4'b0001:4'b0;
           4'b0001:state_next=4'b0011;
           4'b0011:state_next=4'b0010;
           4'b0010:state_next=4'b0110;
           4'b0110:state_next=4'b0111;
           4'b0111:state_next=4'b0101;
           4'b0101:state_next=4'b0100;
           4'b0100:state_next=4'b1100;
           4'b1100:state_next=4'b0;
            default:state_next=4'b0;
        endcase
    end

    /******************状态机输出电路***************/
    //输出寄存器加载信号
    assign out_l=(state!=4'b0) ? 1'b1:1'b0;

    //完成信号
    always @(posedge clk or negedge res_n) begin
        if(!res_n)
            finish<=1'b0;
        else
            finish<=(state==4'b1100) ? 1'b1:1'b0;
    end

    /**********************************************/

    always @(*) begin//移位减法器
        mid={out[30:0],1'b0};
        if(mid[31:16]>=b_reg)begin
            mid[31:16]=mid[31:16]-b_reg;
            mid[0]=1'b1;
        end
        mid={mid[30:0],1'b0};
        if(mid[31:16]>=b_reg)begin
            mid[31:16]=mid[31:16]-b_reg;
            mid[0]=1'b1;
        end
    end
    
endmodule