# ============================================================================
#  HMC8 —— 安路 EG4(EG4S20BG256) 平台 RTL 仿真脚本（ModelSim）
#
#  用法（必须在 al/HMC8/sim/ 目录下执行）：
#     命令行：
#        F:\FPGAIDE\modelsim_ase\win32aloem\vsim.exe -c -do "do rtl_sim.do; run 100us; quit -f"
#     图形界面：在该目录启动 vsim，Transcript 里输入   do rtl_sim.do
#              加载完成后 run -all / run 100us，波形自己 add wave。
#
#  这个脚本干了什么：
#    1) 把 ../al_PROM.mif 转成 al_PROM.hex，给仿真用的存储器模型读；
#    2) 编译「你的 RTL + 仿真存储器模型 sim_mem.v + testbench」；
#    3) 用安路编译好的仿真库加载（testbench 里的 glbl 来自这个库）。
#
#  三个容易踩的坑：
#    a) 工作目录必须是 al/HMC8/sim/：脚本要读 ../al_PROM.mif。
#    b) 顶层必须写 testbench 名 HMC8_SOC_tb。
#       （TD 自动生成的 HMC8_Runs/phy_1/simulation/HMC8_phy_sim.do 里这一格是空的，
#        直接跑会报  ** Error: (vsim-11) Could not find work.<NULL>. ）
#    c) 本脚本用 sim_mem.v 代替 ip/PROM.v、ip/RAM.v，不要同时编译它们（模块重名）。
#       要看「综合后网表」仿真时用 TD 自己生成的 HMC8_Runs/phy_1/simulation/HMC8_phy_sim.v
#       （那份网表里的 BRAM 初值是以 INIT_00/INITP_00 参数内嵌的，不需要 mif）。
# ============================================================================

set ANLOGIC_LIB F:/FPGAIDE/modelsim_ase/Anlogic/eg4d
set RTL         ../../../altera/src

# ---------- 1) al_PROM.mif -> al_PROM.hex（$readmemh 格式）----------
if {![file exists ../al_PROM.mif]} {
    puts "!! 找不到 ../al_PROM.mif，请确认在 al/HMC8/sim/ 下运行"
}
set fin  [open ../al_PROM.mif r]
set fout [open al_PROM.hex w]
set n 0
while {[gets $fin line] >= 0} {
    if {[regexp {^[ \t]*[0-9]+[ \t]*:[ \t]*([0-9]+)[ \t]*;} $line -> v]} {
        puts $fout [format %06X $v]
        incr n
    }
}
close $fin
close $fout
puts "== al_PROM.mif -> al_PROM.hex : $n 个指令字 =="

# ---------- 2) 建库并编译 ----------
if {[file exists work]} { vdel -lib work -all }
vlib work
vmap work work

vlog -quiet -work work sim_mem.v

vlog -quiet -work work \
    $RTL/ALU.v $RTL/DIV_serial.v $RTL/HMC8.v $RTL/HMC8_SOC.v $RTL/MUL_serial.v \
    $RTL/Regs.v $RTL/Timer.v $RTL/UART_receive.v $RTL/UART_send.v \
    $RTL/decoder.v $RTL/jmp_control.v $RTL/pip_control.v

vlog -quiet -work work HMC8_SOC_tb.v

# ---------- 3) 加载（-novopt 保留层次，方便 examine/加波形）----------
vsim -L $ANLOGIC_LIB -novopt work.HMC8_SOC_tb
