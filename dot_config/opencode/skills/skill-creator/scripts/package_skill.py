# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Skill Packager - Creates a distributable zip file of a skill folder.

Usage: uv run package_skill.py <path/to/skill-folder> [output-directory]
Output: Zip file of the skill

Example:
    uv run package_skill.py ~/.config/opencode/skills/my-skill
    uv run package_skill.py ./my-skill ./dist
"""

import sys
import zipfile
from pathlib import Path

# Import validate function - must be run from scripts directory or with proper path
sys.path.insert(0, str(Path(__file__).parent))
from quick_validate import validate_skill


def package_skill(skill_path_str: str, output_dir: str | None = None) -> Path | None:
    """
    Package a skill folder into a zip file.

    Args:
        skill_path_str: Path to the skill folder
        output_dir: Optional output directory for the zip file

    Returns:
        Path to the created zip file, or None if error
    """
    skill_path = Path(skill_path_str).resolve()

    if not skill_path.exists():
        print(f"❌ Error: Skill folder not found: {skill_path}")
        return None

    if not skill_path.is_dir():
        print(f"❌ Error: Path is not a directory: {skill_path}")
        return None

    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        print(f"❌ Error: SKILL.md not found in {skill_path}")
        return None

    # Run validation before packaging
    print("🔍 Validating skill...")
    valid, message = validate_skill(skill_path)
    if not valid:
        print(f"❌ Validation failed: {message}")
        print("   Please fix the validation errors before packaging.")
        return None
    print(f"✅ {message}\n")

    # Determine output location
    skill_name = skill_path.name
    if output_dir:
        output_path = Path(output_dir).resolve()
        output_path.mkdir(parents=True, exist_ok=True)
    else:
        output_path = Path.cwd()

    zip_filename = output_path / f"{skill_name}.zip"

    # Create the zip file
    try:
        with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in skill_path.rglob("*"):
                # Skip __pycache__ directories
                if "__pycache__" in file_path.parts:
                    continue
                if file_path.is_file():
                    arcname = file_path.relative_to(skill_path.parent)
                    zipf.write(file_path, arcname)
                    print(f"  Added: {arcname}")

        print(f"\n✅ Successfully packaged skill to: {zip_filename}")
        return zip_filename

    except Exception as e:
        print(f"❌ Error creating zip file: {e}")
        return None


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: uv run package_skill.py <path/to/skill-folder> [output-directory]"
        )
        print("\nExample:")
        print("  uv run package_skill.py ~/.config/opencode/skills/my-skill")
        print("  uv run package_skill.py ./my-skill ./dist")
        sys.exit(1)

    skill_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"📦 Packaging skill: {skill_path}")
    if output_dir:
        print(f"   Output directory: {output_dir}")
    print()

    result = package_skill(skill_path, output_dir)
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
