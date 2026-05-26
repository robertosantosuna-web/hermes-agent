#!/usr/bin/env python3
"""
Brain Code Validator (AP-12) — LSP-style semantic validation for brain scripts.
Inspired by Hermes v0.14 LSP semantic diagnostics + ruff linting.

Validates Python syntax, imports, and common issues in brain scripts.
Zero tokens, no external deps beyond Python stdlib.
"""
import ast
import sys
import os
from pathlib import Path
from datetime import datetime

HERMES = Path(os.path.expanduser('~/.hermes'))
SCRIPTS_DIR = HERMES / 'scripts'
BRAIN_DIRS = [SCRIPTS_DIR, HERMES / 'thalamus', HERMES / 'cortex', HERMES / 'executive']

# ── Validation Rules ──────────────────────────────────────────────────────

def validate_syntax(filepath: str) -> list[dict]:
    """Check if Python file has valid syntax."""
    errors = []
    try:
        with open(filepath) as f:
            source = f.read()
        ast.parse(source, filename=filepath)
    except SyntaxError as e:
        errors.append({
            'type': 'syntax_error',
            'file': filepath,
            'line': e.lineno or 0,
            'message': f'SyntaxError: {e.msg}',
            'severity': 'CRITICAL',
        })
    return errors


def validate_imports(filepath: str) -> list[dict]:
    """Check for likely-broken imports."""
    errors = []
    try:
        with open(filepath) as f:
            source = f.read()
        tree = ast.parse(source, filename=filepath)
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                # Check for common issues
                if isinstance(node, ast.ImportFrom):
                    if node.module and '..' in node.module:
                        errors.append({
                            'type': 'risky_import',
                            'file': filepath,
                            'line': node.lineno,
                            'message': f'Relative import beyond parent: {node.module}',
                            'severity': 'LOW',
                        })
    except SyntaxError:
        pass  # Already caught by validate_syntax
    return errors


def validate_dangerous_patterns(filepath: str) -> list[dict]:
    """Check for dangerous patterns in code (os.system, subprocess without safety)."""
    errors = []
    try:
        with open(filepath) as f:
            source = f.read()
        tree = ast.parse(source, filename=filepath)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # os.system with dynamic input
                if (isinstance(node.func, ast.Attribute) and
                    isinstance(node.func.value, ast.Name) and
                    node.func.value.id == 'os' and
                    node.func.attr == 'system'):
                    for arg in node.args:
                        if not isinstance(arg, ast.Constant):
                            errors.append({
                                'type': 'dangerous_os_system',
                                'file': filepath,
                                'line': node.lineno,
                                'message': 'os.system() with non-constant arg — potential injection',
                                'severity': 'HIGH',
                            })
                
                # subprocess with shell=True
                if (isinstance(node.func, ast.Attribute) and
                    node.func.attr in ('call', 'run', 'Popen')):
                    for kw in node.keywords:
                        if kw.arg == 'shell' and isinstance(kw.value, ast.Constant) and kw.value.value:
                            errors.append({
                                'type': 'shell_true',
                                'file': filepath,
                                'line': node.lineno,
                                'message': 'subprocess with shell=True — prefer list args',
                                'severity': 'MEDIUM',
                            })
    except SyntaxError:
        pass
    return errors


def validate_file(filepath: str) -> list[dict]:
    """Run all validations on a file."""
    if not os.path.exists(filepath):
        return [{'type': 'missing', 'file': filepath, 'message': 'File not found', 'severity': 'CRITICAL'}]
    if not filepath.endswith('.py'):
        return []
    
    errors = []
    errors.extend(validate_syntax(filepath))
    errors.extend(validate_imports(filepath))
    errors.extend(validate_dangerous_patterns(filepath))
    return errors


def validate_all_brain_scripts() -> dict:
    """Validate all Python scripts in brain directories."""
    results = {
        'timestamp': datetime.now().isoformat(),
        'files_checked': 0,
        'files_with_errors': 0,
        'total_errors': 0,
        'errors_by_file': {},
    }
    
    for d in BRAIN_DIRS:
        if not d.exists():
            continue
        for py_file in d.rglob('*.py'):
            fpath = str(py_file)
            errors = validate_file(fpath)
            results['files_checked'] += 1
            if errors:
                results['files_with_errors'] += 1
                results['total_errors'] += len(errors)
                results['errors_by_file'][fpath] = errors
    
    return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Brain Code Validator (LSP-style)')
    parser.add_argument('--file', help='Validate a single file')
    parser.add_argument('--all', action='store_true', help='Validate all brain scripts')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    args = parser.parse_args()
    
    import json
    
    if args.file:
        errors = validate_file(args.file)
        if args.json:
            print(json.dumps({'file': args.file, 'errors': errors}, ensure_ascii=False, indent=2))
        else:
            if not errors:
                print(f'✅ {args.file}: OK')
            else:
                for e in errors:
                    print(f'  [{e["severity"]}] {e["type"]}: {e["message"]} (line {e["line"]})')
        sys.exit(1 if errors else 0)
    
    if args.all:
        results = validate_all_brain_scripts()
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print(f'📋 Validated {results["files_checked"]} files')
            if results['files_with_errors']:
                print(f'⚠ {results["files_with_errors"]} files with {results["total_errors"]} errors:')
                for fpath, errors in results['errors_by_file'].items():
                    print(f'  {fpath}:')
                    for e in errors:
                        print(f'    [{e["severity"]}] {e["type"]}: {e["message"]}')
            else:
                print('✅ All brain scripts pass validation')
        sys.exit(1 if results['files_with_errors'] else 0)
    
    # Default: no args = show status
    results = validate_all_brain_scripts()
    critical = sum(1 for f, errs in results['errors_by_file'].items() 
                   for e in errs if e.get('severity') == 'CRITICAL')
    if critical:
        print(f'🔴 {critical} CRITICAL issues found')
    elif results['files_with_errors']:
        print(f'🟡 {results["files_with_errors"]} files with non-critical issues')
    else:
        print('✅ All brain scripts pass validation')
    sys.exit(0)


if __name__ == '__main__':
    main()
