/*
* key.v  —— 4x4 矩阵按键扫描
* clk      : 50MHz
* rst_n    : 低电平复位
* en       : 使能，高有效；en=0 时回到复位状态（含 key_num 清零）
* key_row  : 行输出，被选行驱动 0、其余行驱动 1；空闲/未使能时全 1
* key_col  : 列输入，外部 10k 上拉；读到 0 表示该键按下
* KI       : 确认一次按下时输出一个时钟周期的正脉冲
* key_num  : 按键编号 = Row*4 + Col = {Row[1:0],Col[1:0]}，确认后保持
*
* 编号表：
*          Col0 Col1 Col2 Col3
*   Row0     0    1    2    3
*   Row1     4    5    6    7
*   Row2     8    9   10   11
*   Row3    12   13   14   15
*
* 状态机（原地锁定式消抖）：
*   S_IDLE : 等 en
*   S_SCAN : 自由扫描找键；行换向后等 20us 再采样列
*   S_DEB  : 锁定候选行，等 10ms 后复检候选列，仍为 0 则确认
*   S_REL  : 仍锁定候选行，等候选列连续 10ms 为 1 才算松开
*
* 时序参数：SETTLE 20us / SCAN 每行 1ms / DEBOUNCE 10ms
*/

module key(clk,rst_n,en,key_row,key_col,KI,key_num);

    parameter CLK_FREQ = 50_000_000;

    localparam SETTLE_MAX = CLK_FREQ / 50_000;   // 20us -> 1000
    localparam SCAN_MAX   = CLK_FREQ / 1_000;    // 1ms  -> 50000
    localparam DEB_MAX    = CLK_FREQ / 100;      // 10ms -> 500000

    //状态编码
    localparam S_IDLE = 2'd0;
    localparam S_SCAN = 2'd1;
    localparam S_DEB  = 2'd2;
    localparam S_REL  = 2'd3;

    input clk;
    input rst_n;
    input en;
    input  [3:0] key_col;
    output reg [3:0] key_row;
    output KI;
    output reg [3:0] key_num;

    reg [3:0] col_d1,col_d2;        //列输入两级同步
    wire [3:0] col_sync;
    reg [1:0] state,state_next;
    reg [1:0] row_idx;              //当前扫描行
    reg [1:0] cand_row,cand_col;    //候选键
    reg [15:0] scan_cnt;            //行内计时
    reg [18:0] deb_cnt;             //消抖/释放计时
    reg [1:0] col_prio;             //列优先编码结果
    wire key_pressed;
    wire cand_pressed;
    wire sample_now;
    wire deb_done;
    wire ki_cond;
    reg  ki_reg;

    //=============== 列输入同步（异步信号两级打拍） ===============
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            col_d1 <= 4'b1111;      //上拉空闲为1，复位取1避免误判按下
            col_d2 <= 4'b1111;
        end
        else begin
            col_d1 <= key_col;
            col_d2 <= col_d1;
        end
    end
    assign col_sync = col_d2;

    //=============== 列优先编码：取列号最小的按下键 ===============
    always @(*) begin
        if(!col_sync[0])      col_prio = 2'd0;
        else if(!col_sync[1]) col_prio = 2'd1;
        else if(!col_sync[2]) col_prio = 2'd2;
        else                  col_prio = 2'd3;
    end
    assign key_pressed  = (col_sync != 4'b1111);            //有列被拉低
    assign cand_pressed = (col_sync[cand_col] == 1'b0);     //1=候选键仍被按下

    //=============== 状态寄存器 ===============
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) state <= S_IDLE;
        else       state <= state_next;
    end

    //=============== 状态转移 ===============
    always @(*) begin
        state_next = state;
        if(!en)
            state_next = S_IDLE;                    //未使能即复位状态
        else case(state)
            S_IDLE: state_next = S_SCAN;

            S_SCAN: begin
                if(sample_now && key_pressed)
                    state_next = S_DEB;             //抓到候选键，转去消抖
                else
                    state_next = S_SCAN;            //否则继续轮转扫描
            end

            S_DEB: begin
                if(deb_done)
                    state_next = (cand_pressed) ? S_REL : S_SCAN;   //10ms后复检
                else
                    state_next = S_DEB;
            end

            S_REL: begin
                if(deb_done && !cand_pressed)
                    state_next = S_SCAN;            //10ms到点且仍为松开
                else
                    state_next = S_REL;
            end

            default: state_next = S_IDLE;
        endcase
    end

    assign sample_now = (scan_cnt == SETTLE_MAX);   //建立时间到，采样一次
    assign deb_done   = (deb_cnt  == DEB_MAX);      //消抖/释放计时到点

    //=============== 行内计时：换行与建立后采样 ===============
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            scan_cnt <= 16'd0;
            row_idx  <= 2'd0;
        end
        else if(state != S_SCAN) begin
            scan_cnt <= 16'd0;                      //离开扫描态即复位
            row_idx  <= 2'd0;                       //回到扫描时从 row0 开始
        end
        else if(scan_cnt == SCAN_MAX) begin
            scan_cnt <= 16'd0;
            row_idx  <= row_idx + 1'b1;             //2位自然回绕 0->1->2->3->0
        end
        else
            scan_cnt <= scan_cnt + 1'b1;
    end

    //=============== 消抖/释放计时 ===============
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n)
            deb_cnt <= 19'd0;
        else if(state == S_DEB) begin               //按下消抖：不监视，直接等满10ms
            deb_cnt <= (deb_cnt == DEB_MAX) ? 19'd0 : deb_cnt + 1'b1;
        end
        else if(state == S_REL) begin
            if(cand_pressed)                        //还按着，计时清零，原地等
                deb_cnt <= 19'd0;
            else                                    //已松开，开始10ms释放计时
                deb_cnt <= (deb_cnt == DEB_MAX) ? 19'd0 : deb_cnt + 1'b1;
        end
        else
            deb_cnt <= 19'd0;
    end

    //=============== 候选键锁存 ===============
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            cand_row <= 2'd0;
            cand_col <= 2'd0;
        end
        else if(!en) begin
            cand_row <= 2'd0;
            cand_col <= 2'd0;
        end
        else if(state == S_SCAN && sample_now && key_pressed) begin
            cand_row <= row_idx;
            cand_col <= col_prio;
        end
    end

    //=============== 行驱动 ===============
    always @(*) begin
        if(state == S_SCAN)
            key_row = ~(4'b0001 << row_idx);        //被选行0，其余1
        else if(state == S_DEB || state == S_REL)
            key_row = ~(4'b0001 << cand_row);       //消抖/等松开期间锁定候选行
        else
            key_row = 4'b1111;                      //空闲/未使能：全1，无键通路
    end

    //=============== 按键值输出 ===============
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n)
            key_num <= 4'd0;
        else if(!en)
            key_num <= 4'd0;                        //未使能即复位状态，一起清零
        else if(ki_cond)
            key_num <= {cand_row,cand_col};         //= Row*4 + Col
    end

    //=============== 中断脉冲：严格单拍 ===============
    //ki_cond 只在 S_DEB 到点那一拍成立（下一拍状态即跳走），天然是单周期条件
    assign ki_cond = en && (state == S_DEB) && deb_done && cand_pressed;

    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) ki_reg <= 1'b0;
        else       ki_reg <= ki_cond;
    end
    assign KI = ki_reg;

endmodule
