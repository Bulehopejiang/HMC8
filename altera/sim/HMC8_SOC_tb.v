`timescale 1ns/1ps
module HMC8_SOC_tb (
    
);

    reg clk,res;
    wire [15:0] out;

    HMC8_SOC uut(
        .clk(clk),.res_n(res),.out(out)
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
        #20;
        repeat(100)@(posedge clk);
        $stop;
    end
    
endmodule