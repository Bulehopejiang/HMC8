`timescale 1ns/1ps
module HMC8_SOC_tb (
    
);

    reg clk,res;
    wire [15:0] out;
    wire Tx;
    reg Rx;

    HMC8_SOC uut(
        .clk(clk),.res_n(res),.out(out),.TX(Tx),.RX(Rx)
    );

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