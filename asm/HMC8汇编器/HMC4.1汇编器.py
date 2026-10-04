from my_tkui import *
from ISA import *

'''窗口类定义'''
filepath = ''  # 当前文件路径
'''创建根窗口'''
window = AppWindow('HMC8汇编器', 1000, 800, 800, 600)
volumn1 = HSplitFrame(window.root)  # 左右控件分布
volumn2 = VSplitFrame(volumn1.right, 4, 1, False)  # 左侧容器上下分布
workplace = LogPanel(volumn2.top, line_number_color='#66CCFF')  # 在右上部分添加文件工作区
logplace = LogPanel(volumn2.bottom, read_only=True, show_line_numbers=False)  # 在右下部分添加日志区域
fileselect = FileSelect(volumn1.left, '选择文件')
message = LogPanel(volumn1.left, read_only=True, show_line_numbers=False)
order_show = '''
指令集：
ADDI imm R2 R3 ;R3=R2+sext(imm)
SLTI imm R2 R3 ;R3=(R2<sext(imm)) ? 1:0
SLLI imm R2 R3 ;R3=R2<<imm
SRLI imm R2 R3 ;R3=R2>>imm
ADD R1 R2 R3 ;R3=R1+R2
SUB R1 R2 R3 ;R3=R1-R2
SLL R1 R2 R3 ;R3=R1<<R2
SRL R1 R2 R3 ;R3=R1>>R2
AND R1 R2 R3 ;R3=R1&R2
OR R1 R2 R3 ;R3=R1|R2
XOR R1 R2 R3 ;R3=R1^R2
JAL imm R3 ;PC=(R3[0]==1) ? PC+sext(imm):PC+1
JALR R1 ;SFR[1]=PC PC=R1
BEQ R1 R2 R3 ;R3=(R1==R2)
BNE R1 R2 R3 ;R3=(R1!=R2)
BLT R1 R2 R3 ;R3=(R1<R2)(有符号)
BGE R1 R2 R3 ;R3=(R1>=R2)(有符号)
BLTU R1 R2 R3 ;R3=(R1<R2)
BGEU R1 R2 R3 ;R3=(R1>=R2)
LB LOW/HIGH imm R3 ;加载高8位或者低8位
LSR imm R2 ;SFR[imm]=R2
ESR imm R2 ;R2=SFR[imm]
IN R1 R2 ;R2=IO[R1]
OUT R1 R2 ;IO[R1]=R2
MUL R1 R2 R3 R4 ;{R1,R4}=R2*R3
DIV R1 R2 R3 R4 ;R1=R2%R3 R4=R2/R3
XORI imm R2 R3 ;R3=R2^sext(imm)
ANDI imm R2 R3 ;R3=R2|sext(imm)
SRAI imm R2 R3 ;R3=R2>>>imm
SRA R1 R2 R3 ;R3=R2>>>R1;
SRL R1 R2 R3 ;R3=R2<<<R1;
'''
regs_show = '''寄存器名称
R+数字（0-15）
'''
fun_show = '''系统函数
LOW:取第8位 HIGH:取高8位
无符号数末尾加u或者U
'''
'''函数定义区'''


def mess_show():  # 信息栏
    message.log('欢迎使用！本软件由bulehopejiang开发', '#0600C8')
    message.log(order_show, color='#0600C8')
    message.log(regs_show, color='#FFA500')
    message.log(fun_show, color='purple')


def signed_to_unsigned_dec(signed_num, bits=16):  # 有符号十进制有符号数转二进制再转无符号十进制
    # 取mask，N位的掩码
    mask = (1 << bits) - 1
    # 计算补码，再直接按无符号取值
    unsigned_val = signed_num & mask
    return unsigned_val


def jump_addr(text: list) -> dict:  # 跳转地址计算函数
    addr = {}
    count = 0
    line = 1
    for i in text:
        if re.match(pattern_addr, i) != None:  # 跳转地址标签
            if re.match(pattern_addr, i).group(1) in addr:  # 若已经出现过了，则出现了地址二义性的问题
                logplace.safe_error(f'出现多个相同的跳转地址{i}出现在第{line}行')
            else:  # 记录跳转地址
                addr[re.match(pattern_addr, i).group(1)] = count
        elif re.match(pattern_express, i) != None:
            continue  # 注释忽略
        else:  # 其他指令地址加1
            count += 1
        line += 1  # 行数加1
    return addr


def reg_check(*arg, line: int) -> bool:  # 寄存器校验函数
    for i in arg:
        if i not in regs:
            logplace.safe_error(f'第{line}行出现未知寄存器{i}')
            return False
    return True


def file_save():  # 文件保存函数
    if not filepath:  # 没选过源文件就保存会写到空路径上，先拦一下
        logplace.safe_warn('尚未选择源文件，无法保存')
        return
    text = workplace.get_all_text().split('\n')
    err = safe_write_text(filepath, '\n'.join(text))  # 使用join将列表元素之间使用'\n'隔开，最后一个元素不追加'\n'
    if err:
        logplace.safe_error(f'保存失败：{err}')
    else:
        logplace.safe_info('文件保存成功')


def save_and_compile():  # 文件保存并编译函数
    logplace.clear()  # 先清除一下日志区域
    text = workplace.get_all_text().split('\n')  # 列表类型,将工作区的字符串打包成列表
    asm_create = FileSelect(volumn1.left, '这是一个隐藏文件选择框')  # 创建一个隐藏的文件选择框，他在触发前不可见
    line = 1  # 代码行数
    addr = 0  # MIF文件地址

    pattern_lb = r"\w+\s+(LOW|HIGH)\s+(\d+|-\d+|\d+U|\d+u|@\w+)\s+(\w+)"  # 半字加载指令格式
    pattern_i = r"\w+\s+(\d+|-\d+)\s+(\w+)\s+(\w+)"  # 立即数指令格式
    pattern_r = r"\w+\s+(\w+)\s+(\w+)\s+(\w+)"  # 寄存器型指令格式
    pattern_sfr = r"\w+\s+(\w+)\s+(\w+)"  # 跳转指令格式
    pattern_jal = r"\w+\s+(@\w+)\s+(\w+)"
    pattern_io = r"\w+\s+(\w+)\s+(\w+)"  # IO指令格式
    pattern_md = r"\w+\s+(\w+)\s+(\w+)\s+(\w+)+\s+(\w+)"  # 乘除法指令格式
    pattern_jalr = r"\w+\s+(\w+)"  #

    asm = []  # 最后将写入MIF的数据
    addr_list = jump_addr(text)  # 跳转地址载入
    print(addr_list)
    for i in text:  # 遍历每一行
        match = re.match(pattern_order, i)  # 匹配指令是否存在
        if match == None:
            if i[0] in [';', '；', '@', '\n']:
                line += 1
                continue  # 若为注释或地址标签则继续
            else:
                logplace.safe_error(f'第{line}行出现未定义指令:{i}')
                return
        elif match.group(1) == 'LB':  # 半字加载指令
            mess = re.match(pattern_lb, i)

            if mess == None:
                logplace.safe_error(f'第{line}行出现指令格式错误')
                return
            if mess.group(1) not in ['LOW', 'HIGH']:  # 检验格式
                logplace.safe_error(f'第{line}行出现指令格式错误:{mess.group(1)}')
                return
            if reg_check(mess.group(3), line=line) == False:  # 检查寄存器
                return
            r1 = regs[mess.group(3)]
            try:  # 尝试转换数据格式
                if '@' in mess.group(2):  # 若为地址标签
                    if mess.group(2) in addr_list:
                        num = addr_list[mess.group(2)]
                    else:
                        logplace.safe_error(f'第{line}行出现未定义的地址标签:{mess.group(2)}')
                        return
                else:  # 先按有符号数转换试试
                    num = signed_to_unsigned_dec(int(mess.group(2)))
            except ValueError:
                try:  # 当成无符号数转换一下试试
                    num = int(mess.group(2).strip('uU'))
                except ValueError:
                    logplace.safe_error(f'第{line}行出现数值格式错误:{mess.group(2)}')
                    return
            except Exception as e:
                logplace.safe_error(f'第{line}行出现未知错误:{e}')
                return
            # print(num)
            if num > 65536:
                logplace.warn(f'第{line}行的立即数:{num}超过65536,超出部分将截断')
            if mess.group(1) == 'LOW':  # 数据分段
                num = num % 256
                load_sign = 0
            else:
                num = (num // 256) % 256
                load_sign = 1
            asm.append(f'{addr} :  {(orders[match.group(1)] << 18) + (num << 8) + (load_sign << 4) + r1};')
            addr += 1
        else:  # 其余指令解析方式
            if match.group(1) in ['ADDI', 'SLTI', 'SLLI', 'SRLI', 'XORI', 'ORI', 'ANDI', 'SRAI']:
                # 立即数指令
                mess = re.match(pattern_i, i)
                if mess == None:
                    logplace.safe_error(f'第{line}行出现指令格式错误')
                    return
                try:
                    num = signed_to_unsigned_dec(int(mess.group(1)))
                except ValueError:
                    logplace.safe_error(f'第{line}行出现数据错误，应当输入有符号数')
                except Exception as e:
                    logplace.safe_error(f'第{line}行出现未知错误:{e}')
                    return
                if num > 511 and int(mess.group(1)) > 0:
                    logplace.warn(f'第{line}行数据超出+511将截断')
                    num = num % 1024
                elif num > 1023:
                    num = num % 1024
                if reg_check(mess.group(2), mess.group(3), line=line) == False:
                    return
                r1 = regs[mess.group(2)]
                r2 = regs[mess.group(3)]
                asm.append(f'{addr} :  {(orders[match.group(1)] << 18) + (num << 8) + (r1 << 4) + r2};')
            elif match.group(1) == 'NOP':
                asm.append(f'{addr} :  {orders[match.group(1)] << 18};')
            elif match.group(1) in ['ADD', 'SUB', 'AND', 'OR', 'XOR', 'SLL', 'SRL', 'BEQ', 'BNE', 'BLT', 'BGE',
                                    'BLTU', 'BGEU', 'SRA', 'SRL','SLA']:
                # 三操作数指令
                mess = re.match(pattern_r, i)
                if reg_check(mess.group(1), mess.group(2), mess.group(3), line=line) == False:
                    return
                r1 = regs[mess.group(1)]
                r2 = regs[mess.group(2)]
                r3 = regs[mess.group(3)]
                asm.append(f'{addr} :  {(orders[match.group(1)] << 18) + (r2 << 8) + (r1 << 4) + r3};')
            elif match.group(1) == 'JAL':
                # 小偏移跳转
                mess = re.match(pattern_jal, i)
                print(mess)
                print(mess.group(0))
                if reg_check(mess.group(2), line=line) == False:
                    return
                r1 = regs[mess.group(2)]
                if mess.group(1) not in addr_list:
                    logplace.safe_error(f'第{line}行出现未知地址{mess.group(1)}')
                    return
                addr_num = addr_list[mess.group(1)]
                if addr_num > 16383:
                    logplace.safe_error(f'第{line}行地址超过16383，发生了截断')
                    return
                '''JAL偏移地址计算'''
                addr_num = signed_to_unsigned_dec(addr_num - addr) % 16384  # 计算偏移地址
                asm.append(f'{addr} :  {(orders[match.group(1)] << 18) + (addr_num << 4) + r1};')
            elif match.group(1) == 'JALR':
                '''JALR绝对地址跳转'''
                mess = re.match(pattern_jalr, i)
                if reg_check(mess.group(1), line=line) == False:
                    return
                r1 = regs[mess.group(1)]
                asm.append(f'{addr} :  {(orders[match.group(1)] << 18) + (r1 << 4)};')
            elif match.group(1) in ['LSR', 'ESR']:  # 特殊寄存器组相关指令
                mess = re.match(pattern_sfr, i)
                if reg_check(mess.group(2), line=line) == False:
                    return
                r2 = regs[mess.group(2)]
                try:
                    addr_num = int(mess.group(1))
                except ValueError:
                    addr_num = int(mess.group(1).strip('uU'))
                except Exception as e:
                    logplace.safe_error(f'第{line}行出现未知错误:{e}')
                    return
                if addr_num > 1024:
                    logplace.safe_error(f'第{line}行地址超长，发生了截断')
                    return
                if match.group(1) == 'LSR':
                    asm.append(f'{addr} :  {(orders[match.group(1)] << 18) + (addr_num << 8) + (r2 << 4)};')
                else:
                    asm.append(f'{addr} :  {(orders[match.group(1)] << 18) + (addr_num << 8) + r2};')
            elif match.group(1) in ['IN', 'OUT']:
                mess = re.match(pattern_io, i)
                if reg_check(mess.group(1), mess.group(2), line=line) == False:
                    return
                r1 = regs[mess.group(1)]
                r2 = regs[mess.group(2)]
                if match.group(1) == 'IN':
                    asm.append(f'{addr} :  {(orders[match.group(1)] << 18) + (r1 << 8) + r2};')
                else:
                    asm.append(f'{addr} :  {(orders[match.group(1)] << 18) + (r1 << 8) + (r2 << 4)};')
            elif match.group(1) in ['MUL', 'DIV']:
                mess = re.match(pattern_md, i)
                if reg_check(mess.group(1), mess.group(2), mess.group(3), mess.group(4), line=line) == False:
                    return
                r1 = regs[mess.group(1)]
                r2 = regs[mess.group(2)]
                r3 = regs[mess.group(3)]
                r4 = regs[mess.group(4)]
                asm.append(f'{addr} :  {(orders[match.group(1)] << 18) + (r1 << 12) + (r3 << 8) + (r2 << 4) + r4};')

            addr += 1
        line += 1  # 行加1

    asm_file = asm_create.ask_file(auto_create=True)
    if not asm_file:  # 用户取消了保存对话框
        logplace.warn('未选择输出文件，编译结果未保存')
        return
    asm.insert(0, 'CONTENT BEGIN')
    asm.insert(0, '\n')
    asm.insert(0, 'DATA_RADIX=UNS;')
    asm.insert(0, 'ADDRESS_RADIX=UNS;')
    asm.insert(0, '\n')
    asm.insert(0, f'DEPTH={mech_rom[1]};')
    asm.insert(0, f'WIDTH={mech_rom[0]};')
    if addr < mech_rom[1] - 1:  # 剩余空间赋0
        asm.append(f'[{addr}..{mech_rom[1] - 1}]  :   0;')
    elif addr > mech_rom[0] - 1:
        logplace.safe_error('程序大小超限')
        return
    asm.append('END;')
    err = safe_write_text(asm_file, '\n'.join(asm))  # 先写临时文件、写完整了再替换，不会留下空文件
    if err:
        logplace.safe_error(f'写入输出文件失败：{err}')
        return
    logplace.safe_info(f'编译完成，共占用{addr * 3}个字节')  # addr 结束时正是总字节数
    logplace.safe_info(f'跳转地址：{addr_list}')
    if filepath:  # 只有确实选过源文件才回写源码，否则不打扰用户
        file_save()


def get_filepath(path: str):  # 获取文件路径
    global filepath, window, logplace
    filepath = path
    # print(filepath)#文件路径调试
    if filepath[-4:] != '.txt':  # 文件类型检测
        logplace.safe_error('文件类型不是.txt文件')
    else:
        logplace.safe_info('文件打开成功')
    workplace.clear()  # 先清除工作区文本内容
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read().split('\n')
        for i in text:
            workplace.pstr(i)


save_but = MyButton(volumn1.left, '保存', on_click=file_save)
sav_comp_bt = MyButton(volumn1.left, '编译并保存', on_click=save_and_compile)


def main():
    '''窗口初始化'''
    window.add(volumn1)  # 添加窗口
    volumn1.right.add(volumn2)  # 添加到右容器
    volumn2.top.add(workplace)  # 添加到右容器的上容器
    volumn2.bottom.add(logplace)  # 添加到右容器的下容器
    volumn1.left.add(fileselect)  # 添加到左右容器的左侧
    fileselect.on_select = get_filepath  # 设置文件路径获取回调函数
    volumn1.left.add(save_but)  # 添加到左右容器的左侧
    volumn1.left.add(sav_comp_bt)  # 添加到左右容器的左侧
    volumn1.left.add(message)  # 添加说明栏
    logplace.set_level_color('info', '#0600C8')  # 日志设为蓝色
    logplace.set_level_color('warn', '#FFA500')  # 警告设为黄色
    logplace.set_level_color('error', '#EE0000')  # 错误设为红色
    workplace.on_save = file_save  # 绑定文件保存回调函数
    workplace.add_highlight(pattern_order, color='#0600C8', name='指令高亮')
    workplace.add_highlight(pattern_regs, color='#FFA500', name='寄存器名称高亮')
    workplace.add_highlight(pattern_addr, color='green', name='跳转地址高亮')
    workplace.add_highlight(pattern_num, color='red', name='立即数高亮')
    workplace.add_highlight(pattern_fun, color='purple', name='系统函数高亮')
    workplace.add_highlight(pattern_express, color='gray', name='注释高亮')
    mess_show()  # 写信息栏
    window.mainloop()  # 启动窗口


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(e)
        try:
            logplace.safe_error(f'发生异常：{type(e).__name__}: {e}')
        except Exception:
            pass