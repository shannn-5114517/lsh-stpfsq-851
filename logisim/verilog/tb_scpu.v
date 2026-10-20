// ============================================================================
//  sCPU 的测试平台（Testbench）
//  期望结果：程序结束后  PC = 7，R[2] = 55
// ============================================================================
`timescale 1ns/1ps

module tb_scpu;

    reg  clk = 0;
    reg  rst = 1;
    wire [7:0] pc, r0, r1, r2, r3;

    // 待测模块
    scpu u (
        .clk     (clk),
        .rst     (rst),
        .pc_out  (pc),
        .r0_out  (r0),
        .r1_out  (r1),
        .r2_out  (r2),
        .r3_out  (r3)
    );

    // 时钟：周期 10ns
    always #5 clk = ~clk;

    integer i;
    initial begin
        // 波形输出
        $dumpfile("scpu.vcd");
        $dumpvars(0, tb_scpu);

        // 复位
        #12 rst = 0;

        $display("");
        $display("cycle | PC | r0 | r1 | r2 | r3");
        $display("------+----+----+----+----+----");

        for (i = 0; i < 100; i = i + 1) begin
            @(posedge clk);
            #1;                     // 等信号稳定后再打印
            $display("%5d | %2d | %2d | %2d | %2d | %2d",
                     i, pc, r0, r1, r2, r3);

            if (pc == 8'd7 && r2 == 8'd55) begin
                $display("");
                $display("==============================================");
                $display("  PASS :  PC = %0d , R[2] = %0d", pc, r2);
                $display("==============================================");
                $finish;
            end
        end

        $display("");
        $display("==============================================");
        $display("  FAIL :  未在 100 个周期内到达 PC=7, R[2]=55");
        $display("==============================================");
        $finish;
    end

endmodule
