"""
Code Analysis Tools - Understand code structure and dependencies
"""

import ast
import re
from pathlib import Path
from typing import Any, Dict, List

from .base import BaseTool


class CodeAnalysisTool(BaseTool):
    """Analyze code structure, imports, functions, classes, and dependencies"""

    @property
    def name(self) -> str:
        return "analyze_code"

    @property
    def description(self) -> str:
        return "Analyze code files to extract structure, imports, functions, classes, and dependencies."

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to code file to analyze"},
                "analysis_type": {
                    "type": "string",
                    "description": "Type of analysis: 'structure', 'imports', 'functions', 'classes', 'dependencies', 'all'",
                    "enum": ["structure", "imports", "functions", "classes", "dependencies", "all"],
                    "default": "all",
                },
                "include_private": {
                    "type": "boolean",
                    "description": "Include private members (starting with _)",
                    "default": False,
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum nesting depth for analysis",
                    "default": 3,
                },
            },
            "required": ["file_path"],
        }

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Analyze code file structure and dependencies.

        Args:
            file_path: Path to code file
            analysis_type: Type of analysis to perform
            include_private: Include private members
            max_depth: Maximum analysis depth

        Returns:
            dict: Analysis results with code structure information
        """
        file_path = kwargs.get("file_path")
        analysis_type = kwargs.get("analysis_type", "all")
        include_private = kwargs.get("include_private", False)
        max_depth = kwargs.get("max_depth", 3)

        if not file_path:
            return {"success": False, "error": "file_path is required"}

        try:
            path = Path(file_path).expanduser().resolve()
        except Exception as e:
            return {"success": False, "error": f"Invalid file path: {e}"}

        if not path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}

        if not path.is_file():
            return {"success": False, "error": f"Not a file: {file_path}"}

        # Detect language
        language = self._detect_language(path)
        if language not in ["python", "javascript", "typescript"]:
            return {
                "success": False,
                "error": f"Unsupported language: {language}. Currently supports Python, JavaScript, and TypeScript.",
            }

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            # Perform analysis based on language and type
            if language == "python":
                analysis = self._analyze_python(content, analysis_type, include_private, max_depth)
            elif language in ["javascript", "typescript"]:
                analysis = self._analyze_javascript(
                    content, analysis_type, include_private, max_depth
                )
            else:
                return {
                    "success": False,
                    "error": f"Analysis not implemented for language: {language}",
                }

            return {
                "success": True,
                "file_path": str(path),
                "language": language,
                "analysis_type": analysis_type,
                **analysis,
            }

        except UnicodeDecodeError:
            return {
                "success": False,
                "error": f"File is not text or uses unsupported encoding: {file_path}",
            }
        except Exception as e:
            return {"success": False, "error": f"Error analyzing code: {e}"}

    def _detect_language(self, path: Path) -> str:
        """Detect programming language from file extension"""
        ext = path.suffix.lower()
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
        }
        return language_map.get(ext, "unknown")

    def _analyze_python(
        self, content: str, analysis_type: str, include_private: bool, max_depth: int
    ) -> Dict[str, Any]:
        """Analyze Python code using AST"""
        try:
            tree = ast.parse(content)
            analyzer = PythonAnalyzer(include_private, max_depth)
            analyzer.visit(tree)

            results = {}

            if analysis_type in ["structure", "all"]:
                results["structure"] = analyzer.get_structure()

            if analysis_type in ["imports", "all"]:
                results["imports"] = analyzer.get_imports()

            if analysis_type in ["functions", "all"]:
                results["functions"] = analyzer.get_functions()

            if analysis_type in ["classes", "all"]:
                results["classes"] = analyzer.get_classes()

            if analysis_type in ["dependencies", "all"]:
                results["dependencies"] = analyzer.get_dependencies()

            return results

        except SyntaxError as e:
            return {
                "error": f"Syntax error in Python code: {e}",
                "line": e.lineno,
                "offset": e.offset,
            }

    def _analyze_javascript(
        self, content: str, analysis_type: str, include_private: bool, max_depth: int
    ) -> Dict[str, Any]:
        """Analyze JavaScript/TypeScript code using regex patterns"""
        # Basic regex-based analysis for JS/TS
        analyzer = JavaScriptAnalyzer(include_private, max_depth)
        return analyzer.analyze(content, analysis_type)


class PythonAnalyzer(ast.NodeVisitor):
    """AST-based Python code analyzer"""

    def __init__(self, include_private: bool, max_depth: int):
        self.include_private = include_private
        self.max_depth = max_depth
        self.current_depth = 0

        # Analysis results
        self.imports = []
        self.functions = []
        self.classes = []
        self.dependencies = set()
        self.structure = []

        # Context tracking
        self.current_class = None
        self.current_function = None

    def visit_Import(self, node):
        """Handle import statements"""
        for alias in node.names:
            self.imports.append(
                {"name": alias.name, "alias": alias.asname, "line": node.lineno, "type": "import"}
            )
            self.dependencies.add(alias.name.split(".")[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """Handle from import statements"""
        module = node.module or ""
        for alias in node.names:
            self.imports.append(
                {
                    "module": module,
                    "name": alias.name,
                    "alias": alias.asname,
                    "line": node.lineno,
                    "type": "from_import",
                }
            )
            if module:
                self.dependencies.add(module.split(".")[0])
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        """Handle function definitions"""
        if self._should_include(node.name):
            func_info = {
                "name": node.name,
                "line": node.lineno,
                "end_line": getattr(node, "end_lineno", node.lineno),
                "args": [arg.arg for arg in node.args.args],
                "class": self.current_class,
                "decorators": [self._get_decorator_name(d) for d in node.decorator_list],
            }
            self.functions.append(func_info)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        """Handle async function definitions"""
        if self._should_include(node.name):
            func_info = {
                "name": node.name,
                "line": node.lineno,
                "end_line": getattr(node, "end_lineno", node.lineno),
                "args": [arg.arg for arg in node.args.args],
                "async": True,
                "class": self.current_class,
                "decorators": [self._get_decorator_name(d) for d in node.decorator_list],
            }
            self.functions.append(func_info)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        """Handle class definitions"""
        if self._should_include(node.name):
            old_class = self.current_class
            self.current_class = node.name

            class_info = {
                "name": node.name,
                "line": node.lineno,
                "end_line": getattr(node, "end_lineno", node.lineno),
                "bases": [self._get_base_name(base) for base in node.bases],
                "decorators": [self._get_decorator_name(d) for d in node.decorator_list],
            }
            self.classes.append(class_info)

            # Visit class body
            self.current_depth += 1
            if self.current_depth <= self.max_depth:
                self.generic_visit(node)
            self.current_depth -= 1

            self.current_class = old_class
        else:
            self.generic_visit(node)

    def _should_include(self, name: str) -> bool:
        """Check if item should be included in analysis"""
        if not self.include_private and name.startswith("_"):
            return False
        return True

    def _get_decorator_name(self, decorator) -> str:
        """Extract decorator name"""
        try:
            if isinstance(decorator, ast.Name):
                return decorator.id
            elif isinstance(decorator, ast.Attribute) and isinstance(decorator.value, ast.Name):
                return f"{decorator.value.id}.{decorator.attr}"
            elif isinstance(decorator, ast.Call):
                return self._get_decorator_name(decorator.func)
            return str(decorator)
        except AttributeError:
            return str(decorator)

    def _get_base_name(self, base) -> str:
        """Extract base class name"""
        try:
            if isinstance(base, ast.Name):
                return base.id
            elif isinstance(base, ast.Attribute) and isinstance(base.value, ast.Name):
                return f"{base.value.id}.{base.attr}"
            return str(base)
        except AttributeError:
            return str(base)

    def get_imports(self) -> List[Dict[str, Any]]:
        """Get import statements"""
        return self.imports

    def get_functions(self) -> List[Dict[str, Any]]:
        """Get function definitions"""
        return self.functions

    def get_classes(self) -> List[Dict[str, Any]]:
        """Get class definitions"""
        return self.classes

    def get_dependencies(self) -> List[str]:
        """Get external dependencies"""
        return sorted(list(self.dependencies))

    def get_structure(self) -> Dict[str, Any]:
        """Get overall code structure"""
        return {
            "total_imports": len(self.imports),
            "total_functions": len(self.functions),
            "total_classes": len(self.classes),
            "total_dependencies": len(self.dependencies),
            "functions": self.functions,
            "classes": self.classes,
            "imports": self.imports,
        }


class JavaScriptAnalyzer:
    """Regex-based JavaScript/TypeScript analyzer"""

    def __init__(self, include_private: bool, max_depth: int):
        self.include_private = include_private
        self.max_depth = max_depth

    def analyze(self, content: str, analysis_type: str) -> Dict[str, Any]:
        """Analyze JavaScript/TypeScript code"""
        results = {}

        if analysis_type in ["imports", "all"]:
            results["imports"] = self._extract_imports(content)

        if analysis_type in ["functions", "all"]:
            results["functions"] = self._extract_functions(content)

        if analysis_type in ["classes", "all"]:
            results["classes"] = self._extract_classes(content)

        if analysis_type in ["structure", "all"]:
            results["structure"] = {
                "total_imports": len(results.get("imports", [])),
                "total_functions": len(results.get("functions", [])),
                "total_classes": len(results.get("classes", [])),
            }

        return results

    def _extract_imports(self, content: str) -> List[Dict[str, Any]]:
        """Extract import statements"""
        imports = []

        # ES6 imports - handle different formats
        # import defaultExport from 'module'
        default_import_pattern = r'import\s+(\w+)\s+from\s+[\'"]([^\'"]+)[\'"];?'
        for match in re.finditer(default_import_pattern, content, re.MULTILINE):
            imports.append(
                {
                    "name": match.group(1),
                    "module": match.group(2),
                    "type": "es6_import",
                    "line": content[: match.start()].count("\n") + 1,
                }
            )

        # import { namedExport } from 'module'
        named_import_pattern = r'import\s*{\s*([^}]+)\s*}\s*from\s+[\'"]([^\'"]+)[\'"];?'
        for match in re.finditer(named_import_pattern, content, re.MULTILINE):
            names = [name.strip().split(" as ")[0] for name in match.group(1).split(",")]
            for name in names:
                if name:
                    imports.append(
                        {
                            "name": name,
                            "module": match.group(2),
                            "type": "es6_import",
                            "line": content[: match.start()].count("\n") + 1,
                        }
                    )

        # import * as alias from 'module'
        star_import_pattern = r'import\s*\*\s+as\s+(\w+)\s+from\s+[\'"]([^\'"]+)[\'"];?'
        for match in re.finditer(star_import_pattern, content, re.MULTILINE):
            imports.append(
                {
                    "name": match.group(1),
                    "module": match.group(2),
                    "type": "es6_import",
                    "line": content[: match.start()].count("\n") + 1,
                }
            )

        # CommonJS requires
        require_pattern = r'(?:const|let|var)\s+(\w+)\s*=\s*require\([\'"]([^\'"]+)[\'"]\);?'
        for match in re.finditer(require_pattern, content, re.MULTILINE):
            imports.append(
                {
                    "name": match.group(1),
                    "module": match.group(2),
                    "type": "commonjs_require",
                    "line": content[: match.start()].count("\n") + 1,
                }
            )

        return imports

    def _extract_functions(self, content: str) -> List[Dict[str, Any]]:
        """Extract function definitions"""
        functions = []

        # Function declarations
        func_pattern = r"(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)\s*=>|function))"
        for match in re.finditer(func_pattern, content, re.MULTILINE):
            name = match.group(1) or match.group(2)
            if name and (self.include_private or not name.startswith("_")):
                functions.append(
                    {
                        "name": name,
                        "type": "function",
                        "line": content[: match.start()].count("\n") + 1,
                    }
                )

        return functions

    def _extract_classes(self, content: str) -> List[Dict[str, Any]]:
        """Extract class definitions"""
        classes = []

        # Class declarations
        class_pattern = r"class\s+(\w+)(?:\s+extends\s+(\w+))?"
        for match in re.finditer(class_pattern, content, re.MULTILINE):
            name = match.group(1)
            if self.include_private or not name.startswith("_"):
                classes.append(
                    {
                        "name": name,
                        "extends": match.group(2),
                        "line": content[: match.start()].count("\n") + 1,
                    }
                )

        return classes
