module jmp_control (
    PROM_out,e,e_addr,PC_add,PC_val,f,f_addr,L_ch
);
    //跳转控制器
    input [23:0] PROM_out;
    output [3:0] e_addr;/*寄存器e f口选择，e口用于条件判断，f口用于加载PC*/
    output [3:0] f_addr;
    output [1:0] PC_add;
    output [15:0] PC_val;
    output L_ch;
    input e;
    input [15:0] f;

    wire [15:0] addr_val;//PC偏移量计算

    assign L_ch=(PROM_out[23:18]==6'd15);

    assign addr_val=(PROM_out[17]) ? {2'b11,PROM_out[17:4]}:{2'b0,PROM_out[17:4]};//偏移量符号扩展

    assign PC_add=(PROM_out[23:18]==6'd14) ? 2'b01:(PROM_out[23:18]==6'd15) ? 2'b10:2'b00;
    assign PC_val=(PROM_out[23:18]==6'd14&&e==1'b1) ? addr_val://JAL
    (PROM_out[23:18]==6'd15) ?  f:16'd1;//JALR
    assign e_addr=PROM_out[3:0];
    assign f_addr=PROM_out[7:4];

endmodule