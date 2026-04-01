# md-linkcheck

A Python CLI tool for validating links in Markdown documentation.

## Features

- **Recursive scanning**: Find all `.md` files in a directory tree
- **Link extraction**: Extract HTTP/HTTPS links and relative file paths
- **Async checking**: Efficient concurrent link validation using aiohttp
- **Multiple output formats**: Terminal tables, JSON, or plain text
- **Configurable**: TOML-based configuration support
- **CI/CD friendly**: Exit codes for integration with build pipelines

## Installation

```bash
pip install md-linkcheck
```

Or install from source:

```bash
git clone https://github.com/md-linkcheck/md-linkcheck.git
cd md-linkcheck
pip install -e .
```

## Quick Start

Check all Markdown files in the current directory:

```bash
md-linkcheck ./docs
```

Generate a JSON report:

```bash
md-linkcheck ./docs --format json --output report.json
```

Exclude specific directories:

```bash
md-linkcheck . --exclude node_modules --exclude build
```

## Usage

```
md-linkcheck [OPTIONS] [PATH]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--output, -o` | Output file path | (stdout) |
| `--format, -f` | Output format: `terminal`, `json`, `text` | `terminal` |
| `--exclude, -e` | Directories to exclude | - |
| `--concurrency, -c` | Max concurrent checks | `10` |
| `--timeout, -t` | Request timeout (seconds) | `10` |
| `--verbose, -v` | Enable verbose output | `false` |
| `--version` | Show version | - |
| `--help` | Show help | - |

## Configuration

Create a `pyproject.toml` in your project root:

```toml
[tool.md-linkcheck]
exclude = ["node_modules", ".git", "build"]
concurrency = 10
timeout = 10
format = "terminal"
```

## Exit Codes

- `0`: All links valid
- `1`: One or more broken links found
- `2`: Error occurred

## Examples

### Basic Usage

```bash
# Check current directory
md-linkcheck .

# Check specific directory
md-linkcheck ./docs

# Check with verbose output
md-linkcheck ./docs --verbose
```

### Output Formats

```bash
# Terminal (default)
md-linkcheck ./docs

# JSON output
md-linkcheck ./docs --format json --output report.json

# Plain text
md-linkcheck ./docs --format text --output report.txt
```

### Advanced Options

```bash
# Custom concurrency and timeout
md-linkcheck ./docs --concurrency 20 --timeout 30

# Exclude multiple directories
md-linkcheck . --exclude node_modules --exclude .venv --exclude build
```

## How It Works

1. **Scan**: Recursively find all `.md` files (excluding `node_modules`, `.git`, etc.)
2. **Parse**: Extract links using markdown-it-py
3. **Check**: 
   - HTTP/HTTPS links: Send HEAD requests (async)
   - Relative paths: Check file existence
4. **Report**: Display results in chosen format

## License

MIT License - see [LICENSE](LICENSE) for details.
