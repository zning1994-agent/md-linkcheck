#!/bin/bash
cd /mnt/user-data/workspace/md-linkcheck
pip install -e ".[dev]" -q
pytest tests/test_parser.py -v
