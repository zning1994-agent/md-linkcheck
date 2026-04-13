# md-linkcheck

用于验证 Markdown 文档中链接的 Python CLI 工具。

## 功能特性

- 递归扫描目录下的所有 `.md` 文件
- 提取 Markdown 中的 HTTP/HTTPS 链接和相对路径引用
- 异步并发检查 HTTP 链接可达性
- 检查相对路径文件是否存在
- 多种输出格式：终端表格（rich）、JSON 文件、纯文本
- 支持排除特定目录（如 node_modules, .git）
- 基础统计：总链接数、有效数、无效数、耗时

## 安装

```bash
pip install -e .
```

## 使用方法

### 基本用法

扫描当前目录下的 Markdown 文件并检查所有链接：

```bash
md-linkcheck
```

扫描指定目录：

```bash
md-linkcheck ./docs
```

扫描单个文件：

```bash
md-linkcheck README.md
```

### 输出格式

使用 `--format` 或 `-f` 指定输出格式。

#### 终端（默认）

在终端中输出 rich 格式的表格：

```bash
md-linkcheck ./docs -f terminal
```

#### JSON

将结构化 JSON 报告输出到文件：

```bash
md-linkcheck ./docs -f json -o report.json
```

JSON 输出示例：

```json
{
  "total_links": 25,
  "valid_count": 23,
  "broken_count": 2,
  "duration": 1.23,
  "broken_links": [
    {
      "file": "docs/api.md",
      "line": 42,
      "url": "https://broken-example.com",
      "type": "http",
      "error": "Status 404"
    }
  ]
}
```

#### 纯文本

简单文本输出：

```bash
md-linkcheck ./docs -f text -o report.txt
```

### 过滤

使用 `--exclude` 或 `-e` 排除扫描目录：

```bash
# 排除单个目录
md-linkcheck ./docs --exclude node_modules

# 排除多个目录
md-linkcheck ./docs --exclude node_modules --exclude .git --exclude build

# 简写形式
md-linkcheck ./docs -e vendor -e cache -e .venv
```

### 性能调优

#### 并发数

使用 `--concurrency` 或 `-c` 控制并发 HTTP 请求数：

```bash
# 对限速服务器使用较低并发
md-linkcheck ./docs -c 5

# 使用更高并发加快检查速度（默认：10）
md-linkcheck ./docs -c 20
```

#### 超时时间

使用 `--timeout` 或 `-t` 设置 HTTP 请求超时时间（秒）：

```bash
# 快速响应用较短超时
md-linkcheck ./docs -t 5

# 慢速服务器用较长超时（默认：10）
md-linkcheck ./docs -t 30
```

#### 组合性能选项

```bash
# 高并发配合理想超时
md-linkcheck ./docs -c 20 -t 15

# CI/CD 用保守设置
md-linkcheck ./docs -c 3 -t 60
```

### 详细模式

使用 `--verbose` 或 `-v` 在链接检查时显示详细进度：

```bash
md-linkcheck ./docs -v
```

详细输出显示正在检查的每个链接：

```
Checking 1/25: https://example.com
Checking 2/25: https://python.org
Checking 3/25: ../images/logo.png
...
```

### 组合示例

```bash
md-linkcheck ./docs \
  --format json \
  --output report.json \
  --exclude node_modules \
  --exclude .git \
  --concurrency 10 \
  --timeout 15 \
  --verbose
```

## 命令行选项

| 选项 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `PATH` | - | 要扫描的目录或文件 | `.`（当前目录） |
| `--output` | `-o` | 报告输出文件路径 | 无（标准输出） |
| `--format` | `-f` | 输出格式：`terminal`、`json`、`text` | `terminal` |
| `--exclude` | `-e` | 要排除的扫描模式（可多次使用） | 无 |
| `--concurrency` | `-c` | 最大并发 HTTP 检查数 | `10` |
| `--timeout` | `-t` | HTTP 请求超时时间（秒） | `10` |
| `--verbose` | `-v` | 显示链接检查进度 | `False` |

## 退出码

- `0`：所有链接有效或未找到链接
- `1`：发现一个或多个失效链接

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 运行测试并查看覆盖率
pytest --cov=md_linkcheck

# 运行指定测试文件
pytest tests/test_checker.py

# 运行匹配模式的测试
pytest -k "test_parser"
```

## 技术栈

| 组件 | 技术选型 | 用途 |
|------|----------|------|
| 语言 | Python 3.10+ | 运行环境 |
| CLI 框架 | click 8.x | 命令行参数解析 |
| 异步 HTTP | aiohttp 3.x | 并发链接检查 |
| 终端输出 | rich 13.x | 格式化输出 |
| Markdown 解析 | markdown-it-py | 链接提取 |

## 许可证

MIT
