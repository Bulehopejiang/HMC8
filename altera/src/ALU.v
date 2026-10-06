module ALU (
    clk,res,alu_op,out_l,out_h,finish,A,B
);
    //运算器
    input clk,res;
    input [5:0] alu_op;
    output [15:0] out_h;
    output reg [15:0] out_l;
    output finish;
    input [15:0] A;
    input [15:0] B;

    wire [15:0] mul_l;
    wire [15:0] mul_h;
    wire [15:0] div_r;
    wire [15:0] div_q;
    wire mul_finish;
    wire div_finish;

    always @(*) begin
        if(mul_finish|div_finish)//乘除法时outl被从组合逻辑区分离出来，交由乘除法器接管
            out_l=(mul_finish) ? mul_l:div_q;
        else
            case (alu_op)//组合逻辑运算区域
                6'd1,6'd5:out_l=A+B;
                6'd20:out_l=(A<B);
                6'd7,6'd3:out_l=A<<B;
                6'd8,6'd4:out_l=A>>B;
                6'd6:out_l=A-B;
                6'd18,6'd2:out_l=($signed(A)<$signed(B));
                6'd11,6'd31:out_l=A&B;
                6'd12,6'd30:out_l=A|B;
                6'd13,6'd29:out_l=A^B;
                6'd16:out_l=(A==B);
                6'd17:out_l=(A!=B);
                6'd19:out_l=($signed(A)>=$signed(B));
                6'd21:out_l=(A>=B);
                6'd32,6'd33:out_l=$signed(A)>>>B;
                6'd34:out_l=$signed(A)<<<B;
                6'd23,6'd24,6'd25,6'd26:out_l=A;
                default:out_l=B;
            endcase
    end

    assign out_h=(mul_finish) ? mul_h:div_r;//高位选择逻辑
    assign finish=div_finish|mul_finish;//乘除完成信号

    DIV_serial DIV_uut(//除法器
        .clk(clk),.res_n(res),.a(A),.b(B),.out({div_r,div_q}),
        .en(alu_op==6'd28),
        .finish(div_finish)
    );

    MUL_serial MUL_uut(//乘法器
        .clk(clk),.res_n(res),.a(A),.b(B),.out({mul_h,mul_l}),
        .en(alu_op==6'd27),
        .finish(mul_finish)
    );

endmodule