module HMC8_SOC (
    clk,res_n,out
);
    
    input clk,res_n;
    output [15:0] out;

    reg resdff1,res;
    wire [15:0] R_bus,W_bus,ADDR_bus;
    wire L,E;
    wire out_int;
    wire SFR_wr;
    wire [15:0] PC_out;
    wire L_ch;
    wire [15:0] RAM_out;
    reg [15:0] SFR [0:1];
    reg [15:0] IO [0:1];

	 RAM	RAM_inst (
	.address ( ADDR_bus ),
	.clock ( clk ),
	.data ( W_bus ),
	.wren ( L==1'b1&&ADDR_bus<16'd2048 ),
	.q ( RAM_out )
	);

    assign out_int=1'b0;
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

    HMC8 HMC8_uut(
        .clk(clk),.res(res),.R_bus(R_bus),.W_bus(W_bus),.ADDR_bus(ADDR_bus),
        .L(L),.E(E),.int_addr(SFR[1]),.out_int(out_int),.SFR_wr(SFR_wr),.L_ch(L_ch),
        .PC_out(PC_out)
    );

endmodule