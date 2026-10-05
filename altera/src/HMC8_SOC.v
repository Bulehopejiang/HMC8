module HMC8_SOC (
    clk,res_n,out,TX,RX
);
    localparam  i_num= 5;
    parameter ip_sel=0;//1 altera 0 al

    input clk,res_n;
    output [15:0] out;
    input RX;
    output TX;

    reg resdff1,res;
    wire [15:0] R_bus,W_bus,ADDR_bus;
    wire L,E;
    wire out_int;
    wire SFR_wr;
    wire [15:0] PC_out;
    wire L_ch;
    wire [15:0] RAM_out;
    reg [15:0] SFR [0:11];
    reg [15:0] IO [0:1];
    wire [i_num-1:0] I;
    wire i_reg_clr;
    wire i;
    wire IF;
    wire en;
    reg i_reg;
    wire [15:0] PC_CH;
    wire UART0_busy;
    wire TI,RI;
    wire [7:0] Rx_data;
    wire TI0;

	generate
    	if(ip_sel)
            RAM	RAM_inst (
            .address ( ADDR_bus ),
            .clock ( clk ),
            .data ( W_bus ),
            .wren ( L==1'b1&&ADDR_bus<16'd2048&&SFR_wr==1'b0 ),
            .q ( RAM_out )
            );
        else
            RAM RAM_uut( .doa(RAM_out), .dia(W_bus), .addra(ADDR_bus), .clka(clk), .wea(L==1'b1&&ADDR_bus<16'd2048&&SFR_wr==1'b0) );
    endgenerate

    always @(posedge clk or negedge res) begin//中断上升沿检测寄存器
        if(!res)
            i_reg<=1'b1;
        else if(i_reg_clr)
            i_reg<=1'b0;
        else if(!IF)
            i_reg<=1'b1;
        else if(en)
            i_reg<=i;
    end
    assign i=|I;
    assign out_int=~i_reg&i;//中断边沿检测

    assign R_bus=(SFR_wr) ? SFR[ADDR_bus]:(ADDR_bus<16'd2048) ? RAM_out:IO[ADDR_bus];

    always @(posedge clk) begin
        resdff1<=res_n;
        res<=resdff1;
    end

    always @(posedge clk or negedge res) begin//输出寄存器
        if(!res)
            SFR[0]<=16'b0;
        else if(L==1'b1&&SFR_wr==1'b1&&ADDR_bus==16'b0)
            SFR[0]<=W_bus;
    end
    assign out=SFR[0];

    always @(posedge clk or negedge res) begin//PC返回寄存器
        if(!res)
            SFR[1]<=16'b0;
        else if(L_ch)
            SFR[1]<=PC_out;
        else if(L==1'b1&&SFR_wr==1'b1&&ADDR_bus==16'd1)
            SFR[1]<=W_bus;
    end

    always @(posedge clk or negedge res) begin//中断标志寄存器1
        if(!res)
            SFR[2]<=16'b0;
        else if(L==1'b1&&SFR_wr==1'b1&&ADDR_bus==16'd2)begin
            SFR[2][4]<=(SFR[3][4]) ? W_bus[4]:1'b0;//S1中断标志位
            SFR[2][3]<=(SFR[3][3]) ? W_bus[3]:1'b0;//S0中断标志位
            SFR[2][2]<=(TI0&SFR[3][2]) ? 1'b1:W_bus[2];//T0中断标志位
            SFR[2][1]<=(RI&SFR[3][1]) ? 1'b1:W_bus[1];//Uart0_Rx中断标志位
            SFR[2][0]<=(TI&SFR[3][0]) ? 1'b1:W_bus[0];//Urat0_Tx中断标志位
        end
        else begin
            SFR[2][2]<=(TI0&SFR[3][2]) ? 1'b1:SFR[2][2];//T0中断标志位
            SFR[2][1]<=(RI&SFR[3][1]) ? 1'b1:SFR[2][1];//Uart0_Rx中断标志位
            SFR[2][0]<=(TI&SFR[3][0]) ? 1'b1:SFR[2][0];//Urat0_Tx中断标志位
        end
    end
	assign I=SFR[2];

    always @(posedge clk or negedge res) begin//中断使能寄存器
        if(!res)
            SFR[3]<=16'b0;
        else if(L==1'b1&&SFR_wr==1'b1&&ADDR_bus==16'd3)
            SFR[3][4:0]<=W_bus[4:0];
    end
	 
    always @(posedge clk or negedge res) begin//中断控制寄存器
        if(!res)
            SFR[4]<=16'b0;
        else if(L==1'b1&&SFR_wr==1'b1&&ADDR_bus==16'd4)
            SFR[4][1:0]<=W_bus[1:0];
        else 
            SFR[4][1:0]<=SFR[4][1:0]&2'b10;//保证低位中断清除信号持续一个周期
    end
    assign IF=SFR[4][1];
    assign i_reg_clr=SFR[4][0];

    always @(posedge clk or negedge res) begin//中断服务函数地址寄存器
        if(!res)
            SFR[5]<=16'b0;
        else if(L==1'b1&&SFR_wr==1'b1&&ADDR_bus==16'd5)
            SFR[5]<=W_bus;
    end


    Timer T0(
        .clk(clk),.res(res),.en(SFR[6][1]),.val(SFR[7]),.div_f(SFR[6][3:2]),
        .clr_cnt(SFR[6][0]),.TI(TI0)
    );

    always @(posedge clk or negedge res) begin//T0控制寄存器
        if(!res)
            SFR[6]<=16'b0;
        else if(TI0)
            SFR[6][4]<=1'b1;
        else if(L==1'b1&&SFR_wr==1'b1&&ADDR_bus==16'd6)begin
            SFR[6][4:0]<=(SFR[6][4:0]) ? W_bus[4:0]&5'b11110:W_bus[5:0];
        end
    end

    always @(posedge clk or negedge res) begin//T0阈值寄存器
        if(!res)
            SFR[7]<=16'b0;
        else if(L==1'b1&&SFR_wr==1'b1&&ADDR_bus==16'd7)
            SFR[7]<=W_bus;
    end

    always @(posedge clk or negedge res) begin//中断PC捕获寄存器
        if(!res)
            SFR[8]<=16'b0;
        else if(out_int)
            SFR[8]<=PC_CH;
        else if(L==1'b1&&SFR_wr==1'b1&&ADDR_bus==16'd8)
            SFR[8]<=W_bus;
    end

    
    UART_send Send_uut(.clk(clk),.reset(res),.en(SFR[9][0]),.TXD(TX),.TI(TI),.Data(SFR[10][7:0]),.busy(UART0_busy));
    UART_receive receive_uut(.clk(clk),.reset(res),.en(SFR[9][1]),.RXD(RX),.RI(RI),.out(Rx_data));

    always @(posedge clk or negedge res) begin//URAT0控制寄存器
        if(!res)
            SFR[9]<=16'b0;
        else if(L==1'b1&&SFR_wr==1'b1&&ADDR_bus==16'd9)begin
            SFR[9][2]<=UART0_busy;
            SFR[9][1:0]<=W_bus[1:0];
        end
        else begin
            SFR[9][2]<=UART0_busy;
            SFR[9][0]<=1'b0;
		  end
    end

    always @(posedge clk or negedge res) begin//TX寄存器
        if(!res)
            SFR[10]<=16'b0;
        else if(L==1'b1&&SFR_wr==1'b1&&ADDR_bus==16'd10)
            SFR[10][7:0]<=W_bus[7:0];
    end

    reg RI_reg;
    always @(posedge clk or negedge res) begin
        if(!res)
            RI_reg<=1'b0;
        else    
            RI_reg<=RI;
    end

    always @(posedge clk or negedge res) begin//RX寄存器
        if(!res)
            SFR[11]<=16'b0;
        else if(RI_reg)
            SFR[11]<=Rx_data[7:0];
        else if(L==1'b1&&SFR_wr==1'b1&&ADDR_bus==16'd11)
            SFR[11][7:0]<=W_bus[7:0];
    end

    HMC8 #(ip_sel)HMC8_uut(
        .clk(clk),.res(res),.R_bus(R_bus),.W_bus(W_bus),.ADDR_bus(ADDR_bus),
        .L(L),.E(E),.int_addr(SFR[5]),.out_int(out_int),.SFR_wr(SFR_wr),.L_ch(L_ch),
        .PC_out(PC_out),.PC_CH(PC_CH),.en(en)
    );

endmodule