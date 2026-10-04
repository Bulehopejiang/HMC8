module Regs (
    clk,res,a,b,c,d,a_addr,b_addr,c_addr,d_addr,L_c,L_d,e,e_addr,f,f_addr
    ,g,g_addr
);
    //寄存器组
    input clk,res;
    input [1:0] L_c;
    input L_d;
    output [15:0] a;
    output [15:0] b;
    input [15:0] c;
    input [15:0] d;
    output [15:0] e;
    output [15:0] f;
    output [15:0] g;
    input [3:0] g_addr;
    input [3:0] a_addr;
    input [3:0] b_addr;
    input [3:0] c_addr;
    input [3:0] d_addr;
    input [3:0] e_addr;
    input [3:0] f_addr;

    reg [15:0] regs [0:15];

    assign a=regs[a_addr];
    assign b=regs[b_addr];
    assign e=regs[e_addr];
    assign f=regs[f_addr];
    assign g=regs[g_addr];

    genvar i;
    generate
        for(i=0;i<16;i=i+1)begin:regs_gen
            always @(posedge clk or negedge res) begin
            if(!res)
                regs[i]<=16'b0;
            else if(L_d==1&&d_addr==i)
                regs[i]<=d;
            else if(L_c==2'b01&&c_addr==i)
                regs[i][7:0]<=c[7:0];
            else if(L_c==2'b10&&c_addr==i)
                regs[i][15:8]<=c[7:0];
            else if(L_c==2'b11&&c_addr==i)
                regs[i]<=c;
            
            end
        end
    endgenerate
    
endmodule