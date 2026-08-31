# 参考资料说明

本目录用于保存与原厂文档管理相关的策略和元数据规范。

原厂 PDF 默认保存在本地 `vendor_manuals/`，不直接提交 Git。

仪表专用 Manual Registry 放在对应 Profile 目录，例如：

```text
instrument_profiles/keysight/dsox3000/manuals.json
instrument_profiles/rohde_schwarz/fsw/manuals.json
instrument_profiles/rohde_schwarz/cmw500/manuals.json
```

本地归档 PDF 后应记录 SHA256，以确保以后能够准确确认 Driver 开发时使用的是哪一版手册。

详细规则见 `MANUAL_POLICY.md`。
