"""生成人类可读的 Instrument Lab Markdown 文档。"""

from pathlib import Path

from .models import (
    CommandDefinition,
    ProbeResult,
)


def generate_markdown(
    output_path: str | Path,
    *,
    title: str,
    commands: list[CommandDefinition],
    results: list[ProbeResult] | None = None,
    metadata: dict | None = None,
) -> None:
    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    metadata = metadata or {}

    result_map = {
        result.command_id: result
        for result in (results or [])
    }

    lines: list[str] = []
    lines.append(f"# {title}")
    lines.append("")

    if metadata:
        lines.append("## 仪表信息")
        lines.append("")
        for key, value in metadata.items():
            lines.append(f"- {key}: {value}")
        lines.append("")

    lines.append("## 命令汇总")
    lines.append("")
    lines.append(f"- 已定义命令：{len(commands)}")

    if results is not None:
        lines.append(f"- 已测试：{len(results)}")
        lines.append(
            "- PASS："
            + str(sum(result.status == "PASS" for result in results))
        )
        lines.append(
            "- FAIL："
            + str(sum(result.status == "FAIL" for result in results))
        )
        lines.append(
            "- SKIPPED："
            + str(sum(result.status == "SKIPPED" for result in results))
        )

    lines.append("")
    lines.append("## 命令列表")
    lines.append("")

    for command in commands:
        lines.append(f"### {command.name}")
        lines.append("")
        lines.append(f"- ID：{command.id}")
        lines.append(f"- 分类：{command.category}")
        lines.append(f"- 主命令：{command.command}")

        if command.set_command:
            lines.append(f"- 设置语法：{command.set_command}")
        if command.query_command:
            lines.append(f"- 查询语法：{command.query_command}")

        lines.append(f"- 类型：{command.kind.value}")
        lines.append(f"- 安全级别：{command.safety.value}")
        lines.append(f"- 响应类型：{command.response_type.value}")
        lines.append(f"- 验证状态：{command.verification_status.value}")
        lines.append(f"- 自动探测：{command.probe_enabled}")

        if command.unit:
            lines.append(f"- 单位：{command.unit}")
        if command.manual_id:
            lines.append(f"- 手册：{command.manual_id}")
        if command.manual_page is not None:
            lines.append(f"- 手册页码：{command.manual_page}")
        if command.manual_section:
            lines.append(f"- 手册章节：{command.manual_section}")
        if command.source:
            lines.append(f"- 来源：{command.source}")

        if command.description:
            lines.append("")
            lines.append(command.description)

        if command.response_notes:
            lines.append("")
            lines.append("响应说明：" + command.response_notes)

        result = result_map.get(command.id)
        if result:
            lines.append("")
            lines.append("#### 硬件探测")
            lines.append("")
            lines.append(f"- 状态：{result.status}")
            if result.raw_response is not None:
                lines.append(f"- 原始响应：{result.raw_response!r}")
            if result.parsed_value is not None:
                lines.append(f"- 解析值：{result.parsed_value!r}")
            if result.parsed_type:
                lines.append(f"- 解析类型：{result.parsed_type}")
            if result.elapsed_ms is not None:
                lines.append(f"- 耗时：{result.elapsed_ms} ms")
            if result.error:
                lines.append(f"- 错误：{result.error}")

        if command.notes:
            lines.append("")
            lines.append("备注：" + command.notes)

        lines.append("")

    output_path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )
