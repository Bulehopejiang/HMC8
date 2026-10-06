module pip_control (
    clk,res,en,finish,alu_op,L_d,L_cb
);
    //流水线控制器
    input clk,res;
    input [5:0] alu_op;
    output en;
    input finish;
    output L_d;
    output [1:0] L_cb;

    reg state,state_next;

    always @(posedge clk or negedge res) begin
        if(!res)
            state<=1'b0;
        else 
            state<=state_next;
    end

    always @(*) begin
        case (state)
            1'b0:state_next=(alu_op==6'd27||alu_op==6'd28);//乘除法运算触发此模块工作
            1'b1:state_next=~finish; 
            default: state_next=0;
        endcase
    end

    assign en=~state;
    assign L_d=(state_next==1'b0&&state==1'b1);
    assign L_cb=(state_next==1'b0&&state==1'b1) ? 2'b11:2'b0;

endmodule