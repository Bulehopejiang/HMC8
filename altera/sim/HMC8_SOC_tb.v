`timescale 1ns/1ps
module HMC8_SOC_tb (
    
);

    reg clk,res;
    wire [15:0] out;
    wire Tx;
    reg Rx;
    wire [15:0] PC;
    wire [15:0] regs [0:15];

    HMC8_SOC uut(
        .clk(clk),.res_n(res),.out(out),.TX(Tx),.RX(Rx)
    );

    assign PC=uut.HMC8_uut.PC;
    assign regs[0]=uut.HMC8_uut.Regs_uut.regs[0];
    assign regs[1]=uut.HMC8_uut.Regs_uut.regs[1];
    assign regs[2]=uut.HMC8_uut.Regs_uut.regs[2];
    assign regs[3]=uut.HMC8_uut.Regs_uut.regs[3];
    assign regs[4]=uut.HMC8_uut.Regs_uut.regs[4];
    assign regs[5]=uut.HMC8_uut.Regs_uut.regs[5];
    assign regs[6]=uut.HMC8_uut.Regs_uut.regs[6];
    assign regs[7]=uut.HMC8_uut.Regs_uut.regs[7];
    assign regs[8]=uut.HMC8_uut.Regs_uut.regs[8];
    assign regs[9]=uut.HMC8_uut.Regs_uut.regs[9];
    assign regs[10]=uut.HMC8_uut.Regs_uut.regs[10];
    assign regs[11]=uut.HMC8_uut.Regs_uut.regs[11];
    assign regs[12]=uut.HMC8_uut.Regs_uut.regs[12];
    assign regs[13]=uut.HMC8_uut.Regs_uut.regs[13];
    assign regs[14]=uut.HMC8_uut.Regs_uut.regs[14];
    assign regs[15]=uut.HMC8_uut.Regs_uut.regs[15];
    

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