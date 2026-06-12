import ast
import logging
import os
import re

logger = logging.getLogger(__name__)


class CodeParser:
    def generate_structure_dropdowns(self, filepath: str, code: str) -> str:
        ext = os.path.splitext(filepath)[1].lower()
        if ext == ".py":
            return self._parse_python(code)
        elif ext in [".js", ".ts", ".jsx", ".tsx"]:
            return self._parse_javascript(code)
        elif ext in [".html", ".htm"]:
            return self._parse_html(code)
        elif ext == ".css":
            return self._parse_css(code)
        return ""

    def _parse_python(self, code: str) -> str:
        try:
            tree = ast.parse(code)

            class PythonStructureVisitor(ast.NodeVisitor):
                def __init__(self):
                    self.imports = []
                    self.classes = []
                    self.functions = []
                    self.consts = []
                    self.current_class = None

                def visit_Import(self, node: ast.Import) -> None:
                    try:
                        self.imports.append(ast.unparse(node))
                    except Exception:
                        pass

                def visit_ImportFrom(self, node):
                    try:
                        self.imports.append(ast.unparse(node))
                    except Exception:
                        pass

                def visit_ClassDef(self, node):
                    self.classes.append(f"class {node.name}")
                    old_class = self.current_class
                    self.current_class = node.name
                    for child in node.body:
                        self.visit(child)
                    self.current_class = old_class

                def visit_FunctionDef(self, node):
                    self.handle_function(node)

                def visit_AsyncFunctionDef(self, node):
                    self.handle_function(node)

                def handle_function(self, node):
                    args = []
                    for arg in node.args.args:
                        if self.current_class and arg.arg == "self":
                            continue
                        args.append(arg.arg)
                    if node.args.vararg:
                        args.append(f"*{node.args.vararg.arg}")
                    if node.args.kwarg:
                        args.append(f"**{node.args.kwarg.arg}")

                    args_str = ", ".join(args)
                    if self.current_class:
                        self.functions.append(
                            f"def {self.current_class}.{node.name}({args_str})"
                        )
                    else:
                        self.functions.append(f"def {node.name}({args_str})")

                def visit_Assign(self, node):
                    for t in node.targets:
                        if isinstance(t, ast.Name) and t.id.isupper():
                            self.consts.append(t.id)

            visitor = PythonStructureVisitor()
            visitor.visit(tree)
            return self._format_dropdowns(
                visitor.imports, visitor.classes, visitor.functions, visitor.consts
            )

        except SyntaxError as e:
            logger.warning(
                f"AST parsing failed (SyntaxError: {e}). Falling back to Regex for structure map."
            )
            return self._parse_python_regex_fallback(code)
        except Exception as e:
            logger.error(f"Unexpected AST parse error: {e}")
            return ""

    def _parse_python_regex_fallback(self, code: str) -> str:
        """Used when a Python file has syntax errors so the AI isn't blinded."""
        imports = re.findall(r"^(?:import|from)\s+[a-zA-Z0-9_\.]+", code, re.MULTILINE)
        classes = [
            f"class {c}"
            for c in re.findall(r"^class\s+([a-zA-Z0-9_]+)", code, re.MULTILINE)
        ]
        functions = [
            f"def {f}()"
            for f in re.findall(r"^[ \t]*def\s+([a-zA-Z0-9_]+)", code, re.MULTILINE)
        ]
        consts = list(set(re.findall(r"^([A-Z_][A-Z0-9_]+)\s*=", code, re.MULTILINE)))

        return self._format_dropdowns(imports, classes, functions, consts)

    def _parse_javascript(self, code: str) -> str:
        imports: list[str] = re.findall(
            r"(?:import|from|require)\s+['\"].*?['\"]", code
        )
        classes = re.findall(r"(?:class|interface)\s+([a-zA-Z0-9_$]+)", code)
        types = re.findall(r"type\s+([a-zA-Z0-9_$]+)\s*=", code)
        classes.extend([f"type {t}" for t in types])

        fn_patterns = [
            r"function\s+([a-zA-Z0-9_$]+)\s*\(([^)]*)\)",
            r"(?:const|let|var|window\.)\s*([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\(([^)]*)\)\s*=>",
            r"^\s*(?:async\s*)?([a-zA-Z0-9_$]+)\s*\(([^)]*)\)\s*\{",
        ]
        raw_fns = []
        for pattern in fn_patterns:
            raw_fns.extend(re.findall(pattern, code, re.MULTILINE))

        clean_fns = []
        seen = set()
        for name, params in raw_fns:
            if name not in seen and name not in [
                "if",
                "for",
                "while",
                "return",
                "catch",
                "switch",
                "await",
                "yield",
                "import",
                "export",
                "default",
            ]:
                clean_fns.append(f"{name}({params.strip()})")
                seen.add(name)

        entities = re.findall(r"(?:const|var|let)\s+([A-Z0-9_]{3,})", code)
        return self._format_dropdowns(
            imports, classes, sorted(clean_fns), sorted(list(set(entities)))
        )

    def _parse_html(self, code: str) -> str:
        scripts: list[str] = re.findall(
            r"<script[\s\S]*?src=['\"](.*?)['\"]", code, re.IGNORECASE
        )
        styles = re.findall(r"<link[\s\S]*?href=['\"](.*?)['\"]", code, re.IGNORECASE)
        ids = re.findall(r"id=['\"](.*?)['\"]", code, re.IGNORECASE)
        return self._format_dropdowns(
            [],
            [f"Script: {s}" for s in scripts],
            [f"ID: #{i}" for i in ids],
            [f"CSS: {s}" for s in styles],
        )

    def _parse_css(self, code: str) -> str:
        selectors = re.findall(r"([#\.]?[a-zA-Z0-9_-]+)\s*\{", code)
        unique_selectors = list(dict.fromkeys(selectors))
        return self._format_dropdowns([], [], unique_selectors[:50], [])

    def _format_dropdowns(
        self, imp: list[str], cls: list[str], fn: list[str], cnst: list[str]
    ) -> str:
        res: str = ""
        if imp:
            res += f"<details><summary>Imports ({len(imp)})</summary>{'<br>'.join(sorted(imp))}</details>\n"
        if cnst:
            res += f"<details><summary>Entities ({len(cnst)})</summary>{'<br>'.join(sorted(cnst))}</details>\n"
        if cls:
            res += f"<details><summary>Classes/Types ({len(cls)})</summary>{'<br>'.join(sorted(cls))}</details>\n"
        if fn:
            res += f"<details><summary>Logic ({len(fn)})</summary>{'<br>'.join(sorted(fn))}</details>\n"
        return res
