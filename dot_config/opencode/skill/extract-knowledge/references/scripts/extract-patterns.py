# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
Utility script for knowledge extraction operations.

Usage:
  uv run extract-patterns.py analyze <path> [--type TYPE]
  uv run extract-patterns.py save <name> <output_path>
  uv run extract-patterns.py validate <knowledge_path>

Commands:
  analyze     Analyze files and output pattern summary
  save        Save knowledge document to specified path
  validate    Validate knowledge document structure

Output: Pattern analysis, saved documents, or validation results
"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime


def analyze_file(file_path: Path) -> dict:
    """Analyze a single file for patterns."""
    if not file_path.exists():
        return {"error": f"File not found: {file_path}"}

    content = file_path.read_text()

    analysis = {
        "path": str(file_path),
        "size": len(content),
        "lines": content.count("\n") + 1,
        "patterns": [],
    }

    # Detect file type and apply relevant analysis
    suffix = file_path.suffix.lower()

    if suffix in [".xml"]:
        # XML patterns
        tags = re.findall(r"<(\w+)[^>]*>", content)
        tag_counts = {}
        for tag in tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        analysis["patterns"].append({"type": "xml_structure", "tags": tag_counts})

    elif suffix in [".yaml", ".yml"]:
        # YAML patterns
        keys = re.findall(r"^(\w+):", content, re.MULTILINE)
        analysis["patterns"].append(
            {"type": "yaml_structure", "top_level_keys": list(set(keys))}
        )

    elif suffix in [".md"]:
        # Markdown patterns
        headers = re.findall(r"^(#{1,6})\s+(.+)$", content, re.MULTILINE)
        analysis["patterns"].append(
            {
                "type": "markdown_structure",
                "headers": [{"level": len(h[0]), "text": h[1]} for h in headers],
            }
        )

    elif suffix in [".py"]:
        # Python patterns
        functions = re.findall(r"^def\s+(\w+)\s*\(", content, re.MULTILINE)
        classes = re.findall(r"^class\s+(\w+)\s*[:\(]", content, re.MULTILINE)
        analysis["patterns"].append(
            {"type": "python_structure", "functions": functions, "classes": classes}
        )

    # Common patterns across all files

    # Naming conventions
    snake_case = len(re.findall(r"\b[a-z]+_[a-z_]+\b", content))
    camel_case = len(re.findall(r"\b[a-z]+[A-Z][a-zA-Z]*\b", content))
    kebab_case = len(re.findall(r"\b[a-z]+-[a-z-]+\b", content))

    if snake_case or camel_case or kebab_case:
        analysis["patterns"].append(
            {
                "type": "naming_convention",
                "snake_case_count": snake_case,
                "camel_case_count": camel_case,
                "kebab_case_count": kebab_case,
            }
        )

    # Emphasis keywords
    keywords = {
        "CRITICAL": len(re.findall(r"\bCRITICAL\b", content)),
        "MUST": len(re.findall(r"\bMUST\b", content)),
        "NEVER": len(re.findall(r"\bNEVER\b", content)),
        "ALWAYS": len(re.findall(r"\bALWAYS\b", content)),
        "TODO": len(re.findall(r"\bTODO\b", content)),
    }
    if any(keywords.values()):
        analysis["patterns"].append({"type": "emphasis_keywords", "counts": keywords})

    return analysis


def analyze_directory(
    dir_path: Path, file_types: list[str] | None = None
) -> list[dict]:
    """Analyze all files in a directory."""
    results = []

    if not dir_path.exists():
        return [{"error": f"Directory not found: {dir_path}"}]

    # Default file types if not specified
    if file_types is None:
        file_types = [".xml", ".yaml", ".yml", ".md", ".py"]

    for file_path in dir_path.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in file_types:
            results.append(analyze_file(file_path))

    return results


def save_knowledge(name: str, output_path: str, content: str | None = None) -> None:
    """Save knowledge document to specified path."""
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    knowledge_file = output_dir / "knowledge.md"

    if content:
        knowledge_file.write_text(content)
    else:
        # Create template if no content provided
        template = f"""# {name}

## Overview
[Description of what this knowledge covers]

## When to Use
[Situations where this knowledge applies]

## Patterns

### Pattern 1
**Problem:** [What situation triggers this]
**Solution:** [How to address it]
**Example:**
```
[Concrete example]
```
**Rationale:** [Why this works]

## Anti-Patterns

### Anti-Pattern 1
**What it looks like:** [Description of the mistake]
**Why it's wrong:** [Problems it causes]
**Instead:** [What to do instead]

## References
- Source: [Original source material]
- Created: {datetime.now().strftime("%Y-%m-%d")}
"""
        knowledge_file.write_text(template)

    print(f"Created: {knowledge_file}")


def validate_knowledge(knowledge_path: Path) -> list[str]:
    """Validate knowledge document structure."""
    errors = []

    if not knowledge_path.exists():
        errors.append(f"File not found: {knowledge_path}")
        return errors

    content = knowledge_path.read_text()

    # Check for required sections
    required_sections = ["## Overview", "## When to Use"]
    for section in required_sections:
        if section not in content:
            errors.append(f"Missing required section: {section}")

    # Check for at least one pattern or convention
    has_pattern = "### Pattern" in content or "### Convention" in content
    has_template = "### Template" in content
    has_guideline = "### Guideline" in content

    if not (has_pattern or has_template or has_guideline):
        errors.append("No patterns, templates, or guidelines found")

    # Check for examples
    if "```" not in content:
        errors.append("No code examples found (missing ``` blocks)")

    # Check for empty sections (just header, no content)
    lines = content.split("\n")
    for i, line in enumerate(lines[:-1]):
        if line.startswith("##") and lines[i + 1].startswith("#"):
            errors.append(f"Empty section: {line}")

    return errors


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == "analyze":
        if len(sys.argv) < 3:
            print("Usage: uv run extract-patterns.py analyze <path>")
            sys.exit(1)

        path = Path(sys.argv[2])

        if path.is_file():
            result = analyze_file(path)
        else:
            result = analyze_directory(path)

        print(json.dumps(result, indent=2))

    elif command == "save":
        if len(sys.argv) < 4:
            print("Usage: uv run extract-patterns.py save <name> <output_path>")
            sys.exit(1)

        name = sys.argv[2]
        output_path = sys.argv[3]
        save_knowledge(name, output_path)

    elif command == "validate":
        if len(sys.argv) < 3:
            print("Usage: uv run extract-patterns.py validate <knowledge_path>")
            sys.exit(1)

        knowledge_path = Path(sys.argv[2])
        errors = validate_knowledge(knowledge_path)

        if errors:
            print("Validation FAILED:")
            for e in errors:
                print(f"  - {e}")
            sys.exit(1)
        else:
            print(f"Validation PASSED: {knowledge_path}")

    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
