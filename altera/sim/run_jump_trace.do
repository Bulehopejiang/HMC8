# ============================================================================
#  跳转指令调试仿真脚本
#
#  用法（工作目录必须是 altera/simulation/modelsim，因为 altsyncram 会去那里找 PROM.mif）：
#      cd altera\simulation\modelsim
#      F:\FPGAIDE\modelsim_ase\win32aloem\vsim.exe -c -do ..\..\sim\run_jump_trace.do
#
#  与 Quartus 自动生成的 HMC8_run_msim_rtl_verilog.do 用的是同一套库和源码，
#  区别只是最顶层换成 tb_jump_trace（会逐拍打印 PC / 译码器 / 寄存器现场）。
# ============================================================================
transcript on
if {[file exists work]} {
	vdel -lib work -all
}
vlib work
vmap work work

set SRC ../../src
set IP  ../../ip

vlog -vlog01compat -work work +incdir+$SRC "$SRC/HMC8_SOC.v"
vlog -vlog01compat -work work +incdir+$SRC "$SRC/Regs.v"
vlog -vlog01compat -work work +incdir+$SRC "$SRC/pip_control.v"
vlog -vlog01compat -work work +incdir+$SRC "$SRC/MUL_serial.v"
vlog -vlog01compat -work work +incdir+$SRC "$SRC/jmp_control.v"
vlog -vlog01compat -work work +incdir+$SRC "$SRC/DIV_serial.v"
vlog -vlog01compat -work work +incdir+$SRC "$SRC/decoder.v"
vlog -vlog01compat -work work +incdir+$SRC "$SRC/HMC8.v"
vlog -vlog01compat -work work +incdir+$SRC "$SRC/ALU.v"
vlog -vlog01compat -work work +incdir+$IP  "$IP/PROM.v"
vlog -vlog01compat -work work +incdir+$IP  "$IP/RAM.v"
vlog -vlog01compat -work work +incdir+.    "../../sim/tb_jump_trace.v"

vsim -t 1ps -L altera_ver -L lpm_ver -L sgate_ver -L altera_mf_ver -L altera_lnsim_ver -L cycloneive_ver -L work -voptargs="+acc" tb_jump_trace
run -all
quit -f
