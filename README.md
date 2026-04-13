# md-linkcheck

A Python CLI tool for validating links in Markdown documentation.

## Features

- Recursively scan all `.md` files in a directory
- Extract HTTP/HTTPS links and relative path references from Markdown
- Async concurrent checking of HTTP link accessibility
- Check if relative path files exist
- Multiple output formats: terminal table (rich), JSON file, concise text
- Support excluding specific directories (e.g., node_modules, .git)
- Basic statistics: total links, valid count, broken count, duration

## Installation

```bash
pip install -e .
```

## Usage

### Basic Usage

Scan the current directory for Markdown files and check all links:

```bash
md-linkcheck
```

Scan a specific directory:

```bash
md-linkcheck ./docs
```

Scan a single file:

```bash
md-linkcheck README.md
```

### Output Formats

Use `--format` or `-f` to specify the output format.

#### Terminal (default)

Rich-formatted table output in the terminal:

```bash
md-linkcheck ./docs -f terminal
```

#### JSON

Output structured JSON report to a file:

```bash
md-linkcheck ./docs -f json -o report.json
```

JSON output example:

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

#### Concise

Simple concise text output:

```bash
md-linkcheck ./docs -f concise -o report.txt
```

### Filtering

Use `--exclude` or `-e` to exclude directories from scanning.

```bash
# Exclude single directory
md-linkcheck ./docs --exclude node_modules

# Exclude multiple directories
md-linkcheck ./docs --exclude node_modules --exclude .git --exclude build

# Short form
md-linkcheck ./docs -e vendor -e cache -e .venv
```

### Performance Tuning

#### Concurrency

Use `--concurrency` or `-c` to control the number of concurrent HTTP requests:

```bash
# Lower concurrency for rate-limited servers
md-linkcheck ./docs -c 5

# Higher concurrency for faster checking (default: 10)
md-linkcheck ./docs -c 20
```

#### Timeout

Use `--timeout` or `-t` to set HTTP request timeout in seconds:

```bash
# Shorter timeout for fast responses
md-linkcheck ./docs -t 5

# Longer timeout for slow servers (default: 10)
md-linkcheck ./docs -t 30
```

#### Combined Performance Options

```bash
# High concurrency with reasonable timeout
md-linkcheck ./docs -c 20 -t 15

# Conservative settings for CI/CD
md-linkcheck ./docs -c 3 -t 60
```

### Verbose Mode

Use `--verbose` or `-v` to show detailed progress during link checking:

```bash
md-linkcheck ./docs -v
```

Verbose output shows each link being checked:

```
Checking 1/25: https://example.com
Checking 2/25: https://python.org
Checking 3/25: ../images/logo.png
...
```

### Combined Example

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

## Command Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `PATH` | - | Directory or file to scan | `.` (current directory) |
| `--output` | `-o` | Output file path for the report | None (stdout) |
| `--format` | `-f` | Output format: `terminal`, `json`, `concise` | `terminal` |
| `--exclude` | `-e` | Patterns to exclude from scanning (can be used multiple times) | None |
| `--concurrency` | `-c` | Maximum number of concurrent HTTP checks | `10` |
| `--timeout` | `-t` | Timeout in seconds for HTTP requests | `10` |
| `--verbose` | `-v` | Show progress during link checking | `False` |

## Exit Codes

- `0`: All links are valid or no links found
- `1`: One or more broken links found

## Development

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=md_linkcheck

# Run specific test file
pytest tests/test_checker.py

# Run tests matching a pattern
pytest -k "test_parser"
```

## Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Language | Python 3.10+ | Runtime environment |
| CLI Framework | click 8.x | Command-line argument parsing |
| Async HTTP | aiohttp 3.x | Concurrent link checking |
| Terminal Output | rich 13.x | Formatted output |
| Markdown Parsing | markdown-it-py | Link extraction |

## License

MIT
