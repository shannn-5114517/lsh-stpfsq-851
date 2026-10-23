// ============================================================
//  f6_scpu.v  ——  sISA v3.0 处理器（ysyx F6 完整版）
//
//  指令（8 位）：
//    add   : 00 | rd | rs1 | rs2       R[rd] = R[rs1] + R[rs2]
//    io    : 01 | rd | i/o | idx       R[rd] <=> dev[idx]
//    li    : 10 | rd |  s  | imm2      R[rd] = imm2 << (s << 1)
//    bner0 : 11 | offset(4) | rs2      if (R[0] != R[rs2]) PC += sign_ext(offset)
//
//  设备关联（讲义指定）：
//    i/o=1, idx=000  → LED（输出）
//    i/o=1, idx=001  → 七段数码管（输出）
//    i/o=0, idx=000  → 拨码开关（输入）
//    i/o=0, idx=001  → 按钮（输入）
//
//  对应 Logisim 电路：wholeF6.circ
// ============================================================
`timescale 1ns / 1ps

module f6_scpu (
    input  wire       clk,
    input  wire       rst,
    input  wire [7:0] sw,        // 拨码开关
    input  wire [7:0] btn,       // 按钮
    output wire [7:0] led,       // LED
    output wire [7:0] seg7_data, // 七段数码管数据（低 4 位有效）
    output wire [7:0] pc_out,    // 调试：PC
    output wire [7:0] r0,        // 调试：GPR[0]
    output wire [7:0] r1,        // 调试：GPR[1]
    output wire [7:0] r2,        // 调试：GPR[2]
    output wire [7:0] r3         // 调试：GPR[3]
);

    // ----------------------------------------------------------
    //  指令存储器（256 × 8）
    // ----------------------------------------------------------
    reg [7:0] rom [0:255];
    integer k;
    initial begin
        for (k = 0; k < 256; k = k + 1) rom[k] = 8'h00;
    end

    // ----------------------------------------------------------
    //  PC（程序计数器）
    // ----------------------------------------------------------
    reg  [7:0] pc;
    wire [7:0] pc_next;
    assign pc_out = pc;

    // ----------------------------------------------------------
    //  取指
    // ----------------------------------------------------------
    wire [7:0] instr = rom[pc];

    // ----------------------------------------------------------
    //  译码（对应 dec 模块）
    // ----------------------------------------------------------
    wire [1:0] opcode = instr[7:6];
    wire [1:0] rd     = instr[5:4];
    wire [1:0] rs1    = instr[3:2];
    wire [1:0] rs2    = instr[1:0];

    wire [1:0] s      = instr[3:2];   // li 用：移位选择
    wire [1:0] imm2   = instr[1:0];   // li 用：2 位立即数
    wire       io_dir = instr[3];     // io 用：0=输入，1=输出
    wire [2:0] idx    = instr[2:0];   // io 用：设备编号
    wire [3:0] offset = instr[5:2];   // bner0 用：相对偏移

    wire is_add   = (opcode == 2'b00);
    wire is_io    = (opcode == 2'b01);
    wire is_li    = (opcode == 2'b10);
    wire is_bner0 = (opcode == 2'b11);

    // ----------------------------------------------------------
    //  立即数生成
    // ----------------------------------------------------------
    // li：把 2 位 imm 左移 (s*2) 位（对应 Shifter）
    // ⚠️ 注意：s 只 2 位，s<<1 会溢出（s=10 时 2<<1=4 存不下）
    //    必须先在 3 位上算 s*2（等价于 s 后面拼一个 0）
    wire [2:0] shift_amt = {s, 1'b0};          // s*2，用 3 位装
    wire [7:0] imm8      = {6'b0, imm2} << shift_amt;

    // bner0：4 位 → 8 位 符号扩展（对应 Bit Extender Type=Sign Extend）
    wire [7:0] offset8 = {{4{offset[3]}}, offset};

    // ----------------------------------------------------------
    //  GPR（4 × 8 位）
    // ----------------------------------------------------------
    reg [7:0] gpr [0:3];
    assign r0 = gpr[0];
    assign r1 = gpr[1];
    assign r2 = gpr[2];
    assign r3 = gpr[3];

    // ----------------------------------------------------------
    //  读口（对应 MUX_raddr1 三路复用 + raddr2）
    //    add   → rs1
    //    bner0 → 0（读 R[0]）
    //    io    → rd（读 R[rd]）★
    // ----------------------------------------------------------
    wire [1:0] raddr1 = is_io    ? rd :
                        is_bner0 ? 2'b00 : rs1;
    wire [7:0] rdata1 = gpr[raddr1];
    wire [7:0] rdata2 = gpr[rs2];

    // ----------------------------------------------------------
    //  ALU（8 位加法器）
    // ----------------------------------------------------------
    wire [7:0] alu_result = rdata1 + rdata2;

    // ----------------------------------------------------------
    //  比较器（bner0 用）
    //    bner0 时 raddr1 = 0，所以 rdata1 = R[0]
    // ----------------------------------------------------------
    wire bne      = (rdata1 != rdata2);
    wire pc_taken = is_bner0 & bne;

    // ----------------------------------------------------------
    //  输入设备选择（对应输入 MUX）
    //    idx=000 → 拨码开关，idx=001 → 按钮
    // ----------------------------------------------------------
    wire [7:0] io_rdata = idx[0] ? btn : sw;

    // ----------------------------------------------------------
    //  写回数据选择（对应 MUX_wdata 三选一）
    //    io 输入 → io_rdata
    //    add     → alu_result
    //    其他    → imm8（li）
    // ----------------------------------------------------------
    wire is_io_in = is_io & ~io_dir;

    reg [7:0] wdata;
    always @(*) begin
        if (is_io_in)     wdata = io_rdata;
        else if (is_add)  wdata = alu_result;
        else              wdata = imm8;
    end

    // ----------------------------------------------------------
    //  写使能
    //    wen = is_add | is_li | (is_io & ~io_dir)
    //    注意：io 输出时不写 GPR！
    // ----------------------------------------------------------
    wire wen = is_add | is_li | is_io_in;

    // ----------------------------------------------------------
    //  PC 更新（对应 MUX_addB + Adder_pc，一个加法器干两件事）
    // ----------------------------------------------------------
    wire [7:0] add_b = pc_taken ? offset8 : 8'd1;
    assign pc_next = pc + add_b;

    // ----------------------------------------------------------
    //  输出设备（带锁存，对应 led_reg / seg7_reg）
    // ----------------------------------------------------------
    reg [7:0] led_reg;
    reg [7:0] seg7_reg;
    assign led       = led_reg;
    assign seg7_data = seg7_reg;

    wire we_led  = is_io & io_dir & (idx == 3'b000);
    wire we_seg7 = is_io & io_dir & (idx == 3'b001);

    // ----------------------------------------------------------
    //  时序逻辑
    // ----------------------------------------------------------
    integer j;
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            pc       <= 8'd0;
            led_reg  <= 8'd0;
            seg7_reg <= 8'd0;
            for (j = 0; j < 4; j = j + 1) gpr[j] <= 8'd0;
        end else begin
            if (wen)       gpr[rd]  <= wdata;
            if (we_led)    led_reg  <= rdata1;
            if (we_seg7)   seg7_reg <= rdata1;
            pc <= pc_next;
        end
    end

endmodule
