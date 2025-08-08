"""Main CLI module for Webamon CLI tool."""

import csv
import json
import time
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from typing import Optional, List, Dict, Any, Tuple

from .client import WebamonClient
from .config import Config
from . import __version__

console = Console()


def _load_scan_fields() -> List[Dict[str, str]]:
    """Load scan fields from the included JSON file."""
    # Try multiple possible locations for the fields file
    possible_paths = [
        Path(__file__).parent / "scans_fields.json",  # Installed package location
        Path(__file__).parent.parent / "webamon_cli" / "scans_fields.json",  # Development location
    ]
    
    for fields_file in possible_paths:
        try:
            if fields_file.exists():
                with open(fields_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (json.JSONDecodeError, Exception):
            continue
    
    return []


def _format_error_message(error: Exception) -> None:
    """Format and display error messages with better formatting for multi-line errors."""
    error_msg = str(error)
    if '\n' in error_msg:
        # Multi-line error (like quota messages) - format nicely
        lines = error_msg.split('\n')
        console.print(f"[red]Error:[/red] {lines[0]}")
        for line in lines[1:]:
            if line.strip():
                if 'https://' in line:
                    console.print(f"[blue]{line.strip()}[/blue]")
                else:
                    console.print(f"[yellow]{line.strip()}[/yellow]")
    else:
        console.print(f"[red]Error:[/red] {error_msg}")


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


def _export_to_file(data: List[Dict[str, Any]], filename: str, format_type: str, title: str = "Results") -> None:
    """Export data to file in the specified format."""
    try:
        if format_type == 'json':
            # Export as JSON
            export_filename = filename if filename.endswith('.json') else f"{filename}.json"
            with open(export_filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        elif format_type == 'csv':
            # Export as CSV
            export_filename = filename if filename.endswith('.csv') else f"{filename}.csv"
            if data:
                # Get all unique keys from all items
                all_keys = set()
                for item in data:
                    all_keys.update(item.keys())
                
                fieldnames = sorted(all_keys)
                
                with open(export_filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for item in data:
                        # Flatten complex values for CSV
                        row = {}
                        for key in fieldnames:
                            value = item.get(key, '')
                            if isinstance(value, (list, dict)):
                                row[key] = json.dumps(value) if value else ''
                            else:
                                row[key] = str(value) if value is not None else ''
                        writer.writerow(row)
        
        elif format_type == 'table':
            # Export as Markdown table
            export_filename = filename if filename.endswith('.md') else f"{filename}.md"
            
            if data:
                # Process data for table display
                processed_data, _ = _process_table_data(data)
                
                # Get all unique keys
                all_keys = set()
                for item in processed_data:
                    all_keys.update(item.keys())
                
                fieldnames = sorted(all_keys)
                
                with open(export_filename, 'w', encoding='utf-8') as f:
                    f.write(f"# {title}\n\n")
                    
                    # Write markdown table header
                    f.write("| " + " | ".join(fieldnames) + " |\n")
                    f.write("| " + " | ".join(["---"] * len(fieldnames)) + " |\n")
                    
                    # Write data rows
                    for item in processed_data:
                        row_values = []
                        for key in fieldnames:
                            value = item.get(key, '')
                            # Clean value for markdown (remove pipes and newlines)
                            clean_value = str(value).replace('|', '\\|').replace('\n', ' ').replace('\r', '')
                            row_values.append(clean_value)
                        f.write("| " + " | ".join(row_values) + " |\n")
        
        console.print(f"[green]✓[/green] Exported {len(data)} results to: [cyan]{export_filename}[/cyan]")
        
    except Exception as e:
        console.print(f"[red]Error exporting to file:[/red] {e}")


def _generate_pagination_commands(search_term: str, results: Optional[str], pagination: Dict[str, Any], 
                                lucene: bool = False, index: Optional[str] = None, 
                                fields: Optional[str] = None, output_format: str = 'table',
                                export: Optional[str] = None) -> List[str]:
    """Generate next/previous pagination command suggestions."""
    commands = []
    
    # Base command construction
    if lucene:
        base_cmd = f'webamon search --lucene "{search_term}" --index {index}'
    else:
        base_cmd = f'webamon search "{search_term}"'
        if results:
            base_cmd += f' "{results}"'
    
    # Add common options
    if fields:
        base_cmd += f' --fields {fields}'
    if output_format != 'table':
        base_cmd += f' --format {output_format}'
    if export:
        base_cmd += f' --export {export}'
    
    # Add navigation commands
    if pagination.get('prev_from') is not None:
        prev_from = pagination['prev_from']
        size = pagination.get('size', 10)
        prev_cmd = f'{base_cmd} --from {prev_from} --size {size}'
        commands.append(f"◀ Previous: {prev_cmd}")
    
    if pagination.get('has_more') and pagination.get('next_from') is not None:
        next_from = pagination['next_from']
        size = pagination.get('size', 10)
        next_cmd = f'{base_cmd} --from {next_from} --size {size}'
        commands.append(f"▶ Next: {next_cmd}")
    
    return commands


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
@click.option('-v', '--verbose', is_flag=True, help='Show request URL and response status code')
@click.version_option(version=__version__, prog_name='webamon')
@click.pass_context
def main(ctx, api_key: Optional[str], config_file: Optional[str], verbose: bool):
    """Webamon Search CLI - The Google of Threat Intelligence.
    
    Search domains, scan websites, and retrieve screenshots using the Webamon API.
    """
    ctx.ensure_object(dict)
    
    # Load configuration
    config = Config.load(config_file)
    
    # Override config with command line options
    if api_key:
        config.api_key = api_key
    
    # Store config, verbose flag, and client in context
    ctx.obj['config'] = config
    ctx.obj['verbose'] = verbose
    ctx.obj['client'] = WebamonClient(config, verbose=verbose)


@main.command()
@click.pass_context
def status(ctx):
    """Check API status and connection."""
    client = ctx.obj['client']
    config = ctx.obj['config']
    
    # Show which API endpoint we're attempting to connect to
    api_tier = "Pro" if config.api_key else "Free"
    console.print(f"[cyan]Checking {api_tier} API:[/cyan] {config.api_url}")
    
    try:
        test_result = client.test_connection()
        
        console.print("[green]✓ Webamon Search API is accessible[/green]")
        console.print("[dim]The Google of Threat Intelligence[/dim]")
        
        # Show additional tier information
        if config.api_key:
            console.print("[dim]✓ API key configured - Pro features available[/dim]")
        else:
            console.print("[dim]ℹ️  Free tier (20 queries/day) - Add API key for Pro features[/dim]")
            
    except Exception as e:
        console.print(f"[red]✗ Failed to connect to {config.api_url}:[/red]")
        _format_error_message(e)
        ctx.exit(1)


@main.command()
@click.option('--search', '-s', help='Filter fields by name (case-insensitive)')
@click.option('--category', '-c', help='Filter by category (e.g., "certificate", "domain", "cookie")')
@click.option('--format', 'output_format', 
              type=click.Choice(['table', 'json', 'list']), 
              default='table', help='Output format')
@click.pass_context
def fields(ctx, search: Optional[str], category: Optional[str], output_format: str):
    """Show available scan fields with descriptions.
    
    Use this command to discover what fields you can use with --fields or RESULTS arguments.
    
    Examples:
    \b
    webamon fields                           # Show all fields
    webamon fields --search domain          # Fields containing "domain"
    webamon fields --category certificate   # Certificate-related fields
    webamon fields --format json            # JSON output
    webamon fields --search title --format list  # Simple list format
    """
    fields_data = _load_scan_fields()
    
    if not fields_data:
        console.print("[red]Error:[/red] Could not load scan fields data")
        console.print("\n[yellow]This might happen if:[/yellow]")
        console.print("• The package wasn't installed properly")
        console.print("• You're running from source without installing")
        console.print("\n[yellow]Solutions:[/yellow]")
        console.print("• Install the package: [cyan]pip install .[/cyan]")
        console.print("• Or install in development mode: [cyan]pip install -e .[/cyan]")
        console.print("• Or force reinstall: [cyan]pip install --force-reinstall .[/cyan]")
        ctx.exit(1)
    
    # Filter fields based on search and category
    filtered_fields = fields_data
    
    if search:
        search_lower = search.lower()
        filtered_fields = [
            field for field in filtered_fields 
            if search_lower in field['name'].lower() or search_lower in field['description'].lower()
        ]
    
    if category:
        category_lower = category.lower()
        filtered_fields = [
            field for field in filtered_fields 
            if field['name'].lower().startswith(category_lower + '.')
        ]
    
    if not filtered_fields:
        console.print(f"[yellow]No fields found matching criteria[/yellow]")
        if search:
            console.print(f"Search: '{search}'")
        if category:
            console.print(f"Category: '{category}'")
        return
    
    # Display results
    if output_format == 'json':
        console.print_json(data=filtered_fields)
    elif output_format == 'list':
        for field in filtered_fields:
            console.print(field['name'])
    else:  # table format
        table = Table(title=f"Available Scan Fields ({len(filtered_fields)} found)")
        table.add_column("Field Name", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        
        for field in filtered_fields:
            table.add_row(field['name'], field['description'])
        
        console.print(table)
        
        # Show usage hints
        console.print(f"\n[dim]💡 Usage: webamon search example.com field1,field2,field3[/dim]")
        console.print(f"[dim]💡 Lucene: webamon search --lucene 'field:value' --index scans --fields field1,field2[/dim]")


@main.command()
@click.argument('domain')
@click.option('--size', '-s', default=10, help='Number of results to return (max: 100)')
@click.option('--from', 'from_offset', default=0, help='Starting offset for pagination (Pro users only)')
@click.option('--fields', help='Comma-separated list of fields to return (separate from search fields)')
@click.option('--format', 'output_format', 
              type=click.Choice(['table', 'json', 'csv']), 
              default='table', help='Output format (json=complete raw data, table=readable with simplified complex data, csv=comma-separated values)')
@click.option('--export', '-o', help='Export results to file (format: json→.json, table→.md, csv→.csv)')
@click.pass_context
def infostealers(ctx, domain: str, size: int, from_offset: int, fields: Optional[str], output_format: str, export: Optional[str]):
    """Search infostealers index for compromised credentials by domain.
    
    DOMAIN: Domain to search for compromised credentials (e.g., example.com, bank-site.com)
    
    This command searches for:
    - Direct domain matches in the domain field
    - Email addresses with @domain in the username field
    
    Domains with hyphens are automatically quoted for proper search syntax.
    
    Examples:
    \b
    webamon infostealers example.com
    webamon infostealers bank-site.com --size 50
    webamon infostealers example.com --fields domain,username,password
    webamon infostealers example.com --format json
    """
    config = ctx.obj['config']
    client = ctx.obj['client']
    
    # Check if pagination is being used without API key
    if from_offset > 0 and not config.api_key:
        console.print("[yellow]Warning:[/yellow] Pagination is only available for Pro users with API keys")
        console.print("Using free tier - pagination parameters will be ignored")
        from_offset = 0
    
    # Check if size is being used without API key
    if size > 10 and not config.api_key:
        console.print("[yellow]Warning:[/yellow] Size parameter is only available for Pro users with API keys")
        console.print("Using free tier - limiting to 10 results")
        size = 10
    
    # Build Lucene query - quote domain if it contains hyphens
    if '-' in domain:
        quoted_domain = f'"{domain}"'
    else:
        quoted_domain = domain
    
    lucene_query = f'domain:{quoted_domain} OR username:@{domain}'
    
    try:
        console.print(f"[dim]Searching infostealers for domain: {domain}[/dim]")
        response = client.search_lucene(lucene_query, 'infostealers', fields=fields, size=size, from_offset=from_offset)
        
        if output_format == 'table':
            # Handle response structure (dict with results/pagination or just list)
            data = response.get('results', response) if isinstance(response, dict) else response
            pagination = response.get('pagination') if isinstance(response, dict) else None
            total_hits = response.get('total_hits') if isinstance(response, dict) else None
            
            if isinstance(data, list) and len(data) > 0:
                # Process data for table display
                processed_data, omitted_fields = _process_table_data(data)
                
                # Create title with pagination info
                title = f"Infostealers Results for: {domain}"
                if pagination and isinstance(pagination, dict):
                    total = pagination.get('total')
                    if total:
                        title += f" ({total:,} total)"
                elif total_hits is not None:
                    title += f" ({total_hits:,} total matches)"
                elif len(data) > 0:
                    title += f" ({len(data)} results)"
                
                table = Table(title=title)
                
                # Get all unique keys for columns
                all_keys = set()
                for item in processed_data:
                    all_keys.update(item.keys())
                
                # Add columns
                for key in sorted(all_keys):
                    table.add_column(key.replace('_', ' ').title(), style="cyan", overflow="fold")
                
                # Add rows
                for item in processed_data:
                    row = []
                    for key in sorted(all_keys):
                        value = item.get(key, '')
                        row.append(_format_table_value(value))
                    table.add_row(*row)
                
                console.print(table)
                
                # Show omitted fields notice
                if omitted_fields:
                    console.print(f"\n[yellow]Note:[/yellow] Complex fields omitted from table view: {', '.join(omitted_fields)}")
                    console.print("[dim]Use --format json to see all fields[/dim]")
                
                # Show enhanced summary with pagination info
                if pagination and isinstance(pagination, dict):
                    total = pagination.get('total')
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
                    
                    # Show enhanced pagination navigation with copy-paste commands
                    if prev_from is not None or (has_more and next_from is not None):
                        console.print(f"\n[cyan]📄 Pagination Navigation:[/cyan]")
                        
                        # Generate complete commands for copy-paste
                        pagination_commands = _generate_pagination_commands(
                            f'domain:\"{domain}\" OR username:@{domain}', None, pagination, 
                            True, 'infostealers', fields, output_format, export
                        )
                        
                        # For infostealers, we need to construct the commands differently
                        infostealers_commands = []
                        if pagination.get('prev_from') is not None:
                            prev_from = pagination['prev_from']
                            size = pagination.get('size', 10)
                            base_cmd = f'webamon infostealers "{domain}"'
                            if fields:
                                base_cmd += f' --fields {fields}'
                            if output_format != 'table':
                                base_cmd += f' --format {output_format}'
                            if export:
                                base_cmd += f' --export {export}'
                            prev_cmd = f'{base_cmd} --from {prev_from} --size {size}'
                            infostealers_commands.append(f"◀ Previous: {prev_cmd}")
                        
                        if pagination.get('has_more') and pagination.get('next_from') is not None:
                            next_from = pagination['next_from']
                            size = pagination.get('size', 10)
                            base_cmd = f'webamon infostealers "{domain}"'
                            if fields:
                                base_cmd += f' --fields {fields}'
                            if output_format != 'table':
                                base_cmd += f' --format {output_format}'
                            if export:
                                base_cmd += f' --export {export}'
                            next_cmd = f'{base_cmd} --from {next_from} --size {size}'
                            infostealers_commands.append(f"▶ Next: {next_cmd}")
                        
                        for cmd in infostealers_commands:
                            console.print(f"[dim]{cmd}[/dim]")
                        
                        # Also show the short format for reference
                        nav_hints = []
                        if prev_from is not None and prev_from >= 0:
                            nav_hints.append(f"--from {prev_from} --size {size_val}")
                        if has_more and next_from is not None:
                            nav_hints.append(f"--from {next_from} --size {size_val}")
                        
                        if nav_hints:
                            console.print(f"[dim]Quick options: {' | '.join(nav_hints)}[/dim]")
                else:
                    # Fallback summary without pagination
                    summary = f"[dim]Showing {len(data)} results"
                    if len(data) == size and size < 100:
                        summary += f" (use --size {min(size * 2, 100)} for more)"
                    if from_offset > 0:
                        summary += f" starting from offset {from_offset}"
                    summary += "[/dim]"
                    console.print(f"\n{summary}")
                
                # Handle export for table format
                if export:
                    title = f"Infostealers Results for: {domain}"
                    _export_to_file(data, export, 'table', title)
                    
            elif isinstance(data, list) and len(data) == 0:
                console.print(f"[yellow]No compromised credentials found for domain: {domain}[/yellow]")
                console.print("[dim]This domain appears clean in our infostealers database[/dim]")
            else:
                # Fallback for unexpected data structure in table format
                console.print(f"[yellow]Unexpected data format for table display[/yellow]")
                console.print(f"[dim]Data type: {type(response)}[/dim]")
                console.print_json(data=response)
        elif output_format == 'csv':
            # Handle response structure (dict with results/pagination or just list)
            data = response.get('results', response) if isinstance(response, dict) else response
            
            if isinstance(data, list) and len(data) > 0:
                title = f"Infostealers Results for: {domain}"
                console.print(f"[dim]CSV format - showing first few rows as table preview[/dim]")
                
                # Get all unique keys
                all_keys = set()
                for item in data:
                    all_keys.update(item.keys())
                fieldnames = sorted(all_keys)
                
                # Create table for preview
                table = Table(title=f"CSV Preview: {title}")
                for key in fieldnames:
                    table.add_column(key.replace('_', ' ').title(), style="cyan")
                
                # Show first 5 rows
                preview_data = data[:5]
                for item in preview_data:
                    row = []
                    for key in fieldnames:
                        value = item.get(key, '')
                        if isinstance(value, (list, dict)):
                            row.append(json.dumps(value) if value else '')
                        else:
                            row.append(str(value) if value is not None else '')
                    table.add_row(*row)
                
                console.print(table)
                
                if len(data) > 5:
                    console.print(f"[dim]... and {len(data) - 5} more rows[/dim]")
                
                # Export CSV
                if export:
                    _export_to_file(data, export, 'csv', title)
                else:
                    filename = f"infostealers_{domain.replace('.', '_')}"
                    console.print(f"[dim]Auto-exporting CSV to: {filename}.csv[/dim]")
                    _export_to_file(data, filename, 'csv', title)
            else:
                console.print(f"[yellow]No compromised credentials found for domain: {domain}[/yellow]")
                
        else:  # json format
            console.print_json(data=response)
            
            # Handle export for JSON format
            if export:
                # Extract data for export
                data = response.get('results', response) if isinstance(response, dict) else response
                if isinstance(data, list):
                    title = f"Infostealers Results for: {domain}"
                    _export_to_file(data, export, 'json', title)
            
    except Exception as e:
        _format_error_message(e)
        ctx.exit(1)


@main.command()
@click.argument('search_term')
@click.argument('results', required=False)
@click.option('--size', '-s', default=10, help='Number of results to return (max: 100)')
@click.option('--from', 'from_offset', default=0, help='Starting offset for pagination (Pro users only)')
@click.option('--lucene', is_flag=True, help='Use Lucene query syntax')
@click.option('--index', help='Index to search (required for Lucene queries)')
@click.option('--fields', help='Comma-separated list of fields to return (separate from search fields)')
@click.option('--format', 'output_format', 
              type=click.Choice(['table', 'json', 'csv']), 
              default='table', help='Output format (table=readable with simplified complex data, json=complete raw data, csv=comma-separated values)')
@click.option('--export', '-o', help='Export results to file (format: json→.json, table→.md, csv→.csv)')
@click.pass_context
def search(ctx, search_term: str, results: Optional[str], size: int, from_offset: int,
           lucene: bool, index: Optional[str], fields: Optional[str], output_format: str, export: Optional[str]):
    """Search the Webamon threat intelligence database.
    
    SEARCH_TERM: The search term (IP, domain, URL, hash, etc.)
    RESULTS: Comma-separated list of fields to search within
             (Optional - defaults to: page_title,domain.name,resolved_url,dom)
             Examples: domain.name,resolved_url,page_title
    
    Note: RESULTS controls which fields to search within, --fields controls which fields to return.
    Table format automatically simplifies complex nested data for readability.
    Search matches are highlighted with yellow background in table view.
    Use --format json to see complete data including all nested fields.
    
    Examples:
    \b
    # Basic search (uses default search and return fields)
    webamon search example.com
    webamon search example.com --size 20
    
    # Basic search with custom search fields (returns same fields)
    webamon search example.com domain.name,resolved_url
    
    # Basic search with custom return fields (uses default search fields)
    webamon search example.com --fields page_title,domain.name
    
    # Basic search with both custom search and return fields
    webamon search example.com tag --fields page_title,domain.name
    
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
        results = "page_title,domain.name,resolved_url,dom"
    
    # Check if pagination is being used without API key
    if from_offset > 0 and not config.api_key:
        console.print("[yellow]Warning:[/yellow] Pagination is only available for Pro users with API keys")
        console.print("Using free tier - pagination parameters will be ignored")
        from_offset = 0
    
    try:
        if lucene:
            response = client.search_lucene(search_term, index, fields, size, from_offset)
        else:
            response = client.search(search_term, results, size, from_offset, fields)
        
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
            
            # Create title with pagination info if available (used by all formats)
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
            
            if output_format == 'table':
                if isinstance(data, list) and data:
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
                        
                        # Show enhanced pagination navigation with copy-paste commands
                        if prev_from is not None or (has_more and next_from is not None):
                            console.print(f"\n[cyan]📄 Pagination Navigation:[/cyan]")
                            
                            # Generate complete commands for copy-paste
                            pagination_commands = _generate_pagination_commands(
                                search_term, results, pagination, lucene, index, fields, output_format, export
                            )
                            
                            for cmd in pagination_commands:
                                console.print(f"[dim]{cmd}[/dim]")
                            
                            # Also show the short format for reference
                            nav_hints = []
                            if prev_from is not None and prev_from >= 0:
                                nav_hints.append(f"--from {prev_from} --size {size_val}")
                            if has_more and next_from is not None:
                                nav_hints.append(f"--from {next_from} --size {size_val}")
                            elif has_more and from_pos is not None:
                                calculated_next = from_pos + size_val
                                nav_hints.append(f"--from {calculated_next} --size {size_val}")
                            
                            if nav_hints:
                                console.print(f"[dim]Quick options: {' | '.join(nav_hints)}[/dim]")
                    else:
                        # Fallback summary without pagination
                        summary = f"[dim]Showing {len(data)} results"
                        if total_hits is not None and total_hits != len(data):
                            summary += f" of {total_hits:,} total matches"
                        summary += "[/dim]"
                        console.print(f"\n{summary}")
                    
                    # Handle export for table format
                    if export:
                        _export_to_file(data, export, 'table', title)
                else:
                    console.print(f"[yellow]No search results found for '{search_term}'[/yellow]")
                    
            elif output_format == 'csv':
                # CSV output format
                if isinstance(data, list) and data:
                    # Display CSV data as table for console output
                    console.print(f"[dim]CSV format - showing first few rows as table preview[/dim]")
                    
                    # Get all unique keys
                    all_keys = set()
                    for item in data:
                        all_keys.update(item.keys())
                    fieldnames = sorted(all_keys)
                    
                    # Create table for preview
                    table = Table(title=f"CSV Preview: {title}")
                    for key in fieldnames:
                        table.add_column(key.replace('_', ' ').title(), style="cyan")
                    
                    # Show first 5 rows
                    preview_data = data[:5]
                    for item in preview_data:
                        row = []
                        for key in fieldnames:
                            value = item.get(key, '')
                            if isinstance(value, (list, dict)):
                                row.append(json.dumps(value) if value else '')
                            else:
                                row.append(str(value) if value is not None else '')
                        table.add_row(*row)
                    
                    console.print(table)
                    
                    if len(data) > 5:
                        console.print(f"[dim]... and {len(data) - 5} more rows[/dim]")
                    
                    # Always export CSV to file when using CSV format
                    if export:
                        _export_to_file(data, export, 'csv', title)
                    else:
                        # Auto-export CSV if no filename specified
                        filename = f"webamon_search_{search_term.replace(' ', '_').replace('/', '_')}"
                        console.print(f"[dim]Auto-exporting CSV to: {filename}.csv[/dim]")
                        _export_to_file(data, filename, 'csv', title)
                        
                else:
                    console.print("[yellow]No data to display in CSV format[/yellow]")
                    
            else:  # json format
                console.print_json(data=response)
                
                # Handle export for JSON format
                if export and isinstance(data, list):
                    _export_to_file(data, export, 'json', title)
            
    except Exception as e:
        _format_error_message(e)
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
        _format_error_message(e)
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
                # Silent delay to allow backend processing
                time.sleep(4)
                
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
        _format_error_message(e)
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
        _format_error_message(e)
        ctx.exit(1)


@main.command()
@click.option('--api-key', help='API key (optional, enables pro features)')
@click.pass_context
def configure(ctx, api_key: Optional[str]):
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
    verbose = ctx.obj.get('verbose', False) if ctx.obj else False
    client = WebamonClient(config, verbose=verbose)
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