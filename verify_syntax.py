#!/usr/bin/env python3
"""Verify all Python files have valid syntax."""
import py_compile
import sys
from pathlib import Path

def verify_file(path):
    """Verify a single file compiles correctly."""
    try:
        py_compile.compile(str(path), doraise=True)
        return True, None
    except py_compile.PyCompileError as e:
        return False, str(e)

def main():
    base = Path("/mnt/user-data/workspace/md-linkcheck")
    src_files = list((base / "src" / "md_linkcheck").glob("*.py"))
    test_files = list((base / "tests").glob("test_*.py"))
    all_files = src_files + test_files
    
    errors = []
    for f in all_files:
        ok, err = verify_file(f)
        if not ok:
            errors.append(f"{f}: {err}")
    
    if errors:
        print("Syntax errors found:")
        for e in errors:
            print(f"  {e}")
        return 1
    
    print(f"All {len(all_files)} Python files have valid syntax.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
