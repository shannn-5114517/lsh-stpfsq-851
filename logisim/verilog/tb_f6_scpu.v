// ============================================================
//  tb_f6_scpu.v  ——  F6 sCPU 的 testbench
//
//  4 组测试：
//    1. li 的 4 种 s（验证 3 / 12 / 48 / 192）
//    2. bner0 的相对偏移（循环累加 1+2+3）
//    3. io 输出（写 LED / 七段）
//    4. io 输入（读拨码）
// ============================================================
`timescale 1ns / 1ps

module tb_f6_scpu;

    reg        clk, rst;
    reg  [7:0] sw, btn;
    wire [7:0] led, seg7_data, pc_out, r0, r1, r2, r3;

    integer errors = 0;

    f6_scpu uut (
        .clk(clk), .rst(rst),
        .sw(sw), .btn(btn),
        .led(led), .seg7_data(seg7_data),
        .pc_out(pc_out), .r0(r0), .r1(r1), .r2(r2), .r3(r3)
    );

    always #5 clk = ~clk;

    // ---------- 打 n 拍 ----------
    task tick(input integer n);
        integer t;
        begin
            for (t = 0; t < n; t = t + 1) @(posedge clk);
            #1;
        end
    endtask

    // ---------- 检查 ----------
    task chk(input [8*24-1:0] name, input [7:0] got, input [7:0] exp);
        begin
            if (got === exp) $display("    PASS  %0s = %0d", name, got);
            else begin
                $display("    FAIL  %0s = %0d   (期望 %0d)", name, got, exp);
                errors = errors + 1;
            end
        end
    endtask

    // ---------- 清 ROM ----------
    task clear_rom;
        integer i;
        begin
            for (i = 0; i < 256; i = i + 1) uut.rom[i] = 8'h00;
        end
    endtask

    // ---------- 复位 ----------
    task do_reset;
        begin
            rst = 1; @(posedge clk); #1; rst = 0;
        end
    endtask

    integer pass_cnt;

    initial begin
        clk = 0; rst = 1; sw = 8'd0; btn = 8'd0;

        $display("");
        $display("==========================================================");
        $display("   F6 sCPU 验证  (sISA v3.0)");
        $display("   add / io / li(移位) / bner0(相对偏移)");
        $display("==========================================================");

        // ========================================================
        // 测试 1：li 的 4 种 s
        // ========================================================
        $display("");
        $display("【测试 1】li 的 4 种 s（imm=11=3）");
        $display("----------------------------------------------------------");
        clear_rom;
        uut.rom[0] = 8'h83;  // li r0, 3    (s=00, imm=11)
        uut.rom[1] = 8'h87;  // li r0, 12   (s=01, imm=11)
        uut.rom[2] = 8'h8b;  // li r0, 48   (s=10, imm=11)
        uut.rom[3] = 8'h8f;  // li r0, 192  (s=11, imm=11)
        uut.rom[4] = 8'hFF;  // bner0 r3,-1 (r0=192,r3=0 → 不等 → 跳回 4，死循环)
        do_reset;
        tick(1); chk("s=00  li r0,3",   r0, 8'd3);
        tick(1); chk("s=01  li r0,12",  r0, 8'd12);
        tick(1); chk("s=10  li r0,48",  r0, 8'd48);
        tick(1); chk("s=11  li r0,192", r0, 8'd192);

        // ========================================================
        // 测试 2：bner0 的相对偏移（循环 1+2+3）
        // ========================================================
        $display("");
        $display("【测试 2】bner0 相对偏移：sum = 1+2+3");
        $display("----------------------------------------------------------");
        // 目标：r1 从 1 加到 4（上界），r2 累加 1+2+3
        //   0: li r1, 1        (rd=01, s=00, imm=01) → 10 01 00 01 = 0x91
        //   1: li r2, 0        (rd=10, s=00, imm=00) → 10 10 00 00 = 0xA0
        //   2: li r3, 1        (rd=11, s=00, imm=01) → 10 11 00 01 = 0xB1
        //   3: add r2, r2, r1  (rd=10, rs1=10, rs2=01) → 00 10 10 01 = 0x29
        //   4: add r1, r1, r3  (rd=01, rs1=01, rs2=11) → 00 01 01 11 = 0x17
        //   5: li r0, 4        (rd=00, s=01, imm=01) → 10 00 01 01 = 0x85
        //   6: bner0 r1, -3    (offset=-3=1101, rs2=01=r1) → 11 1101 01 = 0xF5
        clear_rom;
        uut.rom[0] = 8'h91;  // li r1, 1
        uut.rom[1] = 8'ha0;  // li r2, 0
        uut.rom[2] = 8'hb1;  // li r3, 1
        uut.rom[3] = 8'h29;  // add r2, r2, r1
        uut.rom[4] = 8'h17;  // add r1, r1, r3
        uut.rom[5] = 8'h85;  // li r0, 4   （上界，每轮重设，无害）
        uut.rom[6] = 8'hf5;  // bner0 r1, -3  （R[0]=4 vs R[1]，不等就跳回 4）
        uut.rom[7] = 8'hc3;  // bner0 r3, 0  → offset=0，PC 永远 +0 → 停机死循环
        do_reset;
        // 3 轮循环约 15 拍，多打几拍确认已停
        tick(25);
        $display("    PC = %0d（应停在 7）", pc_out);
        chk("r1 (循环变量)", r1, 8'd4);
        chk("r2 (累加和)",   r2, 8'd6);   // 1+2+3 = 6
        chk("r0 (上界)",     r0, 8'd4);

        // ========================================================
        // 测试 3：io 输出（写 LED / 七段）
        // ========================================================
        $display("");
        $display("【测试 3】io 输出：li r0,12 → out r0,LED → out r0,七段");
        $display("----------------------------------------------------------");
        clear_rom;
        uut.rom[0] = 8'h87;  // li r0, 12       (s=01, imm=11)
        uut.rom[1] = 8'h48;  // out r0, LED     (01 00 1 000)
        uut.rom[2] = 8'h49;  // out r0, 七段    (01 00 1 001)
        uut.rom[3] = 8'hff;  // bner0 r3, -1    (死循环)
        do_reset;
        tick(1); chk("li 后 r0", r0, 8'd12);
        tick(1);
        chk("out LED",       led,       8'd12);
        chk("out 后 r0 不变", r0,        8'd12);   // ← io 输出不写 GPR
        tick(1);
        chk("out 七段",      seg7_data, 8'd12);
        chk("七段后 r0 不变", r0,        8'd12);

        // ========================================================
        // 测试 4：io 输入（读拨码 / 按钮）
        // ========================================================
        $display("");
        $display("【测试 4】io 输入：拨码=5、按钮=9");
        $display("----------------------------------------------------------");
        clear_rom;
        uut.rom[0] = 8'h40;  // in r0, 拨码     (01 00 0 000)
        uut.rom[1] = 8'h51;  // in r1, 按钮     (01 01 0 001)
        uut.rom[2] = 8'hff;  // bner0 r3, -1
        do_reset;
        sw  = 8'd5;
        btn = 8'd9;
        #1;
        tick(1); chk("in r0, 拨码", r0, 8'd5);
        tick(1); chk("in r1, 按钮", r1, 8'd9);

        // ========================================================
        // 测试 5：完整演示程序（读拨码 → LED + 七段 → 循环）
        // ========================================================
        $display("");
        $display("【测试 5】完整演示：读拨码 → 写 LED/七段 → 循环");
        $display("----------------------------------------------------------");
        clear_rom;
        uut.rom[0] = 8'h40;  // in r0, 拨码
        uut.rom[1] = 8'h48;  // out r0, LED
        uut.rom[2] = 8'h49;  // out r0, 七段
        uut.rom[3] = 8'hf7;  // bner0 r3, -3  （跳回 0）
        do_reset;
        sw = 8'd9; #1;
        tick(10);
        $display("    拨码 = 9");
        chk("LED 跟随",    led,       8'd9);
        chk("七段跟随",    seg7_data, 8'd9);
        sw = 8'd6; #1;
        tick(10);
        $display("    拨码改成 6");
        chk("LED 跟随",    led,       8'd6);
        chk("七段跟随",    seg7_data, 8'd6);

        // ========================================================
        // 汇总
        // ========================================================
        $display("");
        $display("==========================================================");
        if (errors == 0) $display("   ✅ 全部测试通过！(0 errors)");
        else             $display("   ❌ 有 %0d 个测试失败", errors);
        $display("==========================================================");
        $display("");
        $finish;
    end

endmodule
