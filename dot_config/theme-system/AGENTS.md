# Agent Guidelines for theme-system

## Build/Test Commands
- **Run main script**: `./theme-manager.py <command>` or `uv run theme-manager.py <command>`
- **Test theme change**: `./theme-manager.py set mocha`
- **Check status**: `./theme-manager.py status`
- **No automated tests configured** - manually test theme changes across applications

## Code Style

### Python (theme-manager.py)
- **Python version**: >=3.11 with `uv` package manager
- **Dependencies**: click, pyyaml, jinja2
- **Types**: Use type hints (`Dict`, `Optional`, `List`, `Path`)
- **Naming**: PascalCase for classes, snake_case for functions/variables
- **Strings**: Double quotes preferred
- **Indentation**: 4 spaces
- **Imports**: Standard library first, then third-party, then click
- **Paths**: Use `pathlib.Path` objects, not strings
- **Docstrings**: Use triple-quoted strings for function documentation
- **Error handling**: Use click.echo() for user feedback with emoji (✅ ❌ ⚠️  🎨)

### Bash Scripts (scripts/)
- **Variables**: ALL_CAPS for constants, lowercase_with_underscores for locals
- **Quoting**: Always quote variables: `"$VARIABLE"`
- **Error handling**: Check command success with `if ! command; then`
- **User feedback**: Use echo with emoji for status messages
- **Functions**: lowercase_with_underscores naming

### Configuration Files
- **YAML**: Use snake_case keys, 2-space indentation (config.yaml)
- **JSON**: Follows Catppuccin theme structure with "colors" and "semantic" sections
- **State files**: Plain text in `state/` directory (current-theme.txt, etc.)