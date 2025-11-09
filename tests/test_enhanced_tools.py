# tests/test_enhanced_tools.py
"""
Test Suite for Enhanced File Operations & Code Analysis Tools (Phase 3)

Tests the new intelligent file tools: ReadTool, SearchReplaceTool, CodeAnalysisTool
"""

import pytest
import tempfile
import os
from pathlib import Path
from isaac.tools.file_ops import ReadTool, SearchReplaceTool
from isaac.tools.code_analysis import CodeAnalysisTool


class TestReadTool:
    """Test enhanced ReadTool with intelligent reading features"""

    def test_read_with_focus_lines(self):
        """Test reading with focus line ranges"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''line 1
line 2
line 3
line 4
line 5
''')
            temp_path = f.name

        try:
            tool = ReadTool()
            result = tool.execute(file_path=temp_path, focus_lines=[2, 3, 4], context_lines=0)

            assert result['success'] is True
            assert 'line 2' in result['content']
            assert 'line 4' in result['content']
            assert 'line 1' not in result['content']
            assert 'line 5' not in result['content']
        finally:
            os.unlink(temp_path)

    def test_read_with_context_lines(self):
        """Test reading with context around focus lines"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''line 1
line 2
line 3
line 4
line 5
''')
            temp_path = f.name

        try:
            tool = ReadTool()
            result = tool.execute(file_path=temp_path, focus_lines=[3], context_lines=1)

            assert result['success'] is True
            assert 'line 2' in result['content']
            assert 'line 3' in result['content']
            assert 'line 4' in result['content']
            assert 'line 1' not in result['content']
            assert 'line 5' not in result['content']
        finally:
            os.unlink(temp_path)


class TestSearchReplaceTool:
    """Test SearchReplaceTool with regex and safety features"""

    def test_simple_search_replace(self):
        """Test basic search and replace"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('Hello world\nHello universe\n')
            temp_path = f.name

        try:
            tool = SearchReplaceTool()
            result = tool.execute(
                file_path=temp_path,
                pattern='Hello',
                replacement='Hi',
                replace_all=True,
                preview=False
            )

            assert result['success'] is True
            assert result['replacements'] == 2

            # Verify file content
            with open(temp_path, 'r') as f:
                content = f.read()
                assert content == 'Hi world\nHi universe\n'
        finally:
            os.unlink(temp_path)

    def test_regex_search_replace(self):
        """Test regex search and replace"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('test123\ntest456\nother\n')
            temp_path = f.name

        try:
            tool = SearchReplaceTool()
            result = tool.execute(
                file_path=temp_path,
                pattern=r'test\d+',
                replacement='replaced',
                regex=True,
                replace_all=True,
                preview=False
            )

            assert result['success'] is True
            assert result['replacements'] == 2

            # Verify file content
            with open(temp_path, 'r') as f:
                content = f.read()
                assert content == 'replaced\nreplaced\nother\n'
        finally:
            os.unlink(temp_path)

    def test_preview_mode(self):
        """Test preview mode doesn't modify file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('Hello world\nHello universe\n')
            temp_path = f.name

        original_content = 'Hello world\nHello universe\n'

        try:
            tool = SearchReplaceTool()
            result = tool.execute(
                file_path=temp_path,
                pattern='Hello',
                replacement='Hi',
                replace_all=True,
                preview=True
            )

            assert result['success'] is True
            assert result['total_matches'] == 2
            assert 'preview' in result

            # Verify file unchanged
            with open(temp_path, 'r') as f:
                content = f.read()
                assert content == original_content
        finally:
            os.unlink(temp_path)


class TestCodeAnalysisTool:
    """Test CodeAnalysisTool for code structure analysis"""

    def test_python_analysis(self):
        """Test Python code analysis"""
        python_code = '''import os
from pathlib import Path

class MyClass:
    def my_method(self):
        return "hello"

def standalone_function():
    pass
'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(python_code)
            temp_path = f.name

        try:
            tool = CodeAnalysisTool()
            result = tool.execute(file_path=temp_path)

            assert result['success'] is True
            assert result['language'] == 'python'

            # Check imports
            imports = result['imports']
            assert len(imports) >= 1  # Should find at least os import

            # Check classes
            classes = result['classes']
            assert len(classes) == 1
            assert classes[0]['name'] == 'MyClass'

            # Check functions
            functions = result['functions']
            assert len(functions) >= 1  # Should find at least standalone_function

        finally:
            os.unlink(temp_path)

    def test_javascript_analysis(self):
        """Test JavaScript code analysis"""
        js_code = '''import React from 'react';
import { useState } from 'react';

function MyComponent() {
    const [count, setCount] = useState(0);
    return <div>Hello</div>;
}

class ApiService {
    fetchData() {
        return fetch('/api/data');
    }
}

export default MyComponent;
'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(js_code)
            temp_path = f.name

        try:
            tool = CodeAnalysisTool()
            result = tool.execute(file_path=temp_path)

            assert result['success'] is True
            assert result['language'] == 'javascript'

            # Check classes
            classes = result['classes']
            assert len(classes) >= 1  # Should find ApiService

            # Check functions
            functions = result['functions']
            assert len(functions) >= 1  # Should find MyComponent

        finally:
            os.unlink(temp_path)