/*
* UART_send.v	
* clk:系统时钟,50MHz
* reset:复位信号,低电平复位
* en:发送使能信号,高电平使能,硬件自动清0
* TXD:串口发送信号
* TI:发送完成标志,高电平有效,保持一个周期
* Data:发送数据
* busy:发送忙标志
*/

module UART_send(clk,reset,en,TXD,TI,Data,busy);

	parameter sys_clk=50_000_000;
	parameter Baud=9600;
	parameter Count_full=(1_000_000_000/Baud)/(1_000_000_000/sys_clk);
    localparam W=$clog2(Count_full);

	input clk;
	input reset;
	input [7:0] Data;
	input en;
	output TXD,busy;
	output TI;
	
	reg state,state_next;
	reg [W-1:0] Count;
	reg [3:0] bit_Count;
	reg EN_old;
	wire Count_en;
	reg shift [9:0];
	integer i;
	
	always@(posedge clk or negedge reset)//移位寄存器
		if(!reset)begin
			shift[0]<=1'b1;
			for(i=1;i<=9;i=i+1)
				shift[i]<=1'b0;
		end
		else if(~EN_old&en)begin
			shift[1]<=1'b0;
			shift[2]<=Data[0];
			shift[3]<=Data[1];
			shift[4]<=Data[2];
			shift[5]<=Data[3];
			shift[6]<=Data[4];
			shift[7]<=Data[5];
			shift[8]<=Data[6];
			shift[9]<=Data[7];
		end
		else if(Count+1'b1==Count_full)begin
			for(i=0;i<9;i=i+1)
				shift[i]<=shift[i+1];
			shift[9]<=1'b1;
		end
	
	assign busy=(state==1'b1) ? 1'b1:1'b0;
	
	always@(posedge clk or negedge reset)//使能信号暂存
		if(!reset)
			EN_old<=1'b0;
		else 
			EN_old<=en;
	
	always@(posedge clk or negedge reset)//状态寄存器
		if(!reset)
			state<=1'b0;
		else 
			state<=state_next;

	always@(*)//状态转移电路
		case(state)
			1'd0:begin
				if(~EN_old&en)state_next=1'd1;else state_next=1'd0;
			end
			1'd1:begin
				if(bit_Count+1'b1>4'd11)state_next=1'd0;else state_next=1'd1;
			end
		endcase
	//相关控制信号
	assign TI=(state==1'd1&&state_next==1'd0) ? 1'b1:1'b0;
	assign TXD=shift[0];
	assign Count_en=(state==1'd1) ? 1'b1:1'b0;
	
	always@(posedge clk or negedge reset)//位计数器
		if(!reset)
			bit_Count<=4'b0;
		else if(Count+1'b1==Count_full)
			bit_Count<=(bit_Count+1'b1>4'd11) ? 4'd0:bit_Count+1'b1;
		else if(state==1'b0)
			bit_Count<=4'b0;
	
	always@(posedge clk or negedge reset)//波特率发生器
		if(!reset)
			Count<={W{1'b0}};
		else if(Count_en)
			Count<=(Count>=Count_full) ? {W{1'b0}}:Count+1'b1;
	
endmodule 