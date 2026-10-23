# minirv 阶段 A：详细搭建步骤（鼠标级）

> **目标**：32 位框架 + `addi` + `jalr` 两条指令
> **时间**：约 3 小时
> **产出**：`minirv.circ`，能跑 `addi` 累加程序
>
> **⚠️ 一天半时间，先做这个，做完再考虑阶段 B**

---

## 目录

- [第 0 步：准备工作](#第-0-步准备工作)
- [第 1 步：模块 `pc`](#第-1-步模块-pc)
- [第 2 步：模块 `rom`](#第-2-步模块-rom)
- [第 3 步：模块 `dec`](#第-3-步模块-dec)
- [第 4 步：模块 `gpr`](#第-4-步模块-gpr)
- [第 5 步：模块 `alu`](#第-5-步模块-alu)
- [第 6 步：顶层 `minirv`](#第-6-步顶层-minirv)
- [第 7 步：验证](#第-7-步验证)

---

## 第 0 步：准备工作

### 0.1 新建文件

```
① 打开 Logisim-evolution
② File → New（新建空白工程）
③ File → Save As... → 保存为 minirv.circ
```

**⚠️ 一定要 **另存为 `minirv.circ`** —— **不要覆盖 `wholeF6.circ`** ⚠️

### 0.2 建 6 个电路页

```
① Project → Add Circuit...
② 依次建（顺序很重要）：
     1. pc
     2. rom
     3. dec
     4. gpr
     5. alu
     6. minirv        ← 顶层，最后建
```

**为什么这个顺序**：**先做"叶子模块"，最后拼顶层** ✅

**⚠️ 建完后，左边电路列表应该是**：

```
（顶部）
  minirv     ← 顶层
  alu
  gpr
  dec
  rom
  pc
  main       ← 可以删掉，或者留着
```

---

## 第 1 步：模块 `pc`

### 1.1 接口

| 端口 | 方向 | 位宽 |
| --- | :-: | :-: |
| **`pc_next`** | 输入 | **32** |
| **`clk`** | 输入 | 1 |
| **`pc_out`** | 输出 | **32** |

### 1.2 操作（5 分钟）

```
① 点左侧 pc 电路页
② 元件库 → Memory → Register
③ 拖出来，属性栏：
     Data Bits = 32        ⚠️ 不是 8
     Label     = pc_reg
④ 元件库 → Wiring → Pin，放 2 个输入 + 1 个输出：
     【pc_next】Data Bits = 32，Output? = No
     【clk】   Data Bits = 1， Output? = No
     【pc_out】Data Bits = 32，Output? = Yes，Facing = West
⑤ 元件库 → Wiring → Constant，放 2 个：
     【常量 1】Data Bits = 1，Value = 1   → 接 WE
     【常量 0】Data Bits = 1，Value = 0   → 接 Clear
⑥ 连线（5 条）：
     pc_next    → Register.D
     clk        → Register 的 clock（左下三角）
     常量 1     → Register.WE
     常量 0     → Register.Clear
     Register.Q → pc_out
⑦ Ctrl + S
```

### 1.3 验证

```
① 在 pc 页里进仿真模式
② 设 pc_next = 100
③ 点 clk 两次（0→1→0）
④ pc_out 应该 = 100
```

**—— 通过就对了** ✅

---

## 第 2 步：模块 `rom`

### 2.1 接口

| 端口 | 方向 | 位宽 |
| --- | :-: | ---: |
| **`addr`** | 输入 | **8**（256 条指令）|
| **`instr`** | 输出 | **32** |

### 2.2 操作（5 分钟）

```
① 点左侧 rom 电路页
② 元件库 → Memory → ROM
③ 属性栏：
     Address Bit Width = 8
     Data Bit Width    = 32       ⚠️ 不是 8
④ 元件库 → Wiring → Pin，放 2 个：
     【addr】Data Bits = 8，Output? = No
     【instr】Data Bits = 32，Output? = Yes，Facing = West
⑤ 连线：
     addr  → ROM 的 A
     ROM 的 D → instr
⑥ Ctrl + S
```

### 2.3 填测试程序（**先不填，等顶层做好再填**）

**—— 先留空（全 0）** ✅

---

## 第 3 步：模块 `dec`（**最复杂，40 分钟**）

### 3.1 接口

**输入**：`instr`（32 位）

**输出（阶段 A 只要 5 个）**：

| 输出 | 位宽 | 说明 |
| --- | :-: | --- |
| **`is_addi`** | 1 | 是不是 addi |
| **`is_jalr`** | 1 | 是不是 jalr |
| **`rd`** | **5** | 目的寄存器 |
| **`rs1`** | **5** | 源寄存器 1 |
| **`imm_i`** | **32** | I 型立即数（符号扩展后）|

**⚠️ 阶段 A 先不做 `is_add`/`is_lui`/`is_lw` 等**（阶段 B/C 再加）✅

### 3.2 放输入引脚

```
① 元件库 → Wiring → Pin
② 属性：
     Label     = instr
     Data Bits = 32
     Output?   = No
```

### 3.3 放 Splitter #1（拆主要字段）

```
① 元件库 → Wiring → Splitter
② 属性栏逐项设：

     Input Bit Width = 32
     Fan Out         = 7

     Bit 0  = 0
     Bit 1  = 0
     Bit 2  = 0
     Bit 3  = 0
     Bit 4  = 0
     Bit 5  = 0
     Bit 6  = 0            ← bit 0~6 → opcode（输出 0）

     Bit 7  = 1
     Bit 8  = 1
     Bit 9  = 1
     Bit 10 = 1
     Bit 11 = 1            ← bit 7~11 → rd（输出 1）

     Bit 12 = 2
     Bit 13 = 2
     Bit 14 = 2            ← bit 12~14 → funct3（输出 2）

     Bit 15 = 3
     Bit 16 = 3
     Bit 17 = 3
     Bit 18 = 3
     Bit 19 = 3            ← bit 15~19 → rs1（输出 3）

     Bit 20 = 4
     Bit 21 = 4
     Bit 22 = 4
     Bit 23 = 4
     Bit 24 = 4            ← bit 20~24 → rs2（输出 4）

     Bit 25 = 5
     Bit 26 = 5
     Bit 27 = 5
     Bit 28 = 5
     Bit 29 = 5
     Bit 30 = 5
     Bit 31 = 5            ← bit 25~31 → funct7（输出 5）

     （输出 6 不用）

③ instr → Splitter #1 的输入
```

**⚠️ 属性栏是"位号 → 路号"的映射** —— **`Bit N = X` 表示"第 N 位分到第 X 路"** ✅

### 3.4 放比较器（检测 `addi` / `jalr`）

**`addi` 的 opcode = `0010011`（7 位）**

```
① 元件库 → Arithmetic → Comparator
② 属性：
     Numeric Width = 7
③ 引脚：
     A ← Splitter #1 输出 0（opcode，7 位）
     B ← 常量（Data Bits = 7，Value = 0010011）
④ "=" 输出 → 记为 is_addi_raw
```

**`jalr` 的 opcode = `1100111`**

```
⑤ 再放一个 Comparator（Numeric Width = 7）
     A ← opcode
     B ← 常量 7 位，Value = 1100111
     输出 → 记为 is_jalr_raw
```

**⚠️ 但 `addi`/`jalr` 还要检查 `funct3 == 000`**（严格来说）

**阶段 A 可以简化**：**只检查 opcode**（因为测试程序只用 funct3=000）

**—— 但为了正确性，建议还是加**：

```
⑥ 再放一个 Comparator（Numeric Width = 3）
     A ← funct3（Splitter 输出 2）
     B ← 常量 3 位，Value = 000
     输出 → funct3_ok

⑦ AND 门：
     is_addi = is_addi_raw AND funct3_ok
     is_jalr = is_jalr_raw AND funct3_ok
```

**嗯，简化：`addi` 和 `jalr` 的 funct3 都是 `000`** —— **共用一个 `funct3_ok`** ✅

### 3.5 放输出引脚 `rd`、`rs1`

```
① Pin → Label = rd，Data Bits = 5，Output? = Yes，Facing = West
② Pin → Label = rs1，Data Bits = 5，Output? = Yes，Facing = West
③ 连线：
     Splitter #1 输出 1（rd）→ rd
     Splitter #1 输出 3（rs1）→ rs1
```

### 3.6 ⭐ 放 Splitter #2（拆 I 型立即数）+ 符号扩展

**I 型 `imm[11:0]` 在 bit 31~20**

```
① 放 Splitter #2
② 属性：
     Input Bit Width = 32
     Fan Out         = 2
     Bit 0~19 = 0          （低 20 位，不用）
     Bit 20~31 = 1         （12 位 imm）
③ instr → Splitter #2 的输入
④ Splitter #2 输出 1（12 位）= imm_i_raw
```

**符号扩展（12 → 32）**：

```
⑤ 元件库 → Wiring → Bit Extender
⑥ 属性：
     Input Bit Width  = 12
     Output Bit Width = 32
     Type             = 【Sign Extend】    ⚠️ 不是 Zero！
⑦ imm_i_raw → Bit Extender 输入
⑧ Bit Extender 输出（32 位）→ imm_i 引脚
```

**⚠️ 必须选 `Sign Extend`** —— **因为 `imm` 可以是负数**（比如 `addi x1, x0, -5`）⚠️

### 3.7 放输出引脚 `is_addi`、`is_jalr`、`imm_i`

```
① Pin → Label = is_addi，Data Bits = 1，Output? = Yes
② Pin → Label = is_jalr，Data Bits = 1，Output? = Yes
③ Pin → Label = imm_i，Data Bits = 32，Output? = Yes
④ 连线（见上面各步）
```

### 3.8 `dec` 的完整引脚清单（**7 个**）

| 引脚 | 方向 | 位宽 |
| --- | :-: | :-: |
| `instr` | 输入 | 32 |
| `is_addi` | 输出 | 1 |
| `is_jalr` | 输出 | 1 |
| `rd` | 输出 | 5 |
| `rs1` | 输出 | 5 |
| `imm_i` | 输出 | 32 |

**⚠️ 只有 `instr` 是输入，其余全是输出** ✅

### 3.9 验证 `dec`

**在 `dec` 页里**：

```
① 进仿真模式
② 设 instr = 00500093（十六进制）—— 这是 addi x1, x0, 5
③ 看输出：
     is_addi = 1
     is_jalr = 0
     rd      = 1
     rs1     = 0
     imm_i   = 5
```

**再测 `jalr x0, 0(x0)`（`00000067`）**：

```
is_jalr = 1
is_addi = 0
rd      = 0
rs1     = 0
imm_i   = 0
```

**—— 都对，`dec` 就完成了** ✅

---

## 第 4 步：模块 `gpr`（**60 分钟**）

### 4.1 接口

| 端口 | 方向 | 位宽 |
| --- | :-: | ---: |
| **`raddr1`** | 输入 | **5** |
| **`rdata1`** | 输出 | **32** |
| **`raddr2`** | 输入 | **5** |
| **`rdata2`** | 输出 | **32** |
| **`waddr`** | 输入 | **5** |
| **`wdata`** | 输入 | **32** |
| **`wen`** | 输入 | 1 |
| **`clk`** | 输入 | 1 |

### 4.2 放 16 个 32 位 Register

```
① 元件库 → Memory → Register
② 放 16 个，属性：
     Data Bits = 32
     Label     = x0、x1、x2、…、x15
③ 排成 4 行 × 4 列（或者 16 行）
```

**⚠️ 16 个寄存器，占地较大** —— **建议排成 16 行，每行间距 60** ✅

### 4.3 放 2 个 4 选 16 MUX（读口）

```
① 元件库 → Plexers → Multiplexer
② 属性：
     Select Bits = 4          ⚠️ 4 位（16 选 1）
     Data Bits   = 32
③ 放 2 个（MUX1、MUX2）
```

**⚠️ `Select Bits = 4` → 16 个数据输入 `D0~D15`** ✅

### 4.4 读口连线

```
① raddr1 的【低 4 位】→ MUX1 的 S
     ⚠️ raddr1 是 5 位，MUX 的 S 是 4 位
     → 用 Splitter 取 raddr1[3:0]
     
     放 Splitter：
       Input Bit Width = 5
       Fan Out = 2
       Bit 0~3 = 0     （4 位 → MUX 的 S）
       Bit 4   = 1     （不用）

② MUX1 的 D0~D15 ← x0~x15 的 Q
③ MUX1 的 Y → rdata1 引脚
④ raddr2 同理 → MUX2 → rdata2
```

### 4.5 写口：译码 + 与门

```
① 元件库 → Plexers → Decoder
② 属性：
     Select Bits = 4          （4-16 译码器）
③ waddr[3:0]（同样用 Splitter 取低 4 位）→ Decoder 的输入
④ 元件库 → Gates → AND Gate
⑤ 放 16 个 AND 门
⑥ 每个 AND：
     In1 ← Decoder 的 Y_i
     In2 ← wen
     Out → Reg_i 的 WE
```

### 4.6 ⭐ `R[0]` 恒为 0 的处理

**两种做法**：

**做法 A（推荐）：`waddr == 0` 时不写**

```
① waddr 是 5 位
② 放一个 5 输入 NOR 门：
     In1~In5 ← waddr[4:0]
     输出 = 1 当且仅当 waddr == 0
③ 放一个 NOT 门，把 NOR 输出取反 → "waddr != 0"
④ 把 "waddr != 0" 接到所有 AND 门的 **第三个输入**
     （AND 门改成 3 输入）
```

**—— 这样 `waddr == 0` 时，所有 WE 都是 0** ✅

**做法 B（更简单）：读 `x0` 时返回 0**

```
不需要改写口，只改读口：
  rdata1 = (raddr1 == 0) ? 0 : MUX1.Y
```

**✅ 阶段 A 用做法 B（简单）**：

```
① MUX1 的 Y → 2 选 1 MUX 的 D0
② 常量 0（32 位）→ 2 选 1 MUX 的 D1
③ S ← (raddr1 == 0)
④ 2 选 1 MUX 的 Y → rdata1
```

**⚠️ `(raddr1 == 0)` 用 5 输入 NOR 门** ✅

### 4.7 写数据广播

```
① wdata（32 位）→ 16 个 Reg 的 D（并联）
```

**—— 一个输出驱动 16 个输入，Logisim 允许** ✅

### 4.8 时钟

```
① clk → 16 个 Reg 的 clock（并联）
```

### 4.9 `gpr` 引脚清单（**8 个**）

| 引脚 | 方向 | 位宽 |
| --- | :-: | :-: |
| `raddr1` | 输入 | 5 |
| `raddr2` | 输入 | 5 |
| `waddr` | 输入 | 5 |
| `wdata` | 输入 | 32 |
| `wen` | 输入 | 1 |
| `clk` | 输入 | 1 |
| `rdata1` | 输出 | 32 |
| `rdata2` | 输出 | 32 |

### 4.10 验证 `gpr`

```
① 进仿真模式
② wen = 1，waddr = 3，wdata = 100
③ 打一拍
④ raddr1 = 3 → rdata1 应该 = 100
⑤ raddr1 = 0 → rdata1 应该 = 0（因为 x0 恒 0）
⑥ waddr = 0，wdata = 999，wen = 1
⑦ 打一拍
⑧ raddr1 = 0 → rdata1 还是 0 ✅
```

---

## 第 5 步：模块 `alu`（**10 分钟**）

### 5.1 接口

| 端口 | 方向 | 位宽 |
| --- | :-: | :-: |
| **`A`** | 输入 | 32 |
| **`B`** | 输入 | 32 |
| **`result`** | 输出 | 32 |
| **`zero`** | 输出 | 1 |

### 5.2 操作

```
① 元件库 → Arithmetic → Adder
② 属性：
     Data Bits = 32
③ Pin：A（32 位）、B（32 位）、result（32 位，输出）
④ 连线：A → Adder.A、B → Adder.B、Adder.S → result

⑤ （可选）比较器：A == B → zero
     元件库 → Arithmetic → Comparator
     Numeric Width = 32
```

**阶段 A 只需要"加法"** ✅

---

## 第 6 步：顶层 `minirv`（**40 分钟**）

### 6.1 放 5 个子电路

```
① 点左侧 minirv 电路页
② 从左侧电路列表拖出：
     pc、rom、dec、gpr、alu
③ 排布建议：
     pc（左）→ rom（中）→ dec（右）
     gpr（右下）→ alu（最右）
```

### 6.2 ⭐ 关键连线：`PC[9:2] → ROM.addr`

**⚠️ 这是最容易错的地方**（见方案第二章）

```
① 放一个 Splitter（在主电路里，不是子电路里）
② 属性：
     Input Bit Width = 32
     Fan Out         = 3
     Bit 0~1  = 0       （丢弃：字节内偏移）
     Bit 2~9  = 1       （8 位 → ROM 地址）⭐
     Bit 10~31 = 2      （丢弃）
③ pc.pc_out（32 位）→ Splitter 输入
④ Splitter 输出 1（8 位）→ rom.addr
```

**—— `PC=0` → ROM 地址 0；`PC=4` → ROM 地址 1** ✅

### 6.3 其余连线

| # | 从 | 到 |
| :-: | --- | --- |
| 1 | `pc.pc_out` | **Splitter → `rom.addr`**（见 6.2）|
| 2 | `rom.instr` | `dec.instr` |
| 3 | `dec.rd` | `gpr.waddr` |
| 4 | `dec.rs1` | `gpr.raddr1` |
| 5 | **`dec.rs1`** | **`alu.A`**（阶段 A 用 rs1 当 A）|
| 6 | **`dec.imm_i`** | **`alu.B`** |
| 7 | `alu.result` | `gpr.wdata` |
| 8 | **`dec.is_addi`** | **`gpr.wen`** |
| 9 | `clk`（Clock 元件）| `pc.clk`、`gpr.clk` |
| 10 | 常量 0 | `pc.rst`（或者 `clear`）|

**⚠️ 阶段 A 的简化**：
- **`is_addi` 直接接 `wen`**（`jalr` 不写 GPR，符合"`jalr x0` 不写"）✅
- **`raddr2` / `rdata2` 暂时不接**（阶段 B 才用）⚠️

**⚠️ `raddr2` 悬空会显示 `u`** —— **接常量 0 占位** ✅

### 6.4 PC 更新：`PC + 4`（**注意是 +4，不是 +1**）

```
① 放一个 Adder（32 位）（如果 alu 不能复用）
     或者：再放一个 Adder
② A ← pc.pc_out
③ B ← 常量 4（32 位）⭐
④ S → pc.pc_next
```

**⚠️ 阶段 A 还不支持 `jalr` 跳转** —— **先做 `PC+4`** ✅

**（`jalr` 的跳转留到阶段 A 的后半部分，或者先不测 `jalr`）**

### 6.5 放 Clock

```
① 元件库 → Wiring → Clock
② 属性：默认即可（频率 1 Hz）
③ Clock → pc.clk、gpr.clk
```

---

## 第 7 步：验证

### 7.1 填测试程序

**⚠️ 程序要填在 `rom` 子电路里**。

**测试程序 1（`addi` 累加）**：

| 地址 | 汇编 | 机器码（Hex）|
| :-: | --- | :-: |
| **0** | `addi x1, x0, 5` | **`00500093`** |
| **1** | `addi x2, x0, 7` | **`00700113`** |
| **2** | `addi x3, x1, 12` | **`00C08193`** |
| **3** | `jalr x0, 0(x0)` | **`00000067`** |

**编码推导**（**给你看懂，不用背**）：

**`addi x1, x0, 5`**：
```
imm[11:0] = 5      = 000000000101
rs1       = x0     = 00000
funct3    =        = 000
rd        = x1     = 00001
opcode    = addi   = 0010011

拼成 32 位：
0000 0000 0101 | 00000 | 000 | 00001 | 0010011
= 0000 0000 0101 0000 0000 0000 1001 0011
= 0x00500093  ✅
```

**`addi x2, x0, 7`**：
```
imm = 7 = 000000000111
rs1 = 00000
funct3 = 000
rd = x2 = 00010
opcode = 0010011
= 0000 0000 0111 0000 0000 0001 0001 0011
= 0x00700113  ✅
```

**`addi x3, x1, 12`**：
```
imm = 12 = 000000001100
rs1 = x1 = 00001
funct3 = 000
rd = x3 = 00011
opcode = 0010011
= 0000 0000 1100 0000 1000 0001 1001 0011
= 0x00C08193  ✅
```

**`jalr x0, 0(x0)`**：
```
imm = 0
rs1 = x0 = 00000
funct3 = 000
rd = x0 = 00000
opcode = 1100111
= 0000 0000 0000 0000 0000 0000 0110 0111
= 0x00000067  ✅
```

### 7.2 填 ROM

```
① 双击 rom 子电路里的 ROM
② 表格填（**十六进制**）：

   地址 0：00500093
   地址 1：00700113
   地址 2：00C08193
   地址 3：00000067
```

**⚠️ Logisim 的 ROM 表格**：
- **左边是地址（十六进制）**
- **右边是数据（十六进制）**

**如果表格只有"按字节"的输入** → **要拆成 4 个字节**（小端序）：

| 地址 | 数据 |
| :-: | :-: |
| 0x00 | `93` |
| 0x01 | `00` |
| 0x02 | `50` |
| 0x03 | `00` |
| 0x04 | `13` |
| 0x05 | `01` |
| 0x06 | `70` |
| 0x07 | `00` |
| … | … |

**⚠️ 这取决于 ROM 的 `Data Bit Width`** —— **如果是 32，直接填 32 位值；如果是 8，要拆字节** ✅

**—— 我们设的是 `Data Bit Width = 32`，所以直接填 `00500093`** ✅

### 7.3 打拍验证

**预期**：

| 拍 | PC | x1 | x2 | x3 |
| :-: | :-: | :-: | :-: | :-: |
| 0 | 0 | 0 | 0 | 0 |
| 1 | 4 | **5** | 0 | 0 |
| 2 | 8 | 5 | **7** | 0 |
| 3 | 12 | 5 | 7 | **17** |
| 4 | 16 | 5 | 7 | 17（`jalr` 没实现，PC 继续 +4）|

**⚠️ 因为阶段 A 还没实现 `jalr` 的跳转** —— **PC 会一直 +4** ✅

**如果 x1=5、x2=7、x3=17** → **阶段 A 的核心成功** ✅

### 7.4 加 Probe 观察

```
① 在顶层放 4 个 Probe：
     PC（接 pc.pc_out）
     x1（从 gpr 方块拉出来，需要加输出引脚）
     x2
     x3
```

**⚠️ `gpr` 里要加 3 个"调试输出"**：

```
在 gpr 页里：
  放 3 个输出引脚：x1_out、x2_out、x3_out（32 位）
  分别接 Reg1、Reg2、Reg3 的 Q
```

**—— 和 F5/F6 里给 `gpr` 加 `r0_out` 一样** ✅

---

## ⏰ 时间分配建议（一天半）

| 时段 | 任务 | 时间 |
| :-: | --- | :-: |
| **第 1 天上午** | 第 0~2 步（`pc`、`rom`）| **30 分钟** |
| **第 1 天上午** | **第 3 步（`dec`）** | **60 分钟** |
| **第 1 天下午** | **第 4 步（`gpr`）** | **90 分钟** |
| **第 1 天下午** | 第 5 步（`alu`）| **10 分钟** |
| **第 1 天晚上** | **第 6 步（顶层）** | **60 分钟** |
| **第 1 天晚上** | 第 7 步（验证 + 调试）| **60 分钟** |
| **第 2 天上午** | **预留调试** | **60 分钟** |
| **第 2 天上午** | （如果顺利）**冲阶段 B** | **60 分钟** |

**—— 一天半刚好够"阶段 A + 一点调试"** ✅

---

## ⚠️ 阶段 A 的 6 个坑

| # | 坑 | 说明 |
| :-: | --- | --- |
| **1** | **PC + 4**（不是 +1）| sCPU 是 +1，这里必须 +4 ⚠️ |
| **2** | **ROM 地址 = `PC[9:2]`** | 要除以 4 ⚠️ |
| **3** | **`imm_i` 用 Sign Extend** | 12→32，不是 Zero ⚠️ |
| **4** | **`x0` 恒为 0** | 读 `x0` 要返回 0 ⚠️ |
| **5** | **`raddr1` 是 5 位，MUX 的 S 是 4 位** | 用 Splitter 取低 4 位 |
| **6** | **16 个寄存器** | 别数错，`Select Bits = 4` |

---

## 📌 阶段 A 完成的标准

**以下 3 条都满足**：

```
① PC 按 0 → 4 → 8 → 12 → 16 递增  ✅
② x1 = 5、x2 = 7、x3 = 17         ✅
③ x0 始终 = 0                      ✅
```

**—— 达到这三条，阶段 A 就成功了** ✅

**然后可以截图存档，写进报告"加分项"章节** 📸

---

## 🎯 如果还有时间：阶段 B 的最小增量

**阶段 B = 加 `add` 和 `lui`**（约 1 小时）

**改动**：

| # | 改什么 | 时间 |
| :-: | --- | :-: |
| 1 | `dec` 加 `is_add`、`is_lui`（2 个比较器 + AND）| 20 分钟 |
| 2 | `dec` 加 `imm_u`（`instr[31:12]` 左移 12）| 20 分钟 |
| 3 | **加 `MUX_aluB`**（选 `rdata2` 还是 `imm_i`）| 10 分钟 |
| 4 | **加 `MUX_wdata`**（选 `alu.result` 还是 `imm_u`）| 10 分钟 |
| 5 | `wen` 加 `is_add \| is_lui` | 5 分钟 |

**测试程序**：

```asm
lui  x1, 0x12345     # x1 = 0x12345000
addi x2, x0, 100     # x2 = 100
add  x3, x1, x2      # x3 = 0x12345000 + 100
```

**编码**：
- `lui x1, 0x12345` = `0x123450B7`
- `addi x2, x0, 100` = `0x06400113`
- `add x3, x1, x2` = `0x002081B3`

**—— 如果阶段 A 顺利，冲一下阶段 B** ✅

---

**—— 阶段 A 步骤完**

> 💡 **建议：先做 `pc`、`rom`、`alu`（30 分钟，简单），再做 `dec`（60 分钟），
> 最后 `gpr`（90 分钟，最耗时）—— 这样一天内能看到"大半成品"** ✅
