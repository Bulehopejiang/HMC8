`timescale 1ns/1ps
module HMC8_SOC_tb (
    
);

    reg clk,res;
    wire [15:0] out;
    wire Tx;
    reg Rx;
    wire [15:0] PC;
    wire [15:0] R0,R1,R2,R3,R4,R5,R6,R7,R8,R9,R10,R11,R12,R13,
	 R14,R15;
	 wire [15:0] SFR1;
	 wire [15:0] SFR2;

    HMC8_SOC uut(
        .clk(clk),.res_n(res),.out(out),.TX(Tx),.RX(Rx)
    );

    assign PC=uut.HMC8_uut.PC;
    assign R0=uut.HMC8_uut.Regs_uut.regs[0];
    assign R1=uut.HMC8_uut.Regs_uut.regs[1];
    assign R2=uut.HMC8_uut.Regs_uut.regs[2];
    assign R3=uut.HMC8_uut.Regs_uut.regs[3];
    assign R4=uut.HMC8_uut.Regs_uut.regs[4];
    assign R5=uut.HMC8_uut.Regs_uut.regs[5];
    assign R6=uut.HMC8_uut.Regs_uut.regs[6];
    assign R7=uut.HMC8_uut.Regs_uut.regs[7];
    assign R8=uut.HMC8_uut.Regs_uut.regs[8];
    assign R9=uut.HMC8_uut.Regs_uut.regs[9];
    assign R10=uut.HMC8_uut.Regs_uut.regs[10];
    assign R11=uut.HMC8_uut.Regs_uut.regs[11];
    assign R12=uut.HMC8_uut.Regs_uut.regs[12];
    assign R13=uut.HMC8_uut.Regs_uut.regs[13];
    assign R14=uut.HMC8_uut.Regs_uut.regs[14];
    assign R15=uut.HMC8_uut.Regs_uut.regs[15];
    assign SFR1=uut.SFR[1];
	 assign SFR2=uut.SFR[2];

    initial begin
        clk=0;
        forever begin
            #10 clk=~clk;
        end
    end

    initial begin
        res=0;
        #20;
        res=1;
    end

    initial begin
        Rx=1'b1;
        #20;
        repeat(30)@(posedge clk);
        Send(8'd120);
        #1000_000;
        Send(8'd120);
        #1000_000;
        $stop;
    end
    
    task Send;
        input [7:0] Data;
        integer i;
        begin
            Rx=1'b0;
            #(1_000_000_000/9600);
            for(i=0;i<8;i=i+1)begin
                Rx=Data[i];
                #(1_000_000_000/9600);
            end
            Rx=1'b1;
            #(1_000_000_000/9600);
        end
    endtask

endmodule