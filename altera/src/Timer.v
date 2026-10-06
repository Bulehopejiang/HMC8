module Timer (
    clk,res,en,val,div_f,clr_cnt,TI
);
    //定时器
    input clk,res,en;
    input [1:0] div_f;//分频系数
    input [15:0] val;//阈值
    input clr_cnt;//清零信号
    output TI;//溢出信号

    reg [15:0] cnt;
    reg [1:0] div_f_reg;
    wire div_sign;
    wire cnt_full_sign;
    reg TI_reg;

    always @(posedge clk or negedge res) begin//分频计数器
        if(!res)
            div_f_reg<=2'b0;
        else    
            div_f_reg<=(div_sign) ? 2'b0:div_f_reg+1'b1; 
    end

    assign div_sign=(div_f_reg==div_f);//同步分频信号

    always @(posedge clk or negedge res) begin//主计数器
        if(!res)
            cnt<=16'b0;
        else if(clr_cnt)
            cnt<=16'b0;
        else if(en&div_sign)
            cnt<=(cnt_full_sign) ? 16'b0:cnt+1'b1;
    end
    
    assign cnt_full_sign=(cnt==val);//溢出信号

    always @(posedge clk or negedge res) begin/*溢出信号整型，使之维持一个周期*/
        if(!res)
            TI_reg<=1'b1;
        else 
            TI_reg<=cnt_full_sign;
    end

    assign TI=~TI_reg&cnt_full_sign;

endmodule