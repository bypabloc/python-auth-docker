from __future__ import annotations

from ast import Import as ast_Import
from ast import parse as ast_parse
from ast import walk as ast_walk
from pathlib import Path
from sys import argv as sys_argv
from sys import exit as sys_exit


def validate_imports(file_path: Path) -> int:
    """Validar los imports en un archivo."""
    if "migrations" in file_path.parts:
        return 0

    with file_path.open() as f:
        tree = ast_parse(f.read(), filename=str(file_path))

    errors = []
    for node in ast_walk(tree):
        if isinstance(node, ast_Import):
            line = node.lineno
            col = node.col_offset
            message = (
                f"{file_path}:{line}:{col}: IMP001 Use specific imports instead of "
                f"'import {node.names[0].name}'\n"
                f"{line} | {node.names[0].name}\n"
                f"{' ' * col}^{'^' * len(node.names[0].name)} IMP001"
            )
            errors.append(message)

    if errors:
        for error in errors:
            print(error)
        return 1
    return 0


if __name__ == "__main__":
    exit_code = 0
    for file_arg in sys_argv[1:]:
        file_path = Path(file_arg)
        exit_code += validate_imports(file_path)
    sys_exit(exit_code)
