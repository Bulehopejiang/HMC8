/*
* dig.v  —— 4 位共阴极数码管动态扫描驱动
*
* clk            : 50MHz
* rst_n          : 低电平复位
* en             : 高电平使能；en=0 回到复位状态（全灭、计数器清零）
* digit0~digit3  : 4 位待显示数字，各 4 位 BCD；只显示 0~9，10~15 一律熄灭
* dp[3:0]        : 每位小数点，1=亮；不用时接 4'b0000（默认全暗）
* DigitronCS_Out : 位选，共阴极直连 -> 低电平选中该位
* Digitron_Out   : 段选 {DOT,G,F,E,D,C,B,A}，高电平点亮
*
* 扫描时序（整轮 4ms，刷新率 250Hz）：
*   每位时隙 1ms = 50000 拍 @50MHz
*     前 20us（1000 拍）：消影期，段全灭
*     其余 980us（49000 拍）：显示该位段码
*
* 防重影：
*   1) 段选在消影期强制输出 8'h00；
*   2) 位选用 bit_sel_d（比 bit_sel 晚一拍）并寄存输出，保证"段先灭、位后切"，
*      且 4 路位选同步翻转，不会出现两位同时被选中的瞬态。
*
* 段码表（bit6~bit0 = G~A，高电平亮）：
*   0:3F  1:06  2:5B  3:4F  4:66  5:6D  6:7D  7:07  8:7F  9:6F  其它:00
*
* 注意：动态扫描下每位只在 1/4 时间点亮，实际亮度约为静态驱动的 24.5%；
*       若上板觉得偏暗，请从硬件侧（减小段限流电阻）解决，RTL 无法补偿。
*/

module dig(clk,rst_n,en,digit0,digit1,digit2,digit3,dp,DigitronCS_Out,Digitron_Out);

    parameter CLK_FREQ = 50_000_000;

    localparam BIT_CNT   = CLK_FREQ / 1_000;    // 1ms  -> 50000 拍
    localparam BLANK_CNT = CLK_FREQ / 50_000;   // 20us -> 1000 拍

    input clk;
    input rst_n;
    input en;
    input [3:0] digit0,digit1,digit2,digit3;
    input [3:0] dp;
    output reg [3:0] DigitronCS_Out;
    output reg [7:0] Digitron_Out;

    reg [15:0] scan_cnt;        //位内计时
    reg [1:0]  bit_sel;         //当前扫描位
    reg [1:0]  bit_sel_d;       //位选输出用，比 bit_sel 晚一拍
    reg [3:0]  cur_digit;       //当前位要显示的数字
    reg        cur_dp;          //当前位的小数点
    reg [6:0]  seg;             //当前位的段码

    //=============== 位内计时与位选计数 ===============
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            scan_cnt <= 16'd0;
            bit_sel  <= 2'd0;
        end
        else if(!en) begin
            scan_cnt <= 16'd0;
            bit_sel  <= 2'd0;
        end
        else if(scan_cnt == BIT_CNT - 1) begin
            scan_cnt <= 16'd0;
            bit_sel  <= bit_sel + 1'b1;         //2位自然回绕 0->1->2->3->0
        end
        else
            scan_cnt <= scan_cnt + 1'b1;
    end

    //=============== 位选延迟一拍（配合消影，保证"段先灭、位后切"） ===============
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n)      bit_sel_d <= 2'd0;
        else if(!en)    bit_sel_d <= 2'd0;
        else            bit_sel_d <= bit_sel;
    end

    //=============== 当前位数字选择 ===============
    always @(*) begin
        case(bit_sel)
            2'd0:    cur_digit = digit0;
            2'd1:    cur_digit = digit1;
            2'd2:    cur_digit = digit2;
            default: cur_digit = digit3;
        endcase
    end

    //=============== 当前位小数点选择 ===============
    always @(*) begin
        case(bit_sel)
            2'd0:    cur_dp = dp[0];
            2'd1:    cur_dp = dp[1];
            2'd2:    cur_dp = dp[2];
            default: cur_dp = dp[3];
        endcase
    end

    //=============== 段码译码（0~9，其它熄灭） ===============
    always @(*) begin
        case(cur_digit)
            4'd0:    seg = 7'h3F;   //A B C D E F
            4'd1:    seg = 7'h06;   //  B C
            4'd2:    seg = 7'h5B;   //A B D E G
            4'd3:    seg = 7'h4F;   //A B C D G
            4'd4:    seg = 7'h66;   //  B C F G
            4'd5:    seg = 7'h6D;   //A C D F G
            4'd6:    seg = 7'h7D;   //A C D E F G
            4'd7:    seg = 7'h07;   //A B C
            4'd8:    seg = 7'h7F;   //A B C D E F G
            4'd9:    seg = 7'h6F;   //A B C D F G
            default: seg = 7'h00;   //10~15 熄灭
        endcase
    end

    //=============== 位选输出（寄存，4路同步翻转，低电平选中） ===============
    //位序反向：本板 DigitronCS_Out[3] 在最左、[0] 在最右，与 bit_sel 的递增方向相反。
    //故 bit_sel=0 选中 [3]（最左）、bit_sel=3 选中 [0]（最右），
    //使 digit0 显示在最左、digit3 显示在最右（与汇编里 IO[2]~IO[5] 的书写顺序一致）。
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n)      DigitronCS_Out <= 4'b1111;
        else if(!en)    DigitronCS_Out <= 4'b1111;
        else            DigitronCS_Out <= ~(4'b1000 >> bit_sel_d);
    end

    //=============== 段选输出（寄存，消影期全灭） ===============
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n)                      Digitron_Out <= 8'h00;
        else if(!en)                    Digitron_Out <= 8'h00;
        else if(scan_cnt < BLANK_CNT)   Digitron_Out <= 8'h00;          //消影
        else                            Digitron_Out <= {cur_dp,seg};   //bit7=DOT, bit6~0=G~A
    end

endmodule
