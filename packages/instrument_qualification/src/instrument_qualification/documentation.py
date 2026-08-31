"""生成中文 Qualification Markdown 报告。"""

from pathlib import Path

from .models import (
    CheckStatus,
    QualificationReport,
)


def generate_report_markdown(
    path: str | Path,
    report: QualificationReport,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# 仪表 Driver 实机资格验证报告",
        "",
        "## 仪表信息",
        "",
        f"- Driver 家族：{report.driver_family}",
        f"- 目标型号：{report.target_model}",
        f"- Driver 版本：{report.driver_version}",
        f"- 序列号：{report.serial_number}",
        f"- Firmware：{report.firmware}",
        f"- Resource：{report.resource}",
        "",
        "## 汇总",
        "",
        f"- 总检查项：{len(report.checks)}",
        f"- PASS：{report.passed()}",
        f"- FAIL：{report.failed()}",
        f"- SKIPPED：{report.skipped()}",
        f"- 强制项失败/跳过：{len(report.mandatory_failures())}",
        f"- 是否满足 qualified 条件：{report.eligible_for_qualified()}",
        "",
        "## 检查项",
        "",
    ]

    for result in report.checks:
        if result.status == CheckStatus.PASS:
            marker = "PASS"
        elif result.status == CheckStatus.FAIL:
            marker = "FAIL"
        else:
            marker = "SKIPPED"

        required = "强制" if result.mandatory else "可选"

        lines.append(f"### [{marker}] {result.name}")
        lines.append("")
        lines.append(f"- ID：{result.id}")
        lines.append(f"- 分类：{result.category}")
        lines.append(f"- 要求：{required}")

        if result.elapsed_ms is not None:
            lines.append(f"- 耗时：{result.elapsed_ms} ms")
        if result.message:
            lines.append(f"- 信息：{result.message}")
        if result.evidence:
            lines.append("- 证据：")
            for key, value in result.evidence.items():
                lines.append(f"  - {key}: {value}")

        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
