# md-linkcheck

一个用于验证 Markdown 文档中链接的 Python CLI 工具。

## 功能特性

- 递归扫描指定目录下的所有 `.md` 文件
- 提取 Markdown 中的 HTTP/HTTPS 链接和相对路径引用
- 异步并发检查 HTTP 链接可达性
- 检查相对路径文件是否存在
- 支持多种输出格式：终端表格（rich）、JSON 文件、简洁文本
- 支持排除特定目录（如 node_modules, .git）

## 安装

```bash
pip install -e .
```

## 使用方法

```bash
# 基本用法
md-linkcheck ./docs

# 指定输出格式
md-linkcheck ./docs -f json -o report.json

# 指定并发数和超时时间
md-linkcheck ./docs -c 10 -t 5

# 排除特定目录
md-linkcheck ./docs --exclude node_modules --exclude .git

# 详细输出
md-linkcheck ./docs -v
```

## 命令行参数

- `PATH`: 要扫描的目录或文件路径
- `-o, --output`: 输出文件路径（可选）
- `-f, --format`: 输出格式 [rich, json, text]，默认 rich
- `--exclude`: 要排除的目录名称（可多次使用）
- `-c, --concurrency`: 并发请求数，默认 10
- `-t, --timeout`: HTTP 请求超时时间（秒），默认 5
- `-v, --verbose`: 详细输出模式

## 输出示例

```
✅ Scan Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Links: 25
Valid: 23 | Broken: 2
Duration: 1.23s
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 运行测试并查看覆盖率
pytest --cov=md_linkcheck
```

## 技术栈

- Python 3.10+
- click 8.x - CLI 框架
- aiohttp 3.x - 异步 HTTP 请求
- rich 13.x - 终端输出美化
- markdown-it-py - Markdown 解析

## License

MIT
