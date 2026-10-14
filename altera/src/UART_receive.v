/*
* UART_receive.v
* clk:系统时钟,50MHz
* reset:复位信号,低电平复位
* en:接收使能信号,高电平使能
* RXD:串口接收信号
* RI:接收完成标志,高电平有效,保持一个周期
* out:接收数据
*/

module UART_receive(clk,reset,en,RXD,RI,out);

	parameter sys_clk=50_000_000;
	parameter Baud=9600;
	parameter Count_full=(1_000_000_000/Baud)/(1_000_000_000/sys_clk);
    parameter W=$clog2(Count_full);

	input clk;
	input reset;
    input en;
	input RXD;
	output  RI;
	output  reg [7:0]out;
	
    reg [W-1:0] Count;
    reg state,state_next;
    reg [9:0] bit_count;
    reg shift [9:0];
    integer i;

    reg RI_old;
    wire RI_val;
    reg diff1,diff2;

    always @(posedge clk or negedge reset) begin//异步信号打拍
        if(!reset)begin
            diff1<=1'b0;diff2<=1'b0;
        end
        else begin
            diff1<=RXD;diff2<=diff1;
        end
    end
    
    always@(posedge clk or negedge reset)//位计数器
        if(!reset)
            bit_count<=4'b0;
        else if(state==1'b0)
            bit_count<=4'b0;
        else if(Count>=Count_full)
            bit_count<=(bit_count>=4'd10) ? 4'd0:bit_count+1'b1;
    
    always@(posedge clk or negedge reset)//波特率发生器
        if(!reset)
            Count<={W{1'b0}};
        else if(state==1'b1)
            Count<=(Count>=Count_full) ? {W{1'b0}}:Count+1'b1;
            
    always@(posedge clk or negedge reset)//状态寄存器
        if(!reset)
            state<=1'b0;
        else
            state<=state_next;
            
    always@(*)//状态转移电路
        case(state)
            1'b0:if(diff2==1'b0&&en==1'b1)state_next=1'b1;else state_next=1'b0;
            1'b1:if(bit_count>=4'd10)state_next=1'b0;else state_next=1'b1;
        endcase
        
    always@(posedge clk or negedge reset)//接收移位寄存器
        if(!reset)begin
            shift[0]<=1'b0;
            shift[1]<=1'b0;
            shift[2]<=1'b0;
            shift[3]<=1'b0;
            shift[4]<=1'b0;
            shift[5]<=1'b0;
            shift[6]<=1'b0;
            shift[7]<=1'b0;
            shift[8]<=1'b0;
            shift[9]<=1'b0;
        end
        else if(Count==Count_full/2)begin
            shift[0]<=diff2;
            for(i=9;i>=1;i=i-1)
                shift[i]<=shift[i-1];
        end
        
    always@(posedge clk or negedge reset)//数据寄存器
        if(!reset)
            out<=8'b0;
        else if(state==1'b1&&state_next==1'b0)
            out<={shift[1],shift[2],shift[3],shift[4],shift[5],shift[6],shift[7],shift[8]};
            
    always @(posedge clk or negedge reset) begin//接收完成信号暂存
        if(!reset)
            RI_old<=1'b0;
        else
            RI_old<=RI;
    end

    assign RI_val=(bit_count>=4'd10) ? 1'b1:1'b0;//接收完成信号
    assign RI=~RI_old&RI_val;//接收完成信号保持一个周期        	
    
endmodule 