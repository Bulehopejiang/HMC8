import re
orders={#指令集
    'ADDI':1, #立即数加
    'SLTI':2, #立即数大小比较
    'SLLI':3, #立即数左移
    'SRLI':4, #立即数右移
    'ADD':5,  #加
    'SUB':6,  #减
    'SLL':7,  #左移
    'SRL':8,  #右移
    'NOP':0,  #空操作
    'AND':11, #与
    'OR':12,  #或
    'XOR':13, #异或
    'JAL':14, #判断短跳转
    'JALR':15,#长跳转
    'BEQ':16, #相等
    'BNE':17, #不等
    'BLT':18, #小于 有符号
    'BGE':19, #大于等于 有符号
    'BLTU':20,#小于
    'BGEU':21,#大于等于
    'LB':22,  #半字加载
    'LSR':23, #特殊寄存器加载
    'ESR':24, #特殊寄存器输出
    'IN':25,  #从内存读
    'OUT':26, #从内存写
    'MUL':27, #乘
    'DIV':28, #除
    'XORI':29,#立即数异或
    'ORI':30, #立即数或
    'ANDI':31,#立即数与
    'SRAI':32,#立即数算数右移
    'SRA':33, #算数右移
    'SLA':34  #算数左移
}
pattern_order=r"(BGEU|BLTU|NOP|SRAI|ADDI|BNE|SLTI|SLLI|SRLI|ADD|BEQ|SUB|SLL|SRL|ANDI|ORI|XORI|JALR|JAL|BLT|BGE|LB|SLA|LSR|ESR|IN|OUT|MUL|DIV|XOR|OR|AND|SRA)"
pattern_regs=r"\s+(R15|R14|R13|R12|R11|R10|R9|R8|R7|R6|R5|R4|R3|R2|R1|R0)+"#寄存器格式
pattern_addr=r"(@\w+)+"#跳转地址格式
pattern_num=r"(\s+\d+U|\s+-\d+|\s+\d+|\s+\d+u)+"#立即数格式
pattern_fun=r"(LOW|HIGH)+"#系统函数格式
pattern_express=r"(;[\w+\d++-=@,.，。\s+]+|；[\w+\d++-=@,.，。\s+]+)"#注释格式
regs={#寄存器名称
    'R0':0,
    'R1':1,
    'R2':2,
    'R3':3,
    'R4':4,
    'R5':5,
    'R6':6,
    'R7':7,
    'R8':8,
    'R9':9,
    'R10':10,
    'R11':11,
    'R12':12,
    'R13':13,
    'R14':14,
    'R15':15,
}
mech_rom=(24,1024)