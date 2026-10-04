module MUL_serial (
    clk,res_n,a,b,out,en,finish
);
	// Fmax 66MHZ
    // 【时序优化】端口上不再加 keep/preserve/noextract：
    // 端口上的 noextract 会让综合器为 clk 单独插缓冲并提升成独立全局时钟（GCLK1），
    // 与主时钟树插入延迟差约 1.2ns，白吃掉每个周期的时序余量。
    // 内部寄存器（a_reg/b_reg/state/out/mid）上的属性全部保留，串行结构不会被改写。
    input clk;
    input res_n;
    input en;

    input [15:0] a;
    input [15:0] b;

    output reg [31:0] out/* synthesis keep, preserve, noextract */;
    output reg finish/* synthesis keep, preserve, noextract */;

    reg [15:0] a_reg/* synthesis keep, preserve, noextract */;
    reg [15:0] b_reg/* synthesis keep, preserve, noextract */;

    reg [3:0] state/* synthesis keep, preserve, noextract */;
    reg [3:0] state_next/* synthesis keep, preserve, noextract */;

    wire [3:0] bit_num/* synthesis keep, preserve, noextract */;

    reg [31:0] mid/* synthesis keep, preserve, noextract */;

    wire out_l/* synthesis keep, preserve, noextract */;

    always @(posedge clk or negedge res_n) begin//输入数据寄存器
        if(!res_n)begin
           a_reg<=16'b0;
           b_reg<=16'b0;
        end
        else if(en)begin
            a_reg<=a;
            b_reg<=b;
        end
    end

    always @(posedge clk or negedge res_n) begin//状态寄存器
        if(!res_n)
            state<=3'b0;
        else 
            state<=state_next;
    end

    always @(*) begin //状态转移电路
        case (state)
           4'd0:state_next=(en) ? 4'b1:4'b0;
           4'd1:state_next=4'd2;
           4'd2:state_next=4'd3;
           4'd3:state_next=4'd4;
           4'd4:state_next=4'd5;
           4'd5:state_next=4'd6;
           4'd6:state_next=4'd7;
           4'd7:state_next=4'd8;
           4'd8:state_next=4'd0;
            default:state_next=4'b0;
        endcase
    end

    /****************状态机输出信号**************/
    assign bit_num={state,1'b0}-2'd2;

    //输出寄存器加载信号
    assign out_l=(state!=4'b0) ? 1'b1:1'b0;   
    //完成信号
    always @(posedge clk or negedge res_n) begin
        if(!res_n)
            finish<=1'b0;
        else
            finish<=(state==4'd8) ? 1'b1:1'b0;
    end
 
    /*******************************************/

    always @(posedge clk or negedge res_n) begin//结果寄存器
        if(!res_n)
            out<=32'b0;
        else if(en)
            out<=32'b0;
        else if(out_l)
            out<=mid;
    end

    always @(*) begin//移位加法器
		mid=out;
        mid=(a_reg[bit_num]) ? mid+(b_reg<<bit_num):mid;
        mid=(a_reg[bit_num+1'b1]) ? mid+(b_reg<<bit_num+1'b1):mid;
    end
    
endmodule 
