"""
Pattern Documentation - Automatic pattern documentation generation
Phase 3.4.6: Generate comprehensive documentation for learned patterns
"""

import json
import time
import markdown
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from pathlib import Path
import re
from datetime import datetime
import uuid


@dataclass
class PatternDocumentation:
    """Documentation for a code pattern."""
    pattern_id: str
    title: str
    summary: str
    category: str
    language: str

    # Content sections
    description: str = ""
    examples: List[Dict[str, Any]] = field(default_factory=list)
    when_to_use: List[str] = field(default_factory=list)
    when_not_to_use: List[str] = field(default_factory=list)
    benefits: List[str] = field(default_factory=list)
    drawbacks: List[str] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)

    # Technical details
    complexity: str = "Low"  # Low, Medium, High
    performance_impact: str = "Neutral"  # Positive, Neutral, Negative
    maintainability_impact: str = "Positive"  # Positive, Neutral, Negative

    # Metadata
    author: str = "Isaac AI Assistant"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)

    # Usage statistics
    usage_count: int = 0
    success_rate: float = 0.0
    average_rating: float = 0.0

    # Related patterns
    related_patterns: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)


@dataclass
class DocumentationTemplate:
    """Template for generating pattern documentation."""
    name: str
    category: str
    template: str  # Markdown template with placeholders
    sections: List[str] = field(default_factory=list)


class PatternDocumentationGenerator:
    """Generates comprehensive documentation for code patterns."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the documentation generator."""
        self.config = config or {}
        self.templates: Dict[str, DocumentationTemplate] = {}
        self.documentation: Dict[str, PatternDocumentation] = {}

        # Storage paths
        self.data_dir = Path.home() / '.isaac' / 'pattern_docs'
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Load templates and existing documentation
        self._load_builtin_templates()
        self._load_documentation()

        # Documentation settings
        self.output_format = self.config.get('output_format', 'markdown')
        self.include_examples = self.config.get('include_examples', True)
        self.include_statistics = self.config.get('include_statistics', True)

    def generate_documentation(self, pattern_data: Dict[str, Any],
                             usage_stats: Optional[Dict[str, Any]] = None) -> PatternDocumentation:
        """Generate documentation for a pattern."""
        pattern_id = pattern_data.get('id', str(uuid.uuid4()))

        # Determine template
        category = pattern_data.get('category', 'general')
        template = self._get_template_for_category(category)

        # Extract pattern information
        doc_data = self._extract_pattern_info(pattern_data)

        # Add usage statistics if available
        if usage_stats:
            doc_data.update(self._extract_usage_stats(usage_stats))

        # Generate content sections
        content_sections = self._generate_content_sections(pattern_data, template)

        # Filter to only include valid PatternDocumentation fields
        valid_fields = {
            'title', 'summary', 'category', 'language', 'description', 'examples',
            'when_to_use', 'when_not_to_use', 'benefits', 'drawbacks', 'alternatives',
            'complexity', 'performance_impact', 'maintainability_impact', 'author',
            'version', 'tags', 'usage_count', 'success_rate', 'average_rating'
        }

        filtered_doc_data = {k: v for k, v in doc_data.items() if k in valid_fields}
        filtered_doc_data.update({k: v for k, v in content_sections.items() if k in valid_fields})

        # Create documentation object
        documentation = PatternDocumentation(
            pattern_id=pattern_id,
            **filtered_doc_data
        )

        # Store documentation
        self.documentation[pattern_id] = documentation
        self._save_documentation()

        return documentation

    def update_documentation(self, pattern_id: str, updates: Dict[str, Any]) -> bool:
        """Update existing pattern documentation."""
        if pattern_id not in self.documentation:
            return False

        doc = self.documentation[pattern_id]

        # Update fields
        for key, value in updates.items():
            if hasattr(doc, key):
                setattr(doc, key, value)

        doc.updated_at = time.time()
        self._save_documentation()
        return True

    def generate_markdown(self, pattern_id: str) -> str:
        """Generate markdown documentation for a pattern."""
        if pattern_id not in self.documentation:
            return f"# Pattern Not Found\n\nPattern '{pattern_id}' documentation not found."

        doc = self.documentation[pattern_id]
        template = self._get_template_for_category(doc.category)

        # Fill template
        content = self._fill_template(template.template, doc)

        return content

    def generate_html(self, pattern_id: str) -> str:
        """Generate HTML documentation for a pattern."""
        markdown_content = self.generate_markdown(pattern_id)
        html_content = markdown.markdown(markdown_content, extensions=['tables', 'fenced_code'])

        # Add basic styling
        styled_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{self.documentation[pattern_id].title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #2c3e50; }}
                h2 {{ color: #34495e; }}
                code {{ background: #f8f9fa; padding: 2px 4px; border-radius: 3px; }}
                pre {{ background: #f8f9fa; padding: 10px; border-radius: 5px; overflow-x: auto; }}
                .metadata {{ background: #ecf0f1; padding: 10px; border-radius: 5px; margin: 20px 0; }}
                .stats {{ background: #d5dbdb; padding: 10px; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """

        return styled_html

    def generate_index(self, category: Optional[str] = None) -> str:
        """Generate an index of all documented patterns."""
        patterns = list(self.documentation.values())

        if category:
            patterns = [p for p in patterns if p.category == category]

        # Sort by category, then by title
        patterns.sort(key=lambda p: (p.category, p.title))

        # Group by category
        categories = {}
        for pattern in patterns:
            if pattern.category not in categories:
                categories[pattern.category] = []
            categories[pattern.category].append(pattern)

        # Generate markdown index
        lines = ["# Pattern Documentation Index\n", f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"]

        if category:
            lines.append(f"## {category.title()} Patterns\n")
        else:
            lines.append("## All Patterns\n")

        for cat_name, cat_patterns in categories.items():
            lines.append(f"### {cat_name.title()}\n")

            for pattern in cat_patterns:
                usage_indicator = f" (Used {pattern.usage_count} times)" if pattern.usage_count > 0 else ""
                lines.append(f"- [**{pattern.title}**]({pattern.pattern_id}.md) - {pattern.summary}{usage_indicator}")

            lines.append("")

        # Add statistics
        total_patterns = len(patterns)
        total_usage = sum(p.usage_count for p in patterns)
        avg_success = sum(p.success_rate for p in patterns) / max(1, total_patterns)

        lines.extend([
            "## Statistics\n",
            f"- Total Patterns: {total_patterns}",
            f"- Total Usage: {total_usage}",
            f"- Average Success Rate: {avg_success:.1%}",
            f"- Categories: {len(categories)}"
        ])

        return "\n".join(lines)

    def export_documentation(self, output_dir: str, format: str = 'markdown') -> int:
        """Export all documentation to files."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        exported_count = 0

        # Export individual pattern docs
        for pattern_id, doc in self.documentation.items():
            if format == 'markdown':
                content = self.generate_markdown(pattern_id)
                filename = f"{pattern_id}.md"
            elif format == 'html':
                content = self.generate_html(pattern_id)
                filename = f"{pattern_id}.html"
            else:
                continue

            file_path = output_path / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            exported_count += 1

        # Export index
        index_content = self.generate_index()
        index_path = output_path / "index.md"
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)

        return exported_count

    def search_documentation(self, query: str) -> List[PatternDocumentation]:
        """Search documentation by title, summary, or tags."""
        query_lower = query.lower()
        results = []

        for doc in self.documentation.values():
            if (query_lower in doc.title.lower() or
                query_lower in doc.summary.lower() or
                query_lower in doc.description.lower() or
                any(query_lower in tag.lower() for tag in doc.tags)):
                results.append(doc)

        # Sort by relevance (title matches first, then usage)
        results.sort(key=lambda d: (
            d.title.lower().find(query_lower),
            -d.usage_count
        ))

        return results

    def get_related_patterns(self, pattern_id: str) -> List[PatternDocumentation]:
        """Get patterns related to the given pattern."""
        if pattern_id not in self.documentation:
            return []

        doc = self.documentation[pattern_id]
        related = []

        for related_id in doc.related_patterns:
            if related_id in self.documentation:
                related.append(self.documentation[related_id])

        return related

    def _load_builtin_templates(self):
        """Load built-in documentation templates."""
        self.templates = {
            'function': DocumentationTemplate(
                name='Function Pattern',
                category='function',
                template="""# {title}

**Category:** {category} | **Language:** {language} | **Complexity:** {complexity}

## Summary
{summary}

## Description
{description}

## When to Use
{when_to_use}

## When Not to Use
{when_not_to_use}

## Benefits
{benefits}

## Drawbacks
{drawbacks}

## Examples
{examples}

## Alternatives
{alternatives}

## Technical Details
- **Performance Impact:** {performance_impact}
- **Maintainability Impact:** {maintainability_impact}
- **Prerequisites:** {prerequisites}

## Usage Statistics
{statistics}

## Related Patterns
{related_patterns}

---
**Author:** {author} | **Version:** {version} | **Updated:** {updated_date}
**Tags:** {tags_str}
""",
                sections=['summary', 'description', 'examples', 'when_to_use', 'benefits', 'alternatives']
            ),

            'class': DocumentationTemplate(
                name='Class Pattern',
                category='class',
                template="""# {title}

**Category:** {category} | **Language:** {language} | **Complexity:** {complexity}

## Summary
{summary}

## Description
{description}

## Structure
{class_structure}

## When to Use
{when_to_use}

## When Not to Use
{when_not_to_use}

## Benefits
{benefits}

## Drawbacks
{drawbacks}

## Examples
{examples}

## Inheritance and Composition
{inheritance_notes}

## Technical Details
- **Performance Impact:** {performance_impact}
- **Maintainability Impact:** {maintainability_impact}

## Usage Statistics
{statistics}

## Related Patterns
{related_patterns}

---
**Author:** {author} | **Version:** {version} | **Updated:** {updated_date}
**Tags:** {tags_str}
""",
                sections=['summary', 'description', 'structure', 'examples', 'inheritance']
            ),

            'general': DocumentationTemplate(
                name='General Pattern',
                category='general',
                template="""# {title}

**Category:** {category} | **Language:** {language} | **Complexity:** {complexity}

## Summary
{summary}

## Description
{description}

## When to Use
{when_to_use}

## Benefits
{benefits}

## Examples
{examples}

## Technical Details
- **Performance Impact:** {performance_impact}
- **Maintainability Impact:** {maintainability_impact}

## Usage Statistics
{statistics}

## Related Patterns
{related_patterns}

---
**Author:** {author} | **Version:** {version} | **Updated:** {updated_date}
**Tags:** {tags_str}
""",
                sections=['summary', 'description', 'examples']
            )
        }

    def _load_documentation(self):
        """Load existing documentation from disk."""
        docs_file = self.data_dir / 'documentation.json'
        try:
            if docs_file.exists():
                with open(docs_file, 'r', encoding='utf-8') as f:
                    docs_data = json.load(f)
                    for pattern_id, doc_data in docs_data.items():
                        self.documentation[pattern_id] = PatternDocumentation(**doc_data)
        except Exception as e:
            print(f"Error loading documentation: {e}")

    def _save_documentation(self):
        """Save documentation to disk."""
        docs_file = self.data_dir / 'documentation.json'
        try:
            docs_data = {pid: asdict(doc) for pid, doc in self.documentation.items()}
            with open(docs_file, 'w', encoding='utf-8') as f:
                json.dump(docs_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving documentation: {e}")

    def _get_template_for_category(self, category: str) -> DocumentationTemplate:
        """Get the appropriate template for a category."""
        return self.templates.get(category, self.templates['general'])

    def _extract_pattern_info(self, pattern_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract basic pattern information."""
        return {
            'title': pattern_data.get('name', 'Unnamed Pattern'),
            'summary': pattern_data.get('description', 'No description available'),
            'category': pattern_data.get('category', 'general'),
            'language': pattern_data.get('language', 'python'),
            'description': pattern_data.get('description', ''),
            'examples': pattern_data.get('examples', []),
            'tags': pattern_data.get('tags', [])
        }

    def _extract_usage_stats(self, usage_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Extract usage statistics."""
        return {
            'usage_count': usage_stats.get('total_uses', 0),
            'success_rate': usage_stats.get('success_rate', 0.0),
            'average_rating': usage_stats.get('average_rating', 0.0)
        }

    def _generate_content_sections(self, pattern_data: Dict[str, Any],
                                 template: DocumentationTemplate) -> Dict[str, Any]:
        """Generate content sections based on pattern data."""
        sections = {}

        # Generate examples section
        if self.include_examples and 'examples' in pattern_data:
            examples_md = self._format_examples(pattern_data['examples'])
            sections['examples'] = examples_md

        # Generate when to use section
        sections['when_to_use'] = self._generate_when_to_use(pattern_data)

        # Generate benefits section
        sections['benefits'] = self._generate_benefits(pattern_data)

        # Generate alternatives section
        sections['alternatives'] = self._generate_alternatives(pattern_data)

        # Generate statistics section
        if self.include_statistics:
            sections['statistics'] = self._generate_statistics(pattern_data)

        # Generate related patterns section
        sections['related_patterns'] = self._generate_related_patterns(pattern_data)

        return sections

    def _format_examples(self, examples: List[str]) -> str:
        """Format examples as markdown code blocks."""
        if not examples:
            return "*No examples available*"

        formatted = []
        for i, example in enumerate(examples, 1):
            formatted.append(f"### Example {i}\n```python\n{example}\n```")

        return "\n\n".join(formatted)

    def _generate_when_to_use(self, pattern_data: Dict[str, Any]) -> str:
        """Generate when to use section."""
        category = pattern_data.get('category', 'general')

        suggestions = {
            'function': [
                "When you need to perform a specific operation multiple times",
                "When the operation is complex enough to warrant separation",
                "When you want to improve code readability and maintainability"
            ],
            'class': [
                "When you have related data and behavior that should be encapsulated",
                "When you need to create multiple instances with similar behavior",
                "When inheritance or composition would be beneficial"
            ],
            'loop': [
                "When you need to iterate over a collection of items",
                "When you need to perform an operation a specific number of times",
                "When list comprehensions would make the code less readable"
            ],
            'error_handling': [
                "When operations might fail and you need to handle errors gracefully",
                "When you need to provide meaningful error messages to users",
                "When cleanup is required regardless of success or failure"
            ]
        }

        default_suggestions = [
            "When the pattern improves code organization",
            "When the pattern makes the code more maintainable",
            "When the pattern is well-established in the codebase"
        ]

        use_cases = suggestions.get(category, default_suggestions)

        return "\n".join(f"- {case}" for case in use_cases)

    def _generate_benefits(self, pattern_data: Dict[str, Any]) -> str:
        """Generate benefits section."""
        category = pattern_data.get('category', 'general')

        benefits = {
            'function': [
                "Improves code reusability",
                "Makes code more modular and testable",
                "Reduces code duplication",
                "Enhances code readability"
            ],
            'class': [
                "Encapsulates related data and behavior",
                "Supports inheritance and polymorphism",
                "Improves code organization",
                "Enables better testing through mocking"
            ],
            'error_handling': [
                "Provides graceful error recovery",
                "Improves user experience with meaningful messages",
                "Prevents application crashes",
                "Enables proper resource cleanup"
            ]
        }

        default_benefits = [
            "Improves code maintainability",
            "Enhances code readability",
            "Reduces potential for bugs",
            "Makes code more reusable"
        ]

        pattern_benefits = benefits.get(category, default_benefits)

        return "\n".join(f"- {benefit}" for benefit in pattern_benefits)

    def _generate_alternatives(self, pattern_data: Dict[str, Any]) -> str:
        """Generate alternatives section."""
        category = pattern_data.get('category', 'general')

        alternatives = {
            'function': [
                "Inline code (for simple operations)",
                "Lambda functions (for simple transformations)",
                "Methods within classes (for object-specific operations)"
            ],
            'class': [
                "Modules with functions (for stateless operations)",
                "Named tuples or data classes (for simple data structures)",
                "Functions with closures (for encapsulation without classes)"
            ],
            'loop': [
                "List comprehensions (for simple transformations)",
                "Built-in functions like map/filter (for functional style)",
                "Generator expressions (for memory-efficient iteration)"
            ]
        }

        default_alternatives = [
            "Inline implementation",
            "Different design patterns",
            "Built-in language features"
        ]

        pattern_alternatives = alternatives.get(category, default_alternatives)

        return "\n".join(f"- {alt}" for alt in pattern_alternatives)

    def _generate_statistics(self, pattern_data: Dict[str, Any]) -> str:
        """Generate usage statistics section."""
        usage_count = pattern_data.get('usage_count', 0)
        success_rate = pattern_data.get('success_rate', 0.0)
        rating = pattern_data.get('average_rating', 0.0)

        if usage_count == 0:
            return "*No usage statistics available*"

        stats = [
            f"- **Total Usage:** {usage_count} times",
            f"- **Success Rate:** {success_rate:.1%}",
        ]

        if rating > 0:
            stats.append(f"- **Average Rating:** {rating:.1f}/5.0")

        return "\n".join(stats)

    def _generate_related_patterns(self, pattern_data: Dict[str, Any]) -> str:
        """Generate related patterns section."""
        related = pattern_data.get('related_patterns', [])

        if not related:
            return "*No related patterns identified*"

        related_docs = []
        for pattern_id in related:
            if pattern_id in self.documentation:
                doc = self.documentation[pattern_id]
                related_docs.append(f"- [{doc.title}]({pattern_id}.md) - {doc.summary}")

        if not related_docs:
            return "*No related pattern documentation available*"

        return "\n".join(related_docs)

    def _fill_template(self, template: str, doc: PatternDocumentation) -> str:
        """Fill template with documentation data."""
        # Prepare template variables
        template_vars = {
            'title': doc.title,
            'summary': doc.summary,
            'category': doc.category.title(),
            'language': doc.language.title(),
            'complexity': doc.complexity,
            'description': doc.description or "*No detailed description available*",
            'performance_impact': doc.performance_impact,
            'maintainability_impact': doc.maintainability_impact,
            'author': doc.author,
            'version': doc.version,
            'updated_date': datetime.fromtimestamp(doc.updated_at).strftime('%Y-%m-%d'),
            'tags_str': ', '.join(doc.tags) if doc.tags else 'None',
            'prerequisites': '\n'.join(f"- {p}" for p in doc.prerequisites) if doc.prerequisites else "*None*"
        }

        # Add list sections
        list_sections = {
            'when_to_use': doc.when_to_use,
            'when_not_to_use': doc.when_not_to_use,
            'benefits': doc.benefits,
            'drawbacks': doc.drawbacks,
            'alternatives': doc.alternatives,
            'related_patterns': [f"- {p}" for p in doc.related_patterns]
        }

        for section_name, items in list_sections.items():
            if items:
                template_vars[section_name] = '\n'.join(f"- {item}" for item in items)
            else:
                template_vars[section_name] = "*None specified*"

        # Add special sections
        template_vars['examples'] = self._format_examples(doc.examples) if doc.examples else "*No examples available*"
        template_vars['statistics'] = self._generate_statistics(asdict(doc))

        # Fill template
        filled_template = template
        for key, value in template_vars.items():
            filled_template = filled_template.replace(f"{{{key}}}", str(value))

        return filled_template