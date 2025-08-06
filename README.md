# Webamon Search CLI

**The Google of Threat Intelligence**

A powerful command-line interface for the Webamon Search API. Search & Threat Hunt across the web at scale. Returning unbiased & unfiltered results.

## Installation

### From PyPI

```bash
pip install webamon-cli
```

> **Webamon Search** - The Google of Threat Intelligence. Access millions of scanned domains, IPs, and threat indicators.

### Development Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/webamon-cli.git
cd webamon-cli
```

2. Install in development mode:
```bash
pip install -e .
```

Or install with development dependencies:
```bash
pip install -e ".[dev]"
```

## Quick Start

1. **Start using immediately (no configuration needed for basic searches):**
```bash
webamon search example.com domain.name,resolved_url
```

2. **Configure API key for pro features (optional):**
```bash
webamon configure
```

3. **Test the connection:**
```bash
webamon status
```

4. **Scan a website:**
```bash
webamon scan https://example.com
```

## Usage

### API Endpoints

**Webamon Search - The Google of Threat Intelligence**

The CLI automatically uses the appropriate endpoint:
- **Free tier**: `search.webamon.com` (no API key required)
- **Pro tier**: `pro.webamon.com` (requires API key)

### Configuration

The CLI can be configured in several ways:

1. **Interactive configuration:**
```bash
webamon configure --save
```

2. **Environment variables:**
```bash
export WEBAMON_API_KEY="your-api-key"  # Optional, enables pro features
```

3. **Command-line options:**
```bash
webamon --api-key your-key search example.com domain.name
```

4. **Configuration file:**
The CLI looks for configuration in:
- `~/.webamon/config.json`
- `.webamon.json` in current directory

### Commands

#### Search
Search the Webamon database:

**Basic Search:**

The basic search requires two arguments: `SEARCH_TERM` and `RESULTS`.
- `SEARCH_TERM`: What you're searching for (domain, IP, URL, hash, etc.)
- `RESULTS`: Comma-separated list of fields to search within and return

```bash
# Search for domain information
webamon search example.com domain.name,resolved_url

# Search with more fields
webamon search example.com domain.name,resolved_url,page_title

# Limit results
webamon search example.com domain.name,resolved_url --size 25

# JSON output
webamon search example.com domain.name,resolved_url --format json
```

**Pagination (Pro Users Only):**
```bash
# Use offset for pagination
webamon search example.com domain.name,resolved_url --from 25 --size 25

# Skip first 100 results
webamon search example.com domain.name,resolved_url --from 100 --size 50

# Navigate large result sets
webamon search "*.bank.com" domain.name,resolved_url --from 0 --size 100
```

**Lucene Search:**
```bash
# Advanced Lucene queries
webamon search --lucene 'domain.name:"bank*" AND scan_status:success' --index scans

# Specify fields to return
webamon search --lucene 'domain.name:"example.com"' --index domains --fields domain.name,page_title
```

#### Scan
Initiate website scans:
```bash
# Scan a domain
webamon scan example.com

# Scan and automatically fetch the report
webamon scan example.com --fetch-report

# Scan a full URL
webamon scan https://example.com/login

# JSON output with automatic report fetch
webamon scan example.com --format json --fetch-report
```

#### Report
Get a specific scan report by ID:
```bash
# Get report details (JSON format by default)
webamon report bf18c02d-ff0e-46a9-9a59-5b7b94fb27fb

# Table format for readable summary
webamon report bf18c02d-ff0e-46a9-9a59-5b7b94fb27fb --format table
```

#### Screenshot
Retrieve scan screenshots:
```bash
# Get screenshot info
webamon screenshot 392ac37e-ed52-4693-b49e-b15791231250

# Save screenshot to file
webamon screenshot 392ac37e-ed52-4693-b49e-b15791231250 --save screenshot.png

# JSON output
webamon screenshot 392ac37e-ed52-4693-b49e-b15791231250 --format json
```

#### Status
Check API connectivity:
```bash
webamon status
webamon status --verbose
```

### Global Options

- `--api-url`: Override API base URL (advanced users only)
- `--api-key`: Override API key  
- `--config-file`: Use specific config file
- `--verbose, -v`: Enable verbose output

## Example Workflows

### Security Research
```bash
# Search for subdomains
webamon search "*.example.com" domain.name,resolved_url --size 50

# Scan suspicious domains
webamon scan suspicious-domain.com

# Get screenshots of flagged sites
webamon screenshot <report-id> --save evidence.png
```

### Domain Intelligence
```bash
# Basic domain lookup
webamon search example.com domain.name,resolved_url,page_title

# Advanced search with Lucene
webamon search --lucene 'domain.name:"example.com" AND scan_status:success' --index scans

# Bulk domain analysis
for domain in $(cat domains.txt); do
  webamon search $domain domain.name,resolved_url >> results.json
done
```

### Website Monitoring
```bash
# Scan website
webamon scan https://example.com

# Check scan results
webamon search --lucene 'submission_url:"https://example.com"' --index scans

# Download screenshot
webamon screenshot <report-id> --save monitoring/$(date +%Y%m%d).png
```

## Configuration File Format

```json
{
  "api_url": "https://search.webamon.com",
  "api_key": "your-api-key-here",
  "verbose": false
}
```

## Development

### Setup Development Environment

```bash
# Clone and install
git clone https://github.com/yourusername/webamon-cli.git
cd webamon-cli
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

### Code Formatting

```bash
black webamon_cli/
```

### Type Checking

```bash
mypy webamon_cli/
```

### Testing

```bash
pytest
```

### Building

```bash
python -m build
```

## API Integration

The CLI is designed to work with REST APIs. You may need to customize the client in `webamon_cli/client.py` to match your specific API:

1. **Update endpoints** in the `WebamonClient` class methods
2. **Modify authentication** if your API uses different auth methods
3. **Adjust response parsing** if your API has different response formats

### Example Customization

```python
# In webamon_cli/client.py
def list_items(self, limit: int = 10) -> List[Dict[str, Any]]:
    # Change '/items' to your actual endpoint
    response = self._make_request('GET', '/your-endpoint', params={'limit': limit})
    return response
```

## License

Apache License 2.0

Copyright 2025 Webamon

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request