module HMC8_SOC (
    clk,res_n,out,TX,RX
);
    localparam  i_num= 5;//中断源个数
    parameter ip_sel=0;//1 altera 0 al

    input clk,res_n;
    output [15:0] out;//输出寄存器端口
    input RX;/*串口收发*/
    output TX;

    reg resdff1,res;//异步复位信号打拍
    wire [15:0] R_bus,W_bus,ADDR_bus;//写，读，地址总线
    wire L,E;//内存与特殊寄存器组加载使能与输出允许
    wire out_int;//去往CPU的中断使能信号
    wire SFR_wr;//特殊寄存器组写使能信号
    wire [15:0] PC_out;//PC输出
    wire L_ch;//PC返回寄存器加载使能，用于子程序
    wire [15:0] RAM_out;//RAM输出
    reg [15:0] SFR [0:11];//特殊寄存器区（此区域是紧耦合于CPU的，访问速度较快）
    reg [15:0] IO [0:1];//内存区（低速外设映射到此区域）
    wire [i_num-1:0] I;//中断源输入
    wire i_reg_clr;//中断更新信号
    wire i;//中断信号汇总，是所有中断相或后的信号
    wire IF;//总中断允许
    wire en;//来自CPU的使能信号，由CPU控制
    reg i_reg;//中断寄存，用于与i配合组成一个边沿检测器
    wire [15:0] PC_CH;//用于中断捕获的PC信号
    wire UART0_busy;//UART0忙信号
    wire TI,RI;//UART0对应中断
    wire [7:0] Rx_data;//UART0接收到的数据
    wire TI0;//定时器0中断信号



	generate//RAM IP选择
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
    assign i=|I;//所有中断信号相或
    assign out_int=~i_reg&i;//中断边沿检测

    assign R_bus=(SFR_wr) ? SFR[ADDR_bus]:(ADDR_bus<16'd2048) ? RAM_out:IO[ADDR_bus];//读总线选择逻辑

    always @(posedge clk) begin//复位信号打拍
        resdff1<=res_n;
        res<=resdff1;
    end

    //输出寄存器    地址：0
    always @(posedge clk or negedge res) begin//输出寄存器
        if(!res)
            SFR[0]<=16'b0;
        else if(L==1'b1&&SFR_wr==1'b1&&ADDR_bus==16'b0)
            SFR[0]<=W_bus;
    end
    assign out=SFR[0];

    //PC返回寄存器  地址：1
    always @(posedge clk or negedge res) begin//PC返回寄存器（执行JALR指令时PC值会捕获到此处）
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
	assign I=SFR[2];//送往中断边沿检测器

    /*  中断源使能寄存器    地址：3
        软中断1  软中断0 T0中断   UART0接收中断   UART0发送中断
        4       3       2       1               0
        S1      S0      T0      Rx0             Tx0
    */
    always @(posedge clk or negedge res) begin//各中断源使能寄存器
        if(!res)
            SFR[3]<=16'b0;
        else if(L==1'b1&&SFR_wr==1'b1&&ADDR_bus==16'd3)
            SFR[3][4:0]<=W_bus[4:0];
    end


    /*  中断控制寄存器      地址：4
        总中断   中断更新
        1        0
        IF       RF
    */ 
    always @(posedge clk or negedge res) begin//中断控制寄存器
        if(!res)
            SFR[4]<=16'b0;
        else if(L==1'b1&&SFR_wr==1'b1&&ADDR_bus==16'd4)
            SFR[4][1:0]<=W_bus[1:0];
        else 
            SFR[4][1:0]<=SFR[4][1:0]&2'b10;//保证低位中断清除信号持续一个周期
    end
    assign IF=SFR[4][1];//总中断使能
    assign i_reg_clr=SFR[4][0];//中断更新信号

    //中断服务函数地址寄存器    地址：5
    always @(posedge clk or negedge res) begin//中断服务函数地址寄存器
        if(!res)
            SFR[5]<=16'b0;
        else if(L==1'b1&&SFR_wr==1'b1&&ADDR_bus==16'd5)
            SFR[5]<=W_bus;
    end


    Timer T0(//T0 定时器
        .clk(clk),.res(res),.en(SFR[6][1]),.val(SFR[7]),.div_f(SFR[6][3:2]),
        .clr_cnt(SFR[6][0]),.TI(TI0)
    );

    /*  T0控制寄存器    地址：6
        溢出信号     分频系数               使能     清0
        4           3   2                    1      0
        TI0    分频系数（0默认不分频）        TR0    clr0
    */
    always @(posedge clk or negedge res) begin//T0控制寄存器
        if(!res)
            SFR[6]<=16'b0;
        else if(TI0)
            SFR[6][4]<=1'b1;//定时器溢出位，需要软件清零
        else if(L==1'b1&&SFR_wr==1'b1&&ADDR_bus==16'd6)begin
            SFR[6][4:0]<=(SFR[6][0]) ? W_bus[4:0]&5'b11110:W_bus[5:0];//保证T0清零信号维持一个周期
        end
    end

    //T0阈值寄存器  地址：7
    always @(posedge clk or negedge res) begin//T0阈值寄存器（T0记到此值后自动清零并触发中断）
        if(!res)
            SFR[7]<=16'b0;
        else if(L==1'b1&&SFR_wr==1'b1&&ADDR_bus==16'd7)
            SFR[7]<=W_bus;
    end

    //中断PC捕获寄存器  地址：8
    always @(posedge clk or negedge res) begin//中断PC捕获寄存器（中断被触发后，PC值捕获到此处）
        if(!res)
            SFR[8]<=16'b0;
        else if(out_int)
            SFR[8]<=PC_CH;
        else if(L==1'b1&&SFR_wr==1'b1&&ADDR_bus==16'd8)
            SFR[8]<=W_bus;
    end

    /*UART0*/
    UART_send Send_uut(.clk(clk),.reset(res),.en(SFR[9][0]),.TXD(TX),.TI(TI),.Data(SFR[10][7:0]),.busy(UART0_busy));
    UART_receive receive_uut(.clk(clk),.reset(res),.en(SFR[9][1]),.RXD(RX),.RI(RI),.out(Rx_data));

    /*  URAT0控制寄存器     地址：9
        发送忙           接收使能    发送使能
        2               1           0
        UART0_busy      ER0         ET0
    */
    //发送使能置位后硬件自动清0，再次发送需要软件置位
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

    //TX寄存器  地址：10
    always @(posedge clk or negedge res) begin//TX寄存器
        if(!res)
            SFR[10]<=16'b0;
        else if(L==1'b1&&SFR_wr==1'b1&&ADDR_bus==16'd10)
            SFR[10][7:0]<=W_bus[7:0];
    end

    reg RI_reg;
    always @(posedge clk or negedge res) begin//RI信号打拍，时序需要
        if(!res)
            RI_reg<=1'b0;
        else    
            RI_reg<=RI;
    end

    //RX寄存器  地址：11
    always @(posedge clk or negedge res) begin//RX寄存器
        if(!res)
            SFR[11]<=16'b0;
        else if(RI_reg)
            SFR[11]<=Rx_data[7:0];
        else if(L==1'b1&&SFR_wr==1'b1&&ADDR_bus==16'd11)
            SFR[11][7:0]<=W_bus[7:0];
    end

    HMC8 #(ip_sel)HMC8_uut(//HMC8 RISC CPU
        .clk(clk),.res(res),.R_bus(R_bus),.W_bus(W_bus),.ADDR_bus(ADDR_bus),
        .L(L),.E(E),.int_addr(SFR[5]),.out_int(out_int),.SFR_wr(SFR_wr),.L_ch(L_ch),
        .PC_out(PC_out),.PC_CH(PC_CH),.en(en)
    );


endmodule