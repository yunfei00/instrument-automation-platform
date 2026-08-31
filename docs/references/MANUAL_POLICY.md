# 原厂手册管理策略

原厂手册是 Instrument Automation Platform 知识体系的重要来源，但原始 Vendor PDF 默认只作为**本地参考资料**，不直接提交 Git。

本地建议目录：

```text
vendor_manuals/
  keysight/
    dsox3000/
  rohde_schwarz/
    common/
    fsw/
    cmw500/
```

`vendor_manuals/` 应由 `.gitignore` 忽略。

Git 仓库保存的是可追踪的结构化手册元数据，例如：

- manufacturer
- instrument family
- document title
- document type
- document number
- revision
- publication date
- filename
- SHA256
- official source
- notes

推荐知识链：

```text
Vendor Manual
  -> Manual Registry
  -> Command Catalog
  -> Hardware Probe
  -> Raw Response
  -> Parser
  -> Scenario Test
  -> Qualification
  -> Generated Documentation
```

原厂手册始终保留为原始依据；真正的长期工程资产，是从手册和实机中提炼出的“已验证命令、真实返回格式、Parser、兼容信息和 Qualification 证据”。
