"""Main CLI module for Webamon CLI tool."""

import click
from rich.console import Console
from rich.table import Table
from typing import Optional, List, Dict, Any, Tuple

from .client import WebamonClient
from .config import Config

console = Console()


def _highlight_search_marks(text: str) -> str:
    """Convert <mark> tags to rich formatting for highlighting search matches."""
    if '<mark>' not in text:
        return text
    
    # Replace <mark> tags with rich formatting
    # Use bright yellow background for highlights
    highlighted = text.replace('<mark>', '[black on bright_yellow]')
    highlighted = highlighted.replace('</mark>', '[/black on bright_yellow]')
    
    return highlighted


def _smart_truncate_with_marks(text: str, max_length: int = 50) -> str:
    """Intelligently truncate text while preserving <mark> tags."""
    if len(text) <= max_length:
        return text
    
    # If we have mark tags, try to keep them intact
    if '<mark>' in text:
        # Find the last complete mark tag that fits
        truncate_pos = max_length - 3  # Reserve space for "..."
        
        # Look backwards for a safe place to cut (not inside a tag)
        while truncate_pos > 0:
            if text[truncate_pos] not in ['<', '>', 'k', 'r', 'a', 'm', '/', ' ']:
                break
            truncate_pos -= 1
        
        # Make sure we don't cut in the middle of a mark tag
        test_text = text[:truncate_pos]
        open_marks = test_text.count('<mark>')
        close_marks = test_text.count('</mark>')
        
        # If we have unmatched marks, try to include the closing tag
        if open_marks > close_marks and '</mark>' in text[truncate_pos:]:
            next_close = text.find('</mark>', truncate_pos)
            if next_close != -1 and next_close < max_length + 10:  # Allow some flexibility
                truncate_pos = next_close + 7  # Include the closing tag
        
        return text[:truncate_pos] + "..."
    else:
        # No mark tags, simple truncation
        return text[:max_length - 3] + "..."


def _format_table_value(value: Any) -> str:
    """Format a value for table display, handling different data types."""
    if value is None:
        return "[dim]null[/dim]"
    elif isinstance(value, bool):
        return "[green]true[/green]" if value else "[red]false[/red]"
    elif isinstance(value, (list, dict)):
        # This shouldn't happen after _process_table_data, but safety check
        return "[dim]<complex>[/dim]"
    elif isinstance(value, str):
        # Smart truncation that preserves <mark> tags
        truncated_value = _smart_truncate_with_marks(value, 50)
        
        # Highlight search matches after truncation
        formatted_value = _highlight_search_marks(truncated_value)
        return formatted_value
    else:
        # Numbers, etc.
        str_value = str(value)
        if len(str_value) > 50:
            return str_value[:47] + "..."
        return str_value


def _process_table_data(data: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Process data for table display, handling nested structures intelligently."""
    if not data:
        return [], []
    
    # Analyze the data structure
    sample_item = data[0]
    simple_fields = []
    complex_fields = []
    
    for key, value in sample_item.items():
        if isinstance(value, (dict, list)) and value:  # Non-empty complex types
            if isinstance(value, dict) and len(value) <= 3:
                # Small dicts might be worth flattening
                complex_fields.append((key, 'small_dict'))
            elif isinstance(value, list) and len(value) <= 5 and all(isinstance(x, (str, int, float, bool)) for x in value):
                # Small lists of simple values
                complex_fields.append((key, 'simple_list'))
            else:
                # Large or complex nested structures - omit
                complex_fields.append((key, 'omit'))
        else:
            # Simple values or empty containers
            simple_fields.append(key)
    
    # Process the data
    processed_data = []
    omitted_fields = []
    
    for item in data:
        processed_item = {}
        
        # Add simple fields
        for field in simple_fields:
            processed_item[field] = item.get(field)
        
        # Handle complex fields
        for field, field_type in complex_fields:
            value = item.get(field)
            
            if field_type == 'small_dict' and isinstance(value, dict):
                # Flatten small dicts or show key count
                if len(value) <= 2:
                    # Show as key:value pairs
                    dict_str = ', '.join([f"{k}:{v}" for k, v in value.items()])
                    processed_item[field] = dict_str[:50] + ("..." if len(dict_str) > 50 else "")
                else:
                    processed_item[field] = f"[dim]{len(value)} items[/dim]"
            
            elif field_type == 'simple_list' and isinstance(value, list):
                # Show list as comma-separated or count
                if len(value) <= 3:
                    list_str = ', '.join([str(x) for x in value])
                    processed_item[field] = list_str[:50] + ("..." if len(list_str) > 50 else "")
                else:
                    processed_item[field] = f"[dim]{len(value)} items[/dim]"
            
            elif field_type == 'omit':
                # Track omitted fields
                if field not in omitted_fields:
                    omitted_fields.append(field)
        
        processed_data.append(processed_item)
    
    return processed_data, omitted_fields


@click.group()
@click.option('--api-key', help='API key for authentication')
@click.option('--config-file', help='Path to config file')
@click.pass_context
def main(ctx, api_key: Optional[str], config_file: Optional[str]):
    """Webamon Search CLI - The Google of Threat Intelligence.
    
    Search domains, scan websites, and retrieve screenshots using the Webamon API.
    """
    ctx.ensure_object(dict)
    
    # Load configuration
    config = Config.load(config_file)
    
    # Override config with command line options
    if api_key:
        config.api_key = api_key
    
    # Store config and client in context
    ctx.obj['config'] = config
    ctx.obj['client'] = WebamonClient(config)


@main.command()
@click.pass_context
def status(ctx):
    """Check API status and connection."""
    client = ctx.obj['client']
    config = ctx.obj['config']
    
    try:
        test_result = client.test_connection()
        
        console.print("[green]Webamon Search API is accessible[/green]")
        console.print("[dim]The Google of Threat Intelligence[/dim]")
            
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to connect: {e}")
        ctx.exit(1)


@main.command()
@click.argument('search_term')
@click.argument('results', required=False)
@click.option('--size', '-s', default=10, help='Number of results to return (max: 100)')
@click.option('--from', 'from_offset', default=0, help='Starting offset for pagination (Pro users only)')
@click.option('--lucene', is_flag=True, help='Use Lucene query syntax')
@click.option('--index', help='Index to search (required for Lucene queries)')
@click.option('--fields', help='Comma-separated list of fields to return')
@click.option('--format', 'output_format', 
              type=click.Choice(['table', 'json']), 
              default='table', help='Output format (table=readable with simplified complex data, json=complete raw data)')
@click.pass_context
def search(ctx, search_term: str, results: Optional[str], size: int, from_offset: int,
           lucene: bool, index: Optional[str], fields: Optional[str], output_format: str):
    """Search the Webamon threat intelligence database.
    
    SEARCH_TERM: The search term (IP, domain, URL, hash, etc.)
    RESULTS: Comma-separated list of fields to search within and return
             (Optional - defaults to: page_title,domain,resolved_url,dom)
             Examples: domain.name,resolved_url,page_title
    
    Note: Table format automatically simplifies complex nested data for readability.
    Search matches are highlighted with yellow background in table view.
    Use --format json to see complete data including all nested fields.
    
    Examples:
    \b
    # Basic search (uses default fields)
    webamon search example.com
    webamon search example.com --size 20
    
    # Basic search with custom fields
    webamon search example.com domain.name,resolved_url
    webamon search example.com domain.name,resolved_url,page_title
    
    # Lucene search (no RESULTS argument)
    webamon search --lucene 'domain.name:"bank*" AND scan_status:success' --index scans
    webamon search --lucene 'resolved_ip:[192.168.1.0 TO 192.168.1.255]' --index scans
    
    # Pagination (Pro users only)
    webamon search example.com --from 10 --size 25
    webamon search --lucene 'domain.name:"bank*"' --index scans --from 50 --size 20
    """
    client = ctx.obj['client']
    config = ctx.obj['config']
    
    if lucene and not index:
        console.print("[red]Error:[/red] --index is required when using --lucene")
        ctx.exit(1)
    
    # Set default RESULTS for non-Lucene searches if not provided
    if not lucene and not results:
        results = "page_title,domain,resolved_url,dom"
    
    # Check if pagination is being used without API key
    if from_offset > 0 and not config.api_key:
        console.print("[yellow]Warning:[/yellow] Pagination is only available for Pro users with API keys")
        console.print("Using free tier - pagination parameters will be ignored")
        from_offset = 0
    
    try:
        if lucene:
            response = client.search_lucene(search_term, index, fields, size, from_offset)
        else:
            response = client.search(search_term, results, size, from_offset)
        
        if output_format == 'json':
            console.print_json(data=response)
        else:
            # Handle different response formats
            data = response
            total_hits = None
            pagination = None
            
            if isinstance(response, dict) and 'results' in response:
                data = response['results']
                total_hits = response.get('total_hits')
                pagination = response.get('pagination')
            elif isinstance(response, dict) and 'data' in response:
                data = response['data']
                total_hits = response.get('total_hits')
                pagination = response.get('pagination')
            elif isinstance(response, dict) and 'total_hits' in response:
                total_hits = response.get('total_hits')
                pagination = response.get('pagination')
            
            if isinstance(data, list) and data:
                # Create title with pagination info if available
                title = f"Search Results for '{search_term}'"
                if pagination and isinstance(pagination, dict):
                    total = pagination.get('total', total_hits)
                    from_pos = pagination.get('from', from_offset)
                    if total and from_pos is not None:
                        title += f" ({total:,} total, from {from_pos:,})"
                    elif total:
                        title += f" ({total:,} total)"
                elif total_hits is not None:
                    title += f" ({total_hits:,} total matches)"
                
                table = Table(title=title)
                
                # Process and filter data for better table display
                processed_data, omitted_fields = _process_table_data(data)
                
                # Add columns based on processed data
                if processed_data:
                    for key in processed_data[0].keys():
                        table.add_column(key.replace('_', ' ').title(), style="cyan", overflow="fold")
                    
                    # Add rows
                    for item in processed_data:
                        values = []
                        for value in item.values():
                            values.append(_format_table_value(value))
                        table.add_row(*values)
                
                console.print(table)
                
                # Show information about omitted complex fields
                if omitted_fields:
                    omitted_str = ', '.join(omitted_fields)
                    console.print(f"[yellow]Note:[/yellow] Complex fields omitted from table view: {omitted_str}")
                    console.print("[dim]Use --format json to see all fields[/dim]")
                
                # Show enhanced summary with pagination info
                if pagination and isinstance(pagination, dict):
                    total = pagination.get('total', total_hits)
                    from_pos = pagination.get('from', from_offset)
                    size_val = pagination.get('size', size)
                    has_more = pagination.get('has_more', False)
                    next_from = pagination.get('next_from')
                    prev_from = pagination.get('prev_from')
                    
                    summary = f"[dim]Showing {len(data)} results"
                    if total:
                        summary += f" of {total:,} total"
                    if from_pos is not None:
                        summary += f" (from position {from_pos:,})"
                    summary += "[/dim]"
                    console.print(f"\n{summary}")
                    
                    # Show pagination navigation hints using from/size
                    nav_hints = []
                    if prev_from is not None and prev_from >= 0:
                        nav_hints.append(f"Previous: --from {prev_from} --size {size_val}")
                    if has_more and next_from is not None:
                        nav_hints.append(f"Next: --from {next_from} --size {size_val}")
                    elif has_more and from_pos is not None:
                        # Calculate next_from if not provided
                        calculated_next = from_pos + size_val
                        nav_hints.append(f"Next: --from {calculated_next} --size {size_val}")
                    
                    if nav_hints:
                        console.print(f"[dim]Navigation: {' | '.join(nav_hints)}[/dim]")
                else:
                    # Fallback summary without pagination
                    summary = f"[dim]Showing {len(data)} results"
                    if total_hits is not None and total_hits != len(data):
                        summary += f" of {total_hits:,} total matches"
                    summary += "[/dim]"
                    console.print(f"\n{summary}")
            else:
                console.print_json(data=response)
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        ctx.exit(1)


@main.command()
@click.argument('report_id')
@click.option('--format', 'output_format', 
              type=click.Choice(['table', 'json']), 
              default='json', help='Output format (json=complete raw data, table=readable with simplified complex data)')
@click.pass_context
def report(ctx, report_id: str, output_format: str):
    """Get a specific scan report by report ID.
    
    REPORT_ID: The unique report identifier (e.g., bf18c02d-ff0e-46a9-9a59-5b7b94fb27fb)
    
    This is a convenience command that searches for the report using:
    report_id:<REPORT_ID> in the scans index
    
    Examples:
    \b
    webamon report bf18c02d-ff0e-46a9-9a59-5b7b94fb27fb
    webamon report bf18c02d-ff0e-46a9-9a59-5b7b94fb27fb --format table
    """
    client = ctx.obj['client']
    
    # Build the Lucene query for the report ID
    lucene_query = f'report_id:"{report_id}"'
    
    try:
        console.print(f"[dim]Searching for report: {report_id}[/dim]")
        response = client.search_lucene(lucene_query, 'scans', size=1)
        
        if output_format == 'json':
            console.print_json(data=response)
        else:
            # Handle different response formats
            data = response
            if isinstance(response, dict) and 'results' in response:
                data = response['results']
            elif isinstance(response, dict) and 'data' in response:
                data = response['data']
            
            if isinstance(data, list) and data:
                if len(data) == 1:
                    # Single report found
                    report_data = data[0]
                    
                    # Process data for table display
                    processed_data, omitted_fields = _process_table_data([report_data])
                    
                    if processed_data:
                        table = Table(title=f"Scan Report: {report_id}")
                        table.add_column("Field", style="cyan", width=20)
                        table.add_column("Value", style="white", overflow="fold")
                        
                        # Display as key-value pairs for single report
                        for key, value in processed_data[0].items():
                            formatted_value = _format_table_value(value)
                            table.add_row(key.replace('_', ' ').title(), formatted_value)
                        
                        console.print(table)
                        
                        # Show information about omitted complex fields
                        if omitted_fields:
                            omitted_str = ', '.join(omitted_fields)
                            console.print(f"\n[yellow]Note:[/yellow] Complex fields omitted from table view: {omitted_str}")
                            console.print("[dim]Use --format json to see all fields[/dim]")
                    else:
                        console.print_json(data=report_data)
                else:
                    # Multiple reports found (shouldn't happen with unique IDs)
                    console.print(f"[yellow]Warning:[/yellow] Found {len(data)} reports with ID {report_id}")
                    console.print_json(data=data)
            else:
                console.print(f"[yellow]No report found with ID: {report_id}[/yellow]")
                console.print("[dim]Make sure the report ID is correct and the scan has completed[/dim]")
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        ctx.exit(1)


@main.command()
@click.argument('url')
@click.option('--format', 'output_format', 
              type=click.Choice(['table', 'json']), 
              default='table', help='Output format')
@click.option('--fetch-report', is_flag=True, 
              help='Automatically fetch the detailed report after scan initiation')
@click.pass_context
def scan(ctx, url: str, output_format: str, fetch_report: bool):
    """Initiate a scan for the specified target.
    
    URL: Target domain or URL to scan (e.g., https://example.com or example.com)
    
    Returns a report ID that can be used to retrieve scan results.
    
    Use --fetch-report to automatically fetch the report after scan initiation.
    
    Examples:
    \b
    webamon scan example.com
    webamon scan https://example.com --fetch-report
    webamon scan example.com --format json --fetch-report
    """
    client = ctx.obj['client']
    
    try:
        response = client.scan(url)
        
        # Extract report_id from response for --wait functionality
        report_id = None
        if isinstance(response, dict):
            report_id = response.get('report_id') or response.get('id')
        
        # Display initial scan response
        if output_format == 'json':
            console.print_json(data=response)
        else:
            console.print(f"[green]✓[/green] Scan initiated for: {url}")
            
            if isinstance(response, dict):
                table = Table(title="Scan Details")
                table.add_column("Property", style="cyan")
                table.add_column("Value", style="magenta")
                
                for key, value in response.items():
                    table.add_row(key.replace('_', ' ').title(), str(value))
                
                console.print(table)
                
                # Highlight report ID if present
                if 'report_id' in response:
                    console.print(f"\n[yellow]Report ID:[/yellow] {response['report_id']}")
                    if not fetch_report:
                        console.print("[dim]Use this ID with 'webamon report' to get the scan results[/dim]")
                        console.print("[dim]Or use 'webamon screenshot' to get the screenshot[/dim]")
            else:
                console.print_json(data=response)
        
        # If --fetch-report flag is used and we have a report_id, fetch the report
        if fetch_report and report_id:
            console.print(f"\n[cyan]📋 --fetch-report detected, getting report: {report_id}[/cyan]")
            console.print("[dim]" + "="*60 + "[/dim]")
            
            try:
                # Call the report functionality directly
                report_response = client.search_lucene(f'report_id:"{report_id}"', 'scans', size=1)
                
                # Display report in JSON format (default for report command)
                console.print_json(data=report_response)
                
            except Exception as report_error:
                console.print(f"[yellow]Warning:[/yellow] Failed to fetch report: {report_error}")
                console.print(f"[dim]You can manually fetch the report later with:[/dim]")
                console.print(f"[dim]webamon report {report_id}[/dim]")
        
        elif fetch_report and not report_id:
            console.print("\n[yellow]Warning:[/yellow] --fetch-report flag used but no report_id found in scan response")
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        ctx.exit(1)


@main.command()
@click.argument('report_id')
@click.option('--save', '-o', help='Save screenshot to file')
@click.option('--format', 'output_format', 
              type=click.Choice(['info', 'json']), 
              default='info', help='Output format')
@click.pass_context
def screenshot(ctx, report_id: str, save: Optional[str], output_format: str):
    """Retrieve screenshot for a specific scan report.
    
    REPORT_ID: The report ID from a scan result
    """
    client = ctx.obj['client']
    
    try:
        response = client.screenshot(report_id)
        
        if output_format == 'json':
            console.print_json(data=response)
        else:
            if isinstance(response, dict) and 'report' in response:
                report = response['report']
                
                if 'screenshot' in report:
                    screenshot_data = report['screenshot']
                    
                    if save:
                        # Save base64 image data to file
                        import base64
                        
                        # Remove data URL prefix if present
                        if screenshot_data.startswith('data:image'):
                            screenshot_data = screenshot_data.split(',')[1]
                        
                        with open(save, 'wb') as f:
                            f.write(base64.b64decode(screenshot_data))
                        
                        console.print(f"[green]✓[/green] Screenshot saved to: {save}")
                    else:
                        console.print(f"[green]✓[/green] Screenshot retrieved for report: {report_id}")
                        console.print(f"[yellow]Data size:[/yellow] {len(screenshot_data)} characters")
                        console.print("[dim]Use --save filename.png to save the screenshot[/dim]")
                else:
                    console.print(f"[yellow]No screenshot found for report: {report_id}[/yellow]")
            else:
                console.print_json(data=response)
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        ctx.exit(1)


@main.command()
@click.option('--api-key', help='API key (optional, enables pro features)')
def configure(api_key: Optional[str]):
    """Configure API connection settings.
    
    Configuration is automatically saved after successful validation."""
    
    # Prompt for API key if not provided
    if api_key is None:
        api_key = click.prompt('API key (optional, press Enter to skip)', default='', hide_input=True)
        if api_key == '':
            api_key = None
    
    # Create config (API URL is auto-detected based on API key)
    config = Config(api_key=api_key)
    
    # Show which endpoint will be used
    if api_key:
        console.print("[dim]Using pro.webamon.com (API key detected)[/dim]")
    else:
        console.print("[dim]Using search.webamon.com (no API key)[/dim]")
    
    # Test the connection
    client = WebamonClient(config)
    try:
        console.print(f"[dim]Testing connection to {config.api_url}...[/dim]")
        if config.api_key:
            console.print(f"[dim]Using x-api-key header (length: {len(config.api_key)} chars)[/dim]")
        
        client.test_connection()
        console.print("[green]✓[/green] Configuration valid - API connection successful")
        console.print(f"[cyan]API URL:[/cyan] {config.api_url}")
        console.print(f"[cyan]API Key:[/cyan] {'Set' if config.api_key else 'Not set (free tier)'}")
        
        # Always save the configuration
        config.save()
        console.print("[green]✓[/green] Configuration saved")
            
    except Exception as e:
        console.print(f"[red]✗[/red] Configuration test failed: {e}")
        if config.api_key:
            console.print("[yellow]Debug info:[/yellow]")
            console.print(f"  - API URL: {config.api_url}")
            console.print(f"  - API Key length: {len(config.api_key)} characters")
            console.print(f"  - Using x-api-key header authentication")
            console.print("  - Ensure your API key is valid and has the correct permissions")


if __name__ == '__main__':
    main()