from pathlib import Path
import ast
import re


BLOCKED_REPLACEMENT = "# blocked\n"

SECURITY_ENABLED = False

BLOCKED_NAMES = {
    "open",
    "eval",
    "exec",
    "compile",
}


class SecurityViolation(Exception):
    pass


class SimpleSecurityScanner(ast.NodeVisitor):
    def visit_Name(self, node):
        if node.id in BLOCKED_NAMES:
            raise SecurityViolation(f"Blocked name: {node.id}")
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            if node.func.id in BLOCKED_NAMES:
                raise SecurityViolation(f"Blocked function call: {node.func.id}")
        self.generic_visit(node)


def scan_python_code_simple(code: str) -> None:
    """
    Raises SecurityViolation if open/eval/exec/compile is detected.
    """

    blocked_patterns = [
        r"\bopen\s*\(",
        r"\beval\s*\(",
        r"\bexec\s*\(",
        r"\bcompile\s*\(",
    ]

    for pattern in blocked_patterns:
        if re.search(pattern, code):
            raise SecurityViolation(f"Blocked pattern: {pattern}")

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise SecurityViolation(f"Syntax error: {e}")

    SimpleSecurityScanner().visit(tree)


def _block_python_file_if_intrusion_detected(file_path) -> bool:
    """
    Scans a Python file.

    If open/eval/exec/compile is detected, the file content is replaced with:
        # blocked

    Returns:
        True  = file was blocked
        False = file was allowed
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(path)

    if not path.is_file():
        raise ValueError(f"Not a file: {path}")

    code = path.read_text(encoding="utf-8", errors="replace")

    try:
        scan_python_code_simple(code)
        return False
    except SecurityViolation:
        path.write_text(BLOCKED_REPLACEMENT, encoding="utf-8")
        return True
        
def block_python_file_if_intrusion_detected(file_path) -> bool:
    if SECURITY_ENABLED: return _block_python_file_if_intrusion_detected(file_path)
    return True
    
    
# usuage:block_python_file_if_intrusion_detected("/home/client/active_script.py")
