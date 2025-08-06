# Webamon CLI Examples

This document provides practical examples of using the Webamon CLI tool.

## Quick Start Examples

### Understanding the RESULTS Argument

**New:** For basic search (non-Lucene), RESULTS argument is now optional! 
- **Default fields**: `page_title,domain,resolved_url,dom`
- **Custom fields**: Specify your own field list as before

💡 **Search matches are highlighted with yellow background in table view.**

```bash
# New: Simple syntax with default fields (page_title,domain,resolved_url,dom)
webamon search example.com

# Traditional: Custom fields  
webamon search example.com domain.name,resolved_url

# SEARCH_TERM: What you're looking for (domain, IP, URL, etc.)
# RESULTS: Optional comma-separated list of fields (uses defaults if omitted)
```

**Common RESULTS field combinations:**
- `domain.name,resolved_url` - Domain info with URLs
- `domain.name,resolved_url,page_title` - Add page titles
- `domain.name,resolved_ip,scan_status` - Include IP and scan status
- `submission_url,scan_date,report_id` - Scan information

### 1. Basic Domain Search (Free Tier)
```bash
# Search with default fields (page_title,domain,resolved_url,dom)
webamon search example.com

# Search with more results using default fields
webamon search example.com --size 25

# Search with custom fields
webamon search example.com domain.name,resolved_url,page_title

# Search by IP address with custom fields
webamon search 192.168.1.1 resolved_ip,domain.name,scan_status
```

### 2. Configure Pro API Access
```bash
# Interactive configuration
webamon configure --save

# Or set via environment
export WEBAMON_API_KEY="your-api-key"
webamon status
```

### 3. Website Scanning
```bash
# Scan a website
webamon scan https://example.com

# Scan just a domain
webamon scan example.com

# Scan and automatically get the report
webamon scan example.com --fetch-report

# Scan with JSON output and auto-report
webamon scan example.com --format json --fetch-report
```

### 4. Get Scan Report
```bash
# Get specific report by ID (JSON format by default)
webamon report bf18c02d-ff0e-46a9-9a59-5b7b94fb27fb

# Get readable summary (table format)
webamon report bf18c02d-ff0e-46a9-9a59-5b7b94fb27fb --format table
```

### 5. Screenshot Retrieval
```bash
# Get screenshot info
webamon screenshot bf18c02d-ff0e-46a9-9a59-5b7b94fb27fb

# Save screenshot to file
webamon screenshot bf18c02d-ff0e-46a9-9a59-5b7b94fb27fb --save screenshot.png
```

## Advanced Examples

### Lucene Queries
```bash
# Search for bank-related domains with successful scans
webamon search --lucene 'domain.name:"bank*" AND scan_status:success' --index scans

# Search specific domain with custom fields
webamon search --lucene 'domain.name:"example.com"' --index domains --fields domain.name,page_title,report_id

# Search by IP range
webamon search --lucene 'resolved_ip:[192.168.1.0 TO 192.168.1.255]' --index scans
```

### Pagination (Pro Tier)
```bash
# Navigate through results using offset
webamon search "*.example.com" domain.name,resolved_url --from 0 --size 50
webamon search "*.example.com" domain.name,resolved_url --from 50 --size 50

# Use direct offset (useful for automation)
webamon search "malware" domain.name,resolved_url --from 0 --size 100
webamon search "malware" domain.name,resolved_url --from 100 --size 100

# Large dataset navigation
webamon search --lucene 'scan_status:success' --index scans --from 250 --size 25

# Combine with other options
webamon search --lucene 'domain.name:"bank*"' --index domains --from 60 --size 20 --fields domain.name,page_title
```

### Batch Operations
```bash
# Scan multiple domains
for domain in google.com facebook.com twitter.com; do
  echo "Scanning $domain..."
  webamon scan $domain --format json >> scan_results.json
done

# Search for multiple terms
while read domain; do
  webamon search "$domain" >> domain_intel.json
done < domains.txt
```

### Complete Scan Workflow

#### Option 1: Using --fetch-report flag (recommended)
```bash
#!/bin/bash
# scan_workflow_fetch_report.sh

DOMAIN="example.com"
DATE=$(date +%Y%m%d_%H%M%S)

echo "Starting scan workflow for $DOMAIN at $DATE"

# 1. Scan with auto-report fetch
echo "Scanning $DOMAIN and fetching report..."
COMPLETE_RESULT=$(webamon scan "$DOMAIN" --format json --fetch-report)
echo "$COMPLETE_RESULT" > "complete_${DOMAIN}_${DATE}.json"

# 2. Extract report ID for screenshot
REPORT_ID=$(echo "$COMPLETE_RESULT" | head -n 20 | jq -r '.report_id // empty')
if [ ! -z "$REPORT_ID" ]; then
  echo "Getting screenshot for: $REPORT_ID"
  webamon screenshot "$REPORT_ID" --save "screenshot_${REPORT_ID}.png"
  
  echo "Workflow complete. Files:"
  echo "  - complete_${DOMAIN}_${DATE}.json (scan + report)"
  echo "  - screenshot_${REPORT_ID}.png"
else
  echo "No report ID found in scan result"
fi
```

#### Option 2: Manual steps
```bash
#!/bin/bash
# scan_workflow_manual.sh

DOMAIN="example.com"
DATE=$(date +%Y%m%d_%H%M%S)

echo "Starting scan workflow for $DOMAIN at $DATE"

# 1. Initiate scan
echo "Scanning $DOMAIN..."
SCAN_RESULT=$(webamon scan "$DOMAIN" --format json)
echo "$SCAN_RESULT" > "scan_${DOMAIN}_${DATE}.json"

# 2. Extract report ID
REPORT_ID=$(echo "$SCAN_RESULT" | jq -r '.report_id // empty')
if [ ! -z "$REPORT_ID" ]; then
  echo "Report ID: $REPORT_ID"
  
  # 3. Get detailed report
  echo "Getting detailed report..."
  webamon report "$REPORT_ID" > "report_${REPORT_ID}.json"
  
  # 4. Get screenshot if available
  echo "Getting screenshot..."
  webamon screenshot "$REPORT_ID" --save "screenshot_${REPORT_ID}.png"
  
  echo "Workflow complete. Files:"
  echo "  - scan_${DOMAIN}_${DATE}.json"
  echo "  - report_${REPORT_ID}.json" 
  echo "  - screenshot_${REPORT_ID}.png"
else
  echo "No report ID found in scan result"
fi
```

### Monitoring Workflow
```bash
#!/bin/bash
# monitoring_script.sh

DOMAIN="example.com"
DATE=$(date +%Y%m%d_%H%M%S)

echo "Starting monitoring for $DOMAIN at $DATE"

# Search for existing data
echo "Searching existing data..."
webamon search "$DOMAIN" > "search_${DOMAIN}_${DATE}.json"

# Initiate new scan with auto-report
echo "Initiating new scan..."
SCAN_RESULT=$(webamon scan "$DOMAIN" --format json --fetch-report)
echo "$SCAN_RESULT" > "scan_${DOMAIN}_${DATE}.json"

# Extract report ID for screenshot
REPORT_ID=$(echo "$SCAN_RESULT" | head -n 20 | jq -r '.report_id // empty')
if [ ! -z "$REPORT_ID" ]; then
  echo "Getting screenshot: $REPORT_ID"
  webamon screenshot "$REPORT_ID" --save "screenshot_${DOMAIN}_${DATE}.png"
fi

echo "Monitoring complete for $DOMAIN"
```

### Security Research
```bash
# Find subdomains
webamon search "*.example.com" domain.name,resolved_url --size 50

# Search for specific technologies
webamon search --lucene 'page_title:"WordPress" AND domain.name:"*.com"' --index scans --size 100

# Find recently scanned suspicious domains
webamon search --lucene 'scan_date:[NOW-7DAY TO NOW] AND (page_title:"phishing" OR page_title:"malware")' --index scans
```

### Data Export and Analysis
```bash
# Export search results to CSV (requires jq)
webamon search example.com domain.name,resolved_url,page_title --format json | \
  jq -r '.[] | [.domain_name, .resolved_url, .page_title] | @csv' > results.csv

# Get all scans for a domain over time
webamon search --lucene 'domain.name:"example.com"' --index scans --format json --size 100 | \
  jq '.[] | {date: .scan_date, status: .scan_status, title: .page_title}'
```

## Output Formats

### Table Format (Default)
```bash
webamon search example.com domain.name,resolved_url
# Outputs a clean, readable table with smart data handling
```

The table format intelligently handles complex data for optimal readability:

**Search Highlighting:** 
- **Search matches** appear with yellow background highlighting
- Original `<mark>` tags from API are converted to visual highlights

**Simple Data:** Displayed directly
- Strings, numbers, booleans
- Simple values are shown as-is

**Complex Data Handling:**
- **Small lists** (≤3 items): `"tag1, tag2, tag3"`
- **Small objects** (≤2 keys): `"key1:val1, key2:val2"`
- **Large structures**: `"5 items"` or omitted entirely

**Omitted Fields Notification:**
When complex fields are hidden, you'll see:
```
Note: Complex fields omitted from table view: metadata, scan_details
Use --format json to see all fields
```

### JSON Format
```bash
webamon search example.com domain.name,resolved_url --format json
# Outputs complete raw JSON with all nested data
```

**When to use JSON:**
- Need complete data including nested objects/arrays
- Programmatic processing with scripts
- Integration with tools like `jq`
- Automation and data analysis

### Combining with Other Tools
```bash
# Use with jq for JSON processing
webamon search example.com domain.name --format json | jq '.[] | .domain_name'

# Use with grep for filtering
webamon search "*.example.com" domain.name --format json | jq -r '.[] | .domain_name' | grep -v "www"

# Pipe to other analysis tools
webamon search --lucene 'scan_status:success' --index scans --format json | \
  python analyze_domains.py
```

## Error Handling

### Check API Status
```bash
# Basic connectivity test
webamon status

# Verbose status with details
webamon --verbose status
```

### Handle Rate Limits
```bash
# Add delays between requests
for domain in $(cat large_domain_list.txt); do
  webamon search "$domain" domain.name,resolved_url >> results.json
  sleep 1  # Wait 1 second between requests
done
```

### Debugging
```bash
# Enable verbose output for debugging
webamon --verbose search example.com domain.name

# Check configuration
webamon configure  # Shows current settings
```

## Integration Examples

### Python Script Integration
```python
import subprocess
import json

def webamon_search(domain, fields):
    """Search Webamon via CLI"""
    cmd = ['webamon', 'search', domain, fields, '--format', 'json']
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        return json.loads(result.stdout)
    else:
        raise Exception(f"Webamon search failed: {result.stderr}")

# Usage
results = webamon_search("example.com", "domain.name,resolved_url")
for item in results:
    print(f"Domain: {item.get('domain_name')}, URL: {item.get('resolved_url')}")
```

### Bash Function
```bash
# Add to ~/.bashrc or ~/.bash_profile
webamon_quick() {
    local domain=$1
    echo "Quick lookup for: $domain"
    webamon search "$domain" domain.name,resolved_url,page_title
}

# Usage: webamon_quick example.com
```

## Common Errors and Solutions

### "Missing argument 'RESULTS'" or "RESULTS argument is required" (Legacy)

**Note:** This error is now less common since RESULTS is optional with default fields.

If you encounter this error with older versions:

```bash
# ✅ New: RESULTS is optional (uses defaults: page_title,domain,resolved_url,dom)
webamon search example.com

# ✅ Traditional: Custom RESULTS argument
webamon search example.com domain.name,resolved_url

# ✅ Lucene search never needs RESULTS
webamon search --lucene 'domain.name:"example.com"' --index scans
```

### "Missing argument 'SEARCH_TERM'"

This happens when you use search without specifying what to search for:

```bash
# ❌ Wrong - missing SEARCH_TERM
webamon search domain.name,resolved_url

# ✅ Correct - includes both arguments
webamon search example.com domain.name,resolved_url
```

### "Error: --index is required when using --lucene"

Lucene searches require an index to be specified:

```bash
# ❌ Wrong - missing --index
webamon search --lucene 'domain.name:"example.com"'

# ✅ Correct - includes --index
webamon search --lucene 'domain.name:"example.com"' --index scans
```

### Search Syntax Differences

**Basic Search:** Requires SEARCH_TERM and RESULTS arguments
```bash
webamon search <SEARCH_TERM> <RESULTS> [OPTIONS]
webamon search example.com domain.name,resolved_url
webamon search example.com domain.name,resolved_url --from 50 --size 25
```

**Lucene Search:** Uses --lucene flag with --index, no RESULTS argument needed
```bash
webamon search --lucene '<LUCENE_QUERY>' --index <INDEX> [OPTIONS]
webamon search --lucene 'domain.name:"bank*"' --index scans
webamon search --lucene 'domain.name:"bank*"' --index scans --from 100 --size 50
```

## Tips and Best Practices

1. **Start with Free Tier**: Test basic functionality before getting an API key
2. **Use JSON Format for Automation**: Always use `--format json` when scripting
3. **Respect Rate Limits**: Add delays between requests for bulk operations
4. **Save Screenshots**: Use the `--save` option to preserve evidence
5. **Lucene Syntax**: Learn Lucene query syntax for powerful searches
6. **Error Handling**: Always check return codes in scripts
7. **Configuration**: Use environment variables or config files for API keys
8. **Field Selection**: Use default fields for quick searches, specify custom fields for targeted results