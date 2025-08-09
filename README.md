# Webamon Search CLI

**The Google of Threat Intelligence**

A powerful command-line interface for the Webamon Search API. Search & Threat Hunt across the web at scale. Returning unbiased & unfiltered results.

## Installation

### From PyPI

```bash
pip install webamon-cli
```

> **Webamon Search** - The Google of Threat Intelligence. Access millions of scanned domains, IPs, and threat indicators.

### Global Installation (Linux/macOS)

**Recommended: Install via Package Manager**
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install pipx
pipx install webamon-cli
pipx ensurepath

# Fedora/CentOS/RHEL
sudo dnf install pipx
pipx install webamon-cli
pipx ensurepath

# macOS
brew install pipx
pipx install webamon-cli
pipx ensurepath

# Arch Linux
sudo pacman -S python-pipx
pipx install webamon-cli
pipx ensurepath
```

**Alternative: Install from Source**

If you need the latest development version or package managers don't work:

1. Install pipx first:
```bash
# Ubuntu/Debian: sudo apt install pipx
# Fedora/CentOS: sudo dnf install pipx  
# macOS: brew install pipx
# Arch: sudo pacman -S python-pipx
```

2. Clone and install:
```bash
git clone https://github.com/webamon-org/webamon-cli.git
cd webamon-cli
pipx install .
pipx ensurepath
```

**Verify Installation:**
```bash
# Test the installation
webamon --help

# If command not found, add to PATH:
export PATH="$HOME/.local/bin:$PATH"
# Then restart your terminal or run:
source ~/.bashrc  # Linux
# or
source ~/.zshrc   # macOS
```

### Development Installation

For development work:
```bash
git clone https://github.com/webamon-org/webamon-cli.git
cd webamon-cli
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

## Quick Start

**Install globally:**
```bash
# Ubuntu/Debian
sudo apt install pipx && pipx install webamon-cli

# Fedora/CentOS  
sudo dnf install pipx && pipx install webamon-cli

# macOS
brew install pipx && pipx install webamon-cli
```

**🚀 Start searching immediately - it's that simple!**

No commands needed - just type what you're looking for:
```bash
webamon example.com       # Search for example.com
webamon malware          # Search for malware
webamon nrd_20250801     # Search latest domain registrations
```

**The magic:** `webamon <query>` automatically triggers search - **fastest threat hunting workflow ever!**

**Still works the traditional way too:**
```bash
webamon search example.com     # Explicit search command
webamon configure             # Configure API key for pro features
webamon status               # Test connection
webamon scan https://example.com  # Scan a website
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
webamon configure
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

#### Search - **Default Command** ⚡

**🔥 Amazing: No need to type "search" - just search directly!**

```bash
# Lightning fast - just type what you want to find:
webamon example.com           # Search for example.com
webamon malware              # Search for malware  
webamon 1.1.1.1             # Search for IP address
webamon nrd_20250801 tag     # Search in specific field
```

**Traditional syntax still works:**
```bash
webamon search example.com   # Explicit search command (same result)
```

**How it works:**
- `webamon <SEARCH_TERM>` - Lightning fast default search 🚀
- `webamon <SEARCH_TERM> <RESULTS>` - Search in specific fields
- `SEARCH_TERM`: What you're searching for (domain, IP, URL, hash, etc.)
- `RESULTS`: Comma-separated list of fields to search within
  - **Default search fields**: `page_title,domain.name,resolved_url,dom,tag`
  - **Custom search fields**: Specify your own field list
- `--fields`: Comma-separated list of fields to return (separate from search fields)
  - **Default return fields**: Same as search fields when not specified

💡 **Search matches are highlighted with yellow background in table view.**

**Examples:**
```bash
# Default search (fastest way)
webamon example.com

# Search in specific fields
webamon example.com domain.name,resolved_url

# Custom return fields  
webamon example.com --fields page_title,domain.name

# Both custom search and return fields
webamon example.com tag --fields page_title,domain.name

# Different output formats
webamon example.com --format json
webamon example.com --format csv

# Export results
webamon example.com --export results.json
webamon example.com --format csv --export analysis.csv
```

**Pagination (Pro Users Only):**
```bash
# Limit results with default fields
webamon search example.com --size 25

# Use offset for pagination with default fields
webamon search example.com --from 25 --size 25

# Use offset with custom fields
webamon search example.com domain.name,resolved_url --from 25 --size 25

# Skip first 100 results with default fields
webamon search example.com --from 100 --size 50

# Navigate large result sets
webamon search "*.bank.com" --from 0 --size 100
```

**Lucene Search:**
```bash
# Advanced Lucene queries
webamon search --lucene 'domain.name:"bank*" AND scan_status:success' --index scans

# Specify fields to return
webamon search --lucene 'domain.name:"example.com"' --index scans --fields domain.name,page_title
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

#### Infostealers
Search for compromised credentials by domain:
```bash
# Search for compromised credentials
webamon infostealers example.com

# Search domain with hyphens (automatically quoted)
webamon infostealers bank-site.com

# Get more results (Pro users)
webamon infostealers example.com --size 50

# Specify fields to return
webamon infostealers example.com --fields domain,username,password

# JSON output
webamon infostealers example.com --format json

# CSV output (auto-exports to file)
webamon infostealers example.com --format csv

# Export to custom file
webamon infostealers example.com --export compromised_creds
webamon infostealers example.com --format csv --export creds.csv
```

#### Screenshot
Retrieve scan screenshots:
```bash
# Get screenshot info
webamon screenshot bf18c02d-ff0e-46a9-9a59-5b7b94fb27fb

# Save screenshot to file
webamon screenshot bf18c02d-ff0e-46a9-9a59-5b7b94fb27fb --save screenshot.png

```

#### Status
Check API connectivity:
```bash
webamon status
```

#### Fields
Discover available scan fields:
```bash
# Show all available fields
webamon fields

# Search for specific fields
webamon fields --search domain

# Show fields by category
webamon fields --category certificate

# Get fields as a simple list
webamon fields --search ip --format list
```

### Global Options

- `--api-key`: Override API key  
- `--config-file`: Use specific config file
- `--verbose, -v`: Enable verbose output

## Example Workflows

### Security Research
```bash
# Search for subdomains with default fields
webamon search "*.example.com"

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
  webamon search $domain >> results.json
done
```



## Quotas and Pricing

### Free Tier
- **20 daily API calls**
- **10 results per response**
- Basic search functionality
- Limited infostealer data access

### Pro Plans
When you hit the daily quota, the CLI will suggest upgrading to Pro for expanded access:

- **Founding Analyst**: 1,000+ daily calls, up to 100 results per response
- **Enterprise**: 10,000+ daily calls, up to 500 results per response
- **All plans**: Complete infostealer data access, pagination, priority support

For current pricing and features, visit: https://webamon.com/pricing

If you exceed your quota, you'll see a helpful error message with upgrade information.

## Configuration File Format

```json
{
  "api_key": "your-api-key-here",
  "verbose": false
}
```

## Development

### Setup Development Environment

```bash
# Clone and install
git clone https://github.com/webamon-org/webamon-cli.git
cd webamon-cli
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

### Building

```bash
python -m build
```


## Uninstall

### Global Installation (pipx)
```bash
pipx uninstall webamon-cli
```

### PyPI Installation
```bash
pip uninstall webamon-cli
```

### Development Installation
```bash
# If installed with pip install -e .
pip uninstall webamon-cli

# Remove the repository
rm -rf webamon-cli
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

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines on:

- Setting up your development environment
- Code style and testing requirements  
- Submitting bug reports and feature requests
- Pull request process and code review

Quick start: Fork → Branch → Code → Test → Pull Request

## Security

Security is important to us. Please see [SECURITY.md](SECURITY.md) for:

- Reporting security vulnerabilities
- Security best practices for users
- API key and data protection guidelines
- Incident response procedures