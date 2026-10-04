# RISC-V 非特权指令集完整清单

> 本文档逐条罗列 RISC-V 非特权架构规范（Volume I: Unprivileged Architecture）中定义的全部指令。
> 全部内容由 PDF 原文机器抽取并交叉校验，非凭记忆整理。

| 项目 | 内容 |
| --- | --- |
| 源文件 | `riscv-unprivileged.pdf` |
| 规范全名 | The RISC-V Instruction Set Manual, Volume I: Unprivileged Architecture |
| 版本 | 20260120: Official Release |
| 篇幅 | 696页（PDF页号），37章 |
| 抽取方式 | `pypdf` 逐页抽取为纯文本，再按规则解析指令清单 |

---

## 一、阅读口径（重要）

### 1.1 "一条指令"怎么算

RISC-V 的指令数量取决于口径。本文档统一按**助记符去重**计数，并遵守以下规则：

| 情形 | 计法 | 例子 |
| --- | --- | --- |
| 后缀变体 | **算不同指令** | `vaesdf.vv` 与 `vaesdf.vs` 是两条 |
| 位宽变体 | **算不同指令** | `LR.W` 与 `LR.D` 是两条，`FCVT.L.S` 与 `FCVT.W.S` 是两条 |
| 汇编伪指令 | **单独成表，不计入** | `ret`、`call`、`nop`、`li`、`mv` |
| 通配模板 | **按模板列出，不展开** | `vlseg<nf>e<eew>.v` 见下节 |
| 复用编码不新增名 | **不重复计数** | Zfinx 复用 F 的助记符，故新增 0 条 |

### 1.2 通配模板：段访存与编码空间

规范对**向量段访存**不逐条枚举，而是给出模板：

```
vlseg<nf>e<eew>.v vd, (rs1), vm    # 单位步长段加载模板
```

其中 `<nf>` 取 2~8（段内字段数），`<eew>` 取 8/16/32/64（元素宽度）。若完全展开，仅单位步长段加载就有 7×4=28 条，再乘以（存储/常量步长/索引有序/索引无序/首错即停）等变体，可膨胀到数千条。

同理，`mop.r.n`、`mop.rr.n`、`c.mop.n` 也用编码序号 n 表示一族指令。

**本文档按模板列出**，不人为展开——展开后的具体条数取决于实现选择的 nf/eew 组合，规范本身不做规定。

### 1.3 关于编码字段

核心整数指令集（第36章）的编码直接取自规范清单表，"编码字段"列即规范给出的字段布局，例如：

```
imm[12|10:5] rs2 rs1 000 imm[4:1|11] 1100011     ← BEQ
```

表示：立即数按 12|10:5 与 4:1|11 两段拼接，`rs2`/`rs1`/`000`/`rd` 依次排列，末 7 位操作码 `1100011`。带点的浮点/向量指令不在第36章清单中，故其编码列标为 —，请按规范正文对应章节查阅。

### 1.4 页号约定

所有"页"列均为**PDF页号**。规范文档自身的页脚页码比PDF页号小19（例如PDF第604页，页脚标"Page 585"），引用时请注意换算。

---

## 二、指令总览索引

| 章节 | 内容 | 条数 |
| --- | --- | --- |
| 三 | RV32I / RV64I / RV32E / RV64E 基础整数 | 见各表 |
| 四 | Zicsr / Zifencei / Zicntr | 见各表 |
| 五 | M / A / Zawrs（第36章清单） | 见各表 |
| 六 | F / D / Q / Zfh / BF16 / Zfa / Zfinx | 见各表 |
| 七 | C / Zc\* / Zilsd / Zclsd | 见各表 |
| 八 | 位操作 Zba / Zbb / Zbs / Zbc / Zbkb / Zbkc / Zbkx | 见各表 |
| 九 | Zicond / Zimop / Zcmop / Zihint\* / CMO / Ztso | 见各表 |
| 十 | V 向量扩展 | 见各表 |
| 十一 | 密码学标量（Zk\*） | 见各表 |
| 十二 | 密码学向量（Zvk\*） | 见各表 |
| 十三 | 控制流完整性 Zicfilp / Zicfiss | 见各表 |
| 十四 | 汇编伪指令总表 | 见各表 |
| 十五 | 统计与结论 | — |

---

## 三、基础整数指令集（RV32I / RV64I / RV32E / RV64E）

> 编码字段取自规范第36章权威清单（PDF第604页起）。

### 3.1 RV32I 基础整数指令集（40条）

规范自述："RV32I contains 40 unique instructions"（原文第1739行）。下表列出42行——其中 `FENCE.TSO` 属 Ztso、`PAUSE` 属 Zihintpause，因与 RV32I 共用编码空间而被规范一并排在同一张表内，故基础集本身是40条。

### RV32I Base Instruction Set

（规范PDF第604页起，共42条）

| 助记符 | 编码字段 | 说明 |
| --- | --- | --- |
| `LUI` | `imm[31:12] rd 0110111` | 把20位立即数装入rd高20位，低12位清0 |
| `AUIPC` | `imm[31:12] rd 0010111` | 把20位立即数加到PC高位，结果写rd |
| `JAL` | `imm[20\|10:1\|11\|19:12] rd 1101111` | 跳转并链接：rd←PC+4，PC←PC+偏移（rd=x0即无条件跳转） |
| `JALR` | `imm[11:0] rs1 000 rd 1100111` | 间接跳转并链接：rd←PC+4，PC←(rs1+偏移)&~1（rd=x0,rs1=x1即ret） |
| `BEQ` | `imm[12\|10:5] rs2 rs1 000 imm[4:1\|11] 1100011` | rs1==rs2则跳转（PC相对） |
| `BNE` | `imm[12\|10:5] rs2 rs1 001 imm[4:1\|11] 1100011` | rs1!=rs2则跳转 |
| `BLT` | `imm[12\|10:5] rs2 rs1 100 imm[4:1\|11] 1100011` | 有符号rs1<rs2则跳转 |
| `BGE` | `imm[12\|10:5] rs2 rs1 101 imm[4:1\|11] 1100011` | 有符号rs1>=rs2则跳转 |
| `BLTU` | `imm[12\|10:5] rs2 rs1 110 imm[4:1\|11] 1100011` | 无符号rs1<rs2则跳转 |
| `BGEU` | `imm[12\|10:5] rs2 rs1 111 imm[4:1\|11] 1100011` | 无符号rs1>=rs2则跳转 |
| `LB` | `imm[11:0] rs1 000 rd 0000011` | 加载字节并符号扩展 |
| `LH` | `imm[11:0] rs1 001 rd 0000011` | 加载半字并符号扩展 |
| `LW` | `imm[11:0] rs1 010 rd 0000011` | 加载32位字 |
| `LBU` | `imm[11:0] rs1 100 rd 0000011` | 加载字节并零扩展 |
| `LHU` | `imm[11:0] rs1 101 rd 0000011` | 加载半字并零扩展 |
| `SB` | `imm[11:5] rs2 rs1 000 imm[4:0] 0100011` | 存储字节（取rs2低8位） |
| `SH` | `imm[11:5] rs2 rs1 001 imm[4:0] 0100011` | 存储半字（取rs2低16位） |
| `SW` | `imm[11:5] rs2 rs1 010 imm[4:0] 0100011` | 存储32位字 |
| `ADDI` | `imm[11:0] rs1 000 rd 0010011` | rd←rs1+符号扩展立即数 |
| `SLTI` | `imm[11:0] rs1 010 rd 0010011` | rd←(rs1<有符号立即数)?1:0 |
| `SLTIU` | `imm[11:0] rs1 011 rd 0010011` | rd←(rs1<无符号立即数)?1:0（立即数先符号扩展再作无符号比较） |
| `XORI` | `imm[11:0] rs1 100 rd 0010011` | rd←rs1^立即数 |
| `ORI` | `imm[11:0] rs1 110 rd 0010011` | rd←rs1\|立即数 |
| `ANDI` | `imm[11:0] rs1 111 rd 0010011` | rd←rs1&立即数 |
| `SLLI` | `0000000 shamt rs1 001 rd 0010011` | 逻辑左移，移位量取立即数 |
| `SRLI` | `0000000 shamt rs1 101 rd 0010011` | 逻辑右移，移位量取立即数 |
| `SRAI` | `0100000 shamt rs1 101 rd 0010011` | 算术右移，移位量取立即数 |
| `ADD` | `0000000 rs2 rs1 000 rd 0110011` | rd←rs1+rs2 |
| `SUB` | `0100000 rs2 rs1 000 rd 0110011` | rd←rs1-rs2 |
| `SLL` | `0000000 rs2 rs1 001 rd 0110011` | 逻辑左移，移位量取rs2低5位 |
| `SLT` | `0000000 rs2 rs1 010 rd 0110011` | rd←(rs1<rs2)?1:0，有符号 |
| `SLTU` | `0000000 rs2 rs1 011 rd 0110011` | rd←(rs1<rs2)?1:0，无符号 |
| `XOR` | `0000000 rs2 rs1 100 rd 0110011` | rd←rs1^rs2 |
| `SRL` | `0000000 rs2 rs1 101 rd 0110011` | 逻辑右移，移位量取rs2低5位 |
| `SRA` | `0100000 rs2 rs1 101 rd 0110011` | 算术右移，移位量取rs2低5位 |
| `OR` | `0000000 rs2 rs1 110 rd 0110011` | rd←rs1\|rs2 |
| `AND` | `0000000 rs2 rs1 111 rd 0110011` | rd←rs1&rs2 |
| `FENCE` | `fm pred succ rs1 000 rd 0001111` | 内存与IO顺序屏障，fm/pred/succ指定前后可重排的访问类型 |
| `FENCE.TSO` | `1000 0011 0011 00000 000 00000 0001111` | FENCE的预定义编码，等价于全序的TSO语义屏障（属Ztso） |
| `PAUSE` | `0000 0001 0000 00000 000 00000 0001111` | FENCE的预定义编码，提示处理器进入低功耗自旋等待（属Zihintpause） |
| `ECALL` | `000000000000 00000 000 00000 1110011` | 环境调用：向执行环境请求服务（系统调用） |
| `EBREAK` | `000000000001 00000 000 00000 1110011` | 断点：把控制权交给调试环境 |

### 3.2 RV64I 基础整数指令集（在RV32I基础上新增12条）

下表15行中含 `SLLI`/`SRLI`/`SRAI` 三条——它们在RV64下只是移位量字段变宽，并非新指令，故RV64I实际新增12条。

### RV64I Base Instruction Set (in addition to RV32I)

（规范PDF第606页起，共15条）

| 助记符 | 编码字段 | 说明 |
| --- | --- | --- |
| `LWU` | `imm[11:0] rs1 110 rd 0000011` | 加载32位字并零扩展到64位 |
| `LD` | `imm[11:0] rs1 011 rd 0000011` | 加载64位双字 |
| `SD` | `imm[11:5] rs2 rs1 011 imm[4:0] 0100011` | 存储64位双字 |
| `SLLI` | `000000 shamt rs1 001 rd 0010011` | 逻辑左移，移位量取立即数 |
| `SRLI` | `000000 shamt rs1 101 rd 0010011` | 逻辑右移，移位量取立即数 |
| `SRAI` | `010000 shamt rs1 101 rd 0010011` | 算术右移，移位量取立即数 |
| `ADDIW` | `imm[11:0] rs1 000 rd 0011011` | rd←符号扩展32位(rs1+立即数) |
| `SLLIW` | `0000000 shamt rs1 001 rd 0011011` | 32位逻辑左移，结果符号扩展到64位 |
| `SRLIW` | `0000000 shamt rs1 101 rd 0011011` | 32位逻辑右移，结果符号扩展到64位 |
| `SRAIW` | `0100000 shamt rs1 101 rd 0011011` | 32位算术右移，结果符号扩展到64位 |
| `ADDW` | `0000000 rs2 rs1 000 rd 0111011` | 32位加法，结果符号扩展到64位 |
| `SUBW` | `0100000 rs2 rs1 000 rd 0111011` | 32位减法，结果符号扩展到64位 |
| `SLLW` | `0000000 rs2 rs1 001 rd 0111011` | 32位逻辑左移，结果符号扩展到64位 |
| `SRLW` | `0000000 rs2 rs1 101 rd 0111011` | 32位逻辑右移，结果符号扩展到64位 |
| `SRAW` | `0100000 rs2 rs1 101 rd 0111011` | 32位算术右移，结果符号扩展到64位 |

### 3.3 RV32E / RV64E（嵌入式基础集）

**新增指令：0 条。** 文本：“RV32E and RV64E are reduced versions of RV32I and RV64I, respectively: the only change is to reduce the number of integer registers to 16”（2501–2502）；“RV32E and RV64E use the same instruction-set encoding as RV32I and RV64I respectively, except that only registers x0-x15 are provided. All encodings specifying the other registers x16-x31 are reserved.”（2518–2519）。

**关于 Zicsr：** 本版文本第 2498–2526 行**没有**任何“移除 CSR 类指令/Zicsr”的表述,该章内不出现 CSR、Zicsr、counter 等词（全文检索确认）。它只说明寄存器数减到 16、x16–x31 编码保留（2521–2523 说明旧版草稿曾把这些编码列为 custom,本版改为 reserved）。故按本版文本：RV32E/RV64E 既不新增指令,也未声明删除 Zicsr。

### 3.4 RV32I 的附加项（HINT与别名，不计入40条）

| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| NOP | NOP | 不改变体系结构状态,规范编码为 ADDI x0, x0, 0 | 2036–2041 |
| FENCE.TSO | FENCE.TSO | fm=1000、前驱=RW、后继=RW 的 FENCE 变体 | 2328 |
| PAUSE | PAUSE | FENCE 提示:pred=W、succ=0、fm=0、rd=x0、rs1=x0 | 2473（编码见 3271） |
| NTL.P1 | 无（编码为 ADD x0, x0, x2） | 目标指令无最内层私有 cache 时间局部性 | 2444 |
| NTL.PALL | 无（编码为 ADD x0, x0, x3） | 目标指令无任何私有 cache 级时间局部性 | 2445 |
| NTL.S1 | 无（编码为 ADD x0, x0, x4） | 目标指令无最内层共享 cache 时间局部性 | 2446 |
| NTL.ALL | 无（编码为 ADD x0, x0, x5） | 目标指令无任何 cache 级时间局部性 | 2447 |
| slli x0, x0, 0x1f | slli x0, x0, 0x1f | 半主机（semihosting）入口标记 HINT | 2448 |
| srai x0, x0, 7 | srai x0, x0, 7 | 半主机出口标记 HINT | 2449 |

第 2 章出现的伪指令/别名：MV（1970）、SEQZ（1976）、NOT（1979）、SNEZ（2032）、J（2074）、JR（2082）、RET（2083）；另提到 BGT/BGTU/BLE/BLEU 可由反转操作数的 BLT/BLTU/BGE/BGEU 合成（2151）。

## 四、控制状态寄存器与计数器（Zicsr / Zifencei / Zicntr / Zihpm）

### RV32/RV64 Zicsr Standard Extension

（规范PDF第606页起，共6条）

| 助记符 | 编码字段 | 说明 |
| --- | --- | --- |
| `CSRRW` | `csr rs1 001 rd 1110011` | 原子交换：rd←CSR，CSR←rs1 |
| `CSRRS` | `csr rs1 010 rd 1110011` | 原子置位：rd←CSR，CSR←CSR\|rs1 |
| `CSRRC` | `csr rs1 011 rd 1110011` | 原子清位：rd←CSR，CSR←CSR&~rs1 |
| `CSRRWI` | `csr uimm 101 rd 1110011` | 立即数版CSRRW（rs1字段改放5位零扩展立即数，不读寄存器） |
| `CSRRSI` | `csr uimm 110 rd 1110011` | 立即数版CSRRS |
| `CSRRCI` | `csr uimm 111 rd 1110011` | 立即数版CSRRC |

### RV32/RV64 Zifencei Standard Extension

（规范PDF第606页起，共1条）

| 助记符 | 编码字段 | 说明 |
| --- | --- | --- |
| `FENCE.I` | `imm[11:0] rs1 001 rd 0001111` | 指令流屏障：保证先前写入的指令对后续取指可见 |

**真指令：0 条。** 本章只定义 CSR 与**伪指令**：
| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| RDCYCLE | RDCYCLE rd | 读 cycle CSR 低 XLEN 位（伪指令） | 2988, 3003 |
| RDCYCLEH | RDCYCLEH rd | 读 cycle 的 63-32 位,仅 XLEN=32（伪指令） | 2995–2996, 3005 |
| RDTIME | RDTIME rd | 读 time CSR 低 XLEN 位（伪指令） | 2988, 3047 |
| RDTIMEH | RDTIMEH rd | 读 time 的 63-32 位,仅 XLEN=32（伪指令） | 2995–2996, 3048 |
| RDINSTRET | RDINSTRET rd | 读 instret CSR 低 XLEN 位（伪指令） | 2988, 3080 |
| RDINSTRETH | RDINSTRETH rd | 读 instret 的 63-32 位,仅 XLEN=32（伪指令） | 2995–2996, 3081 |

文本明确：“the RDCYCLE, RDTIME, and RDINSTRET **pseudoinstructions**”（2988、2995）、“The counter pseudoinstructions are mapped to the read-only `csrrs rd, counter, x0` canonical form”（2991）。**故 RDCYCLE/RDTIME/RDINSTRET 系列不是指令,而是 Zicsr 指令 csrrs 的伪指令别名**；本章不定义任何新指令。
CSR 名（非指令）：cycle、time、instret（2969）、hpmcounter3–hpmcounter31（3095–3096）、hpmcounter3h–hpmcounter31h（3097）。**小计：0 条指令 + 6 条伪指令 + CSR 名。**

> 第18章（RVWMO内存一致性模型）与第19章（Ztso）不定义任何新助记符：Ztso 的全部内容就是 `FENCE.TSO` 这一条预定义编码，已列在上文RV32I表中。

## 五、整数乘除、原子与等待指令（M / A / Zacas / Zabha / Zalasr / Zawrs）

### 5.1 M 扩展（整数乘除，13条）

### RV32M Standard Extension

（规范PDF第606页起，共8条）

| 助记符 | 编码字段 | 说明 |
| --- | --- | --- |
| `MUL` | `0000001 rs2 rs1 000 rd 0110011` | 取乘积低XLEN位（有符号×有符号） |
| `MULH` | `0000001 rs2 rs1 001 rd 0110011` | 取乘积高XLEN位（有符号×有符号） |
| `MULHSU` | `0000001 rs2 rs1 010 rd 0110011` | 取乘积高XLEN位（有符号×无符号） |
| `MULHU` | `0000001 rs2 rs1 011 rd 0110011` | 取乘积高XLEN位（无符号×无符号） |
| `DIV` | `0000001 rs2 rs1 100 rd 0110011` | 有符号除法，除零得-1，溢出(最小负数/-1)得最小负数 |
| `DIVU` | `0000001 rs2 rs1 101 rd 0110011` | 无符号除法，除零得全1 |
| `REM` | `0000001 rs2 rs1 110 rd 0110011` | 有符号取余，余数符号与被除数相同；除零得被除数 |
| `REMU` | `0000001 rs2 rs1 111 rd 0110011` | 无符号取余 |

### RV64M Standard Extension (in addition to RV32M)

（规范PDF第607页起，共5条）

| 助记符 | 编码字段 | 说明 |
| --- | --- | --- |
| `MULW` | `0000001 rs2 rs1 000 rd 0111011` | 32位乘法取低32位，结果符号扩展（RV64） |
| `DIVW` | `0000001 rs2 rs1 100 rd 0111011` | 32位有符号除法，结果符号扩展（RV64） |
| `DIVUW` | `0000001 rs2 rs1 101 rd 0111011` | 32位无符号除法，结果符号扩展（RV64） |
| `REMW` | `0000001 rs2 rs1 110 rd 0111011` | 32位有符号取余，结果符号扩展（RV64） |
| `REMUW` | `0000001 rs2 rs1 111 rd 0111011` | 32位无符号取余，结果符号扩展（RV64） |

### 5.2 A 扩展（原子指令，22条）

> 本版规范把 A 扩展拆成两个子扩展命名：**Zalrsc**（LR/SC 共4条）与 **Zaamo**（AMO 共18条），合称 A。同理 M 的乘法子集命名为 **Zmmul**（`MUL`/`MULH`/`MULHU`/`MULHSU` 及 RV64 的 `MULW`，编码与 M 相同）。

### RV32A Standard Extension

（规范PDF第608页起，共11条）

| 助记符 | 编码字段 | 说明 |
| --- | --- | --- |
| `LR.W` | `00010 aq rl 00000 rs1 010 rd 0101111` | 加载保留：读32位并登记保留集（rs2须为x0） |
| `SC.W` | `00011 aq rl rs2 rs1 010 rd 0101111` | 条件存储：保留集有效则写入并回0，否则不写并回非0 |
| `AMOSWAP.W` | `00001 aq rl rs2 rs1 010 rd 0101111` | 原子交换32位 |
| `AMOADD.W` | `00000 aq rl rs2 rs1 010 rd 0101111` | 原子加32位 |
| `AMOXOR.W` | `00100 aq rl rs2 rs1 010 rd 0101111` | 原子异或32位 |
| `AMOAND.W` | `01100 aq rl rs2 rs1 010 rd 0101111` | 原子与32位 |
| `AMOOR.W` | `01000 aq rl rs2 rs1 010 rd 0101111` | 原子或32位 |
| `AMOMIN.W` | `10000 aq rl rs2 rs1 010 rd 0101111` | 原子取最小值（有符号） |
| `AMOMAX.W` | `10100 aq rl rs2 rs1 010 rd 0101111` | 原子取最大值（有符号） |
| `AMOMINU.W` | `11000 aq rl rs2 rs1 010 rd 0101111` | 原子取最小值（无符号） |
| `AMOMAXU.W` | `11100 aq rl rs2 rs1 010 rd 0101111` | 原子取最大值（无符号） |

### RV64A Standard Extension (in addition to RV32A)

（规范PDF第608页起，共11条）

| 助记符 | 编码字段 | 说明 |
| --- | --- | --- |
| `LR.D` | `00010 aq rl 00000 rs1 011 rd 0101111` | 加载保留64位（RV64） |
| `SC.D` | `00011 aq rl rs2 rs1 011 rd 0101111` | 条件存储64位（RV64） |
| `AMOSWAP.D` | `00001 aq rl rs2 rs1 011 rd 0101111` | 原子交换64位（RV64） |
| `AMOADD.D` | `00000 aq rl rs2 rs1 011 rd 0101111` | 原子加64位（RV64） |
| `AMOXOR.D` | `00100 aq rl rs2 rs1 011 rd 0101111` | 原子异或64位（RV64） |
| `AMOAND.D` | `01100 aq rl rs2 rs1 011 rd 0101111` | 原子与64位（RV64） |
| `AMOOR.D` | `01000 aq rl rs2 rs1 011 rd 0101111` | 原子或64位（RV64） |
| `AMOMIN.D` | `10000 aq rl rs2 rs1 011 rd 0101111` | 原子取最小值（有符号，64位） |
| `AMOMAX.D` | `10100 aq rl rs2 rs1 011 rd 0101111` | 原子取最大值（有符号，64位） |
| `AMOMINU.D` | `11000 aq rl rs2 rs1 011 rd 0101111` | 原子取最小值（无符号，64位） |
| `AMOMAXU.D` | `11100 aq rl rs2 rs1 011 rd 0101111` | 原子取最大值（无符号，64位） |

### 5.3 Zacas

| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| AMOCAS.W | AMOCAS.W rd, rs2, (rs1) | 原子 32 位比较并交换 | 4001–4002 |
| AMOCAS.D | AMOCAS.D rd, rs2, (rs1) | 原子 64 位比较并交换（RV32 用寄存器对 rd/rd+1、rs2/rs2+1） | 4001, 4010–4011 |
| AMOCAS.Q | AMOCAS.Q rd, rs2, (rs1) | 原子 128 位比较并交换,仅 RV64 | 4001, 4052 |

可带 aq/rl,示例 `amocas.d.aqrl`（4097）、`amocas.q.aqrl`（4149、4153、4157）。**小计：3 条。**

### 5.4 Zabha

| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| AMOSWAP.B/H | AMOSWAP.{B,H} rd, rs2, (rs1) | 原子交换字节/半字 | 4196 |
| AMOADD.B/H | AMOADD.{B,H} rd, rs2, (rs1) | 原子加字节/半字 | 4196 |
| AMOAND.B/H | AMOAND.{B,H} rd, rs2, (rs1) | 原子与字节/半字 | 4196 |
| AMOOR.B/H | AMOOR.{B,H} rd, rs2, (rs1) | 原子或字节/半字 | 4196 |
| AMOXOR.B/H | AMOXOR.{B,H} rd, rs2, (rs1) | 原子异或字节/半字 | 4196 |
| AMOMAX[U].B/H | AMOMAX{,U}.{B,H} rd, rs2, (rs1) | 原子有/无符号最大字节/半字 | 4196 |
| AMOMIN[U].B/H | AMOMIN{,U}.{B,H} rd, rs2, (rs1) | 原子有/无符号最小字节/半字 | 4196 |
| AMOCAS.B/H | AMOCAS.{B,H} rd, rs2, (rs1) | 原子比较并交换字节/半字,需同时实现 Zacas | 4186–4187, 4196 |

文本总述：“Zabha extension provides the AMO[ADD|AND|OR|XOR|SWAP|MIN[U]|MAX[U]].[B|H] instructions. If Zacas extension is also implemented, Zabha further provides the AMOCAS.[B|H] instructions.”（4186–4187）。Zabha 不支持字节/半字 LR/SC（4206）。**小计：模板 8 条（展开为 20 条：AMO 9 类×2 宽度 + AMOCAS×2 宽度）。**

### 5.5 Zalasr

| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| lb.{aq,aqrl} | lb.{aq,aqrl} rd, (rs1) | 原子装入字节,带 acquire 排序标注 | 4249 |
| lh.{aq,aqrl} | lh.{aq,aqrl} rd, (rs1) | 原子装入半字 | 4250 |
| lw.{aq,aqrl} | lw.{aq,aqrl} rd, (rs1) | 原子装入字 | 4251 |
| ld.{aq,aqrl} | ld.{aq,aqrl} rd, (rs1) | 原子装入双字,仅 RV64 | 4252, 4264 |
| sb.{rl,aqrl} | sb.{rl,aqrl} rs2, (rs1) | 原子存储字节,带 release 排序标注 | 4280 |
| sh.{rl,aqrl} | sh.{rl,aqrl} rs2, (rs1) | 原子存储半字 | 4281 |
| sw.{rl,aqrl} | sw.{rl,aqrl} rs2, (rs1) | 原子存储字 | 4282 |
| sd.{rl,aqrl} | sd.{rl,aqrl} rs2, (rs1) | 原子存储双字,仅 RV64 | 4283, 4293 |

无 aq 位的 load 形式与无 rl 位的 store 形式为 RESERVED（4264、4293）。**小计：模板 8 条（展开为 16 条）。**

### 5.6 Zawrs

### Zawrs Standard Extension

（规范PDF第615页起，共2条）

| 助记符 | 编码字段 | 说明 |
| --- | --- | --- |
| `WRS.NTO` | `000000001101 00000 000 00000 1110011` | 等待保留集，超时则继续：供自旋锁使用，不超时不下退 |
| `WRS.STO` | `000000011101 00000 000 00000 1110011` | 等待保留集，短超时后继续（允许被外部事件打断） |

## 六、浮点指令集（F / D / Q / Zfh / BF16 / Zfa / Zfinx）

### 6.1 F 扩展（单精度，30条）

### RV32F Standard Extension

（规范PDF第609页起，共26条）

| 助记符 | 编码字段 | 说明 |
| --- | --- | --- |
| `FLW` | `imm[11:0] rs1 010 rd 0000111` | 从内存加载单精度浮点数到浮点寄存器 |
| `FSW` | `imm[11:5] rs2 rs1 010 imm[4:0] 0100111` | 把单精度浮点数存入内存 |
| `FMADD.S` | `rs3 00 rs2 rs1 rm rd 1000011` | 融合乘加：rd←rs1×rs2+rs3（单精度(32位)，单次舍入） |
| `FMSUB.S` | `rs3 00 rs2 rs1 rm rd 1000111` | 融合乘加：rd←rs1×rs2-rs3（单精度(32位)，单次舍入） |
| `FNMSUB.S` | `rs3 00 rs2 rs1 rm rd 1001011` | 融合乘加：rd←-(rs1×rs2)+rs3（单精度(32位)，单次舍入） |
| `FNMADD.S` | `rs3 00 rs2 rs1 rm rd 1001111` | 融合乘加：rd←-(rs1×rs2)-rs3（单精度(32位)，单次舍入） |
| `FADD.S` | `0000000 rs2 rs1 rm rd 1010011` | 单精度(32位)加法 |
| `FSUB.S` | `0000100 rs2 rs1 rm rd 1010011` | 单精度(32位)减法 |
| `FMUL.S` | `0001000 rs2 rs1 rm rd 1010011` | 单精度(32位)乘法 |
| `FDIV.S` | `0001100 rs2 rs1 rm rd 1010011` | 单精度(32位)除法 |
| `FSQRT.S` | `0101100 00000 rs1 rm rd 1010011` | 单精度(32位)平方根 |
| `FSGNJ.S` | `0010000 rs2 rs1 000 rd 1010011` | 符号注入：取rs1数值、取rs2符号（单精度(32位)） |
| `FSGNJN.S` | `0010000 rs2 rs1 001 rd 1010011` | 符号注入：取rs1数值、取rs2符号的反（单精度(32位)） |
| `FSGNJX.S` | `0010000 rs2 rs1 010 rd 1010011` | 符号注入：rs1与rs2符号按异或合成（单精度(32位)） |
| `FMIN.S` | `0010100 rs2 rs1 000 rd 1010011` | 取较小值（单精度(32位)，NaN处理按IEEE-754-2019） |
| `FMAX.S` | `0010100 rs2 rs1 001 rd 1010011` | 取较大值（单精度(32位)） |
| `FCVT.W.S` | `1100000 00000 rs1 rm rd 1010011` | 类型转换：单精度(32位)→32位有符号整数 |
| `FCVT.WU.S` | `1100000 00001 rs1 rm rd 1010011` | 类型转换：单精度(32位)→32位无符号整数 |
| `FMV.X.W` | `1110000 00000 rs1 000 rd 1010011` | 位模式搬运（不转换）：32位有符号整数的位→X |
| `FEQ.S` | `1010000 rs2 rs1 010 rd 1010011` | 相等比较，写整数结果（单精度(32位)，静默版不触发异常） |
| `FLT.S` | `1010000 rs2 rs1 001 rd 1010011` | 小于比较，写整数结果（单精度(32位)，静默版） |
| `FLE.S` | `1010000 rs2 rs1 000 rd 1010011` | 小于等于比较，写整数结果（单精度(32位)，静默版） |
| `FCLASS.S` | `1110000 00000 rs1 001 rd 1010011` | 分类：按10类位图写整数结果（单精度(32位)） |
| `FCVT.S.W` | `1101000 00000 rs1 rm rd 1010011` | 类型转换：32位有符号整数→单精度(32位) |
| `FCVT.S.WU` | `1101000 00001 rs1 rm rd 1010011` | 类型转换：32位无符号整数→单精度(32位) |
| `FMV.W.X` | `1111000 00000 rs1 000 rd 1010011` | 位模式搬运（不转换）：X的位→32位有符号整数 |

### RV64F Standard Extension (in addition to RV32F)

（规范PDF第609页起，共4条）

| 助记符 | 编码字段 | 说明 |
| --- | --- | --- |
| `FCVT.L.S` | `1100000 00010 rs1 rm rd 1010011` | 类型转换：单精度(32位)→64位有符号整数 |
| `FCVT.LU.S` | `1100000 00011 rs1 rm rd 1010011` | 类型转换：单精度(32位)→64位无符号整数 |
| `FCVT.S.L` | `1101000 00010 rs1 rm rd 1010011` | 类型转换：64位有符号整数→单精度(32位) |
| `FCVT.S.LU` | `1101000 00011 rs1 rm rd 1010011` | 类型转换：64位无符号整数→单精度(32位) |

### 6.2 D 扩展（双精度，32条）

### RV32D Standard Extension

（规范PDF第610页起，共26条）

| 助记符 | 编码字段 | 说明 |
| --- | --- | --- |
| `FLD` | `imm[11:0] rs1 011 rd 0000111` | 从内存加载双精度浮点数 |
| `FSD` | `imm[11:5] rs2 rs1 011 imm[4:0] 0100111` | 把双精度浮点数存入内存 |
| `FMADD.D` | `rs3 01 rs2 rs1 rm rd 1000011` | 融合乘加：rd←rs1×rs2+rs3（双精度(64位)，单次舍入） |
| `FMSUB.D` | `rs3 01 rs2 rs1 rm rd 1000111` | 融合乘加：rd←rs1×rs2-rs3（双精度(64位)，单次舍入） |
| `FNMSUB.D` | `rs3 01 rs2 rs1 rm rd 1001011` | 融合乘加：rd←-(rs1×rs2)+rs3（双精度(64位)，单次舍入） |
| `FNMADD.D` | `rs3 01 rs2 rs1 rm rd 1001111` | 融合乘加：rd←-(rs1×rs2)-rs3（双精度(64位)，单次舍入） |
| `FADD.D` | `0000001 rs2 rs1 rm rd 1010011` | 双精度(64位)加法 |
| `FSUB.D` | `0000101 rs2 rs1 rm rd 1010011` | 双精度(64位)减法 |
| `FMUL.D` | `0001001 rs2 rs1 rm rd 1010011` | 双精度(64位)乘法 |
| `FDIV.D` | `0001101 rs2 rs1 rm rd 1010011` | 双精度(64位)除法 |
| `FSQRT.D` | `0101101 00000 rs1 rm rd 1010011` | 双精度(64位)平方根 |
| `FSGNJ.D` | `0010001 rs2 rs1 000 rd 1010011` | 符号注入：取rs1数值、取rs2符号（双精度(64位)） |
| `FSGNJN.D` | `0010001 rs2 rs1 001 rd 1010011` | 符号注入：取rs1数值、取rs2符号的反（双精度(64位)） |
| `FSGNJX.D` | `0010001 rs2 rs1 010 rd 1010011` | 符号注入：rs1与rs2符号按异或合成（双精度(64位)） |
| `FMIN.D` | `0010101 rs2 rs1 000 rd 1010011` | 取较小值（双精度(64位)，NaN处理按IEEE-754-2019） |
| `FMAX.D` | `0010101 rs2 rs1 001 rd 1010011` | 取较大值（双精度(64位)） |
| `FCVT.S.D` | `0100000 00001 rs1 rm rd 1010011` | 类型转换：双精度(64位)→单精度(32位) |
| `FCVT.D.S` | `0100001 00000 rs1 rm rd 1010011` | 类型转换：单精度(32位)→双精度(64位) |
| `FEQ.D` | `1010001 rs2 rs1 010 rd 1010011` | 相等比较，写整数结果（双精度(64位)，静默版不触发异常） |
| `FLT.D` | `1010001 rs2 rs1 001 rd 1010011` | 小于比较，写整数结果（双精度(64位)，静默版） |
| `FLE.D` | `1010001 rs2 rs1 000 rd 1010011` | 小于等于比较，写整数结果（双精度(64位)，静默版） |
| `FCLASS.D` | `1110001 00000 rs1 001 rd 1010011` | 分类：按10类位图写整数结果（双精度(64位)） |
| `FCVT.W.D` | `1100001 00000 rs1 rm rd 1010011` | 类型转换：双精度(64位)→32位有符号整数 |
| `FCVT.WU.D` | `1100001 00001 rs1 rm rd 1010011` | 类型转换：双精度(64位)→32位无符号整数 |
| `FCVT.D.W` | `1101001 00000 rs1 rm rd 1010011` | 类型转换：32位有符号整数→双精度(64位) |
| `FCVT.D.WU` | `1101001 00001 rs1 rm rd 1010011` | 类型转换：32位无符号整数→双精度(64位) |

### RV64D Standard Extension (in addition to RV32D)

（规范PDF第610页起，共6条）

| 助记符 | 编码字段 | 说明 |
| --- | --- | --- |
| `FCVT.L.D` | `1100001 00010 rs1 rm rd 1010011` | 类型转换：双精度(64位)→64位有符号整数 |
| `FCVT.LU.D` | `1100001 00011 rs1 rm rd 1010011` | 类型转换：双精度(64位)→64位无符号整数 |
| `FMV.X.D` | `1110001 00000 rs1 000 rd 1010011` | 位模式搬运（不转换）：双精度(64位)的位→X |
| `FCVT.D.L` | `1101001 00010 rs1 rm rd 1010011` | 类型转换：64位有符号整数→双精度(64位) |
| `FCVT.D.LU` | `1101001 00011 rs1 rm rd 1010011` | 类型转换：64位无符号整数→双精度(64位) |
| `FMV.D.X` | `1111001 00000 rs1 000 rd 1010011` | 位模式搬运（不转换）：X的位→双精度(64位) |

### 6.3 Q 扩展（四精度，32条）

### RV32Q Standard Extension

（规范PDF第612页起，共28条）

| 助记符 | 编码字段 | 说明 |
| --- | --- | --- |
| `FLQ` | `imm[11:0] rs1 100 rd 0000111` | 从内存加载四精度浮点数 |
| `FSQ` | `imm[11:5] rs2 rs1 100 imm[4:0] 0100111` | 把四精度浮点数存入内存 |
| `FMADD.Q` | `rs3 11 rs2 rs1 rm rd 1000011` | 融合乘加：rd←rs1×rs2+rs3（四精度(128位)，单次舍入） |
| `FMSUB.Q` | `rs3 11 rs2 rs1 rm rd 1000111` | 融合乘加：rd←rs1×rs2-rs3（四精度(128位)，单次舍入） |
| `FNMSUB.Q` | `rs3 11 rs2 rs1 rm rd 1001011` | 融合乘加：rd←-(rs1×rs2)+rs3（四精度(128位)，单次舍入） |
| `FNMADD.Q` | `rs3 11 rs2 rs1 rm rd 1001111` | 融合乘加：rd←-(rs1×rs2)-rs3（四精度(128位)，单次舍入） |
| `FADD.Q` | `0000011 rs2 rs1 rm rd 1010011` | 四精度(128位)加法 |
| `FSUB.Q` | `0000111 rs2 rs1 rm rd 1010011` | 四精度(128位)减法 |
| `FMUL.Q` | `0001011 rs2 rs1 rm rd 1010011` | 四精度(128位)乘法 |
| `FDIV.Q` | `0001111 rs2 rs1 rm rd 1010011` | 四精度(128位)除法 |
| `FSQRT.Q` | `0101111 00000 rs1 rm rd 1010011` | 四精度(128位)平方根 |
| `FSGNJ.Q` | `0010011 rs2 rs1 000 rd 1010011` | 符号注入：取rs1数值、取rs2符号（四精度(128位)） |
| `FSGNJN.Q` | `0010011 rs2 rs1 001 rd 1010011` | 符号注入：取rs1数值、取rs2符号的反（四精度(128位)） |
| `FSGNJX.Q` | `0010011 rs2 rs1 010 rd 1010011` | 符号注入：rs1与rs2符号按异或合成（四精度(128位)） |
| `FMIN.Q` | `0010111 rs2 rs1 000 rd 1010011` | 取较小值（四精度(128位)，NaN处理按IEEE-754-2019） |
| `FMAX.Q` | `0010111 rs2 rs1 001 rd 1010011` | 取较大值（四精度(128位)） |
| `FCVT.S.Q` | `0100000 00011 rs1 rm rd 1010011` | 类型转换：四精度(128位)→单精度(32位) |
| `FCVT.Q.S` | `0100011 00000 rs1 rm rd 1010011` | 类型转换：单精度(32位)→四精度(128位) |
| `FCVT.D.Q` | `0100001 00011 rs1 rm rd 1010011` | 类型转换：四精度(128位)→双精度(64位) |
| `FCVT.Q.D` | `0100011 00001 rs1 rm rd 1010011` | 类型转换：双精度(64位)→四精度(128位) |
| `FEQ.Q` | `1010011 rs2 rs1 010 rd 1010011` | 相等比较，写整数结果（四精度(128位)，静默版不触发异常） |
| `FLT.Q` | `1010011 rs2 rs1 001 rd 1010011` | 小于比较，写整数结果（四精度(128位)，静默版） |
| `FLE.Q` | `1010011 rs2 rs1 000 rd 1010011` | 小于等于比较，写整数结果（四精度(128位)，静默版） |
| `FCLASS.Q` | `1110011 00000 rs1 001 rd 1010011` | 分类：按10类位图写整数结果（四精度(128位)） |
| `FCVT.W.Q` | `1100011 00000 rs1 rm rd 1010011` | 类型转换：四精度(128位)→32位有符号整数 |
| `FCVT.WU.Q` | `1100011 00001 rs1 rm rd 1010011` | 类型转换：四精度(128位)→32位无符号整数 |
| `FCVT.Q.W` | `1101011 00000 rs1 rm rd 1010011` | 类型转换：32位有符号整数→四精度(128位) |
| `FCVT.Q.WU` | `1101011 00001 rs1 rm rd 1010011` | 类型转换：32位无符号整数→四精度(128位) |

### RV64Q Standard Extension (in addition to RV32Q)

（规范PDF第612页起，共4条）

| 助记符 | 编码字段 | 说明 |
| --- | --- | --- |
| `FCVT.L.Q` | `1100011 00010 rs1 rm rd 1010011` | 类型转换：四精度(128位)→64位有符号整数 |
| `FCVT.LU.Q` | `1100011 00011 rs1 rm rd 1010011` | 类型转换：四精度(128位)→64位无符号整数 |
| `FCVT.Q.L` | `1101011 00010 rs1 rm rd 1010011` | 类型转换：64位有符号整数→四精度(128位) |
| `FCVT.Q.LU` | `1101011 00011 rs1 rm rd 1010011` | 类型转换：64位无符号整数→四精度(128位) |

### 6.4 Zfh 扩展（半精度，36条）

### RV32Zfh Standard Extension

（规范PDF第614页起，共32条）

| 助记符 | 编码字段 | 说明 |
| --- | --- | --- |
| `FLH` | `imm[11:0] rs1 001 rd 0000111` | 从内存加载半精度浮点数 |
| `FSH` | `imm[11:5] rs2 rs1 001 imm[4:0] 0100111` | 把半精度浮点数存入内存 |
| `FMADD.H` | `rs3 10 rs2 rs1 rm rd 1000011` | 融合乘加：rd←rs1×rs2+rs3（半精度(16位)，单次舍入） |
| `FMSUB.H` | `rs3 10 rs2 rs1 rm rd 1000111` | 融合乘加：rd←rs1×rs2-rs3（半精度(16位)，单次舍入） |
| `FNMSUB.H` | `rs3 10 rs2 rs1 rm rd 1001011` | 融合乘加：rd←-(rs1×rs2)+rs3（半精度(16位)，单次舍入） |
| `FNMADD.H` | `rs3 10 rs2 rs1 rm rd 1001111` | 融合乘加：rd←-(rs1×rs2)-rs3（半精度(16位)，单次舍入） |
| `FADD.H` | `0000010 rs2 rs1 rm rd 1010011` | 半精度(16位)加法 |
| `FSUB.H` | `0000110 rs2 rs1 rm rd 1010011` | 半精度(16位)减法 |
| `FMUL.H` | `0001010 rs2 rs1 rm rd 1010011` | 半精度(16位)乘法 |
| `FDIV.H` | `0001110 rs2 rs1 rm rd 1010011` | 半精度(16位)除法 |
| `FSQRT.H` | `0101110 00000 rs1 rm rd 1010011` | 半精度(16位)平方根 |
| `FSGNJ.H` | `0010010 rs2 rs1 000 rd 1010011` | 符号注入：取rs1数值、取rs2符号（半精度(16位)） |
| `FSGNJN.H` | `0010010 rs2 rs1 001 rd 1010011` | 符号注入：取rs1数值、取rs2符号的反（半精度(16位)） |
| `FSGNJX.H` | `0010010 rs2 rs1 010 rd 1010011` | 符号注入：rs1与rs2符号按异或合成（半精度(16位)） |
| `FMIN.H` | `0010110 rs2 rs1 000 rd 1010011` | 取较小值（半精度(16位)，NaN处理按IEEE-754-2019） |
| `FMAX.H` | `0010110 rs2 rs1 001 rd 1010011` | 取较大值（半精度(16位)） |
| `FCVT.S.H` | `0100000 00010 rs1 rm rd 1010011` | 类型转换：半精度(16位)→单精度(32位) |
| `FCVT.H.S` | `0100010 00000 rs1 rm rd 1010011` | 类型转换：单精度(32位)→半精度(16位) |
| `FCVT.D.H` | `0100001 00010 rs1 rm rd 1010011` | 类型转换：半精度(16位)→双精度(64位) |
| `FCVT.H.D` | `0100010 00001 rs1 rm rd 1010011` | 类型转换：双精度(64位)→半精度(16位) |
| `FCVT.Q.H` | `0100011 00010 rs1 rm rd 1010011` | 类型转换：半精度(16位)→四精度(128位) |
| `FCVT.H.Q` | `0100010 00011 rs1 rm rd 1010011` | 类型转换：四精度(128位)→半精度(16位) |
| `FEQ.H` | `1010010 rs2 rs1 010 rd 1010011` | 相等比较，写整数结果（半精度(16位)，静默版不触发异常） |
| `FLT.H` | `1010010 rs2 rs1 001 rd 1010011` | 小于比较，写整数结果（半精度(16位)，静默版） |
| `FLE.H` | `1010010 rs2 rs1 000 rd 1010011` | 小于等于比较，写整数结果（半精度(16位)，静默版） |
| `FCLASS.H` | `1110010 00000 rs1 001 rd 1010011` | 分类：按10类位图写整数结果（半精度(16位)） |
| `FCVT.W.H` | `1100010 00000 rs1 rm rd 1010011` | 类型转换：半精度(16位)→32位有符号整数 |
| `FCVT.WU.H` | `1100010 00001 rs1 rm rd 1010011` | 类型转换：半精度(16位)→32位无符号整数 |
| `FMV.X.H` | `1110010 00000 rs1 000 rd 1010011` | 位模式搬运（不转换）：半精度(16位)的位→X |
| `FCVT.H.W` | `1101010 00000 rs1 rm rd 1010011` | 类型转换：32位有符号整数→半精度(16位) |
| `FCVT.H.WU` | `1101010 00001 rs1 rm rd 1010011` | 类型转换：32位无符号整数→半精度(16位) |
| `FMV.H.X` | `1111010 00000 rs1 000 rd 1010011` | 位模式搬运（不转换）：X的位→半精度(16位) |

### RV64Zfh Standard Extension (in addition to RV32Zfh)

（规范PDF第615页起，共4条）

| 助记符 | 编码字段 | 说明 |
| --- | --- | --- |
| `FCVT.L.H` | `1100010 00010 rs1 rm rd 1010011` | 类型转换：半精度(16位)→64位有符号整数 |
| `FCVT.LU.H` | `1100010 00011 rs1 rm rd 1010011` | 类型转换：半精度(16位)→64位无符号整数 |
| `FCVT.H.L` | `1101010 00010 rs1 rm rd 1010011` | 类型转换：64位有符号整数→半精度(16位) |
| `FCVT.H.LU` | `1101010 00011 rs1 rm rd 1010011` | 类型转换：64位无符号整数→半精度(16位) |

### 6.5 Zfhmin（Zfh的最小数据搬运子集）

| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| FLH | flh rd, offset(rs1) | 半精度加载（Zfhmin 内含） | 6183 |
| FSH | fsh rs2, offset(rs1) | 半精度存储（Zfhmin 内含） | 6183 |
| FMV.X.H | fmv.x.h rd, rs1 | 半精度位型移入整数 rd（Zfhmin 内含） | 6183 |
| FMV.H.X | fmv.h.x rd, rs1 | 整数低 16 位移入浮点 rd（Zfhmin 内含） | 6183 |
| FCVT.S.H | fcvt.s.h rd, rs1, rm | 半精度→单精度（Zfhmin 内含） | 6183 |
| FCVT.H.S | fcvt.h.s rd, rs1, rm | 单精度→半精度（Zfhmin 内含） | 6183 |
| FCVT.D.H | fcvt.d.h rd, rs1, rm | 半精度→双精度，**仅当 D 扩展存在时** Zfhmin 才含 | 6184 |
| FCVT.H.D | fcvt.h.d rd, rs1, rm | 双精度→半精度，**仅当 D 扩展存在时** Zfhmin 才含 | 6184 |
| FCVT.Q.H | fcvt.q.h rd, rs1, rm | 半精度→四精度，**仅当 Q 扩展存在时** Zfhmin 才含 | 6185 |
| FCVT.H.Q | fcvt.h.q rd, rs1, rm | 四精度→半精度，**仅当 Q 扩展存在时** Zfhmin 才含 | 6185 |

Zfh 与 Zfhmin 的指令集合差异（按文本 6177–6189）：
- Zfhmin 是 Zfh 的**子集**，只含**数据搬运与转换**指令：FLH、FSH、FMV.X.H、FMV.H.X、FCVT.S.H、FCVT.H.S；若 D 存在再加 FCVT.D.H、FCVT.H.D；若 Q 存在再加 FCVT.Q.H、FCVT.H.Q（6183–6185）。
- Zfh 额外含全部算术/比较/分类/符号注入指令：FADD.H、FSUB.H、FMUL.H、FDIV.H、FSQRT.H、FMIN.H、FMAX.H、FMADD.H、FMSUB.H、FNMSUB.H、FNMADD.H、FCVT.W[U].H、FCVT.L[U].H、FCVT.H.W[U]、FCVT.H.L[U]、FSGNJ.H、FSGNJN.H、FSGNJX.H、FEQ.H、FLT.H、FLE.H、FCLASS.H。文本明确 **Zfhmin 不含 FSGNJ.H**，因为可用 FSGNJ.S 在半精度值间搬移（6188–6189）。

### 6.6 BF16 系列（Zfbfmin / Zvfbfmin / Zvfbfwma）

| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| FCVT.BF16.S | fcvt.bf16.s rd, rs1 | 标量收缩转换 FP32→BF16，按 RM 舍入；异常 OF/UF/NX/NV | 6428（正文小写 6479） |
| FCVT.S.BF16 | fcvt.s.bf16 rd, rs1 | 标量扩展转换 BF16→FP32，转换精确，结果 NaN-boxing；异常 NV | 6429（正文小写 6501） |
| FLH | flh rd, offset(rs1) | 由 Zfbfmin 复用（定义在第 24 章） | 6430 |
| FSH | fsh rs2, offset(rs1) | 由 Zfbfmin 复用（定义在第 24 章） | 6431 |
| FMV.H.X | fmv.h.x rd, rs1 | 由 Zfbfmin 复用 | 6432 |
| FMV.X.H | fmv.x.h rd, rs1 | 由 Zfbfmin 复用 | 6433 |

文本称 Zfbfmin 共含六条指令（6398）。

| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| vfncvtbf16.f.f.w | vfncvtbf16.f.f.w vd, vs2, vm | 向量收缩转换 FP32→BF16，按 frm 舍入；SEW 必须为 16 | 6464（正文 6527） |
| vfwcvtbf16.f.f.v | vfwcvtbf16.f.f.v vd, vs2, vm | 向量扩展转换 BF16→FP32，精确；SEW 必须为 16 | 6465（正文 6551） |

| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| VFWMACCBF16 | vfwmaccbf16.vv vd, vs1, vs2, vm / vfwmaccbf16.vf vd, rs1, vs2, vm | 向量 BF16 扩展融合乘加，累加到 FP32，按 frm 舍入；SEW 必须为 16 | 6473（正文 6577–6578） |

### 6.7 Zfa（附加浮点，33条）

| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| FLI.S | fli.s rd, rs1 | 从 rs1 字段编码的 32 个常量中加载单精度常数（编码同 FMV.W.X 但 rs2=1） | 6632 |
| FLI.D | fli.d rd, rs1 | 双精度版本（需 D），编码同 FLI.S 但 fmt=D | 6688 |
| FLI.Q | fli.q rd, rs1 | 四精度版本（需 Q），fmt=Q | 6692 |
| FLI.H | fli.h rd, rs1 | 半精度版本（需 Zfh 或 Zvfh），fmt=H；入口 29 改为 +∞ | 6695 |
| FMINM.S | fminm.s rd, rs1, rs2 | 类似 FMIN.S，但任一输入为 NaN 时结果为规范 NaN | 6704 |
| FMAXM.S | fmaxm.s rd, rs1, rs2 | 类似 FMAX.S，但任一输入为 NaN 时结果为规范 NaN | 6704 |
| FMINM.D | fminm.d rd, rs1, rs2 | 双精度最小（需 D，IEEE 754-2019 minimum） | 6706 |
| FMAXM.D | fmaxm.d rd, rs1, rs2 | 双精度最大（需 D） | 6706 |
| FMINM.H | fminm.h rd, rs1, rs2 | 半精度最小（需 Zfh） | 6708 |
| FMAXM.H | fmaxm.h rd, rs1, rs2 | 半精度最大（需 Zfh） | 6708 |
| FMINM.Q | fminm.q rd, rs1, rs2 | 四精度最小（需 Q） | 6710 |
| FMAXM.Q | fmaxm.q rd, rs1, rs2 | 四精度最大（需 Q） | 6710 |
| FROUND.S | fround.s rd, rs1, rm | 按 rm 把单精度值舍入为整数并以单精度格式写 rd；±0/∞ 原样复制 | 6718 |
| FROUNDNX.S | froundnx.s rd, rs1, rm | 同 FROUND.S，但结果与输入不等且非 NaN 时置不精确标志 | 6723 |
| FROUND.D | fround.d rd, rs1, rm | 双精度版本（需 D） | 6725 |
| FROUNDNX.D | froundnx.d rd, rs1, rm | 双精度版本（需 D） | 6725 |
| FROUND.H | fround.h rd, rs1, rm | 半精度版本（需 Zfh） | 6727 |
| FROUNDNX.H | froundnx.h rd, rs1, rm | 半精度版本（需 Zfh） | 6727 |
| FROUND.Q | fround.q rd, rs1, rm | 四精度版本（需 Q） | 6729 |
| FROUNDNX.Q | froundnx.q rd, rs1, rm | 四精度版本（需 Q） | 6729 |
| FCVTMOD.W.D | fcvtmod.w.d rd, rs1, rtz | 类似 FCVT.W.D 但恒向零舍入，取 31:0 后符号扩展写整数 rd；±∞/NaN→0；需 D，rm 必须显式写 rtz | 6736（汇编语法 6746） |
| FMVH.X.D | fmvh.x.d rd, rs1 | 把浮点 rs1 的 63:32 位移入整数 rd；**仅 RV32**（需 D） | 6751 |
| FMVP.D.X | fmvp.d.x rd, rs1, rs2 | 由整数寄存器对 rs1(31:0)、rs2(63:32) 组成双精度数写入浮点 rd；**仅 RV32**（需 D） | 6759 |
| FMVH.X.Q | fmvh.x.q rd, rs1 | 把浮点 rs1 的 127:64 位移入整数 rd；**仅 RV64**（需 Q） | 6763 |
| FMVP.Q.X | fmvp.q.x rd, rs1, rs2 | 由整数寄存器对 rs1(63:0)、rs2(127:64) 组成四精度数写入浮点 rd；**仅 RV64**（需 Q） | 6768 |
| FLEQ.S | fleq.s rd, rs1, rs2 | 类似 FLE.S，但安静 NaN 输入不置无效运算标志 | 6773 |
| FLTQ.S | fltq.s rd, rs1, rs2 | 类似 FLT.S，但安静 NaN 输入不置无效运算标志 | 6773 |
| FLEQ.D | fleq.d rd, rs1, rs2 | 双精度版本（需 D） | 6775 |
| FLTQ.D | fltq.d rd, rs1, rs2 | 双精度版本（需 D） | 6775 |
| FLEQ.H | fleq.h rd, rs1, rs2 | 半精度版本（需 Zfh） | 6777 |
| FLTQ.H | fltq.h rd, rs1, rs2 | 半精度版本（需 Zfh） | 6777 |
| FLEQ.Q | fleq.q rd, rs1, rs2 | 四精度版本（需 Q） | 6779 |
| FLTQ.Q | fltq.q rd, rs1, rs2 | 四精度版本（需 Q） | 6779 |

注：正文以大写写出（FLI.S、FMINM.S、FROUND.S、FCVTMOD.W.D），汇编语法为小写（fli.s / fminm.s / fround.s / fcvtmod.w.d，见 6746）。编码依据：FLI 同 FMV.W.X 但 rs2=1（6634）；FMINM/FMAXM 同 FMIN/FMAX 但指令位 13=1（6715）；FROUND/FROUNDNX 同 FCVT.S.D 但 rs2=4/5（6722、6724）；FCVTMOD.W.D 同 FCVT.W.D 但 rs2=8、rm=1（6743）；FLEQ/FLTQ 同 FLE/FLT 但指令位 14=1（6781）。

### 6.8 Zfinx / Zdinx / Zhinx / Zhinxmin（复用F/D/H助记符，新增0条）

**本章不新增任何浮点助记符**——文本说法是：Zfinx “adds all of the instructions that the F extension adds, except for the transfer instructions FLW, FSW, FMV.W.X, FMV.X.W, C.FLW[SP], and C.FSW[SP]”（6801–6802）；Zdinx “adds all of the instructions that the D extension adds, except for … FLD, FSD, FMV.D.X, FMV.X.D, C.FLD[SP], and C.FSD[SP]”（6827–6831）；Zhinx “adds all of the instructions that the Zfh extension adds, except for the transfer instructions FLH, FSH, FMV.H.X, and FMV.X.H”（6852–6853）。三者都是**复用 F/D/H 的指令名，只把 f 寄存器换成同号的 x 寄存器**：“The Zfinx variants of these F-extension instructions have the same semantics, except that whenever such an instruction would have accessed an f register, it instead accesses the x register with the same number.”（6807–6808；D 版 6832–6833；H 版 6854–6856）。因此没有为它们编造新助记符。

| 扩展 | 复用助记符集合（沿用 F/D/Zfh 名字） | 与 F/D/Zfh 的差异 | 证据行号 |
| --- | --- | --- | --- |
| Zfinx | F 扩展除搬运类以外的全部：FADD.S、FSUB.S、FMUL.S、FDIV.S、FSQRT.S、FMIN.S、FMAX.S、FMADD.S、FMSUB.S、FNMSUB.S、FNMADD.S、FCVT.*.*（W/WU/L/LU ↔ S）、FSGNJ.S、FSGNJN.S、FSGNJX.S、FEQ.S、FLT.S、FLE.S、FCLASS.S、FMV.S/FNEG.S/FABS.S 等 | **不提供** FLW、FSW、FMV.W.X、FMV.X.W、C.FLW[SP]、C.FSW[SP]；操作数改用同号 x 寄存器；w<XLEN 的结果用符号位填充高位（无 NaN-boxing） | 6801、6807、6811 |
| Zdinx | D 扩展除搬运类以外的全部：FADD.D…FCLASS.D、FCVT.*.*（↔D）等 | **不提供** FLD、FSD、FMV.D.X、FMV.X.D、C.FLD[SP]、C.FSD[SP]；RV32 下双精度放**偶数对齐 x 寄存器对**（低位在低号寄存器，写 x0 整体无效） | 6827、6831、6835、6840 |
| Zhinx | Zfh 扩展除搬运类以外的全部：FADD.H…FCLASS.H、FCVT.*.*（↔H）等 | **不提供** FLH、FSH、FMV.H.X、FMV.X.H | 6852 |
| Zhinxmin | Zhinx 中的 FCVT.S.H、FCVT.H.S（若 Zdinx 存在，还含 FCVT.D.H、FCVT.H.D） | 最小子集，仅转换指令；不新增助记符 | 6860–6861 |

本章仅**提及**（并非由本章定义）的助记符：FLW、FSW、FMV.W.X、FMV.X.W、C.FLW[SP]、C.FSW[SP]（6802）、FLD、FSD、FMV.D.X、FMV.X.D、C.FLD[SP]、C.FSD[SP]（6831）、FLH、FSH、FMV.H.X、FMV.X.H（6853）；这些是 F/D/Zfh/C 扩展的指令，被 Zfinx 系列**排除**。

- 本范围指令总数（按助记符去重，不含汇编伪指令/旧名别名、不重复计入 Zfhmin 与 Zfinx 系列复用的名字）：**168**
- 各扩展条数小计（同上口径）：F = 30；D = 32；Q = 32；Zfh = 36；Zfhmin = 10（复用 Zfh 名字，其中 6 条为 Zfhmin 核心、4 条条件包含）；BF16 = 5 条新助记符（Zfbfmin 新的 2 条 + 复用 4 条 → 6 条，Zvfbfmin = 2，Zvfbfwma = 1）；Zfa = 33；Zfinx/Zdinx/Zhinx/Zhinxmin = 0 条新助记符
- 另附第 21 章定义的汇编伪指令 9 条（FRCSR、FSCSR、FRRM、FSRM、FRFLAGS、FSFLAGS、FMV.S、FNEG.S、FABS.S）及 2 个旧名别名（FMV.S.X、FMV.X.S），均未计入上述 168 条

### 6.9 F 扩展相关伪指令

| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| FLW | flw rd, offset(rs1) | 从内存加载单精度值到浮点寄存器 rd | 5556 |
| FSW | fsw rs2, offset(rs1) | 把浮点寄存器 rs2 的单精度值存入内存 | 5557 |
| FADD.S | fadd.s rd, rs1, rs2, rm | 单精度加法 | 5575 |
| FSUB.S | fsub.s rd, rs1, rs2, rm | 单精度减法（rs1−rs2） | 5576 |
| FMUL.S | fmul.s rd, rs1, rs2, rm | 单精度乘法 | 5575 |
| FDIV.S | fdiv.s rd, rs1, rs2, rm | 单精度除法（rs1/rs2） | 5577 |
| FSQRT.S | fsqrt.s rd, rs1, rm | 单精度平方根 | 5577 |
| FMIN.S | fmin.s rd, rs1, rs2 | 取较小者（−0.0 < +0.0；单 NaN 时返回非 NaN） | 5589 |
| FMAX.S | fmax.s rd, rs1, rs2 | 取较大者（同上） | 5589 |
| FMADD.S | fmadd.s rd, rs1, rs2, rs3, rm | 融合乘加 (rs1×rs2)+rs3 | 5611 |
| FMSUB.S | fmsub.s rd, rs1, rs2, rs3, rm | 融合乘减 (rs1×rs2)−rs3 | 5613 |
| FNMSUB.S | fnmsub.s rd, rs1, rs2, rs3, rm | 乘积取反后加 rs3：−(rs1×rs2)+rs3 | 5615 |
| FNMADD.S | fnmadd.s rd, rs1, rs2, rs3, rm | 乘积取反后减 rs3：−(rs1×rs2)−rs3 | 5620 |
| FCVT.W.S | fcvt.w.s rd, rs1, rm | 单精度→32 位有符号整数（XLEN>32 时结果符号扩展） | 5647 |
| FCVT.WU.S | fcvt.wu.s rd, rs1, rm | 单精度→32 位无符号整数 | 5650 |
| FCVT.L.S | fcvt.l.s rd, rs1, rm | 单精度→64 位有符号整数，**仅 RV64** | 5647 |
| FCVT.LU.S | fcvt.lu.s rd, rs1, rm | 单精度→64 位无符号整数，**仅 RV64** | 5650 |
| FCVT.S.W | fcvt.s.w rd, rs1, rm | 32 位有符号整数→单精度（fcvt.s.w rd,x0 得 +0 且不置标志） | 5648 |
| FCVT.S.WU | fcvt.s.wu rd, rs1, rm | 32 位无符号整数→单精度 | 5650 |
| FCVT.S.L | fcvt.s.l rd, rs1, rm | 64 位有符号整数→单精度，**仅 RV64** | 5648 |
| FCVT.S.LU | fcvt.s.lu rd, rs1, rm | 64 位无符号整数→单精度，**仅 RV64** | 5650 |
| FSGNJ.S | fsgnj.s rd, rs1, rs2 | 取 rs1 除符号位外的全部位，符号位取 rs2 的符号位 | 5681 |
| FSGNJN.S | fsgnjn.s rd, rs1, rs2 | 同上，符号位取 rs2 符号位取反 | 5681 |
| FSGNJX.S | fsgnjx.s rd, rs1, rs2 | 同上，符号位为 rs1 与 rs2 符号位异或 | 5681 |
| FMV.X.W | fmv.x.w rd, rs1 | 浮点寄存器 rs1 的低 32 位原样移入整数 rd；RV64 时高 32 位用该浮点数的符号位填充（RV32/RV64 均定义，并非 RV32 专有） | 5700 |
| FMV.W.X | fmv.w.x rd, rs1 | 整数 rs1 低 32 位原样移入浮点寄存器 rd | 5705 |
| FEQ.S | feq.s rd, rs1, rs2 | 相等比较（安静比较），结果写整数 rd，NaN 结果为 0 | 5734 |
| FLT.S | flt.s rd, rs1, rs2 | 小于比较（信号比较），rs1<rs2 写 1 到整数 rd | 5734 |
| FLE.S | fle.s rd, rs1, rs2 | 小于等于比较（信号比较），rs1≤rs2 写 1 到整数 rd | 5734 |
| FCLASS.S | fclass.s rd, rs1 | 分类，把 10 位类别掩码写入整数 rd（表 28） | 5750 |

Chapter 21 另定义下列**汇编伪指令**（非独立新助记符，基于 CSR 访问指令/SGNJ）：
| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| FRCSR | frcsr rd | 读 fcsr 到整数 rd（伪指令） | 5463 |
| FSCSR | fscsr rd, rs1 | 交换 fcsr 内容（伪指令） | 5463 |
| FRRM | frrm rd | 读 frm（fcsr 位 7—5）到 rd 低 3 位（伪指令） | 5468 |
| FSRM | fsrm rd, rs1 | 交换 frm 内容（伪指令） | 5470 |
| FRFLAGS | frflags rd | 读 fflags（fcsr 位 4—0，伪指令） | 5472 |
| FSFLAGS | fsflags rd, rs1 | 交换 fflags 内容（伪指令） | 5472 |
| FMV.S | fmv.s rx, ry | 等价 FSGNJ.S rx, ry, ry（伪指令） | 5685 |
| FNEG.S | fneg.s rx, ry | 等价 FSGNJN.S rx, ry, ry（伪指令） | 5686 |
| FABS.S | fabs.s rx, ry | 等价 FSGNJX.S rx, ry, ry（伪指令） | 5687 |
| FMV.S.X / FMV.X.S | — | FMV.W.X / FMV.X.W 的旧名（工具两侧都支持） | 5709 |

## 七、压缩指令集（C / Zc* / Zilsd / Zclsd）

### Zca（第28章 28.3–28.5 逐条定义节 + 28.8 RVC 指令清单；第29章 §29.5 确认 Zca = C 去掉 c.f*）

| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| C.LWSP | C.LWSP rd, offset(sp) | 以 sp(x2) 为基址加载 32 位字（零扩展偏移×4），rd≠x0 | 7070（清单 7511） |
| C.LDSP | C.LDSP rd, offset(sp) | RV64C 专用，以 sp 为基址加载 64 位双字（偏移×8），rd≠x0 | 7073（清单 7513） |
| C.SWSP | C.SWSP rs2, offset(sp) | 以 sp 为基址存储 32 位字 | 7092（清单 7520） |
| C.SDSP | C.SDSP rs2, offset(sp) | RV64C 专用，以 sp 为基址存储 64 位双字 | 7094（清单 7522） |
| C.LW | C.LW rd′, offset(rs1′) | 以 rs1′ 为基址加载 32 位字（rd′/rs1′ 限 x8–x15） | 7146（清单 7473） |
| C.LD | C.LD rd′, offset(rs1′) | RV64C 专用，加载 64 位双字 | 7148（清单 7475） |
| C.SW | C.SW rs2′, offset(rs1′) | 存储 32 位字 | 7166（清单 7478） |
| C.SD | C.SD rs2′, offset(rs1′) | RV64C 专用，存储 64 位双字 | 7168（清单 7480） |
| C.J | C.J offset | 无条件跳转，±2 KiB | 7189（清单 7504） |
| C.JAL | C.JAL offset | RV32C 专用，跳转并把 pc+2 写入 x1 | 7191（清单 7488） |
| C.JR | C.JR rs1 | 寄存器间接跳转，rs1≠x0（Zca 中的独立指令） | 7201（清单 7514） |
| C.JALR | C.JALR rs1 | 寄存器间接跳转并链接（写 x1），rs1≠x0（独立指令） | 7203（清单 7517） |
| C.BEQZ | C.BEQZ rs1′, offset | rs1′=0 时分支，±256 B | 7221（清单 7505） |
| C.BNEZ | C.BNEZ rs1′, offset | rs1′≠0 时分支 | 7224（清单 7506） |
| C.LI | C.LI rd, imm | 把符号扩展 6 位立即数装入 rd | 7238（清单 7490） |
| C.LUI | C.LUI rd, imm | 非零 6 位立即数装入 bit17–12，清低 12 位并符号扩展，rd≠x2 | 7240（清单 7492） |
| C.ADDI | C.ADDI rd, imm | rd = rd + 非零符号扩展 6 位立即数 | 7255（清单 7487） |
| C.ADDIW | C.ADDIW rd, imm | RV64C 专用，32 位加后符号扩展（imm=0 即 sext.w），rd≠x0 | 7261（清单 7489） |
| C.ADDI16SP | C.ADDI16SP nzimm | sp = sp + nzimm（16 的倍数，[-512,496]），nzimm≠0 | 7265（清单 7491） |
| C.ADDI4SPN | C.ADDI4SPN rd′, nzuimm | 非零零扩展立即数×4 加到 sp，结果写 rd′，nzuimm≠0 | 7274（清单 7471） |
| C.SLLI | C.SLLI rd, shamt | rd = rd << shamt（RV32 时 shamt[5] 须为 0） | 7281（清单 7509） |
| C.SRLI | C.SRLI rd′, shamt | rd′ = rd′ >> shamt（逻辑右移） | 7294（清单 7493） |
| C.SRAI | C.SRAI rd′, shamt | rd′ = rd′ >> shamt（算术右移） | 7299（清单 7494） |
| C.ANDI | C.ANDI rd′, imm | rd′ = rd′ & 符号扩展 6 位立即数 | 7311（清单 7495） |
| C.MV | C.MV rd, rs2 | rd = rs2，rs2≠x0 | 7321（清单 7515） |
| C.ADD | C.ADD rd, rs2 | rd = rd + rs2，rs2≠x0 | 7329（清单 7518） |
| C.AND | C.AND rd′, rs2′ | rd′ = rd′ & rs2′ | 7340（清单 7499） |
| C.OR | C.OR rd′, rs2′ | rd′ = rd′ \| rs2′ | 7342（清单 7498） |
| C.XOR | C.XOR rd′, rs2′ | rd′ = rd′ ^ rs2′ | 7344（清单 7497） |
| C.SUB | C.SUB rd′, rs2′ | rd′ = rd′ − rs2′ | 7349（清单 7496） |
| C.ADDW | C.ADDW rd′, rs2′ | RV64C 专用，32 位加后符号扩展 | 7351（清单 7501） |
| C.SUBW | C.SUBW rd′, rs2′ | RV64C 专用，32 位减后符号扩展 | 7353（清单 7500） |
| C.NOP | C.NOP | 空操作（不改变用户可见状态，只推进 pc） | 7375（清单 7486） |
| C.EBREAK | C.EBREAK | 断点，控制权交回调试环境 | 7381（清单 7516） |

（§28.5.4 另有一条"全 0 的 16 位指令永久保留为非法指令"的保留编码，无独立助记符：7360–7364、7470；清单中 `C.ADDI4SPN(RES, uimm=0)`、`C.JR(RES, rs1=0)` 等 RES/HINT 标注见 7471、7486–7522。）

### Zcf（RV32 only）

| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| C.FLW | C.FLW rd′, offset(rs1′) | RV32FC 专用，加载单精度浮点（偏移×4） | 7151（清单 7474） |
| C.FSW | C.FSW rs2′, offset(rs1′) | RV32FC 专用，存储单精度浮点 | 7174（清单 7479） |
| C.FLWSP | C.FLWSP rd, offset(sp) | RV32FC 专用，以 sp 为基址加载单精度浮点 | 7079（清单 7512） |
| C.FSWSP | C.FSWSP rs2, offset(sp) | RV32FC 专用，以 sp 为基址存储单精度浮点 | 7097（清单 7521） |

### Zcd

| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| C.FLD | C.FLD rd′, offset(rs1′) | RV32DC/RV64DC，加载双精度浮点（偏移×8） | 7154（清单 7472） |
| C.FSD | C.FSD rs2′, offset(rs1′) | RV32DC/RV64DC，存储双精度浮点 | 7177（清单 7477） |
| C.FLDSP | C.FLDSP rd, offset(sp) | RV32DC/RV64DC，以 sp 为基址加载双精度浮点 | 7082（清单 7510） |
| C.FSDSP | C.FSDSP rs2, offset(sp) | RV32DC/RV64DC，以 sp 为基址存储双精度浮点 | 7100（清单 7519） |

### Zcb（第29章 §29.8、§29.12）

| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| c.lbu | c.lbu rd′, uimm(rs1′) | 加载无符号字节并零扩展到 XLEN | 7718（概述 7633；格式 7691） |
| c.lhu | c.lhu rd′, uimm(rs1′) | 加载无符号半字并零扩展 | 7743（概述 7638） |
| c.lh | c.lh rd′, uimm(rs1′) | 加载有符号半字并符号扩展 | 7768（概述 7639） |
| c.sb | c.sb rs2′, uimm(rs1′) | 存储字节 | 7793（概述 7640；格式 7692） |
| c.sh | c.sh rs2′, uimm(rs1′) | 存储半字 | 7818（概述 7641） |
| c.zext.b | c.zext.b rd′/rs1′ | 最低字节零扩展到 XLEN（= andi rd′,rd′,0xff） | 7843（概述 7642；格式 7703） |
| c.sext.b | c.sext.b rd′/rs1′ | 最低字节符号扩展（需 Zbb） | 7866（概述 7643） |
| c.zext.h | c.zext.h rd′/rs1′ | 最低半字零扩展（需 Zbb） | 7888（概述 7644） |
| c.sext.h | c.sext.h rd′/rs1′ | 最低半字符号扩展（需 Zbb） | 7909（概述 7645） |
| c.zext.w | c.zext.w rd′/rs1′ | 最低字零扩展（RV64，需 Zba；= add.uw rd′,rd′,zero） | 7931（概述 7646） |
| c.not | c.not rd′/rs1′ | 按位取反（= xori rd′,rd′,-1） | 7954（概述 7647） |
| c.mul | c.mul rsd′, rs2′ | 乘法取低 XLEN 位（需 M 或 Zmmul；用 CA 格式） | 7976（概述 7648；7630） |

### Zcmp（第29章 §29.9、§29.13）

| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| cm.push | cm.push {reg_list}, -stack_adj | 建立栈帧：保存 ra 与 0–12 个 s 寄存器并调整 sp | 8248（概述 7668；编码 8250–8252） |
| cm.pop | cm.pop {reg_list}, stack_adj | 销毁栈帧：恢复寄存器并调整 sp | 8378（概述 7669；编码 8380–8382） |
| cm.popretz | cm.popretz {reg_list}, stack_adj | 恢复寄存器、调整 sp、a0=0 并 ret | 8508（概述 7671；编码 8510–8512） |
| cm.popret | cm.popret {reg_list}, stack_adj | 恢复寄存器、调整 sp 并 ret | 8641（概述 7670；编码 8643–8645） |
| cm.mvsa01 | cm.mvsa01 r1s′, r2s′ | 把 a0/a1 原子地移入两个不同的 s0–s7 寄存器 | 8771（概述 7673；编码 8773–8775） |
| cm.mva01s | cm.mva01s r1s′, r2s′ | 把两个 s0–s7 寄存器原子地移入 a0/a1 | 8806（概述 7672；编码 8808–8810） |

（`cm.push.e`/`cm.pop.e`/`cm.popretz.e`/`cm.popret.e`/`cm.mvsa01.e`/`cm.mva01s.e` 只是 rlist 0–3 等编码"保留给未来 EABI 变体"的说明，非本版定义指令：8253、8383、8513、8646、8767 附近注释、8818–8819。）

### Zcmt（第29章 §29.10、§29.14）

| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| cm.jt | cm.jt index | 经 jvt 跳转表跳转（index<32） | 8919（概述 7686；编码 8921–8923） |
| cm.jalt | cm.jalt index | 经跳转表跳转并链接到 ra（index≥32） | 8960（概述 7687；编码 8962–8964） |

### Zcmop（定义不在给定三段范围内：§10.1，行 3332–3361；按文本实际出现的编码清单列出）

| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| C.MOP.1 | C.MOP.1（无操作数；隐式关联 x1） | 不写任何寄存器的 MOP（对应 C.LUI x1, 0 的保留空间） | 3347（定义 3333–3338） |
| C.MOP.3 | C.MOP.3（隐式 x3） | 同上 | 3348 |
| C.MOP.5 | C.MOP.5（隐式 x5） | 同上 | 3349 |
| C.MOP.7 | C.MOP.7（隐式 x7） | 同上 | 3350 |
| C.MOP.9 | C.MOP.9（隐式 x9） | 同上 | 3351 |
| C.MOP.11 | C.MOP.11（隐式 x11） | 同上 | 3352 |
| C.MOP.13 | C.MOP.13（隐式 x13） | 同上 | 3353 |
| C.MOP.15 | C.MOP.15（隐式 x15） | 同上 | 3354 |

文本只给出奇数编号 1,3,5,7,9,11,13,15 共 8 条（3333–3334 明言"odd integer between 1 and 15, inclusive"），未出现偶数编号。

### Zilsd（第35章 §35.1、§35.5；RV32 only，32 位编码，非 16 位压缩）

| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| ld | ld rd, offset(rs1) | RV32 专用，把 64 位双字装入偶/奇寄存器对 rd,rd+1（rd 须为偶数） | 21414（表格 21353；编码 21416–21418） |
| sd | sd rs2, offset(rs1) | RV32 专用，从偶/奇寄存器对 rs2,rs2+1 存储 64 位双字 | 21430（表格 21354；编码 21432–21434） |

### Zclsd（第35章 §35.2、§35.5；RV32 only，16 位压缩编码，与 Zcf 编码重叠、不兼容）

| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| c.ldsp | c.ldsp rd, offset(sp) | RV32 专用，以 sp 为基址把 64 位双字装入偶/奇寄存器对（rd≠x0 且 rd 为偶数） | 21446（表格 21380；编码 21448–21450、21454） |
| c.sdsp | c.sdsp rs2, offset(sp) | RV32 专用，以 sp 为基址从偶/奇寄存器对存储 64 位双字 | 21463（表格 21382；编码 21465–21467） |
| c.ld | c.ld rd′, offset(rs1′) | RV32 专用，把 64 位双字装入 rd′ 寄存器对（仅限 x8–15） | 21479（表格 21384；编码 21481–21483；21390） |
| c.sd | c.sd rs2′, offset(rs1′) | RV32 专用，从 rs2′ 寄存器对存储 64 位双字（仅限 x8–15） | 21495（表格 21385；编码 21497–21499） |

### HINT / 别名 / 伪指令（不计入上面的指令小计）

| 名称 | 操作数形式 | 说明 | 证据行号 |
| --- | --- | --- | --- |
| C.NOP（imm≠0） | C.NOP | 作为 C.NOP 的 HINT 编码点（63 个码点，留给未来标准用途） | 7418（另 7376、7420） |
| C.ADDI（rd≠x0, imm=0） | C.ADDI rd, 0 | HINT（rd 被自身副本覆盖） | 7421（7400） |
| C.LI（rd=x0） | C.LI x0, imm | HINT | 7422 |
| C.LUI（rd=x0, imm≠0） | C.LUI x0, imm | HINT | 7423 |
| C.MV（rd=x0, rs2≠x0） | C.MV x0, rs2 | HINT | 7424 |
| C.ADD（rd=x0, rs2≠x0, rs2≠x2–x5） | C.ADD x0, rs2 | HINT（27 个码点） | 7425 |
| C.NTL.P1 | C.ADD x0, x2 | HINT 名称（非零溢出提示），即 C.ADD rd=x0, rs2=x2 | 7430（定义 3186–3188） |
| C.NTL.PALL | C.ADD x0, x3 | 同上 | 7431 |
| C.NTL.S1 | C.ADD x0, x4 | 同上 | 7432 |
| C.NTL.ALL | C.ADD x0, x5 | 同上 | 7433 |
| C.SLLI（rd=x0 或 shamt=0） | C.SLLI rd, shamt | HINT（RV32 63 个 / RV64 95 个码点） | 7434 |
| C.SRLI（shamt=0） | C.SRLI rd′, 0 | HINT | 7435 |
| C.SRAI（shamt=0） | C.SRAI rd′, 0 | HINT | 7436 |
| C.NOP（rd=x0 的 C.ADDI 编码点） | C.ADDI x0, imm | 文本明确"rd=x0 的编码点即 C.NOP 指令"——C.NOP 是独立指令而非别名（"C.NOP expands to nop"） | 7257、7375–7376 |
| C.ADDI16SP（C.LUI 的 rd=x2 编码点） | C.LUI x2, imm | 文本说明 rd=x2 且 imm≠0 的码点"对应 C.ADDI16SP 指令"（独立指令，共享 opcode） | 7243、7265 |
| C.EBREAK（C.ADD 的 rs2=x0 码点） | C.ADD rd, x0 且 rs1=x0 | 文本说明该码点对应 C.EBREAK，"thus can also use the CR format"（独立指令） | 7330–7331、7386–7387 |
| c.sext.w | c.addiw rd, 0 | 文本明记为伪指令（RV64），"c.sext.w is a pseudoinstruction for c.addiw rd, 0"；该名称在全文中仅此一处出现 | 7631 |
| C.SSPUSH / C.SSPOPCHK | C.SSPUSH x1 / C.SSPOPCHK x5 | 属第34章 Zicfiss（不在给定三段内），复用 Zcmop 的 C.MOP.1/C.MOP.5 编码 | 21014、21021、21024、21051、21076 |

---

**总数（按助记符去重）**

- 第28章（C = Zca+Zcf+Zcd）：42 条 = Zca 34 + Zcf 4 + Zcd 4
- 第29章新增（相对第28章）：20 条 = Zcb 12 + Zcmp 6 + Zcmt 2
- Zcmop：8 条（C.MOP.1/3/5/7/9/11/13/15）
- 第35章 Zilsd：2 条（ld、sd，32 位编码，不是 C. 压缩助记符）
- 第35章 Zclsd：4 个名称（c.ld、c.sd、c.ldsp、c.sdsp），与第28章 RV64C 的 C.LD/C.SD/C.LDSP/C.SDSP 同名 → 新增去重后 0 条
- **压缩指令助记符合计：42 + 20 + 8 = 70 条（去重；含 Zclsd 复用名称则为 70，不另计）**

**各子扩展小计**

| 子扩展 | 条数 |
| --- | --- |
| Zca | 34 |
| Zcf | 4 |
| Zcd | 4 |
| Zcb | 12 |
| Zcmp | 6 |
| Zcmt | 2 |
| Zcmop | 8 |
| Zilsd | 2（ld/sd，32 位，不计入压缩指令） |
| Zclsd | 4（RV32 版 c.ld/c.sd/c.ldsp/c.sdsp，名称与 Zca 的 RV64 版重合，不新增计数） |
| 合计（压缩） | 70 |

**RV32 / RV64 区分**

- 仅 RV32：C.JAL（7191，"C.JAL is an RV32C-only"）；C.FLW、C.FSW、C.FLWSP、C.FSWSP（7151/7174/7079/7097，"RV32FC-only"）→ 即整个 Zcf 只存在于 RV32（7589、7611–7614）；C.JAL 与 C.ADDIW 复用同一 opcode（6905–6906）。
- 仅 RV64：C.ADDIW（7261）、C.LD（7148）、C.SD（7168）、C.LDSP（7073）、C.SDSP（7094）、C.ADDW（7351）、C.SUBW（7353）（均标 "RV64C-only"）；c.zext.w（7932 "Encoding (RV64)"，需 Zba）。
- RV32 与 RV64 均有：其余 Zca 指令、C.FLD/C.FSD/C.FLDSP/C.FSDSP（"RV32DC/RV64DC-only"，7082/7100/7154/7177）、全部 Zcb、Zcmp、Zcmt、Zcmop（编码均标 "Encoding (RV32, RV64)"）。
- 仅 RV32 的成对访存扩展：Zilsd 的 ld/sd（21351 "RV32-only"，表格 21352–21354）与 Zclsd 的 c.ld/c.sd/c.ldsp/c.sdsp（21375 "RV32-only"，表格 21379–21385）；Zclsd 复用 Zca 中 RV64C 的 C.LD/C.SD/C.LDSP/C.SDSP 编码，与 Zcf 编码重叠且不兼容（21374）；配对寄存器必须是偶数号，C.LD/C.SD 只能用 x8–15（21344–21346、21390）。

## 八、位操作扩展（Zba / Zbb / Zbs / Zbc / Zbkb / Zbkc / Zbkx）

### Zba（地址生成，共8条）

| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| `add.uw` | `add.uw rd, rs1, rs2` | 把`rs1`低32位零扩展后与`rs2`做XLEN宽加法（`base + EXTZ(rs1[31:0])`）；仅RV64 | 9076, 9110, 9267, 9283 |
| `sh1add` | `sh1add rd, rs1, rs2` | `rs1`左移1位后加`rs2`；RV32/RV64 | 9085, 9111, 10232, 10243 |
| `sh1add.uw` | `sh1add.uw rd, rs1, rs2` | `rs1`低字零扩展后左移1位，再加`rs2`；仅RV64（编码为OP-32） | 9090, 9112, 10251, 10266 |
| `sh2add` | `sh2add rd, rs1, rs2` | `rs1`左移2位后加`rs2`；RV32/RV64 | 9091, 9113, 10274, 10285 |
| `sh2add.uw` | `sh2add.uw rd, rs1, rs2` | `rs1`低字零扩展后左移2位，再加`rs2`；仅RV64 | 9092, 9114, 10293, 10308 |
| `sh3add` | `sh3add rd, rs1, rs2` | `rs1`左移3位后加`rs2`；RV32/RV64 | 9093, 9115, 10316, 10327 |
| `sh3add.uw` | `sh3add.uw rd, rs1, rs2` | `rs1`低字零扩展后左移3位，再加`rs2`；仅RV64 | 9094, 9116, 10335, 10350 |
| `slli.uw` | `slli.uw rd, rs1, shamt` | 取`rs1`低字零扩展后逻辑左移立即数`shamt`；仅RV64 | 9095, 9117, 10358, 10370 |

（Zba定义节见9098，成员表见9109–9117；表中操作数写作`imm`，定义节写作`shamt`，见10358）

### Zbb（基础位操作，共24条）

| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| `andn` | `andn rd, rs1, rs2` | `rs1`与`rs2`取反后按位与（`rs1 & ~rs2`）；RV32/RV64 | 9035, 9121, 9291, 9303 |
| `clz` | `clz rd, rs` | 统计前导零个数（输入0输出XLEN）；RV32/RV64 | 9040, 9135, 9587, 9607 |
| `clzw` | `clzw rd, rs` | 统计最低字内前导零个数（输入0输出32）；仅RV64（OP-IMM-32） | 9048, 9136, 9615, 9635 |
| `cpop` | `cpop rd, rs` | 统计置位数（popcount）；RV32/RV64 | 9049, 9143, 9643, 9665 |
| `cpopw` | `cpopw rd, rs` | 统计最低字内置位数；仅RV64（OP-IMM-32） | 9050, 9144, 9673, 9689 |
| `ctz` | `ctz rd, rs` | 统计尾部零个数；RV32/RV64 | 9051, 9137, 9697, 9717 |
| `ctzw` | `ctzw rd, rs` | 统计最低字内尾部零个数；仅RV64（OP-IMM-32） | 9052, 9138, 9725, 9746 |
| `max` | `max rd, rs1, rs2` | 有符号最大值；RV32/RV64 | 9053, 9149, 9754, 9776 |
| `maxu` | `maxu rd, rs1, rs2` | 无符号最大值；RV32/RV64 | 9054, 9150, 9784, 9800 |
| `min` | `min rd, rs1, rs2` | 有符号最小值；RV32/RV64 | 9055, 9151, 9808, 9824 |
| `minu` | `minu rd, rs1, rs2` | 无符号最小值；RV32/RV64 | 9056, 9152, 9832, 9848 |
| `orc.b` | `orc.b rd, rs` | 按字节粒度做位或合并（字节非零→全1，否则全0）；RV32/RV64 | 9057, 9187, 9856, 9876 |
| `orn` | `orn rd, rs1, rs2` | `rs1`与`rs2`取反后按位或（`rs1 \| ~rs2`）；RV32/RV64 | 9058, 9122, 9884, 9895 |
| `rev8` | `rev8 rd, rs` | 寄存器字节序反转（RV32与RV64编码不同）；RV32/RV64 | 9062, 9191, 9980, 10009 |
| `rol` | `rol rd, rs1, rs2` | 按`rs2`低log2(XLEN)位循环左移；RV32/RV64 | 9063, 9171, 10041, 10056 |
| `rolw` | `rolw rd, rs1, rs2` | 对`rs1`最低字循环左移，结果符号扩展；仅RV64（OP-32） | 9064, 9172, 10065, 10081 |
| `ror` | `ror rd, rs1, rs2` | 按`rs2`低log2(XLEN)位循环右移；RV32/RV64 | 9065, 9173, 10090, 10105 |
| `rori` | `rori rd, rs1, shamt` | 按立即数`shamt`循环右移（RV32下shamt[5]=1为保留）；RV32/RV64 | 9066, 9174, 10114, 10134 |
| `roriw` | `roriw rd, rs1, shamt` | 对`rs1`最低字按立即数循环右移，结果符号扩展；仅RV64（OP-IMM-32） | 9067, 9175, 10143, 10158 |
| `rorw` | `rorw rd, rs1, rs2` | 对`rs1`最低字循环右移，结果符号扩展；仅RV64（OP-32） | 9068, 9176, 10167, 10183 |
| `sext.b` | `sext.b rd, rs` | 把最低字节符号扩展到XLEN；RV32/RV64 | 9069, 9159, 10192, 10204 |
| `sext.h` | `sext.h rd, rs` | 把最低半字符号扩展到XLEN；RV32/RV64 | 9070, 9164, 10212, 10224 |
| `xnor` | `xnor rd, rs1, rs2` | 按位同或（`~(rs1 ^ rs2)`）；RV32/RV64 | 9072, 9127, 10409, 10420 |
| `zext.h` | `zext.h rd, rs` | 把最低半字零扩展到XLEN（RV32与RV64编码不同）；RV32/RV64 | 9073, 9165, 10493, 10511 |

（Zbb定义节见9118；分节表：逻辑取反9119–9127、前导/尾部零9133–9138、计数9139–9144、最值9145–9152、符号/零扩展9153–9165、旋转9166–9176、OR Combine9181–9187、字节反转9188–9191）

### Zbs（单比特指令，共8条）

| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| `bclr` | `bclr rd, rs1, rs2` | 清除`rs1`中由`rs2`低log2(XLEN)位指定的单个比特；RV32/RV64 | 9077, 9208, 9312, 9325 |
| `bclri` | `bclri rd, rs1, shamt`（表中写作`imm`） | 按立即数索引清位（RV32下shamt[5]=1为保留）；RV32/RV64 | 9078, 9209, 9333, 9351 |
| `bext` | `bext rd, rs1, rs2` | 抽取`rs1`中由`rs2`索引的单个比特；RV32/RV64 | 9079, 9210, 9359, 9372 |
| `bexti` | `bexti rd, rs1, shamt`（表中写作`imm`） | 按立即数索引抽位；RV32/RV64 | 9080, 9211, 9380, 9398 |
| `binv` | `binv rd, rs1, rs2` | 翻转`rs1`中由`rs2`索引的单个比特；RV32/RV64 | 9081, 9212, 9406, 9419 |
| `binvi` | `binvi rd, rs1, shamt`（表中写作`imm`） | 按立即数索引翻转单比特；RV32/RV64 | 9082, 9213, 9427, 9445 |
| `bset` | `bset rd, rs1, rs2` | 置位`rs1`中由`rs2`索引的单个比特；RV32/RV64 | 9083, 9214, 9453, 9466 |
| `bseti` | `bseti rd, rs1, shamt`（表中写作`imm`） | 按立即数索引置单个比特；RV32/RV64 | 9084, 9215, 9474, 9491 |

（Zbs定义节见9204，成员表见9207–9215）

### Zbc（无进位乘法，共3条）

| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| `clmul` | `clmul rd, rs1, rs2` | 无进位乘法积的低半部分；RV32/RV64 | 9037, 9201, 9499, 9518 |
| `clmulh` | `clmulh rd, rs1, rs2` | 无进位乘法积的高半部分；RV32/RV64 | 9038, 9202, 9527, 9546 |
| `clmulr` | `clmulr rd, rs1, rs2` | 无进位乘法积的`2·XLEN−2:XLEN−1`位（用于CRC）；RV32/RV64 | 9039, 9203, 9555, 9579 |

（Zbc定义节见9192；Zbkc只含`clmul`/`clmulh`，见9245–9247）

### Zbkb（面向密码学的位操作，共16条）

| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| `rol` | `rol rd, rs1, rs2` | 循环左移；RV32/RV64 | 9220, 10041 |
| `rolw` | `rolw rd, rs1, rs2` | 字循环左移并符号扩展；仅RV64 | 9221, 10065 |
| `ror` | `ror rd, rs1, rs2` | 循环右移；RV32/RV64 | 9222, 10090 |
| `rori` | `rori rd, rs1, shamt` | 立即数循环右移；RV32/RV64 | 9223, 10114 |
| `roriw` | `roriw rd, rs1, shamt` | 字立即数循环右移并符号扩展；仅RV64 | 9224, 10143 |
| `rorw` | `rorw rd, rs1, rs2` | 字循环右移并符号扩展；仅RV64 | 9225, 10167 |
| `andn` | `andn rd, rs1, rs2` | 与反码相与；RV32/RV64 | 9226, 9291 |
| `orn` | `orn rd, rs1, rs2` | 或反码相或；RV32/RV64 | 9227, 9884 |
| `xnor` | `xnor rd, rs1, rs2` | 同或；RV32/RV64 | 9228, 10409 |
| `pack` | `pack rd, rs1, rs2` | 把`rs1`/`rs2`的低半（XLEN/2位）拼进`rd`；RV32/RV64 | 9059, 9229, 9904, 9918 |
| `packh` | `packh rd, rs1, rs2` | 把`rs1`/`rs2`的最低字节拼进`rd`低16位；RV32/RV64 | 9060, 9230, 9931, 9945 |
| `packw` | `packw rd, rs1, rs2` | 把`rs1`/`rs2`低16位拼进`rd`低32位并符号扩展；仅RV64（原文“only exists on RV64”） | 9061, 9231, 9953, 9960, 9967 |
| `brev8` | `brev8 rd, rs` | 逐字节位序反转；RV32/RV64 | 9036, 9232, 10018, 10033 |
| `rev8` | `rev8 rd, rs` | 字节序反转；RV32/RV64 | 9233, 9980 |
| `zip` | `zip rd, rs` | 位交织（源高/低半分别散布到结果的奇/偶位）；仅RV32（原文“available only on RV32”） | 9074, 9234, 10520, 10527, 10541 |
| `unzip` | `unzip rd, rs` | 位去交织（`zip`的逆操作）；仅RV32 | 9071, 9235, 10381, 10388, 10401 |

（Zbkb定义节见9216，成员表见9219–9235；表中该组未给出操作数形式，操作数取自各定义节）

### Zbkc（面向密码学的无进位乘法，共2条）

| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| `clmul` | `clmul rd, rs1, rs2` | 无进位乘法积的低半部分（GHASH用）；RV32/RV64 | 9246, 9499, 9519 |
| `clmulh` | `clmulh rd, rs1, rs2` | 无进位乘法积的高半部分；RV32/RV64 | 9247, 9527, 9547 |

（Zbkc定义节见9239；该扩展只含这两条。`clmulr`不属于Zbkc，见9579只列Zbc）

### Zbkx（交叉排列，共2条）

| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| `xperm4` | `xperm4 rd, rs1, rs2` | 以`rs1`为4位元素查找表、`rs2`为4位索引做半字节交叉排列，越界取0；RV32/RV64 | 9256, 10461, 10485 |
| `xperm8` | `xperm8 rd, rs1, rs2` | 同上，粒度为8位字节；RV32/RV64 | 9257, 10429, 10453 |

（Zbkx定义节见9248）

### 伪指令（本章明确标记为Pseudoinstruction的项）

| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| `zext.w` | `zext.w rd, rs1` → `add.uw rd, rs1, zero` | 零扩展字：伪指令展开为`add.uw`（`zero`即`x0`）；RV64 | 9268, 9269 |

本章另有两条“同编码别名”说明（不是独立助记符，仅供实现参照）：
- RV32下`pack rd, rs1, x0`即`zext.h`指令，故RV32中含`pack`的扩展也含`zext.h`（9920–9923）。
- RV64下`packw rd, rs1, x0`即`zext.h`指令，故RV64中含`packw`的扩展也含`zext.h`（9969–9972）。
- `slli.uw`等价于对`rs1`先做`zext.w`再`slli`（10371–10372）。

### 统计

- 本范围（8999–10544行）指令总数（按助记符去重）：**51条**
- 各子扩展条数小计（成员重叠，故小计之和大于51）：
  - Zba：8
  - Zbb：24
  - Zbs：8
  - Zbc：3
  - Zbkb：16
  - Zbkc：2
  - Zbkx：2
  - 小计之和：63
- `B`标准扩展＝Zba∪Zbb∪Zbs，共40条（9097）
- 伪指令：1条（`zext.w`），不计入上面的51条
- 定义节计数交叉验证：30.9.1–30.9.51共51个定义节（9263、9287、9308、9329、9355、9376、9402、9423、9449、9470、9495、9523、9551、9583、9611、9639、9669、9693、9721、9750、9780、9804、9828、9852、9880、9900、9927、9949、9976、10014、10037、10061、10086、10110、10139、10163、10188、10208、10228、10247、10270、10289、10312、10331、10354、10376、10405、10425、10457、10489、10515），与去重条数一致

### 不确定/需说明的项

1. **RV32/RV64列的归属无法从纯文本还原**：本章汇总表的表头是`RV32 RV64`两列，但抽取文本把单个`✓`统一提到助记符前（如9048行的`✓ clzw`、9074行的`✓ zip`），列位置信息丢失。因此“仅RV32”与“仅RV64”的判定依据是：①文中约定的`w`后缀与`.uw`后缀语义（9012–9020）；②定义节中的`OP-32`/`OP-IMM-32`编码标注（如9619、9677、10069、10362）；③描述中的明确语句（`packw`：9960“only exists on RV64”；`zip`/`unzip`：10388、10527“available only on RV32”）；④`Included in`表中的“(RV32)”标注（10401、10541）。单`✓`行共14条：`clzw`、`cpopw`、`ctzw`、`packw`、`rolw`、`roriw`、`rorw`、`add.uw`、`sh1add.uw`、`sh2add.uw`、`sh3add.uw`、`slli.uw`、`zip`、`unzip`。
2. **Zicond不在本章范围**：本章（第30章，8999–10544行）不含Zicond。Zicond是第11章（3364行起），指令为`czero.eqz`、`czero.nez`（3368、3369，定义节3371、3394）。按要求只列本章找到的指令，故未计入51条。
3. **`sh<N>add`模板写法不存在**：原文没有使用通配符模板，而是逐条枚举`sh1add`/`sh2add`/`sh3add`及各自的`.uw`变体（9085、9090–9094、9111–9116），故按原文枚举列出，未做任何展开。
4. **`rev8`与`zext.h`各是一条助记符对应两种编码**（RV32/RV64编码不同），不是两条指令：明确说明见10001、10508。计数时各算1条。
5. **本章提到但未在本章定义的名称**（不计入）：
   - `c.zext.h`：仅在`pack`/`packw`注解中被提及（9922、9971），属Zcb压缩扩展，本章无定义节；本规范其他位置的对应条目是`c.zext.w`（7927、7931）。
   - 基础ISA指令的“提及”：`slli`（9105、10372）、`slli/srai`与`slli/srli`（9156–9157）、`sll/srl/or`（9180）、`neg`（9179、9771）——只用于对比说明，非本章定义指令。
   - `slli`、`srli`、`srai`等出现在附录指令清单（16789–16791），与本范围无关。
6. **非指令记号**（不是助记符）：操作数`rd`/`rs`/`rs1`/`rs2`/`shamt`/`imm`/`base`，寄存器名`zero`/`x0`，以及编码标签`OP`、`OP-32`、`OP-IMM`、`OP-IMM-32`、`ADD.UW`、`BCLR/BEXT`、`MINMAX/CLMUL`、`SEXT.B/SEXT.H`、`ZEXT.H`（10196、10216、10497、10501，抽取时单词间带空格）等——它们是编码组名或抽取伪影，未计入指令表。
7. **`bset`与`bseti`原文操作数缺空格**：9453写作`bset rd, rs1,rs2`，9474写作`bseti rd, rs1,shamt`，表中已按标准形式`rd, rs1, rs2`/`rd, rs1, shamt`列出，功能与证据不受影响。

## 九、提示、条件与缓存管理扩展

### 9.1 Zihintntl（非时序局部性提示）

| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| NTL.P1 | 无（编码为 ADD x0, x0, x2） | 目标指令对最内层私有 cache 无时间局部性 | 3135–3137 |
| NTL.PALL | 无（编码为 ADD x0, x0, x3） | 对任何私有 cache 级无时间局部性 | 3138–3139 |
| NTL.S1 | 无（编码为 ADD x0, x0, x4） | 对最内层共享 cache 无时间局部性 | 3140–3142 |
| NTL.ALL | 无（编码为 ADD x0, x0, x5） | 对任何 cache 级无时间局部性 | 3143–3144 |
| C.NTL.P1 | 无（编码为 C.ADD x0, x2） | 压缩形式 NTL.P1 HINT,需 C 或 Zca | 3186–3187 |
| C.NTL.PALL | 无（编码为 C.ADD x0, x3） | 压缩形式 NTL.PALL HINT | 3187 |
| C.NTL.S1 | 无（编码为 C.ADD x0, x4） | 压缩形式 NTL.S1 HINT | 3187 |
| C.NTL.ALL | 无（编码为 C.ADD x0, x5） | 压缩形式 NTL.ALL HINT | 3188 |

注：文本正文写作大写 `NTL.P1`/`C.NTL.P1`,未出现小写 `ntl.p1` 形式。**小计：8 条 HINT（4 条基础 + 4 条压缩）。**

### 9.2 Zihintpause（自旋等待提示）

| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| PAUSE | PAUSE | 提示降低本 hart 指令退休速率,编码为 pred=W、succ=0、fm=0、rd=x0、rs1=x0 的 FENCE | 3256, 3271 |

**小计：1 条**（与第 2 章 HINT 表 2473 行的 PAUSE 为同一条指令,已去重）。

### 9.3 Zimop / Zcmop（May-Be-Operation）

| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| `MOP.R.n` | MOP.R.n rd, rs1 | 初定义仅写 0 到 x[rd],n 为 0–31 的整数（共 32 条） | 3301–3303, 3315–3317 |
| `MOP.RR.n` | MOP.RR.n rd, rs1, rs2 | 初定义仅写 0 到 x[rd],n 为 0–7 的整数（共 8 条） | 3307–3309, 3315–3317 |
| `C.MOP.n` | C.MOP.n（无形参） | 16 位压缩 MOP,不写任何寄存器,可被重定义读 x[n],n 为 1–15 的**奇数**（共 8 条） | 3333–3337, 3347–3354 |

Zimop 编码空间共 40 个 MOP（3289）；Zcmop 定义 8 条 16 位 MOP,编码在 C.LUI x n, 0 的保留空间,依赖 Zca（3333–3338）。表 10 列出 C.MOP.1/3/5/7/9/11/13/15 及编码与“可重定义为读取的寄存器 x1/x3/x5/x7/x9/x11/x13/x15”（3345–3354）。按文本原样保留 n 模板,未展开。**小计：模板 3 条（展开为 32+8+8=48 条）。**

### 9.4 Zicond（整数条件运算）

| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| czero.eqz | czero.eqz rd, rs1, rs2 | rs2==0 时 rd=0,否则 rd=rs1 | 3368, 3371–3382 |
| czero.nez | czero.nez rd, rs1, rs2 | rs2!=0 时 rd=0,否则 rd=rs1 | 3369, 3394–3405 |

**小计：2 条。**（用法示例中出现的 add/sub/or/xor/and 属 RV32I 已有指令,3424–3476,不重复计数。）

### 9.5 CMO（缓存管理：Zicbom / Zicboz / Zicbop）

| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| cbo.clean | cbo.clean offset(base) | 对 cache 块执行 clean,偏移须为 0 或省略 | 5217, 5263, 5269–5272 |
| cbo.flush | cbo.flush offset(base) | 对 cache 块执行 flush（clean+invalidate） | 5218, 5282, 5291 |
| cbo.inval | cbo.inval offset(base) | 对 cache 块执行 invalidate（可按 CSR 编程改为 flush） | 5219, 5301, 5307 |
| cbo.zero | cbo.zero offset(base) | 将 cache 块全部字节写 0 | 5237, 5323, 5332 |
| prefetch.i | prefetch.i offset(base) | 提示该 cache 块将被取指访问（HINT） | 5255, 5343, 5349 |
| prefetch.r | prefetch.r offset(base) | 提示该 cache 块将被数据读访问（HINT） | 5256, 5358, 5367 |
| prefetch.w | prefetch.w offset(base) | 提示该 cache 块将被数据写访问（HINT） | 5257, 5376, 5382 |

扩展归属：Zicbom = cbo.clean/cbo.flush/cbo.inval（4783–4784、5215–5219）；Zicboz = cbo.zero（4785、5235–5237）；Zicbop = prefetch.r/prefetch.w/prefetch.i（4786–4787、5253–5257）。prefetch 系列编码为 rd=0b00000 的 ORI,imm[4:0] 须为 0（5246、5250）。**小计：7 条。**

## 十、V 向量扩展（第31章）

> 向量指令按规范原文章节归类，"说明"列取自规范原文的汇编清单注释。

### 31.3.4.3. Vector Tail Agnostic and Vector Mask Agnostic vta and vma
（共1条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vsetvli` | `t0, a0, e32, m4, ta, ma` | Tail agnostic, mask agnostic | 304 |

### 31.6. Configuration-Setting Instructions (vsetvli/vsetivli/vsetvl)
（共3条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vsetvli` | `rd, rs1, vtypei` | rd = new vl, rs1 = AVL, vtypei = new vtype setting | 317 |
| `vsetivli` | `rd, uimm, vtypei` | rd = new vl, uimm = AVL, vtypei = new vtype | 317 |
| `vsetvl` | `rd, rs1, rs2` | rd = new vl, rs1 = AVL, rs2 = new vtype value | 317 |

### 31.6.1. vtype encoding
（共1条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vsetvli` | `t0, a0, e8, m1, ta, ma` | SEW= 8, LMUL=1 | 318 |

### 31.7.4. Vector Unit-Stride Instructions
（共10条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vle8.v` | `vd, (rs1), vm` | 8-bit unit-stride load | 324 |
| `vle16.v` | `vd, (rs1), vm` | 16-bit unit-stride load | 324 |
| `vle32.v` | `vd, (rs1), vm` | 32-bit unit-stride load | 325 |
| `vle64.v` | `vd, (rs1), vm` | 64-bit unit-stride load | 325 |
| `vse8.v` | `vs3, (rs1), vm` | 8-bit unit-stride store | 325 |
| `vse16.v` | `vs3, (rs1), vm` | 16-bit unit-stride store | 325 |
| `vse32.v` | `vs3, (rs1), vm` | 32-bit unit-stride store | 325 |
| `vse64.v` | `vs3, (rs1), vm` | 64-bit unit-stride store | 325 |
| `vlm.v` | `vd, (rs1)` | Load byte vector of length ceil(vl/8) | 325 |
| `vsm.v` | `vs3, (rs1)` | Store byte vector of length ceil(vl/8) | 325 |

### 31.7.5. Vector Constant-Stride Instructions
（共8条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vlse8.v` | `vd, (rs1), rs2, vm` | 8-bit constant-stride load | 325 |
| `vlse16.v` | `vd, (rs1), rs2, vm` | 16-bit constant-stride load | 325 |
| `vlse32.v` | `vd, (rs1), rs2, vm` | 32-bit constant-stride load | 325 |
| `vlse64.v` | `vd, (rs1), rs2, vm` | 64-bit constant-stride load | 325 |
| `vsse8.v` | `vs3, (rs1), rs2, vm` | 8-bit constant-stride store | 325 |
| `vsse16.v` | `vs3, (rs1), rs2, vm` | 16-bit constant-stride store | 325 |
| `vsse32.v` | `vs3, (rs1), rs2, vm` | 32-bit constant-stride store | 326 |
| `vsse64.v` | `vs3, (rs1), rs2, vm` | 64-bit constant-stride store | 326 |

### 31.7.6. Vector Indexed Instructions
（共16条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vluxei8.v` | `vd, (rs1), vs2, vm` | unordered 8-bit indexed load of SEW data | 326 |
| `vluxei16.v` | `vd, (rs1), vs2, vm` | unordered 16-bit indexed load of SEW data | 326 |
| `vluxei32.v` | `vd, (rs1), vs2, vm` | unordered 32-bit indexed load of SEW data | 326 |
| `vluxei64.v` | `vd, (rs1), vs2, vm` | unordered 64-bit indexed load of SEW data | 326 |
| `vloxei8.v` | `vd, (rs1), vs2, vm` | ordered 8-bit indexed load of SEW data | 326 |
| `vloxei16.v` | `vd, (rs1), vs2, vm` | ordered 16-bit indexed load of SEW data | 326 |
| `vloxei32.v` | `vd, (rs1), vs2, vm` | ordered 32-bit indexed load of SEW data | 326 |
| `vloxei64.v` | `vd, (rs1), vs2, vm` | ordered 64-bit indexed load of SEW data | 326 |
| `vsuxei8.v` | `vs3, (rs1), vs2, vm` | unordered 8-bit indexed store of SEW data | 326 |
| `vsuxei16.v` | `vs3, (rs1), vs2, vm` | unordered 16-bit indexed store of SEW data | 326 |
| `vsuxei32.v` | `vs3, (rs1), vs2, vm` | unordered 32-bit indexed store of SEW data | 326 |
| `vsuxei64.v` | `vs3, (rs1), vs2, vm` | unordered 64-bit indexed store of SEW data | 326 |
| `vsoxei8.v` | `vs3, (rs1), vs2, vm` | ordered 8-bit indexed store of SEW data | 327 |
| `vsoxei16.v` | `vs3, (rs1), vs2, vm` | ordered 16-bit indexed store of SEW data | 327 |
| `vsoxei32.v` | `vs3, (rs1), vs2, vm` | ordered 32-bit indexed store of SEW data | 327 |
| `vsoxei64.v` | `vs3, (rs1), vs2, vm` | ordered 64-bit indexed store of SEW data | 327 |

### 31.7.7. Unit-stride Fault-Only-First Loads
（共7条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vle8ff.v` | `vd, (rs1), vm` | 8-bit unit-stride fault-only-first load | 327 |
| `vle16ff.v` | `vd, (rs1), vm` | 16-bit unit-stride fault-only-first load | 327 |
| `vle32ff.v` | `vd, (rs1), vm` | 32-bit unit-stride fault-only-first load | 327 |
| `vle64ff.v` | `vd, (rs1), vm` | 64-bit unit-stride fault-only-first load | 327 |
| `vsetvli` | `a1, x0, e8, m8, ta, ma` | Vector of bytes of maximum length | 328 |
| `vmseq.vi` | `v0, v8, 0` | Set v0[i] where v8[i] = 0 | 328 |
| `vfirst.m` | `a2, v0` | Find first set bit | 328 |

### 31.7.8.1. Vector Unit-Stride Segment Loads and Stores
（共8条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vlseg<nf>e<eew>.v` | `vd, (rs1), vm` | Unit-stride segment load template | 329 |
| `vsseg<nf>e<eew>.v` | `vs3, (rs1), vm` | Unit-stride segment store template | 329 |
| `vlseg8e8.v` | `vd, (rs1), vm` | Load eight vector registers with eight byte | 330 |
| `vsseg3e32.v` | `vs3, (rs1), vm` | Store packed vector of 3*4-byte segments from | 330 |
| `vsetvli` | `a1, t0, e8, m1, ta, ma` | — | 330 |
| `vlseg3e8.v` | `v8, (a0), vm` | — | 330 |
| `vlseg2e32.v` | `v8, (a0), vm` | — | 330 |
| `vlseg<nf>e<eew>ff.v` | `vd, (rs1), vm` | Unit-stride fault-only-first segment | 330 |

### 31.7.8.2. Vector Constant-Stride Segment Loads and Stores
（共5条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vlsseg<nf>e<eew>.v` | `vd, (rs1), rs2, vm` | Constant-stride segment loads | 331 |
| `vssseg<nf>e<eew>.v` | `vs3, (rs1), rs2, vm` | Constant-stride segment stores | 331 |
| `vsetvli` | `a1, t0, e8, m1, ta, ma` | — | 331 |
| `vlsseg3e8.v` | `v4, (x5), x6` | Load bytes at addresses x5+i*x6 into v4[i], | 331 |
| `vssseg2e32.v` | `v2, (x5), x6` | Store words from v2[i] to address x5+i*x6 | 331 |

### 31.7.8.3. Vector Indexed Segment Loads and Stores
（共7条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vluxseg<nf>ei<eew>.v` | `vd, (rs1), vs2, vm` | Indexed-unordered segment loads | 331 |
| `vloxseg<nf>ei<eew>.v` | `vd, (rs1), vs2, vm` | Indexed-ordered segment loads | 331 |
| `vsuxseg<nf>ei<eew>.v` | `vs3, (rs1), vs2, vm` | Indexed-unordered segment stores | 331 |
| `vsoxseg<nf>ei<eew>.v` | `vs3, (rs1), vs2, vm` | Indexed-ordered segment stores | 331 |
| `vsetvli` | `a1, t0, e8, m1, ta, ma` | — | 331 |
| `vluxseg3ei8.v` | `v4, (x5), v3` | Load bytes at addresses x5+v3[i] into v4[i], | 331 |
| `vsuxseg2ei32.v` | `v2, (x5), v5` | Store words from v2[i] to address x5+v5[i] | 331 |

### 31.7.9. Vector Load/Store Whole Register Instructions
（共26条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vl1r.v` | `v3, (a0)` | Pseudoinstruction equal to vl1re8.v | 333 |
| `vl1re8.v` | `v3, (a0)` | Load v3 with VLEN/8 bytes held at address in a0 | 333 |
| `vl1re16.v` | `v3, (a0)` | Load v3 with VLEN/16 halfwords held at address in a0 | 333 |
| `vl1re32.v` | `v3, (a0)` | Load v3 with VLEN/32 words held at address in a0 | 333 |
| `vl1re64.v` | `v3, (a0)` | Load v3 with VLEN/64 doublewords held at address in a0 | 333 |
| `vl2r.v` | `v2, (a0)` | Pseudoinstruction equal to vl2re8.v | 333 |
| `vl2re8.v` | `v2, (a0)` | Load v2-v3 with 2*VLEN/8 bytes from address in a0 | 333 |
| `vl2re16.v` | `v2, (a0)` | Load v2-v3 with 2*VLEN/16 halfwords held at address in | 333 |
| `vl2re32.v` | `v2, (a0)` | Load v2-v3 with 2*VLEN/32 words held at address in a0 | 333 |
| `vl2re64.v` | `v2, (a0)` | Load v2-v3 with 2*VLEN/64 doublewords held at address | 333 |
| `vl4r.v` | `v4, (a0)` | Pseudoinstruction equal to vl4re8.v | 333 |
| `vl4re8.v` | `v4, (a0)` | Load v4-v7 with 4*VLEN/8 bytes from address in a0 | 333 |
| `vl4re16.v` | `v4, (a0)` | — | 333 |
| `vl4re32.v` | `v4, (a0)` | — | 333 |
| `vl4re64.v` | `v4, (a0)` | — | 333 |
| `vl8r.v` | `v8, (a0)` | Pseudoinstruction equal to vl8re8.v | 333 |
| `vl8re8.v` | `v8, (a0)` | Load v8-v15 with 8*VLEN/8 bytes from address in a0 | 333 |
| `vl8re16.v` | `v8, (a0)` | — | 333 |
| `vl8re32.v` | `v8, (a0)` | — | 333 |
| `vl8re64.v` | `v8, (a0)` | — | 333 |
| `vs1r.v` | `v3, (a1)` | Store v3 to address in a1 | 333 |
| `vs2r.v` | `v2, (a1)` | Store v2-v3 to address in a1 | 333 |
| `vs4r.v` | `v4, (a1)` | Store v4-v7 to address in a1 | 333 |
| `vs8r.v` | `v8, (a1)` | Store v8-v15 to address in a1 | 334 |
| `vsetvli` | `t1, x0, e8, m8, ta, ma` | Maximum VLMAX | 334 |
| `vlm.v` | `v0, (a0)` | Load mask register | 334 |

### 31.11.1. Vector Single-Width Integer Add and Subtract
（共7条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vadd.vv` | `vd, vs2, vs1, vm` | Vector-vector | 339 |
| `vadd.vx` | `vd, vs2, rs1, vm` | vector-scalar | 339 |
| `vadd.vi` | `vd, vs2, imm, vm` | vector-immediate | 339 |
| `vsub.vv` | `vd, vs2, vs1, vm` | Vector-vector | 339 |
| `vsub.vx` | `vd, vs2, rs1, vm` | vector-scalar | 339 |
| `vrsub.vx` | `vd, vs2, rs1, vm` | vd[i] = x[rs1] - vs2[i] | 339 |
| `vrsub.vi` | `vd, vs2, imm, vm` | vd[i] = imm - vs2[i] | 339 |

### 31.11.2. Vector Widening Integer Add/Subtract
（共16条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vwaddu.vv` | `vd, vs2, vs1, vm` | vector-vector | 339 |
| `vwaddu.vx` | `vd, vs2, rs1, vm` | vector-scalar | 339 |
| `vwsubu.vv` | `vd, vs2, vs1, vm` | vector-vector | 339 |
| `vwsubu.vx` | `vd, vs2, rs1, vm` | vector-scalar | 339 |
| `vwadd.vv` | `vd, vs2, vs1, vm` | vector-vector | 339 |
| `vwadd.vx` | `vd, vs2, rs1, vm` | vector-scalar | 339 |
| `vwsub.vv` | `vd, vs2, vs1, vm` | vector-vector | 339 |
| `vwsub.vx` | `vd, vs2, rs1, vm` | vector-scalar | 339 |
| `vwaddu.wv` | `vd, vs2, vs1, vm` | vector-vector | 339 |
| `vwaddu.wx` | `vd, vs2, rs1, vm` | vector-scalar | 339 |
| `vwsubu.wv` | `vd, vs2, vs1, vm` | vector-vector | 340 |
| `vwsubu.wx` | `vd, vs2, rs1, vm` | vector-scalar | 340 |
| `vwadd.wv` | `vd, vs2, vs1, vm` | vector-vector | 340 |
| `vwadd.wx` | `vd, vs2, rs1, vm` | vector-scalar | 340 |
| `vwsub.wv` | `vd, vs2, vs1, vm` | vector-vector | 340 |
| `vwsub.wx` | `vd, vs2, rs1, vm` | vector-scalar | 340 |

### 31.11.3. Vector Integer Extension
（共6条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vzext.vf2` | `vd, vs2, vm` | Zero-extend SEW/2 source to SEW destination | 340 |
| `vsext.vf2` | `vd, vs2, vm` | Sign-extend SEW/2 source to SEW destination | 340 |
| `vzext.vf4` | `vd, vs2, vm` | Zero-extend SEW/4 source to SEW destination | 340 |
| `vsext.vf4` | `vd, vs2, vm` | Sign-extend SEW/4 source to SEW destination | 340 |
| `vzext.vf8` | `vd, vs2, vm` | Zero-extend SEW/8 source to SEW destination | 340 |
| `vsext.vf8` | `vd, vs2, vm` | Sign-extend SEW/8 source to SEW destination | 340 |

### 31.11.4. Vector Integer Add-with-Carry / Subtract-with-Borrow Instructions
（共16条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vadc.vvm` | `vd, vs2, vs1, v0` | Vector-vector | 341 |
| `vadc.vxm` | `vd, vs2, rs1, v0` | Vector-scalar | 341 |
| `vadc.vim` | `vd, vs2, imm, v0` | Vector-immediate | 341 |
| `vmadc.vvm` | `vd, vs2, vs1, v0` | Vector-vector | 341 |
| `vmadc.vxm` | `vd, vs2, rs1, v0` | Vector-scalar | 341 |
| `vmadc.vim` | `vd, vs2, imm, v0` | Vector-immediate | 341 |
| `vmadc.vv` | `vd, vs2, vs1` | Vector-vector, no carry-in | 341 |
| `vmadc.vx` | `vd, vs2, rs1` | Vector-scalar, no carry-in | 341 |
| `vmadc.vi` | `vd, vs2, imm` | Vector-immediate, no carry-in | 341 |
| `vmmv.m` | `v0, v1` | Move temp carry into v0 for next word | 341 |
| `vsbc.vvm` | `vd, vs2, vs1, v0` | Vector-vector | 342 |
| `vsbc.vxm` | `vd, vs2, rs1, v0` | Vector-scalar | 342 |
| `vmsbc.vvm` | `vd, vs2, vs1, v0` | Vector-vector | 342 |
| `vmsbc.vxm` | `vd, vs2, rs1, v0` | Vector-scalar | 342 |
| `vmsbc.vv` | `vd, vs2, vs1` | Vector-vector, no borrow-in | 342 |
| `vmsbc.vx` | `vd, vs2, rs1` | Vector-scalar, no borrow-in | 342 |

### 31.11.5. Vector Bitwise Logical Instructions
（共9条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vand.vv` | `vd, vs2, vs1, vm` | Vector-vector | 342 |
| `vand.vx` | `vd, vs2, rs1, vm` | vector-scalar | 342 |
| `vand.vi` | `vd, vs2, imm, vm` | vector-immediate | 342 |
| `vor.vv` | `vd, vs2, vs1, vm` | Vector-vector | 342 |
| `vor.vx` | `vd, vs2, rs1, vm` | vector-scalar | 342 |
| `vor.vi` | `vd, vs2, imm, vm` | vector-immediate | 342 |
| `vxor.vv` | `vd, vs2, vs1, vm` | Vector-vector | 342 |
| `vxor.vx` | `vd, vs2, rs1, vm` | vector-scalar | 342 |
| `vxor.vi` | `vd, vs2, imm, vm` | vector-immediate | 342 |

### 31.11.6. Vector Single-Width Shift Instructions
（共9条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vsll.vv` | `vd, vs2, vs1, vm` | Vector-vector | 343 |
| `vsll.vx` | `vd, vs2, rs1, vm` | vector-scalar | 343 |
| `vsll.vi` | `vd, vs2, uimm, vm` | vector-immediate | 343 |
| `vsrl.vv` | `vd, vs2, vs1, vm` | Vector-vector | 343 |
| `vsrl.vx` | `vd, vs2, rs1, vm` | vector-scalar | 343 |
| `vsrl.vi` | `vd, vs2, uimm, vm` | vector-immediate | 343 |
| `vsra.vv` | `vd, vs2, vs1, vm` | Vector-vector | 343 |
| `vsra.vx` | `vd, vs2, rs1, vm` | vector-scalar | 343 |
| `vsra.vi` | `vd, vs2, uimm, vm` | vector-immediate | 343 |

### 31.11.7. Vector Narrowing Integer Right Shift Instructions
（共6条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vnsrl.wv` | `vd, vs2, vs1, vm` | vector-vector | 343 |
| `vnsrl.wx` | `vd, vs2, rs1, vm` | vector-scalar | 343 |
| `vnsrl.wi` | `vd, vs2, uimm, vm` | vector-immediate | 343 |
| `vnsra.wv` | `vd, vs2, vs1, vm` | vector-vector | 343 |
| `vnsra.wx` | `vd, vs2, rs1, vm` | vector-scalar | 343 |
| `vnsra.wi` | `vd, vs2, uimm, vm` | vector-immediate | 343 |

### 31.11.8. Vector Integer Compare Instructions
（共20条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vmseq.vv` | `vd, vs2, vs1, vm` | Vector-vector | 344 |
| `vmseq.vx` | `vd, vs2, rs1, vm` | vector-scalar | 344 |
| `vmseq.vi` | `vd, vs2, imm, vm` | vector-immediate | 344 |
| `vmsne.vv` | `vd, vs2, vs1, vm` | Vector-vector | 344 |
| `vmsne.vx` | `vd, vs2, rs1, vm` | vector-scalar | 344 |
| `vmsne.vi` | `vd, vs2, imm, vm` | vector-immediate | 344 |
| `vmsltu.vv` | `vd, vs2, vs1, vm` | Vector-vector | 344 |
| `vmsltu.vx` | `vd, vs2, rs1, vm` | Vector-scalar | 344 |
| `vmslt.vv` | `vd, vs2, vs1, vm` | Vector-vector | 344 |
| `vmslt.vx` | `vd, vs2, rs1, vm` | vector-scalar | 344 |
| `vmsleu.vv` | `vd, vs2, vs1, vm` | Vector-vector | 344 |
| `vmsleu.vx` | `vd, vs2, rs1, vm` | vector-scalar | 344 |
| `vmsleu.vi` | `vd, vs2, imm, vm` | Vector-immediate | 344 |
| `vmsle.vv` | `vd, vs2, vs1, vm` | Vector-vector | 344 |
| `vmsle.vx` | `vd, vs2, rs1, vm` | vector-scalar | 344 |
| `vmsle.vi` | `vd, vs2, imm, vm` | vector-immediate | 344 |
| `vmsgtu.vx` | `vd, vs2, rs1, vm` | Vector-scalar | 344 |
| `vmsgtu.vi` | `vd, vs2, imm, vm` | Vector-immediate | 344 |
| `vmsgt.vx` | `vd, vs2, rs1, vm` | Vector-scalar | 344 |
| `vmsgt.vi` | `vd, vs2, imm, vm` | Vector-immediate | 344 |

### 31.11.9. Vector Integer Min/Max Instructions
（共8条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vminu.vv` | `vd, vs2, vs1, vm` | Vector-vector | 347 |
| `vminu.vx` | `vd, vs2, rs1, vm` | vector-scalar | 347 |
| `vmin.vv` | `vd, vs2, vs1, vm` | Vector-vector | 347 |
| `vmin.vx` | `vd, vs2, rs1, vm` | vector-scalar | 347 |
| `vmaxu.vv` | `vd, vs2, vs1, vm` | Vector-vector | 347 |
| `vmaxu.vx` | `vd, vs2, rs1, vm` | vector-scalar | 347 |
| `vmax.vv` | `vd, vs2, vs1, vm` | Vector-vector | 347 |
| `vmax.vx` | `vd, vs2, rs1, vm` | vector-scalar | 347 |

### 31.11.10. Vector Single-Width Integer Multiply Instructions
（共8条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vmul.vv` | `vd, vs2, vs1, vm` | Vector-vector | 347 |
| `vmul.vx` | `vd, vs2, rs1, vm` | vector-scalar | 347 |
| `vmulh.vv` | `vd, vs2, vs1, vm` | Vector-vector | 347 |
| `vmulh.vx` | `vd, vs2, rs1, vm` | vector-scalar | 347 |
| `vmulhu.vv` | `vd, vs2, vs1, vm` | Vector-vector | 347 |
| `vmulhu.vx` | `vd, vs2, rs1, vm` | vector-scalar | 347 |
| `vmulhsu.vv` | `vd, vs2, vs1, vm` | Vector-vector | 347 |
| `vmulhsu.vx` | `vd, vs2, rs1, vm` | vector-scalar | 347 |

### 31.11.11. Vector Integer Divide Instructions
（共8条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vdivu.vv` | `vd, vs2, vs1, vm` | Vector-vector | 348 |
| `vdivu.vx` | `vd, vs2, rs1, vm` | vector-scalar | 348 |
| `vdiv.vv` | `vd, vs2, vs1, vm` | Vector-vector | 348 |
| `vdiv.vx` | `vd, vs2, rs1, vm` | vector-scalar | 348 |
| `vremu.vv` | `vd, vs2, vs1, vm` | Vector-vector | 348 |
| `vremu.vx` | `vd, vs2, rs1, vm` | vector-scalar | 348 |
| `vrem.vv` | `vd, vs2, vs1, vm` | Vector-vector | 348 |
| `vrem.vx` | `vd, vs2, rs1, vm` | vector-scalar | 348 |

### 31.11.12. Vector Widening Integer Multiply Instructions
（共6条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vwmul.vv` | `vd, vs2, vs1, vm` | vector-vector | 348 |
| `vwmul.vx` | `vd, vs2, rs1, vm` | vector-scalar | 348 |
| `vwmulu.vv` | `vd, vs2, vs1, vm` | vector-vector | 348 |
| `vwmulu.vx` | `vd, vs2, rs1, vm` | vector-scalar | 348 |
| `vwmulsu.vv` | `vd, vs2, vs1, vm` | vector-vector | 348 |
| `vwmulsu.vx` | `vd, vs2, rs1, vm` | vector-scalar | 348 |

### 31.11.13. Vector Single-Width Integer Multiply-Add Instructions
（共8条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vmacc.vv` | `vd, vs1, vs2, vm` | vd[i] = (vs1[i] * vs2[i]) + vd[i] | 349 |
| `vmacc.vx` | `vd, rs1, vs2, vm` | vd[i] = (x[rs1] * vs2[i]) + vd[i] | 349 |
| `vnmsac.vv` | `vd, vs1, vs2, vm` | vd[i] = -(vs1[i] * vs2[i]) + vd[i] | 349 |
| `vnmsac.vx` | `vd, rs1, vs2, vm` | vd[i] = -(x[rs1] * vs2[i]) + vd[i] | 349 |
| `vmadd.vv` | `vd, vs1, vs2, vm` | vd[i] = (vs1[i] * vd[i]) + vs2[i] | 349 |
| `vmadd.vx` | `vd, rs1, vs2, vm` | vd[i] = (x[rs1] * vd[i]) + vs2[i] | 349 |
| `vnmsub.vv` | `vd, vs1, vs2, vm` | vd[i] = -(vs1[i] * vd[i]) + vs2[i] | 349 |
| `vnmsub.vx` | `vd, rs1, vs2, vm` | vd[i] = -(x[rs1] * vd[i]) + vs2[i] | 349 |

### 31.11.14. Vector Widening Integer Multiply-Add Instructions
（共7条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vwmaccu.vv` | `vd, vs1, vs2, vm` | vd[i] = (vs1[i] * vs2[i]) + vd[i] | 349 |
| `vwmaccu.vx` | `vd, rs1, vs2, vm` | vd[i] = (x[rs1] * vs2[i]) + vd[i] | 349 |
| `vwmacc.vv` | `vd, vs1, vs2, vm` | vd[i] = (vs1[i] * vs2[i]) + vd[i] | 349 |
| `vwmacc.vx` | `vd, rs1, vs2, vm` | vd[i] = (x[rs1] * vs2[i]) + vd[i] | 349 |
| `vwmaccsu.vv` | `vd, vs1, vs2, vm` | vd[i] = (signed(vs1[i]) * unsigned(vs2[i])) + | 349 |
| `vwmaccsu.vx` | `vd, rs1, vs2, vm` | vd[i] = (signed(x[rs1]) * unsigned(vs2[i])) + | 349 |
| `vwmaccus.vx` | `vd, rs1, vs2, vm` | vd[i] = (unsigned(x[rs1]) * signed(vs2[i])) + | 349 |

### 31.11.15. Vector Integer Merge Instructions
（共3条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vmerge.vvm` | `vd, vs2, vs1, v0` | vd[i] = v0.mask[i] ? vs1[i] : vs2[i] | 350 |
| `vmerge.vxm` | `vd, vs2, rs1, v0` | vd[i] = v0.mask[i] ? x[rs1] : vs2[i] | 350 |
| `vmerge.vim` | `vd, vs2, imm, v0` | vd[i] = v0.mask[i] ? imm : vs2[i] | 350 |

### 31.11.16. Vector Integer Move Instructions
（共4条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vmv.v.v` | `vd, vs1` | vd[i] = vs1[i] | 350 |
| `vmv.v.x` | `vd, rs1` | vd[i] = x[rs1] | 350 |
| `vmv.v.i` | `vd, imm` | vd[i] = imm | 350 |
| `vmerge.vim` | `vd, vd, 1, v0.` | — | 350 |

### 31.12.1. Vector Single-Width Saturating Add and Subtract
（共10条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vsaddu.vv` | `vd, vs2, vs1, vm` | Vector-vector | 351 |
| `vsaddu.vx` | `vd, vs2, rs1, vm` | vector-scalar | 351 |
| `vsaddu.vi` | `vd, vs2, imm, vm` | vector-immediate | 351 |
| `vsadd.vv` | `vd, vs2, vs1, vm` | Vector-vector | 351 |
| `vsadd.vx` | `vd, vs2, rs1, vm` | vector-scalar | 351 |
| `vsadd.vi` | `vd, vs2, imm, vm` | vector-immediate | 351 |
| `vssubu.vv` | `vd, vs2, vs1, vm` | Vector-vector | 351 |
| `vssubu.vx` | `vd, vs2, rs1, vm` | vector-scalar | 351 |
| `vssub.vv` | `vd, vs2, vs1, vm` | Vector-vector | 351 |
| `vssub.vx` | `vd, vs2, rs1, vm` | vector-scalar | 351 |

### 31.12.2. Vector Single-Width Averaging Add and Subtract
（共8条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vaaddu.vv` | `vd, vs2, vs1, vm` | roundoff_unsigned(vs2[i] + vs1[i], 1) | 352 |
| `vaaddu.vx` | `vd, vs2, rs1, vm` | roundoff_unsigned(vs2[i] + x[rs1], 1) | 352 |
| `vaadd.vv` | `vd, vs2, vs1, vm` | roundoff_signed(vs2[i] + vs1[i], 1) | 352 |
| `vaadd.vx` | `vd, vs2, rs1, vm` | roundoff_signed(vs2[i] + x[rs1], 1) | 352 |
| `vasubu.vv` | `vd, vs2, vs1, vm` | roundoff_unsigned(vs2[i] - vs1[i], 1) | 352 |
| `vasubu.vx` | `vd, vs2, rs1, vm` | roundoff_unsigned(vs2[i] - x[rs1], 1) | 352 |
| `vasub.vv` | `vd, vs2, vs1, vm` | roundoff_signed(vs2[i] - vs1[i], 1) | 352 |
| `vasub.vx` | `vd, vs2, rs1, vm` | roundoff_signed(vs2[i] - x[rs1], 1) | 352 |

### 31.12.3. Vector Single-Width Fractional Multiply with Rounding and Saturation
（共2条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vsmul.vv` | `vd, vs2, vs1, vm` | vd[i] = clip(roundoff_signed(vs2[i]*vs1[i], SEW- | 352 |
| `vsmul.vx` | `vd, vs2, rs1, vm` | vd[i] = clip(roundoff_signed(vs2[i]*x[rs1], SEW- | 352 |

### 31.12.4. Vector Single-Width Scaling Shift Instructions
（共6条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vssrl.vv` | `vd, vs2, vs1, vm` | vd[i] = roundoff_unsigned(vs2[i], vs1[i]) | 353 |
| `vssrl.vx` | `vd, vs2, rs1, vm` | vd[i] = roundoff_unsigned(vs2[i], x[rs1]) | 353 |
| `vssrl.vi` | `vd, vs2, uimm, vm` | vd[i] = roundoff_unsigned(vs2[i], uimm) | 353 |
| `vssra.vv` | `vd, vs2, vs1, vm` | vd[i] = roundoff_signed(vs2[i],vs1[i]) | 353 |
| `vssra.vx` | `vd, vs2, rs1, vm` | vd[i] = roundoff_signed(vs2[i], x[rs1]) | 353 |
| `vssra.vi` | `vd, vs2, uimm, vm` | vd[i] = roundoff_signed(vs2[i], uimm) | 353 |

### 31.12.5. Vector Narrowing Fixed-Point Clip Instructions
（共6条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vnclipu.wv` | `vd, vs2, vs1, vm` | vd[i] = clip(roundoff_unsigned(vs2[i], vs1[i])) | 353 |
| `vnclipu.wx` | `vd, vs2, rs1, vm` | vd[i] = clip(roundoff_unsigned(vs2[i], x[rs1])) | 353 |
| `vnclipu.wi` | `vd, vs2, uimm, vm` | vd[i] = clip(roundoff_unsigned(vs2[i], uimm)) | 353 |
| `vnclip.wv` | `vd, vs2, vs1, vm` | vd[i] = clip(roundoff_signed(vs2[i], vs1[i])) | 353 |
| `vnclip.wx` | `vd, vs2, rs1, vm` | vd[i] = clip(roundoff_signed(vs2[i], x[rs1])) | 353 |
| `vnclip.wi` | `vd, vs2, uimm, vm` | vd[i] = clip(roundoff_signed(vs2[i], uimm)) | 353 |

### 31.13.2. Vector Single-Width Floating-Point Add/Subtract Instructions
（共5条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vfadd.vv` | `vd, vs2, vs1, vm` | Vector-vector | 354 |
| `vfadd.vf` | `vd, vs2, rs1, vm` | vector-scalar | 354 |
| `vfsub.vv` | `vd, vs2, vs1, vm` | Vector-vector | 354 |
| `vfsub.vf` | `vd, vs2, rs1, vm` | Vector-scalar vd[i] = vs2[i] - f[rs1] | 354 |
| `vfrsub.vf` | `vd, vs2, rs1, vm` | Scalar-vector vd[i] = f[rs1] - vs2[i] | 354 |

### 31.13.3. Vector Widening Floating-Point Add/Subtract Instructions
（共8条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vfwadd.vv` | `vd, vs2, vs1, vm` | vector-vector | 355 |
| `vfwadd.vf` | `vd, vs2, rs1, vm` | vector-scalar | 355 |
| `vfwsub.vv` | `vd, vs2, vs1, vm` | vector-vector | 355 |
| `vfwsub.vf` | `vd, vs2, rs1, vm` | vector-scalar | 355 |
| `vfwadd.wv` | `vd, vs2, vs1, vm` | vector-vector | 355 |
| `vfwadd.wf` | `vd, vs2, rs1, vm` | vector-scalar | 355 |
| `vfwsub.wv` | `vd, vs2, vs1, vm` | vector-vector | 355 |
| `vfwsub.wf` | `vd, vs2, rs1, vm` | vector-scalar | 355 |

### 31.13.4. Vector Single-Width Floating-Point Multiply/Divide Instructions
（共5条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vfmul.vv` | `vd, vs2, vs1, vm` | Vector-vector | 355 |
| `vfmul.vf` | `vd, vs2, rs1, vm` | vector-scalar | 355 |
| `vfdiv.vv` | `vd, vs2, vs1, vm` | Vector-vector | 355 |
| `vfdiv.vf` | `vd, vs2, rs1, vm` | vector-scalar | 355 |
| `vfrdiv.vf` | `vd, vs2, rs1, vm` | scalar-vector, vd[i] = f[rs1]/vs2[i] | 355 |

### 31.13.5. Vector Widening Floating-Point Multiply
（共2条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vfwmul.vv` | `vd, vs2, vs1, vm` | vector-vector | 355 |
| `vfwmul.vf` | `vd, vs2, rs1, vm` | vector-scalar | 355 |

### 31.13.6. Vector Single-Width Floating-Point Fused Multiply-Add Instructions
（共16条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vfmacc.vv` | `vd, vs1, vs2, vm` | vd[i] = (vs1[i] * vs2[i]) + vd[i] | 355 |
| `vfmacc.vf` | `vd, rs1, vs2, vm` | vd[i] = (f[rs1] * vs2[i]) + vd[i] | 355 |
| `vfnmacc.vv` | `vd, vs1, vs2, vm` | vd[i] = -(vs1[i] * vs2[i]) - vd[i] | 355 |
| `vfnmacc.vf` | `vd, rs1, vs2, vm` | vd[i] = -(f[rs1] * vs2[i]) - vd[i] | 356 |
| `vfmsac.vv` | `vd, vs1, vs2, vm` | vd[i] = (vs1[i] * vs2[i]) - vd[i] | 356 |
| `vfmsac.vf` | `vd, rs1, vs2, vm` | vd[i] = (f[rs1] * vs2[i]) - vd[i] | 356 |
| `vfnmsac.vv` | `vd, vs1, vs2, vm` | vd[i] = -(vs1[i] * vs2[i]) + vd[i] | 356 |
| `vfnmsac.vf` | `vd, rs1, vs2, vm` | vd[i] = -(f[rs1] * vs2[i]) + vd[i] | 356 |
| `vfmadd.vv` | `vd, vs1, vs2, vm` | vd[i] = (vs1[i] * vd[i]) + vs2[i] | 356 |
| `vfmadd.vf` | `vd, rs1, vs2, vm` | vd[i] = (f[rs1] * vd[i]) + vs2[i] | 356 |
| `vfnmadd.vv` | `vd, vs1, vs2, vm` | vd[i] = -(vs1[i] * vd[i]) - vs2[i] | 356 |
| `vfnmadd.vf` | `vd, rs1, vs2, vm` | vd[i] = -(f[rs1] * vd[i]) - vs2[i] | 356 |
| `vfmsub.vv` | `vd, vs1, vs2, vm` | vd[i] = (vs1[i] * vd[i]) - vs2[i] | 356 |
| `vfmsub.vf` | `vd, rs1, vs2, vm` | vd[i] = (f[rs1] * vd[i]) - vs2[i] | 356 |
| `vfnmsub.vv` | `vd, vs1, vs2, vm` | vd[i] = -(vs1[i] * vd[i]) + vs2[i] | 356 |
| `vfnmsub.vf` | `vd, rs1, vs2, vm` | vd[i] = -(f[rs1] * vd[i]) + vs2[i] | 356 |

### 31.13.7. Vector Widening Floating-Point Fused Multiply-Add Instructions
（共8条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vfwmacc.vv` | `vd, vs1, vs2, vm` | vd[i] = (vs1[i] * vs2[i]) + vd[i] | 356 |
| `vfwmacc.vf` | `vd, rs1, vs2, vm` | vd[i] = (f[rs1] * vs2[i]) + vd[i] | 356 |
| `vfwnmacc.vv` | `vd, vs1, vs2, vm` | vd[i] = -(vs1[i] * vs2[i]) - vd[i] | 356 |
| `vfwnmacc.vf` | `vd, rs1, vs2, vm` | vd[i] = -(f[rs1] * vs2[i]) - vd[i] | 356 |
| `vfwmsac.vv` | `vd, vs1, vs2, vm` | vd[i] = (vs1[i] * vs2[i]) - vd[i] | 356 |
| `vfwmsac.vf` | `vd, rs1, vs2, vm` | vd[i] = (f[rs1] * vs2[i]) - vd[i] | 356 |
| `vfwnmsac.vv` | `vd, vs1, vs2, vm` | vd[i] = -(vs1[i] * vs2[i]) + vd[i] | 356 |
| `vfwnmsac.vf` | `vd, rs1, vs2, vm` | vd[i] = -(f[rs1] * vs2[i]) + vd[i] | 357 |

### 31.13.8. Vector Floating-Point Square-Root Instruction
（共1条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vfsqrt.v` | `vd, vs2, vm` | Vector-vector square root | 357 |

### 31.13.9. Vector Floating-Point Reciprocal Square-Root Estimate Instruction
（共1条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vfrsqrt7.v` | `vd, vs2, vm` | — | 357 |

### 31.13.10. Vector Floating-Point Reciprocal Estimate Instruction
（共1条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vfrec7.v` | `vd, vs2, vm` | — | 361 |

### 31.13.11. Vector Floating-Point MIN/MAX Instructions
（共4条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vfmin.vv` | `vd, vs2, vs1, vm` | Vector-vector | 366 |
| `vfmin.vf` | `vd, vs2, rs1, vm` | vector-scalar | 366 |
| `vfmax.vv` | `vd, vs2, vs1, vm` | Vector-vector | 366 |
| `vfmax.vf` | `vd, vs2, rs1, vm` | vector-scalar | 366 |

### 31.13.12. Vector Floating-Point Sign-Injection Instructions
（共7条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vfsgnj.vv` | `vd, vs2, vs1, vm` | Vector-vector | 366 |
| `vfsgnj.vf` | `vd, vs2, rs1, vm` | vector-scalar | 366 |
| `vfsgnjn.vv` | `vd, vs2, vs1, vm` | Vector-vector | 366 |
| `vfsgnjn.vf` | `vd, vs2, rs1, vm` | vector-scalar | 367 |
| `vfsgnjx.vv` | `vd, vs2, vs1, vm` | Vector-vector | 367 |
| `vfsgnjx.vf` | `vd, vs2, rs1, vm` | vector-scalar | 367 |
| `vfneg.v` | `vd,vs = vfsgnjn.vv vd,vs,vs.` | — | 367 |

### 31.13.13. Vector Floating-Point Compare Instructions
（共12条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vmfeq.vv` | `vd, vs2, vs1, vm` | Vector-vector | 367 |
| `vmfeq.vf` | `vd, vs2, rs1, vm` | vector-scalar | 367 |
| `vmfne.vv` | `vd, vs2, vs1, vm` | Vector-vector | 367 |
| `vmfne.vf` | `vd, vs2, rs1, vm` | vector-scalar | 367 |
| `vmflt.vv` | `vd, vs2, vs1, vm` | Vector-vector | 367 |
| `vmflt.vf` | `vd, vs2, rs1, vm` | vector-scalar | 367 |
| `vmfle.vv` | `vd, vs2, vs1, vm` | Vector-vector | 367 |
| `vmfle.vf` | `vd, vs2, rs1, vm` | vector-scalar | 367 |
| `vmfgt.vf` | `vd, vs2, rs1, vm` | vector-scalar | 367 |
| `vmfge.vf` | `vd, vs2, rs1, vm` | vector-scalar | 367 |
| `vmand.mm` | `v0, v0, v1` | Only set where A and B are ordered, | 368 |
| `vmfgt.vv` | `v0, va, vb, v0.t` | so only set flags on ordered values. | 368 |

### 31.13.14. Vector Floating-Point Classify Instruction
（共1条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vfclass.v` | `vd, vs2, vm` | Vector-vector | 368 |

### 31.13.15. Vector Floating-Point Merge Instruction
（共1条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vfmerge.vfm` | `vd, vs2, rs1, v0` | vd[i] = v0.mask[i] ? f[rs1] : vs2[i] | 369 |

### 31.13.16. Vector Floating-Point Move Instruction
（共1条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vfmv.v.f` | `vd, rs1` | vd[i] = f[rs1] | 369 |

### 31.13.17. Single-Width Floating-Point/Integer Type-Convert Instructions
（共6条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vfcvt.xu.f.v` | `vd, vs2, vm` | Convert float to unsigned integer. | 369 |
| `vfcvt.x.f.v` | `vd, vs2, vm` | Convert float to signed integer. | 369 |
| `vfcvt.rtz.xu.f.v` | `vd, vs2, vm` | Convert float to unsigned integer, truncating. | 369 |
| `vfcvt.rtz.x.f.v` | `vd, vs2, vm` | Convert float to signed integer, truncating. | 369 |
| `vfcvt.f.xu.v` | `vd, vs2, vm` | Convert unsigned integer to float. | 369 |
| `vfcvt.f.x.v` | `vd, vs2, vm` | Convert signed integer to float. | 369 |

### 31.13.18. Widening Floating-Point/Integer Type-Convert Instructions
（共7条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vfwcvt.xu.f.v` | `vd, vs2, vm` | Convert float to double-width unsigned | 369 |
| `vfwcvt.x.f.v` | `vd, vs2, vm` | Convert float to double-width signed integer. | 369 |
| `vfwcvt.rtz.xu.f.v` | `vd, vs2, vm` | Convert float to double-width unsigned | 370 |
| `vfwcvt.rtz.x.f.v` | `vd, vs2, vm` | Convert float to double-width signed integer, | 370 |
| `vfwcvt.f.xu.v` | `vd, vs2, vm` | Convert unsigned integer to double-width | 370 |
| `vfwcvt.f.x.v` | `vd, vs2, vm` | Convert signed integer to double-width float. | 370 |
| `vfwcvt.f.f.v` | `vd, vs2, vm` | Convert single-width float to double-width | 370 |

### 31.13.19. Narrowing Floating-Point/Integer Type-Convert Instructions
（共8条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vfncvt.xu.f.w` | `vd, vs2, vm` | Convert double-width float to unsigned | 370 |
| `vfncvt.x.f.w` | `vd, vs2, vm` | Convert double-width float to signed integer. | 370 |
| `vfncvt.rtz.xu.f.w` | `vd, vs2, vm` | Convert double-width float to unsigned | 370 |
| `vfncvt.rtz.x.f.w` | `vd, vs2, vm` | Convert double-width float to signed integer, | 370 |
| `vfncvt.f.xu.w` | `vd, vs2, vm` | Convert double-width unsigned integer to | 370 |
| `vfncvt.f.x.w` | `vd, vs2, vm` | Convert double-width signed integer to float. | 370 |
| `vfncvt.f.f.w` | `vd, vs2, vm` | Convert double-width float to single-width | 370 |
| `vfncvt.rod.f.f.w` | `vd, vs2, vm` | Convert double-width float to single-width | 370 |

### 31.14.1. Vector Single-Width Integer Reduction Instructions
（共8条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vredsum.vs` | `vd, vs2, vs1, vm` | vd[0] = sum( vs1[0] , vs2[*] ) | 372 |
| `vredmaxu.vs` | `vd, vs2, vs1, vm` | vd[0] = maxu( vs1[0] , vs2[*] ) | 372 |
| `vredmax.vs` | `vd, vs2, vs1, vm` | vd[0] = max( vs1[0] , vs2[*] ) | 372 |
| `vredminu.vs` | `vd, vs2, vs1, vm` | vd[0] = minu( vs1[0] , vs2[*] ) | 372 |
| `vredmin.vs` | `vd, vs2, vs1, vm` | vd[0] = min( vs1[0] , vs2[*] ) | 372 |
| `vredand.vs` | `vd, vs2, vs1, vm` | vd[0] = and( vs1[0] , vs2[*] ) | 372 |
| `vredor.vs` | `vd, vs2, vs1, vm` | vd[0] = or( vs1[0] , vs2[*] ) | 372 |
| `vredxor.vs` | `vd, vs2, vs1, vm` | vd[0] = xor( vs1[0] , vs2[*] ) | 372 |

### 31.14.2. Vector Widening Integer Reduction Instructions
（共2条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vwredsumu.vs` | `vd, vs2, vs1, vm` | 2*SEW = 2*SEW + sum(zero-extend(SEW)) | 372 |
| `vwredsum.vs` | `vd, vs2, vs1, vm` | 2*SEW = 2*SEW + sum(sign-extend(SEW)) | 372 |

### 31.14.3. Vector Single-Width Floating-Point Reduction Instructions
（共4条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vfredosum.vs` | `vd, vs2, vs1, vm` | Ordered sum | 372 |
| `vfredusum.vs` | `vd, vs2, vs1, vm` | Unordered sum | 372 |
| `vfredmax.vs` | `vd, vs2, vs1, vm` | Maximum value | 372 |
| `vfredmin.vs` | `vd, vs2, vs1, vm` | Minimum value | 372 |

### 31.14.4. Vector Widening Floating-Point Reduction Instructions
（共2条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vfwredosum.vs` | `vd, vs2, vs1, vm` | Ordered sum | 374 |
| `vfwredusum.vs` | `vd, vs2, vs1, vm` | Unordered sum | 374 |

### 31.15.1. Vector Mask-Register Logical Instructions
（共12条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vmand.mm` | `vd, vs2, vs1` | vd.mask[i] = vs2.mask[i] && vs1.mask[i] | 374 |
| `vmnand.mm` | `vd, vs2, vs1` | vd.mask[i] = !(vs2.mask[i] && vs1.mask[i]) | 374 |
| `vmandn.mm` | `vd, vs2, vs1` | vd.mask[i] = vs2.mask[i] && !vs1.mask[i] | 374 |
| `vmxor.mm` | `vd, vs2, vs1` | vd.mask[i] = vs2.mask[i] ^^ vs1.mask[i] | 374 |
| `vmor.mm` | `vd, vs2, vs1` | vd.mask[i] = vs2.mask[i] \|\| vs1.mask[i] | 374 |
| `vmnor.mm` | `vd, vs2, vs1` | vd.mask[i] = !(vs2.mask[i] \|\| vs1.mask[i]) | 374 |
| `vmorn.mm` | `vd, vs2, vs1` | vd.mask[i] = vs2.mask[i] \|\| !vs1.mask[i] | 374 |
| `vmxnor.mm` | `vd, vs2, vs1` | vd.mask[i] = !(vs2.mask[i] ^^ vs1.mask[i]) | 374 |
| `vmmv.m` | `vd, vs => vmand.mm vd, vs, vs` | Copy mask register | 374 |
| `vmclr.m` | `vd => vmxor.mm vd, vd, vd` | Clear mask register | 375 |
| `vmset.m` | `vd => vmxnor.mm vd, vd, vd` | Set mask register | 375 |
| `vmnot.m` | `vd, vs => vmnand.mm vd, vs, vs` | Invert bits | 375 |

### 31.15.2. Vector count population in mask vcpop.m
（共1条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vcpop.m` | `rd, vs2, vm` | — | 375 |

### 31.15.3. vfirst find-first-set mask bit
（共1条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vfirst.m` | `rd, vs2, vm` | — | 376 |

### 31.15.4. vmsbf.m set-before-first mask bit
（共1条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vmsbf.m` | `vd, vs2, vm` | — | 376 |

### 31.15.5. vmsif.m set-including-first mask bit
（共1条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vmsif.m` | `vd, vs2, vm` | — | 377 |

### 31.15.6. vmsof.m set-only-first mask bit
（共1条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vmsof.m` | `vd, vs2, vm` | — | 378 |

### 31.15.8. Vector Iota Instruction
（共7条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `viota.m` | `vd, vs2, vm` | — | 380 |
| `vsetvli` | `a5, a0, e32, m8, ta, ma` | 32-bit integers | 381 |
| `vle32.v` | `v8, (a1)` | Load input vector | 381 |
| `vmsne.vi` | `v0, v8, 0` | Locate non-zero values | 381 |
| `vcpop.m` | `a5, v0` | Count number of elements set in v0 | 381 |
| `vsll.vi` | `v16, v16, 2, v0.t` | Multiply offsets by four bytes | 381 |
| `vsuxei32.v` | `v8, (a2), v16, v0.t` | Scatter using scaled viota results under | 381 |

### 31.15.9. Vector Element Index Instruction
（共1条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vid.v` | `vd, vm` | Write element ID to destination. | 381 |

### 31.16.1. Integer Scalar Move Instructions
（共2条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vmv.x.s` | `rd, vs2` | x[rd] = vs2[0] (vs1=0) | 382 |
| `vmv.s.x` | `vd, rs1` | vd[0] = x[rs1] (vs2=0) | 382 |

### 31.16.2. Floating-Point Scalar Move Instructions
（共2条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vfmv.f.s` | `rd, vs2` | f[rd] = vs2[0] (rs1=0) | 382 |
| `vfmv.s.f` | `vd, rs1` | vd[0] = f[rs1] (vs2=0) | 382 |

### 31.16.3.1. Vector Slide-up Instructions
（共2条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vslideup.vx` | `vd, vs2, rs1, vm` | vd[i+x[rs1]] = vs2[i] | 383 |
| `vslideup.vi` | `vd, vs2, uimm, vm` | vd[i+uimm] = vs2[i] | 383 |

### 31.16.3.2. Vector Slide-down Instructions
（共2条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vslidedown.vx` | `vd, vs2, rs1, vm` | vd[i] = vs2[i+x[rs1]] | 383 |
| `vslidedown.vi` | `vd, vs2, uimm, vm` | vd[i] = vs2[i+uimm] | 383 |

### 31.16.3.3. Vector Slide-1-up
（共1条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vslide1up.vx` | `vd, vs2, rs1, vm` | vd[0]=x[rs1], vd[i+1] = vs2[i] | 384 |

### 31.16.3.4. Vector Floating-Point Slide-1-up Instruction
（共1条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vfslide1up.vf` | `vd, vs2, rs1, vm` | vd[0]=f[rs1], vd[i+1] = vs2[i] | 384 |

### 31.16.3.5. Vector Slide-1-down Instruction
（共1条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vslide1down.vx` | `vd, vs2, rs1, vm` | vd[i] = vs2[i+1], vd[vl-1]=x[rs1] | 385 |

### 31.16.3.6. Vector Floating-Point Slide-1-down Instruction
（共1条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vfslide1down.vf` | `vd, vs2, rs1, vm` | vd[i] = vs2[i+1], vd[vl-1]=f[rs1] | 385 |

### 31.16.4. Vector Register Gather Instructions
（共4条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vrgather.vv` | `vd, vs2, vs1, vm` | vd[i] = (vs1[i] >= VLMAX) ? 0 : vs2[vs1[i]]; | 385 |
| `vrgatherei16.vv` | `vd, vs2, vs1, vm` | vd[i] = (vs1[i] >= VLMAX) ? 0 : vs2[vs1[i]]; | 386 |
| `vrgather.vx` | `vd, vs2, rs1, vm` | vd[i] = (x[rs1] >= VLMAX) ? 0 : vs2[x[rs1]] | 386 |
| `vrgather.vi` | `vd, vs2, uimm, vm` | vd[i] = (uimm >= VLMAX) ? 0 : vs2[uimm] | 386 |

### 31.16.5. Vector Compress Instruction
（共2条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vcompress.vm` | `vd, vs2, vs1` | Compress into vd elements of vs2 where vs1 is | 386 |
| `vsetivli` | `t0, 9, e8, m1, tu, ma` | — | 386 |

### 31.16.6. Whole Vector Register Move
（共5条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vmv<nr>r.v` | `vd, vs2` | General form | 388 |
| `vmv1r.v` | `v1, v2` | Copy v1=v2 | 388 |
| `vmv2r.v` | `v10, v12` | Copy v10=v12; v11=v13 | 388 |
| `vmv4r.v` | `v4, v8` | Copy v4=v8; v5=v9; v6=v10; v7=v11 | 388 |
| `vmv8r.v` | `v0, v8` | Copy v0=v8; v1=v9; ...; v7=v15 | 388 |

## 十一、密码学标量扩展（Zk*，第32章）

### Zbkb（Bitmanip instructions for Cryptography，本章无汇总表，32.2.1 仅指向第 30 章）
| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| brev8 | brev8 rd, rs（32.3.13 节）/ brev8 rd, rs1（32.6.4.2） | 反转寄存器中每个字节内的位序 | 15474, 15478, 15493, 16907, 16957 |
| pack | pack rd, rs1, rs2 | 把 rs1、rs2 的低半部分打包进 rd | 15573, 15577, 15591, 16904, 17010 |
| packh | packh rd, rs1, rs2 | 把 rs1、rs2 的最低字节打包进 rd 的低 16 位 | 15595, 15599, 15613, 16905, 17011 |
| packw | packw rd, rs1, rs2 | 打包低 16 位并符号扩展到 XLEN（仅 RV64） | 15617, 15621, 15627, 15634, 16906, 17010 |
| rev8 | rev8 rd, rs（32.3.20 节）/ rev8 rd, rs1（32.6.4.2） | 字节序反转；RV32 与 RV64 编码不同 | 15638, 15642, 15663, 15672, 16908, 16958 |
| rol | rol rd, rs1, rs2 | 循环左移（寄存器） | 15676, 15680, 15696, 16896, 16945 |
| rolw | rolw rd, rs1, rs2 | 循环左移字（寄存器，RV64） | 15700, 15704, 15721, 16899, 16946 |
| ror | ror rd, rs1, rs2 | 循环右移（寄存器） | 15725, 15729, 15745, 16895, 16945 |
| rori | rori rd, rs1, shamt | 循环右移（立即数） | 15749, 15753, 15774, 16897, 16947 |
| roriw | roriw rd, rs1, shamt | 循环右移字（立即数，RV64） | 15778, 15782, 15798, 16900, 16947 |
| rorw | rorw rd, rs1, rs2 | 循环右移字（寄存器，RV64） | 15802, 15806, 15823, 16898, 16946 |
| andn | andn rd, rs1, rs2 | rs1 与 rs2 反码做按位与 | 15453, 15457, 15469, 15470, 16901, 16993 |
| orn | orn rd, rs1, rs2 | rs1 与 rs2 反码做按位或 | 15553, 15557, 15568, 15569, 16902, 16994 |
| xnor | xnor rd, rs1, rs2 | 按位同或 | 16408, 16412, 16423, 16424, 16903, 16995 |
| unzip | unzip rd, rs | 位去交织（仅 RV32） | 16380, 16385, 16391, 16404, 16910, 16970 |
| zip | zip rd, rs | 位交织（仅 RV32） | 16490, 16495, 16502, 16515, 16909, 16969 |

### Zbkc（Carry-less multiply instructions，本章无汇总表，32.2.2 仅指向第 30 章）
| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| clmul | clmul rd, rs1, rs2 | 无进位乘（低半部分，Galois/Counter Mode） | 15497, 15501, 15507, 15520, 15521, 16891, 16980 |
| clmulh | clmulh rd, rs1, rs2 | 无进位乘（高半部分） | 15525, 15529, 15535, 15548, 15549, 16892, 16981 |

### Zbkx（Crossbar permutation instructions，本章无汇总表，32.2.3 仅指向第 30 章）
| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| xperm8 / XPERM8（Sail 子句名） | xperm8 rd, rs1, rs2 | 按字节查表置换（rs1 为表，rs2 为索引） | 16428, 16432, 16445, 16455, 16894, 17024 |
| xperm4 / XPERM4（Sail 子句名） | xperm4 rd, rs1, rs2 | 按半字节（nibble）查表置换 | 16459, 16463, 16476, 16486, 16893, 17023 |

### Zknd（NIST Suite: AES Decryption）
| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| aes32dsi / AES32DSI | aes32dsi rd, rs1, rs2, bs | AES 最终轮解密（RV32），逆 SBox 后与 rs1 异或 | 15010, 15103, 15107, 15116, 15128 |
| aes32dsmi / AES32DSMI | aes32dsmi rd, rs1, rs2, bs | AES 中间轮解密（RV32），逆 SBox + 部分逆 MixColumn | 15011, 15134, 15138, 15147, 15157 |
| aes64ds / AES64DS | aes64ds rd, rs1, rs2 | AES 解密最终轮（RV64），逆 ShiftRows+SubBytes | 15012, 15220, 15224, 15240, 15248 |
| aes64dsm / AES64DSM | aes64dsm rd, rs1, rs2 | AES 解密中间轮（RV64），逆 ShiftRows+SubBytes+MixColumns | 15013, 15254, 15258, 15274, 15283 |
| aes64im / AES64IM | aes64im rd, rs1 | AES 解密密钥编排逆 MixColumns（RV64） | 15014, 15358, 15363, 15373, 15381 |
| aes64ks1i / AES64KS1I | aes64ks1i rd, rs1, rnum | AES 密钥编排指令 1（RV64，rnum∈0x0..0xA） | 15015, 15387, 15392, 15402, 15419 |
| aes64ks2 / AES64KS2 | aes64ks2 rd, rs1, rs2 | AES 密钥编排指令 2（RV64），密钥字异或 | 15020, 15425, 15429, 15438, 15447 |

### Zkne（NIST Suite: AES Encryption）
| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| aes32esi / AES32ESI | aes32esi rd, rs1, rs2, bs | AES 最终轮加密（RV32），正向 SBox 后与 rs1 异或 | 15026, 15163, 15167, 15176, 15185 |
| aes32esmi / AES32ESMI | aes32esmi rd, rs1, rs2, bs | AES 中间轮加密（RV32），正向 SBox + 部分 MixColumn | 15027, 15191, 15195, 15204, 15214 |
| aes64es / AES64ES | aes64es rd, rs1, rs2 | AES 加密最终轮（RV64） | 15028, 15289, 15293, 15309, 15317 |
| aes64esm / AES64ESM | aes64esm rd, rs1, rs2 | AES 加密中间轮（RV64） | 15029, 15323, 15327, 15343, 15352 |
| aes64ks1i | aes64ks1i rd, rs1, rnum | 密钥编排指令 1（与 Zknd 共用，RV64） | 15030, 15032, 15392, 15418 |
| aes64ks2 | aes64ks2 rd, rs1, rs2 | 密钥编排指令 2（与 Zknd 共用，RV64） | 15031, 15032, 15429, 15446 |

### Zknh（NIST Suite: Hash Function Instructions）
| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| sha256sig0 / SHA256SIG0 | sha256sig0 rd, rs1 | SHA2-256 Sigma0 变换（RV32/RV64 均可） | 15036, 15827, 15831, 15842, 15850 |
| sha256sig1 / SHA256SIG1 | sha256sig1 rd, rs1 | SHA2-256 Sigma1 变换 | 15037, 15856, 15860, 15871, 15879 |
| sha256sum0 / SHA256SUM0 | sha256sum0 rd, rs1 | SHA2-256 Sum0 变换 | 15038, 15885, 15889, 15900, 15908 |
| sha256sum1 / SHA256SUM1 | sha256sum1 rd, rs1 | SHA2-256 Sum1 变换 | 15039, 15914, 15918, 15929, 15937 |
| sha512sig0h / SHA512SIG0H | sha512sig0h rd, rs1, rs2 | SHA2-512 Sigma0 高半（仅 RV32） | 15040, 15943, 15948, 15964, 15971 |
| sha512sig0l / SHA512SIG0L | sha512sig0l rd, rs1, rs2 | SHA2-512 Sigma0 低半（仅 RV32） | 15041, 15977, 15982, 15998, 16005 |
| sha512sig1h / SHA512SIG1H | sha512sig1h rd, rs1, rs2 | SHA2-512 Sigma1 高半（仅 RV32） | 15042, 16011, 16016, 16032, 16039 |
| sha512sig1l / SHA512SIG1L | sha512sig1l rd, rs1, rs2 | SHA2-512 Sigma1 低半（仅 RV32） | 15043, 16045, 16050, 16066, 16073 |
| sha512sum0r / SHA512SUM0R | sha512sum0r rd, rs1, rs2 | SHA2-512 Sum0（仅 RV32） | 15044, 16079, 16083, 16100, 16107 |
| sha512sum1r / SHA512SUM1R | sha512sum1r rd, rs1, rs2 | SHA2-512 Sum1（仅 RV32） | 15045, 16113, 16117, 16134, 16141 |
| sha512sig0 / SHA512SIG0 | sha512sig0 rd, rs1 | SHA2-512 Sigma0（仅 RV64） | 15046, 16147, 16151, 16160, 16166 |
| sha512sig1 / SHA512SIG1 | sha512sig1 rd, rs1 | SHA2-512 Sigma1（仅 RV64） | 15047, 16172, 16176, 16185, 16191 |
| sha512sum0 / SHA512SUM0 | sha512sum0 rd, rs1 | SHA2-512 Sum0（仅 RV64） | 15048, 16197, 16201, 16210, 16216 |
| sha512sum1 / SHA512SUM1 | sha512sum1 rd, rs1 | SHA2-512 Sum1（仅 RV64） | 15049, 16222, 16226, 16235, 16241 |

### Zksed（ShangMi Suite: SM4 Block Cipher Instructions）
| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| sm4ed / SM4ED | sm4ed rd, rs1, rs2, bs | SM4 加/解密轮函数（SBox+线性层，RV32/RV64 均可） | 15057, 16307, 16312, 16323, 16339 |
| sm4ks / SM4KS | sm4ks rd, rs1, rs2, bs | SM4 密钥编排（RV32/RV64 均可） | 15058, 16344, 16349, 16360, 16375 |

### Zksh（ShangMi Suite: SM3 Hash Function Instructions）
| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| sm3p0 / SM3P0 | sm3p0 rd, rs1 | SM3 P0 变换（RV32/RV64 均可） | 15062, 16247, 16252, 16264, 16272 |
| sm3p1 / SM3P1 | sm3p1 rd, rs1 | SM3 P1 变换（RV32/RV64 均可） | 15063, 16277, 16282, 16294, 16302 |

### Zkr（Entropy Source Extension）
| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| （无） | — | **该扩展仅定义 CSR，无新指令**：定义非特权 CSR `seed`（地址 0x015，32 位：OPST[31:30]、reserved[29:24]、custom[23:16]、entropy[15:0]）；并在 `mseccfg` 中增加 SSEED/USEED 字段控制访问 | 15064, 15065, 16530, 16531, 16533, 16653, 16654 |

说明（Zkr 范围）：
- 文本只给出 `seed` 的 CSR 语义与访问控制，未定义任何新助记符。文中出现的 `csrrw rd, seed, x0`（16541）与编码示意中的 `CSRRW`（16543-16545）是既有 Zicsr 指令用法，不是本章新指令。
- `mnoise`（NOISE_TEST）是非规范性自定义 CSR 建议接口（17536-17549），也不属于新指令。

### Zkt（Data Independent Execution Latency Subset）
| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| （无） | — | **该扩展不定义任何新指令**：明确写明 "Zkt does not define a set of instructions available in the core; it just restricts the behaviour of certain instructions if those are implemented"（Zkt 只是对已实现指令的恒定时间约束） | 15098, 16665, 16666, 16681, 16682 |

说明（Zkt 范围）：
- 32.5.5 给出的是"被纳入恒定时间要求的既有指令清单"，不是新指令定义：
  - RVI 清单（16777-16814，含 `lui/auipc/addi/slti/sltiu/xori/ori/andi/slli/srli/srai/add/sub/sll/slt/sltu/xor/srl/sra/or/and/addiw/slliw/srliw/sraiw/addw/subw/sllw/srlw/sraw`）
  - RVM 清单（16815-16822，`mul/mulh/mulhsu/mulhu/mulw`）
  - RVC 清单（16823-16841，`c.nop/c.addi/c.addiw/c.lui/c.srli/c.srai/c.andi/c.sub/c.xor/c.or/c.and/c.subw/c.addw/c.slli/c.mv/c.add`）
  - Zcb 清单（16842-16851，`c.mul/c.not/c.zext.b`）
  - RVK 清单（16852-16884，即本章 Zk* 密码指令）
  - RVB 清单（16885-16910，即 Zbkb/Zbkc/Zbkx 指令）
- 这些条目均属其他扩展，仅有"实施时须保证延迟与数据无关"的约束，故不计入本章新指令总数。

### 汇总扩展（Zkn / Zks / Zk，均只做扩展组合，不定义新助记符）
| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| （无） | — | Zkn = Zbkb+Zbkc+Zbkx+Zkne+Zknd+Zknh 的简写，不新增指令 | 15069, 15071, 15072, 15073, 15074, 15075, 15076, 15077, 15078 |
| （无） | — | Zks = Zbkb+Zbkc+Zbkx+Zksed+Zksh 的简写，不新增指令 | 15079, 15081, 15082, 15083, 15084, 15085, 15086, 15087 |
| （无） | — | Zk = Zkn+Zkr+Zkt 的简写，不新增指令 | 15091, 15093, 15094, 15095, 15096, 15097 |

### 统计

**本范围指令总数（按助记符去重）：49**

**各子扩展条数小计**

| 子扩展 | 条数 | 备注 |
| --- | --- | --- |
| Zbkb | 16 | 本章无汇总表（32.2.1 指向第 30 章）；其中 15 条同时属于 Zbb（`andn`、`orn`、`xnor`、`pack`、`packh`、`rev8`、`rol`、`ror`、`rori` 见 15469-15470、15568-15569、16423-16424、15590-15591、15612-15613、15671-15672、15695-15696、15744-15745、15773-15774），`zip`/`unzip`/`packw` 为 Zbkb 独有 |
| Zbkc | 2 | 本章无汇总表；两条与 Zbc 共用（15520-15521、15548-15549） |
| Zbkx | 2 | 本章无汇总表；两条为 Zbkx 定义（16455、16486） |
| Zknd | 7 | 含与 Zkne 共用的 `aes64ks1i`、`aes64ks2` |
| Zkne | 6 | 含与 Zknd 共用的 `aes64ks1i`、`aes64ks2` |
| Zknh | 14 | — |
| Zksed | 2 | — |
| Zksh | 2 | — |
| Zkr | 0 | **该扩展仅定义 CSR，无新指令**（`seed` CSR 0x015、`mseccfg.SSEED/USEED`） |
| Zkt | 0 | **该扩展不定义任何新指令**，仅给出恒定时间约束清单 |
| Zkn（组合） | 45 | Zbkb+Zbkc+Zbkx+Zkne+Zknd+Zknh，去重后 |
| Zks（组合） | 24 | Zbkb+Zbkc+Zbkx+Zksed+Zksh，去重后 |
| Zk（组合） | 45 | Zkn+Zkr+Zkt，去重后 |

补充计数：Zbkb/Zbkc/Zbkx 的 20 条助记符在本章 32.3 节均以 "Included in" 同时列出 Zbb 或 Zbc 与 Zbkb/Zbkc/Zbkx（如 15469-15470、15520-15521），即它们并非密码学扩展新定义的操作码；本章真正新定义的密码指令为 49 − 20 = **29** 条（AES 11 + SHA2 14 + SM4 2 + SM3 2）。

**仅适用于 RV32 的指令（12 条）**
`aes32dsi`、`aes32dsmi`、`aes32esi`、`aes32esmi`、`sha512sig0h`、`sha512sig0l`、`sha512sig1h`、`sha512sig1l`、`sha512sum0r`、`sha512sum1r`、`zip`、`unzip`
（依据：15010-15011、15026-15027、15040-15045 汇总表 RV32 勾选；15105、15136、15165、15193、15953、15987、16021、16055、16088、16122、16391、16502 节内 "implemented on RV32 only"／"available only on RV32"；16856-16859、16871-16876、16909-16910 Zkt 清单）

**仅适用于 RV64 的指令（15 条）**
`aes64ds`、`aes64dsm`、`aes64es`、`aes64esm`、`aes64im`、`aes64ks1i`、`aes64ks2`、`sha512sig0`、`sha512sig1`、`sha512sum0`、`sha512sum1`、`packw`、`rolw`、`rorw`、`roriw`
（依据：15012-15015、15020、15028-15031、15046-15049 汇总表 RV64 勾选；15627 "only exists on RV64"；16860-16866、16877-16880、16898-16900、16906 Zkt 清单；16944-16947 "RV32, RV64: ror/rol/rori  RV64 only: rorw, rolw, roriw"；16976-16977 说明 RV64 上 zip/unzip 不需要）

**RV32 与 RV64 均适用（22 条）**
`sha256sig0`、`sha256sig1`、`sha256sum0`、`sha256sum1`（15836、15865、15894、15923）、`sm3p0`、`sm3p1`（16257、16287）、`sm4ed`、`sm4ks`（16319、16356），以及 `andn`、`orn`、`xnor`、`pack`、`packh`、`rev8`、`rol`、`ror`、`rori`、`clmul`、`clmulh`、`xperm4`、`xperm8`（16891-16908 Zkt 清单双勾选）。

**别名说明**：本章未定义任何助记符别名。仅有 `rev8` 一个助记符在 RV32 与 RV64 对应不同编码（15663 "The rev8 mnemonic corresponds to different instruction encodings in RV32 and RV64"），并非别名关系；`aes64ks1i`/`aes64ks2` 是两个扩展（Zknd、Zkne）共用同一助记符与编码（15021-15022、15032），也不是别名。

**大小写说明**：本章助记符正式形式均为小写（32.3 各节 `Mnemonic` 行）；大写形式出现在各指令 `Operation` 段的 Sail 子句名中，如 `AES32DSI`(15116)、`AES32DSMI`(15147)、`AES32ESI`(15176)、`AES32ESMI`(15204)、`AES64DS`(15240)、`AES64DSM`(15274)、`AES64ES`(15309)、`AES64ESM`(15343)、`AES64IM`(15373)、`AES64KS1I`(15402)、`AES64KS2`(15438)、`SHA256SIG0`(15842)、`SHA256SIG1`(15871)、`SHA256SUM0`(15900)、`SHA256SUM1`(15929)、`SHA512SIG0H`(15964)、`SHA512SIG0L`(15998)、`SHA512SIG1H`(16032)、`SHA512SIG1L`(16066)、`SHA512SUM0R`(16100)、`SHA512SUM1R`(16134)、`SHA512SIG0`(16160)、`SHA512SIG1`(16185)、`SHA512SUM0`(16210)、`SHA512SUM1`(16235)、`SM3P0`(16264)、`SM3P1`(16294)、`SM4ED`(16323)、`SM4KS`(16360)、`XPERM8`(16445)、`XPERM4`(16476)。Zbkb/Zbkc 类指令在本章的 `Operation` 段以伪代码给出（无 Sail 子句名），因此没有对应大写写法。

## 十二、密码学向量扩展（Zvk*，第33章）

### Zvbb — Vector Basic Bit-manipulation
| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| vandn.vv | vandn.vv vd, vs2, vs1, vm | 按位与非（vs1 取反后与 vs2 相与） | 18948/18952 |
| vandn.vx | vandn.vx vd, vs2, rs1, vm | 按位与非（rs1 标量取反后与 vs2 相与） | 18948/18953 |
| vbrev.v | vbrev.v vd, vs2, vm | 逐元素比特位反转 | 19003/19007 |
| vbrev8.v | vbrev8.v vd, vs2, vm | 逐字节比特位反转 | 19033/19037 |
| vrev8.v | vrev8.v vd, vs2, vm | 逐元素字节反转（端序交换） | 19417/19421 |
| vclz.v | vclz.v vd, vs2, vm | 逐元素统计前导零个数 | 19175/19179 |
| vctz.v | vctz.v vd, vs2, vm | 逐元素统计尾部零个数 | 19232/19236 |
| vcpop.v | vcpop.v vd, vs2, vm | 逐元素统计置位比特数（popcount） | 19202/19206 |
| vrol.vv | vrol.vv vd, vs2, vs1, vm | 逐元素按 vs1 的移位量循环左移 | 19451/19455 |
| vrol.vx | vrol.vx vd, vs2, rs1, vm | 逐元素按 rs1 的移位量循环左移 | 19451/19456 |
| vror.vv | vror.vv vd, vs2, vs1, vm | 逐元素按 vs1 的移位量循环右移 | 19507/19511 |
| vror.vx | vror.vx vd, vs2, rs1, vm | 逐元素按 rs1 的移位量循环右移 | 19507/19512 |
| vror.vi | vror.vi vd, vs2, uimm, vm | 逐元素按立即数移位量循环右移 | 19507/19513 |
| vwsll.vv | vwsll.vv vd, vs2, vs1, vm | 加宽逻辑左移（移位量取自 vs1） | 20177/20181 |
| vwsll.vx | vwsll.vx vd, vs2, rs1, vm | 加宽逻辑左移（移位量取自 rs1） | 20177/20182 |
| vwsll.vi | vwsll.vi vd, vs2, uimm, vm | 加宽逻辑左移（移位量取自立即数） | 20177/20183 |

### Zvbc — Vector Carry-less Multiplication
| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| vclmul.vv | vclmul.vv vd, vs2, vs1, vm | 64 位无进位乘法，返回乘积低半部（vs1 为向量） | 19067/19071 |
| vclmul.vx | vclmul.vx vd, vs2, rs1, vm | 64 位无进位乘法，返回乘积低半部（rs1 为标量） | 19067/19072 |
| vclmulh.vv | vclmulh.vv vd, vs2, vs1, vm | 64 位无进位乘法，返回乘积高半部（vs1 为向量） | 19125/19129 |
| vclmulh.vx | vclmulh.vx vd, vs2, rs1, vm | 64 位无进位乘法，返回乘积高半部（rs1 为标量） | 19125/19130 |

### Zvkb — Vector Cryptography Bit-manipulation（Zvbb 的真子集，无新增助记符）
| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| vandn.vv | vandn.vv vd, vs2, vs1, vm | 按位与非 | 18217/18952 |
| vandn.vx | vandn.vx vd, vs2, rs1, vm | 按位与非（标量 op1） | 18217/18953 |
| vbrev8.v | vbrev8.v vd, vs2, vm | 逐字节比特位反转 | 18218/19037 |
| vrev8.v | vrev8.v vd, vs2, vm | 逐元素字节反转 | 18219/19421 |
| vrol.vv | vrol.vv vd, vs2, vs1, vm | 循环左移（向量移位量） | 18220/19455 |
| vrol.vx | vrol.vx vd, vs2, rs1, vm | 循环左移（标量移位量） | 18220/19456 |
| vror.vv | vror.vv vd, vs2, vs1, vm | 循环右移（向量移位量） | 18221/19511 |
| vror.vx | vror.vx vd, vs2, rs1, vm | 循环右移（标量移位量） | 18221/19512 |
| vror.vi | vror.vi vd, vs2, uimm, vm | 循环右移（立即数移位量） | 18221/19513 |

### Zvkg — Vector GCM/GMAC
| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| vghsh.vv | vghsh.vv vd, vs2, vs1 | GHASH 单次迭代加-乘（Yi+1 = (Yi ⊕ Xi)·H） | 19264/19268 |
| vgmul.vv | vgmul.vv vd, vs2 | GF(2^128) 上 GHASH 域乘法（等价于 vs1=0 的 vghsh.vv） | 19341/19345 |

### Zvkned — NIST Suite: Vector AES Block Cipher
| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| vaesdf.vv | vaesdf.vv vd, vs2 | AES 解密最终轮（密钥取自对应元素组） | 18545/18549 |
| vaesdf.vs | vaesdf.vs vd, vs2 | AES 解密最终轮（vs2 为标量元素组轮密钥） | 18545/18550 |
| vaesdm.vv | vaesdm.vv vd, vs2 | AES 解密中间轮（含 InvMixColumns） | 18600/18604 |
| vaesdm.vs | vaesdm.vs vd, vs2 | AES 解密中间轮（标量元素组轮密钥） | 18600/18605 |
| vaesef.vv | vaesef.vv vd, vs2 | AES 加密最终轮 | 18656/18660 |
| vaesef.vs | vaesef.vs vd, vs2 | AES 加密最终轮（标量元素组轮密钥） | 18656/18661 |
| vaesem.vv | vaesem.vv vd, vs2 | AES 加密中间轮（含 MixColumns） | 18711/18715 |
| vaesem.vs | vaesem.vs vd, vs2 | AES 加密中间轮（标量元素组轮密钥） | 18711/18716 |
| vaeskf1.vi | vaeskf1.vi vd, vs2, uimm | AES-128 正向密钥扩展单轮 | 18767/18771 |
| vaeskf2.vi | vaeskf2.vi vd, vs2, uimm | AES-256 正向密钥扩展单轮（vd 为上一轮轮密钥） | 18828/18832 |
| vaesz.vs | vaesz.vs vd, vs2 | AES 第 0 轮（异或标量元素组轮密钥），仅有 .vs 形式 | 18893/18897 |

### Zvknha / Zvknhb — NIST Suite: Vector SHA-2 Secure Hash
| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| vsha2ch.vv | vsha2ch.vv vd, vs2, vs1 | SHA-2 压缩两轮（取 vs1 中高两个消息调度字） | 19571/19575 |
| vsha2cl.vv | vsha2cl.vv vd, vs2, vs1 | SHA-2 压缩两轮（取 vs1 中低两个消息调度字） | 19571/19576 |
| vsha2ms.vv | vsha2ms.vv vd, vs2, vs1 | SHA-2 消息调度扩展，生成 4 个消息字 | 19679/19683 |

### Zvksed — ShangMi Suite: SM4 Block Cipher
| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| vsm4k.vi | vsm4k.vi vd, vs2, uimm | SM4 密钥扩展，生成 4 个轮密钥 | 19985/19989 |
| vsm4r.vv | vsm4r.vv vd, vs2 | SM4 加/解密四轮（轮密钥取自对应元素组） | 20085/20089 |
| vsm4r.vs | vsm4r.vs vd, vs2 | SM4 加/解密四轮（vs2 为标量元素组轮密钥） | 20085/20090 |

### Zvksh — ShangMi Suite: SM3 Secure Hash
| 助记符 | 操作数形式 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| vsm3me.vv | vsm3me.vv vd, vs2, vs1 | SM3 消息扩展，生成 8 个消息字 | 19891/19895 |
| vsm3c.vi | vsm3c.vi vd, vs2, uimm | SM3 压缩两轮（rnds 指定轮组） | 19770/19774 |

---

- 本范围指令总数（按助记符去重）：**41**
- 各子扩展条数小计：Zvbb 16、Zvbc 4、Zvkb 9（全部为 Zvbb 子集，去重后不新增）、Zvkg 2、Zvkned 11、Zvknha/Zvknhb 3、Zvksed 3、Zvksh 2
- 组合扩展 Zvkn、Zvknc、Zvkng、Zvks、Zvksc、Zvksg 仅为集合简写（18161–18394），Zvkt 仅定义数据无关执行延迟要求（18397–18540），均未定义新助记符。

> 本章另有独立机器抽取交叉校验，按节归类结果为43条（含从Zvbb复用的助记符），与上表41条去重口径一致，差异来自重复计入。

<details>
<summary>按节归类的向量密码学清单（点开）</summary>

### 33.1.5. Instruction Constraints
（共1条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vsm4r.vs` | `vs2 vd` | — | 493 |

### 33.3.1. vaesdf.[vv,vs]
（共2条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vaesdf.vv` | `vd, vs2` | — | 513 |
| `vaesdf.vs` | `vd, vs2` | — | 513 |

### 33.3.2. vaesdm.[vv,vs]
（共2条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vaesdm.vv` | `vd, vs2` | — | 515 |
| `vaesdm.vs` | `vd, vs2` | — | 515 |

### 33.3.3. vaesef.[vv,vs]
（共2条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vaesef.vv` | `vd, vs2` | — | 517 |
| `vaesef.vs` | `vd, vs2` | — | 517 |

### 33.3.4. vaesem.[vv,vs]
（共2条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vaesem.vv` | `vd, vs2` | — | 519 |
| `vaesem.vs` | `vd, vs2` | — | 519 |

### 33.3.5. vaeskf1.vi
（共1条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vaeskf1.vi` | `vd, vs2, uimm` | — | 521 |

### 33.3.6. vaeskf2.vi
（共1条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vaeskf2.vi` | `vd, vs2, uimm` | — | 523 |

### 33.3.7. vaesz.vs
（共1条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vaesz.vs` | `vd, vs2` | — | 525 |

### 33.3.8. vandn.[vv,vx]
（共2条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vandn.vv` | `vd, vs2, vs1, vm` | — | 527 |
| `vandn.vx` | `vd, vs2, rs1, vm` | — | 527 |

### 33.3.9. vbrev.v
（共1条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vbrev.v` | `vd, vs2, vm` | — | 529 |

### 33.3.10. vbrev8.v
（共1条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vbrev8.v` | `vd, vs2, vm` | — | 530 |

### 33.3.11. vclmul.[vv,vx]
（共2条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vclmul.vv` | `vd, vs2, vs1, vm` | — | 531 |
| `vclmul.vx` | `vd, vs2, rs1, vm` | — | 531 |

### 33.3.12. vclmulh.[vv,vx]
（共2条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vclmulh.vv` | `vd, vs2, vs1, vm` | — | 533 |
| `vclmulh.vx` | `vd, vs2, rs1, vm` | — | 533 |

### 33.3.13. vclz.v
（共1条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vclz.v` | `vd, vs2, vm` | — | 535 |

### 33.3.14. vcpop.v
（共1条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vcpop.v` | `vd, vs2, vm` | — | 535 |

### 33.3.15. vctz.v
（共1条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vctz.v` | `vd, vs2, vm` | — | 536 |

### 33.3.16. vghsh.vv
（共1条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vghsh.vv` | `vd, vs2, vs1` | — | 538 |

### 33.3.17. vgmul.vv
（共1条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vgmul.vv` | `vd, vs2` | — | 540 |

### 33.3.18. vrev8.v
（共1条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vrev8.v` | `vd, vs2, vm` | — | 542 |

### 33.3.19. vrol.[vv,vx]
（共2条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vrol.vv` | `vd, vs2, vs1, vm` | — | 543 |
| `vrol.vx` | `vd, vs2, rs1, vm` | — | 543 |

### 33.3.20. vror.[vv,vx,vi]
（共3条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vror.vv` | `vd, vs2, vs1, vm` | — | 545 |
| `vror.vx` | `vd, vs2, rs1, vm` | — | 545 |
| `vror.vi` | `vd, vs2, uimm, vm` | — | 545 |

### 33.3.21. vsha2c[hl].vv
（共2条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vsha2ch.vv` | `vd, vs2, vs1` | — | 547 |
| `vsha2cl.vv` | `vd, vs2, vs1` | — | 547 |

### 33.3.22. vsha2ms.vv
（共2条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vsha2ms.vv` | `vd, vs2, vs1` | — | 550 |
| `vmerge.vvm` | `{W11, W10, W9, W4}, {W11, W10, W9, W8}, {W7, W6, W5, W4}, V0` | — | 550 |

### 33.3.23. vsm3c.vi
（共1条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vsm3c.vi` | `vd, vs2, uimm` | — | 553 |

### 33.3.24. vsm3me.vv
（共1条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vsm3me.vv` | `vd, vs2, vs1` | — | 556 |

### 33.3.25. vsm4k.vi
（共1条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vsm4k.vi` | `vd, vs2, uimm` | — | 559 |

### 33.3.26. vsm4r.[vv,vs]
（共2条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vsm4r.vv` | `vd, vs2` | — | 562 |
| `vsm4r.vs` | `vd, vs2` | — | 562 |

### 33.3.27. vwsll.[vv,vx,vi]
（共3条）

| 助记符 | 操作数 | 说明（规范原文） | 页 |
| --- | --- | --- | --- |
| `vwsll.vv` | `vd, vs2, vs1, vm` | — | 565 |
| `vwsll.vx` | `vd, vs2, rs1, vm` | — | 565 |
| `vwsll.vi` | `vd, vs2, uimm, vm` | — | 565 |

</details>

## 十三、控制流完整性（Zicfilp / Zicfiss，第34章）

### Zicfilp — Landing Pad（前向边控制流完整性）

| 助记符 | 编码依据 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| `LPAD` | 使用 `AUIPC` 主操作码中的 HINT 码点，带 20 位 LPL 标签 | 着陆垫：间接跳转/调用的合法目标点。ELP 处于 LP_EXPECTED 时只有 LPAD 可执行；标签不匹配或 PC 非4字节对齐则触发 software-check 异常；Zicfilp 未启用时是空操作 | 20809、20850、20934、20943 |

### Zicfiss — Shadow Stack（后向边控制流完整性）

| 助记符 | 编码依据 | 功能 | 证据行号 |
| --- | --- | --- | --- |
| `SSPUSH` | `MOP.RR.7`（Zimop），只支持 x1 与 x5 作 rs2 | 把链接寄存器压入影子栈，并把 ssp 减 XLEN/8；仅当存储完成才递减 | 21020、21046、21050 |
| `C.SSPUSH` | `C.MOP.1`（Zcmop） | `SSPUSH x1` 的16位压缩形式，展开为 `SSPUSH x1` | 21021、21049、21051 |
| `SSPOPCHK` | `MOP.R.28`（Zimop），只支持 x1 与 x5 作 rs1 | 从影子栈弹出影子返回地址与链接寄存器比较，不匹配触发 software-check 异常，匹配则 ssp 加 XLEN/8 | 21023、21071、21075 |
| `C.SSPOPCHK` | `C.MOP.5`（Zcmop） | `SSPOPCHK x5` 的16位压缩形式 | 21024、21074、21076 |
| `SSRDP` | `MOP.R.28`（Zimop），`rd` 不可为 x0 | 把影子栈指针 ssp 读到通用寄存器 | 21026、21178、21179 |
| `SSAMOSWAP.W` | 独立的 AMO 式编码（`AMO` + `010011`） | 对影子栈位置原子交换32位数据；RV32 下交换32位，RV64 下交换32位（结果符号扩展） | 21028、21254、21255、21273 |
| `SSAMOSWAP.D` | 同上，仅 RV64 | 对影子栈位置原子交换64位数据 | 21028、21254、21257 |

**要点**：
- 除 `SSAMOSWAP.W/D` 外，Zicfiss 的全部指令都**借用 Zimop/Zcmop 的 May-Be-Operation 编码**，因此在未实现或未激活 Zicfiss 时自动退化为 Zimop/Zcmop 定义的既有行为（21013、21029）。
- `SSAMOSWAP.W/D` 与 A 扩展的 AMO 一样要求 rs1 地址自然对齐，并可选提供 `aq`/`rl` 释放一致性语义（21292、21298）。
- 依赖关系：Zicfiss 依赖 `Zicsr`、`Zimop`、`Zaamo`；若实现了 `Zcmop`，则额外提供 `C.SSPUSH`、`C.SSPOPCHK`（21013、21014）。

**第34章小计：8条**（Zicfilp 1条 + Zicfiss 7条）

## 十四、汇编伪指令总表

伪指令由汇编器展开为真指令，不属于硬件指令集，单列于此。

| 伪指令 | 展开为 | 所属 | 出处 |
| --- | --- | --- | --- |
| `NOP` | `ADDI x0, x0, 0` | RV32I | 规范第2036–2041行 |
| `MV rd, rs` | `ADDI rd, rs, 0` | RV32I | 规范伪指令表 |
| `NOT rd, rs` | `XORI rd, rs, -1` | RV32I | 同上 |
| `NEG rd, rs` | `SUB rd, x0, rs` | RV32I | 同上 |
| `SEQZ rd, rs` | `SLTIU rd, rs, 1` | RV32I | 同上 |
| `SNEZ rd, rs` | `SLTU rd, x0, rs` | RV32I | 同上 |
| `LI rd, imm` | `LUI`+`ADDI` 或单条 `ADDI` | RV32I | 同上 |
| `J offset` | `JAL x0, offset` | RV32I | 同上 |
| `JR rs` | `JALR x0, rs, 0` | RV32I | 同上 |
| `RET` | `JALR x0, x1, 0` | RV32I | 同上 |
| `CALL offset` | `AUIPC`+`JALR`（或 `JAL`） | RV32I | 同上 |
| `SEXT.W rd, rs` | `ADDIW rd, rs, 0` | RV64I | 规范伪指令表 |
| `CSRR rd, csr` | `CSRRS rd, csr, x0` | Zicsr | 同上 |
| `CSRW csr, rs` | `CSRRW x0, csr, rs` | Zicsr | 同上 |
| `CSRS csr, rs` | `CSRRS x0, csr, rs` | Zicsr | 同上 |
| `CSRC csr, rs` | `CSRRC x0, csr, rs` | Zicsr | 同上 |
| `CSRWI / CSRSI / CSRCI` | 对应的立即数形式，rd=x0 | Zicsr | 同上 |
| `RDCYCLE[H] rd` | `CSRRS rd, cycle[h], x0` | Zicntr | 规范第2988行 |
| `RDTIME[H] rd` | `CSRRS rd, time[h], x0` | Zicntr | 规范第2991行 |
| `RDINSTRET[H] rd` | `CSRRS rd, instret[h], x0` | Zicntr | 规范第2995行 |
| `FMV.S / FNEG.S / FABS.S` | `FSGNJ.S` / `FSGNJN.S` / `FSGNJX.S`（rs1=rs2） | F | 规范第5685–5687行 |
| `FRCSR / FSCSR / FRRM / FSRM / FRFLAGS / FSFLAGS` | fcsr/frm/fflags 的 CSR 访问 | F | 规范第5463–5472行 |
| `zext.w` | `packw rd, rs, x0` 或 `add.uw` | Zbb | 规范第30章 |
| `c.sext.w` | `c.addiw rd, 0` | Zcb | 规范第7631行 |
| `RET`（压缩版） | `C.JR x1` | Zca | 规范第28章 |

**说明**：`FMV.S.X`、`FMV.X.S` 是 `FMV.W.X`、`FMV.X.W` 的旧别名；`C.SSPUSH x1`、`C.SSPOPCHK x5` 是 Zcmop 编码上的独立指令而非伪指令。

## 十五、统计与结论

本文档从规范中抽取到的**去重助记符总数：890条**（大小写不敏感，含通配模板，不含伪指令与扩展名）。

若按大小写敏感计数则为896条——差值6条来自同一助记符在不同扩展中分别以大写与小写列出的情形：
Zilsd 的 `ld`/`sd` 与 RV64I 的 `LD`/`SD` 同名，Zclsd 的 `c.ld`/`c.sd`/`c.ldsp`/`c.sdsp` 与 Zca 的 `C.LD`/`C.SD`/`C.LDSP`/`C.SDSP` 同名，Zk\* 与 Zb\* 的指令在密码学章中以大写（Sail 子句名）与小写（正式助记符）两种写法出现。RISC-V 汇编助记符大小写不敏感，故**890条**是更贴近实际的指令种数。

各分片清点的条数如下。注意各分片口径独立、彼此存在复用（例如 Zbkb 的16条同时属于 Zbb；Zclsd 与 RV64C 同名），因此分片之和不等于总数。

| 分片 | 清点条数 |
| --- | --- |
| 基础整数 + CSR + 乘除原子 + 浮点（第36章权威清单，去重） | 228 |
| 基础与小扩展（第2–20章） | 136 |
| 浮点族（第21–27章） | 168 |
| 压缩指令（第28/29/35章） | 70 |
| 位操作（第30章） | 51 |
| 向量扩展（第31章） | 413 |
| 密码学标量（第32章） | 49 |
| 密码学向量（第33章） | 41 |
| 控制流完整性（第34章） | 8 |
| **去重后总计（大小写不敏感）** | **890** |
| 去重后总计（大小写敏感） | 896 |

## 附录A、全部助记符总索引（按字母序）

| 助记符 | 助记符 | 助记符 | 助记符 | 助记符 | 助记符 |
| --- | --- | --- | --- | --- | --- |
| `ADD` | `add.uw` | `ADDI` | `ADDIW` | `ADDW` | `aes64ks1i` |
| `aes64ks2` | `AMOADD.D` | `AMOADD.W` | `AMOAND.D` | `AMOAND.W` | `AMOCAS.D` |
| `AMOCAS.Q` | `AMOCAS.W` | `AMOMAX.D` | `AMOMAX.W` | `AMOMAXU.D` | `AMOMAXU.W` |
| `AMOMIN.D` | `AMOMIN.W` | `AMOMINU.D` | `AMOMINU.W` | `AMOOR.D` | `AMOOR.W` |
| `AMOSWAP.D` | `AMOSWAP.W` | `AMOXOR.D` | `AMOXOR.W` | `AND` | `ANDI` |
| `andn` | `AUIPC` | `bclr` | `bclri` | `BEQ` | `bext` |
| `bexti` | `BGE` | `BGEU` | `binv` | `binvi` | `BLT` |
| `BLTU` | `BNE` | `brev8` | `bset` | `bseti` | `C.ADD` |
| `C.ADDI` | `C.ADDI16SP` | `C.ADDI4SPN` | `C.ADDIW` | `C.ADDW` | `C.AND` |
| `C.ANDI` | `C.BEQZ` | `C.BNEZ` | `C.EBREAK` | `C.FLD` | `C.FLDSP` |
| `C.FLW` | `C.FLWSP` | `C.FSD` | `C.FSDSP` | `C.FSW` | `C.FSWSP` |
| `C.J` | `C.JAL` | `C.JALR` | `C.JR` | `c.lbu` | `C.LD` |
| `C.LDSP` | `c.lh` | `c.lhu` | `C.LI` | `C.LUI` | `C.LW` |
| `C.LWSP` | `C.MOP.1` | `C.MOP.11` | `C.MOP.13` | `C.MOP.15` | `C.MOP.3` |
| `C.MOP.5` | `C.MOP.7` | `C.MOP.9` | `C.MOP.n` | `c.mul` | `C.MV` |
| `C.NOP` | `c.not` | `C.NTL.ALL` | `C.NTL.P1` | `C.NTL.PALL` | `C.NTL.S1` |
| `C.OR` | `c.sb` | `C.SD` | `C.SDSP` | `c.sext.b` | `c.sext.h` |
| `c.sext.w` | `c.sh` | `C.SLLI` | `C.SRAI` | `C.SRLI` | `C.SSPOPCHK` |
| `C.SSPUSH` | `C.SUB` | `C.SUBW` | `C.SW` | `C.SWSP` | `C.XOR` |
| `c.zext.b` | `c.zext.h` | `c.zext.w` | `cbo.clean` | `cbo.flush` | `cbo.inval` |
| `cbo.zero` | `clmul` | `clmulh` | `clmulr` | `clz` | `clzw` |
| `cm.jalt` | `cm.jt` | `cm.mva01s` | `cm.mvsa01` | `cm.pop` | `cm.popret` |
| `cm.popretz` | `cm.push` | `cpop` | `cpopw` | `CSRRC` | `CSRRCI` |
| `CSRRS` | `CSRRSI` | `CSRRW` | `CSRRWI` | `ctz` | `ctzw` |
| `czero.eqz` | `czero.nez` | `DIV` | `DIVU` | `DIVUW` | `DIVW` |
| `EBREAK` | `ECALL` | `FABS.S` | `FADD.D` | `FADD.H` | `FADD.Q` |
| `FADD.S` | `FCLASS.D` | `FCLASS.H` | `FCLASS.Q` | `FCLASS.S` | `FCVT.BF16.S` |
| `FCVT.D.H` | `FCVT.D.L` | `FCVT.D.LU` | `FCVT.D.Q` | `FCVT.D.S` | `FCVT.D.W` |
| `FCVT.D.WU` | `FCVT.H.D` | `FCVT.H.L` | `FCVT.H.LU` | `FCVT.H.Q` | `FCVT.H.S` |
| `FCVT.H.W` | `FCVT.H.WU` | `FCVT.L.D` | `FCVT.L.H` | `FCVT.L.Q` | `FCVT.L.S` |
| `FCVT.LU.D` | `FCVT.LU.H` | `FCVT.LU.Q` | `FCVT.LU.S` | `FCVT.Q.D` | `FCVT.Q.H` |
| `FCVT.Q.L` | `FCVT.Q.LU` | `FCVT.Q.S` | `FCVT.Q.W` | `FCVT.Q.WU` | `FCVT.S.BF16` |
| `FCVT.S.D` | `FCVT.S.H` | `FCVT.S.L` | `FCVT.S.LU` | `FCVT.S.Q` | `FCVT.S.W` |
| `FCVT.S.WU` | `FCVT.W.D` | `FCVT.W.H` | `FCVT.W.Q` | `FCVT.W.S` | `FCVT.WU.D` |
| `FCVT.WU.H` | `FCVT.WU.Q` | `FCVT.WU.S` | `FCVTMOD.W.D` | `FDIV.D` | `FDIV.H` |
| `FDIV.Q` | `FDIV.S` | `FENCE` | `FENCE.I` | `FENCE.TSO` | `FEQ.D` |
| `FEQ.H` | `FEQ.Q` | `FEQ.S` | `FLD` | `FLE.D` | `FLE.H` |
| `FLE.Q` | `FLE.S` | `FLEQ.D` | `FLEQ.H` | `FLEQ.Q` | `FLEQ.S` |
| `FLH` | `FLI.D` | `FLI.H` | `FLI.Q` | `FLI.S` | `FLQ` |
| `FLT.D` | `FLT.H` | `FLT.Q` | `FLT.S` | `FLTQ.D` | `FLTQ.H` |
| `FLTQ.Q` | `FLTQ.S` | `FLW` | `FMADD.D` | `FMADD.H` | `FMADD.Q` |
| `FMADD.S` | `FMAX.D` | `FMAX.H` | `FMAX.Q` | `FMAX.S` | `FMAXM.D` |
| `FMAXM.H` | `FMAXM.Q` | `FMAXM.S` | `FMIN.D` | `FMIN.H` | `FMIN.Q` |
| `FMIN.S` | `FMINM.D` | `FMINM.H` | `FMINM.Q` | `FMINM.S` | `FMSUB.D` |
| `FMSUB.H` | `FMSUB.Q` | `FMSUB.S` | `FMUL.D` | `FMUL.H` | `FMUL.Q` |
| `FMUL.S` | `FMV.D.X` | `FMV.H.X` | `FMV.S` | `FMV.W.X` | `FMV.X.D` |
| `FMV.X.H` | `FMV.X.W` | `FMVH.X.D` | `FMVH.X.Q` | `FMVP.D.X` | `FMVP.Q.X` |
| `FNEG.S` | `FNMADD.D` | `FNMADD.H` | `FNMADD.Q` | `FNMADD.S` | `FNMSUB.D` |
| `FNMSUB.H` | `FNMSUB.Q` | `FNMSUB.S` | `FRCSR` | `FRFLAGS` | `FROUND.D` |
| `FROUND.H` | `FROUND.Q` | `FROUND.S` | `FROUNDNX.D` | `FROUNDNX.H` | `FROUNDNX.Q` |
| `FROUNDNX.S` | `FRRM` | `FSCSR` | `FSD` | `FSFLAGS` | `FSGNJ.D` |
| `FSGNJ.H` | `FSGNJ.Q` | `FSGNJ.S` | `FSGNJN.D` | `FSGNJN.H` | `FSGNJN.Q` |
| `FSGNJN.S` | `FSGNJX.D` | `FSGNJX.H` | `FSGNJX.Q` | `FSGNJX.S` | `FSH` |
| `FSQ` | `FSQRT.D` | `FSQRT.H` | `FSQRT.Q` | `FSQRT.S` | `FSRM` |
| `FSUB.D` | `FSUB.H` | `FSUB.Q` | `FSUB.S` | `FSW` | `JAL` |
| `JALR` | `LB` | `lb.{aq,aqrl}` | `LBU` | `LD` | `ld.{aq,aqrl}` |
| `LH` | `lh.{aq,aqrl}` | `LHU` | `LPAD` | `LR.D` | `LR.W` |
| `LUI` | `LW` | `lw.{aq,aqrl}` | `LWU` | `max` | `maxu` |
| `min` | `minu` | `MOP.R.n` | `MOP.RR.n` | `MUL` | `MULH` |
| `MULHSU` | `MULHU` | `MULW` | `NOP` | `NTL.ALL` | `NTL.P1` |
| `NTL.PALL` | `NTL.S1` | `OR` | `orc.b` | `ORI` | `orn` |
| `pack` | `packh` | `packw` | `PAUSE` | `prefetch.i` | `prefetch.r` |
| `prefetch.w` | `RDCYCLE` | `RDCYCLEH` | `RDINSTRET` | `RDINSTRETH` | `RDTIME` |
| `RDTIMEH` | `REM` | `REMU` | `REMUW` | `REMW` | `rev8` |
| `rol` | `rolw` | `ror` | `rori` | `roriw` | `rorw` |
| `SB` | `sb.{rl,aqrl}` | `SC.D` | `SC.W` | `SD` | `sd.{rl,aqrl}` |
| `sext.b` | `sext.h` | `SH` | `sh.{rl,aqrl}` | `sh1add` | `sh1add.uw` |
| `sh2add` | `sh2add.uw` | `sh3add` | `sh3add.uw` | `SLL` | `SLLI` |
| `slli.uw` | `SLLIW` | `SLLW` | `SLT` | `SLTI` | `SLTIU` |
| `SLTU` | `SRA` | `SRAI` | `SRAIW` | `SRAW` | `SRL` |
| `SRLI` | `SRLIW` | `SRLW` | `SSAMOSWAP.D` | `SSAMOSWAP.W` | `SSPOPCHK` |
| `SSPUSH` | `SSRDP` | `SUB` | `SUBW` | `SW` | `sw.{rl,aqrl}` |
| `unzip` | `vaadd.vv` | `vaadd.vx` | `vaaddu.vv` | `vaaddu.vx` | `vadc.vim` |
| `vadc.vvm` | `vadc.vxm` | `vadd.vi` | `vadd.vv` | `vadd.vx` | `vaesdf.vs` |
| `vaesdf.vv` | `vaesdm.vs` | `vaesdm.vv` | `vaesef.vs` | `vaesef.vv` | `vaesem.vs` |
| `vaesem.vv` | `vaeskf1.vi` | `vaeskf2.vi` | `vaesz.vs` | `vand.vi` | `vand.vv` |
| `vand.vx` | `vandn.vv` | `vandn.vx` | `vasub.vv` | `vasub.vx` | `vasubu.vv` |
| `vasubu.vx` | `vbrev.v` | `vbrev8.v` | `vclmul.vv` | `vclmul.vx` | `vclmulh.vv` |
| `vclmulh.vx` | `vclz.v` | `vcompress.vm` | `vcpop.m` | `vcpop.v` | `vctz.v` |
| `vdiv.vv` | `vdiv.vx` | `vdivu.vv` | `vdivu.vx` | `vfadd.vf` | `vfadd.vv` |
| `vfclass.v` | `vfcvt.f.x.v` | `vfcvt.f.xu.v` | `vfcvt.rtz.x.f.v` | `vfcvt.rtz.xu.f.v` | `vfcvt.x.f.v` |
| `vfcvt.xu.f.v` | `vfdiv.vf` | `vfdiv.vv` | `vfirst.m` | `vfmacc.vf` | `vfmacc.vv` |
| `vfmadd.vf` | `vfmadd.vv` | `vfmax.vf` | `vfmax.vv` | `vfmerge.vfm` | `vfmin.vf` |
| `vfmin.vv` | `vfmsac.vf` | `vfmsac.vv` | `vfmsub.vf` | `vfmsub.vv` | `vfmul.vf` |
| `vfmul.vv` | `vfmv.f.s` | `vfmv.s.f` | `vfmv.v.f` | `vfncvt.f.f.w` | `vfncvt.f.x.w` |
| `vfncvt.f.xu.w` | `vfncvt.rod.f.f.w` | `vfncvt.rtz.x.f.w` | `vfncvt.rtz.xu.f.w` | `vfncvt.x.f.w` | `vfncvt.xu.f.w` |
| `vfncvtbf16.f.f.w` | `vfneg.v` | `vfnmacc.vf` | `vfnmacc.vv` | `vfnmadd.vf` | `vfnmadd.vv` |
| `vfnmsac.vf` | `vfnmsac.vv` | `vfnmsub.vf` | `vfnmsub.vv` | `vfrdiv.vf` | `vfrec7.v` |
| `vfredmax.vs` | `vfredmin.vs` | `vfredosum.vs` | `vfredusum.vs` | `vfrsqrt7.v` | `vfrsub.vf` |
| `vfsgnj.vf` | `vfsgnj.vv` | `vfsgnjn.vf` | `vfsgnjn.vv` | `vfsgnjx.vf` | `vfsgnjx.vv` |
| `vfslide1down.vf` | `vfslide1up.vf` | `vfsqrt.v` | `vfsub.vf` | `vfsub.vv` | `vfwadd.vf` |
| `vfwadd.vv` | `vfwadd.wf` | `vfwadd.wv` | `vfwcvt.f.f.v` | `vfwcvt.f.x.v` | `vfwcvt.f.xu.v` |
| `vfwcvt.rtz.x.f.v` | `vfwcvt.rtz.xu.f.v` | `vfwcvt.x.f.v` | `vfwcvt.xu.f.v` | `vfwcvtbf16.f.f.v` | `vfwmacc.vf` |
| `vfwmacc.vv` | `VFWMACCBF16` | `vfwmsac.vf` | `vfwmsac.vv` | `vfwmul.vf` | `vfwmul.vv` |
| `vfwnmacc.vf` | `vfwnmacc.vv` | `vfwnmsac.vf` | `vfwnmsac.vv` | `vfwredosum.vs` | `vfwredusum.vs` |
| `vfwsub.vf` | `vfwsub.vv` | `vfwsub.wf` | `vfwsub.wv` | `vghsh.vv` | `vgmul.vv` |
| `vid.v` | `viota.m` | `vl1r.v` | `vl1re16.v` | `vl1re32.v` | `vl1re64.v` |
| `vl1re8.v` | `vl2r.v` | `vl2re16.v` | `vl2re32.v` | `vl2re64.v` | `vl2re8.v` |
| `vl4r.v` | `vl4re16.v` | `vl4re32.v` | `vl4re64.v` | `vl4re8.v` | `vl8r.v` |
| `vl8re16.v` | `vl8re32.v` | `vl8re64.v` | `vl8re8.v` | `vle16.v` | `vle16ff.v` |
| `vle32.v` | `vle32ff.v` | `vle64.v` | `vle64ff.v` | `vle8.v` | `vle8ff.v` |
| `vlm.v` | `vloxei16.v` | `vloxei32.v` | `vloxei64.v` | `vloxei8.v` | `vloxseg<nf>ei<eew>.v` |
| `vlse16.v` | `vlse32.v` | `vlse64.v` | `vlse8.v` | `vlseg2e32.v` | `vlseg3e8.v` |
| `vlseg8e8.v` | `vlseg<nf>e<eew>.v` | `vlseg<nf>e<eew>ff.v` | `vlsseg3e8.v` | `vlsseg<nf>e<eew>.v` | `vluxei16.v` |
| `vluxei32.v` | `vluxei64.v` | `vluxei8.v` | `vluxseg3ei8.v` | `vluxseg<nf>ei<eew>.v` | `vmacc.vv` |
| `vmacc.vx` | `vmadc.vi` | `vmadc.vim` | `vmadc.vv` | `vmadc.vvm` | `vmadc.vx` |
| `vmadc.vxm` | `vmadd.vv` | `vmadd.vx` | `vmand.mm` | `vmandn.mm` | `vmax.vv` |
| `vmax.vx` | `vmaxu.vv` | `vmaxu.vx` | `vmclr.m` | `vmerge.vim` | `vmerge.vvm` |
| `vmerge.vxm` | `vmfeq.vf` | `vmfeq.vv` | `vmfge.vf` | `vmfgt.vf` | `vmfgt.vv` |
| `vmfle.vf` | `vmfle.vv` | `vmflt.vf` | `vmflt.vv` | `vmfne.vf` | `vmfne.vv` |
| `vmin.vv` | `vmin.vx` | `vminu.vv` | `vminu.vx` | `vmmv.m` | `vmnand.mm` |
| `vmnor.mm` | `vmnot.m` | `vmor.mm` | `vmorn.mm` | `vmsbc.vv` | `vmsbc.vvm` |
| `vmsbc.vx` | `vmsbc.vxm` | `vmsbf.m` | `vmseq.vi` | `vmseq.vv` | `vmseq.vx` |
| `vmset.m` | `vmsgt.vi` | `vmsgt.vx` | `vmsgtu.vi` | `vmsgtu.vx` | `vmsif.m` |
| `vmsle.vi` | `vmsle.vv` | `vmsle.vx` | `vmsleu.vi` | `vmsleu.vv` | `vmsleu.vx` |
| `vmslt.vv` | `vmslt.vx` | `vmsltu.vv` | `vmsltu.vx` | `vmsne.vi` | `vmsne.vv` |
| `vmsne.vx` | `vmsof.m` | `vmul.vv` | `vmul.vx` | `vmulh.vv` | `vmulh.vx` |
| `vmulhsu.vv` | `vmulhsu.vx` | `vmulhu.vv` | `vmulhu.vx` | `vmv.s.x` | `vmv.v.i` |
| `vmv.v.v` | `vmv.v.x` | `vmv.x.s` | `vmv1r.v` | `vmv2r.v` | `vmv4r.v` |
| `vmv8r.v` | `vmv<nr>r.v` | `vmxnor.mm` | `vmxor.mm` | `vnclip.wi` | `vnclip.wv` |
| `vnclip.wx` | `vnclipu.wi` | `vnclipu.wv` | `vnclipu.wx` | `vnmsac.vv` | `vnmsac.vx` |
| `vnmsub.vv` | `vnmsub.vx` | `vnsra.wi` | `vnsra.wv` | `vnsra.wx` | `vnsrl.wi` |
| `vnsrl.wv` | `vnsrl.wx` | `vor.vi` | `vor.vv` | `vor.vx` | `vredand.vs` |
| `vredmax.vs` | `vredmaxu.vs` | `vredmin.vs` | `vredminu.vs` | `vredor.vs` | `vredsum.vs` |
| `vredxor.vs` | `vrem.vv` | `vrem.vx` | `vremu.vv` | `vremu.vx` | `vrev8.v` |
| `vrgather.vi` | `vrgather.vv` | `vrgather.vx` | `vrgatherei16.vv` | `vrol.vv` | `vrol.vx` |
| `vror.vi` | `vror.vv` | `vror.vx` | `vrsub.vi` | `vrsub.vx` | `vs1r.v` |
| `vs2r.v` | `vs4r.v` | `vs8r.v` | `vsadd.vi` | `vsadd.vv` | `vsadd.vx` |
| `vsaddu.vi` | `vsaddu.vv` | `vsaddu.vx` | `vsbc.vvm` | `vsbc.vxm` | `vse16.v` |
| `vse32.v` | `vse64.v` | `vse8.v` | `vsetivli` | `vsetvl` | `vsetvli` |
| `vsext.vf2` | `vsext.vf4` | `vsext.vf8` | `vsha2ch.vv` | `vsha2cl.vv` | `vsha2ms.vv` |
| `vslide1down.vx` | `vslide1up.vx` | `vslidedown.vi` | `vslidedown.vx` | `vslideup.vi` | `vslideup.vx` |
| `vsll.vi` | `vsll.vv` | `vsll.vx` | `vsm.v` | `vsm3c.vi` | `vsm3me.vv` |
| `vsm4k.vi` | `vsm4r.vs` | `vsm4r.vv` | `vsmul.vv` | `vsmul.vx` | `vsoxei16.v` |
| `vsoxei32.v` | `vsoxei64.v` | `vsoxei8.v` | `vsoxseg<nf>ei<eew>.v` | `vsra.vi` | `vsra.vv` |
| `vsra.vx` | `vsrl.vi` | `vsrl.vv` | `vsrl.vx` | `vsse16.v` | `vsse32.v` |
| `vsse64.v` | `vsse8.v` | `vsseg3e32.v` | `vsseg<nf>e<eew>.v` | `vssra.vi` | `vssra.vv` |
| `vssra.vx` | `vssrl.vi` | `vssrl.vv` | `vssrl.vx` | `vssseg2e32.v` | `vssseg<nf>e<eew>.v` |
| `vssub.vv` | `vssub.vx` | `vssubu.vv` | `vssubu.vx` | `vsub.vv` | `vsub.vx` |
| `vsuxei16.v` | `vsuxei32.v` | `vsuxei64.v` | `vsuxei8.v` | `vsuxseg2ei32.v` | `vsuxseg<nf>ei<eew>.v` |
| `vwadd.vv` | `vwadd.vx` | `vwadd.wv` | `vwadd.wx` | `vwaddu.vv` | `vwaddu.vx` |
| `vwaddu.wv` | `vwaddu.wx` | `vwmacc.vv` | `vwmacc.vx` | `vwmaccsu.vv` | `vwmaccsu.vx` |
| `vwmaccu.vv` | `vwmaccu.vx` | `vwmaccus.vx` | `vwmul.vv` | `vwmul.vx` | `vwmulsu.vv` |
| `vwmulsu.vx` | `vwmulu.vv` | `vwmulu.vx` | `vwredsum.vs` | `vwredsumu.vs` | `vwsll.vi` |
| `vwsll.vv` | `vwsll.vx` | `vwsub.vv` | `vwsub.vx` | `vwsub.wv` | `vwsub.wx` |
| `vwsubu.vv` | `vwsubu.vx` | `vwsubu.wv` | `vwsubu.wx` | `vxor.vi` | `vxor.vv` |
| `vxor.vx` | `vzext.vf2` | `vzext.vf4` | `vzext.vf8` | `WRS.NTO` | `WRS.STO` |
| `xnor` | `XOR` | `XORI` | `xperm4` | `xperm8` | `zext.h` |
| `zext.w` | `zip` |  |  |  |  |

共890条（大小写不敏感去重）。

