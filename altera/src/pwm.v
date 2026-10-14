/*
* pwm.v
* clk: 50MHz
* rst_n: 低电平复位
* freq_div: 分频系数16bit,0 按不分频处理
* duty: 占空比16bit（高电平的 tick 个数）
* cnt: 计数阈值16bit（PWM 周期 = cnt 个 tick，0 按 1 处理）
* en: PWM使能信号,高电平使能（为 0 时计数器清零、输出拉低）
* pwm_out: PWM输出
*/
module pwm(clk,rst_n,freq_div,duty,cnt,en,pwm_out);
    parameter CLK_FREQ=50000000;   
    input clk;
    input rst_n;
    input [15:0] freq_div;
    input [15:0] duty;
    input [15:0] cnt;
    input en;
    output reg pwm_out;
    reg [15:0] cnt_f;
    reg [15:0] cnt_t;
    reg tick;
    // 0 值保护：freq_div=0 视为不分频(除1)，cnt=0 视为周期 1 个 tick
    wire [15:0] div_v = (freq_div == 16'd0) ? 16'd1 : freq_div;
    wire [15:0] per_v = (cnt      == 16'd0) ? 16'd1 : cnt;
    //分频器
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            cnt_f <= 16'd0;
            tick <= 1'b0;
        end
        else begin
            tick <= 1'b0;
            if(!en) begin
                cnt_f <= 16'd0;
            end
            else if(cnt_f >= div_v - 16'd1) begin
                cnt_f <= 16'd0;
                tick <= 1'b1;
            end
            else begin
                cnt_f <= cnt_f + 16'd1;
            end
        end
    end
    //计数器
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            cnt_t <= 16'd0;
        end
        else if(!en) begin
            cnt_t <= 16'd0;
        end
        else if(tick) begin
            if(cnt_t >= per_v - 16'd1)
                cnt_t <= 16'd0;
            else
                cnt_t <= cnt_t + 16'd1;
        end
    end
    //PWM生成器
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n)
            pwm_out <= 1'b0;
        else if(!en)
            pwm_out <= 1'b0;
        else if(cnt_t < duty)
            pwm_out <= 1'b1;
        else
            pwm_out <= 1'b0;
    end
endmodule