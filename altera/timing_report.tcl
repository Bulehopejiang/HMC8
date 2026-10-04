# ============================================================================
#  时序快查脚本 —— 在已有布局布线结果上重跑 TimeQuest，找出当前最差路径
#
#  用法（必须在 altera 目录下执行，因为脚本里要 project_open HMC8）：
#      F:\FPGAIDE\quartus\bin64\quartus_sta.exe -t timing_report.tcl
#
#  输出三部分：
#      1) Fmax 汇总（Slow 85C / Slow 0C / Fast 0C 三个模型）
#      2) 最差 5 条 setup 路径摘要（起点 / 终点 / 数据延时，用来判断路径有没有"挪窝"）
#      3) 最差 1 条 setup 路径的逐级明细（能看到每一级 LUT 和每一段走线各吃掉多少 ns）
#
#  说明：
#      - 只读数据库 + 打印，不改工程，也不会覆盖 output_files 下的报告；
#      - 前提是工程已经跑完过 Fitter（db 目录里有布局布线网表）；
#      - 每改一版 RTL 重新综合布局布线后跑一次，重点看两件事：
#          (1) Fmax 涨了多少；(2) 最差路径的终点是否换成了别的信号。
# ============================================================================

project_open HMC8
create_timing_netlist
read_sdc
update_timing_netlist

puts "\n########## 1) FMAX SUMMARY ##########"
report_clock_fmax_summary -stdout

puts "\n########## 2) WORST 5 SETUP PATHS (summary) ##########"
report_timing -setup -npaths 5 -detail summary -stdout

puts "\n########## 3) WORST SETUP PATH (full detail) ##########"
report_timing -setup -npaths 1 -detail full_path -stdout

project_close
