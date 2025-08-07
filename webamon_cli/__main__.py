#!/usr/bin/env python3
"""
Main entry point for webamon_cli when run as a module.

This allows the package to be executed with:
python -m webamon_cli
"""

from .cli import main

if __name__ == '__main__':
    main()