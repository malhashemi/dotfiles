---
description: Research app configuration for chezmoi integration including platform scope, cross-platform needs, and theming method
agent: researcher
argument-hint: "[app-name] [optional: additional-questions]"
---

## Context

You are researching how to integrate an application into the chezmoi-managed dotfiles system. This includes determining platform scope, cross-platform configuration needs, and theming integration.

The user has already added the app's config to chezmoi using `chezmoi add`, so the config files exist in the codebase under `dot_config/` or similar.

### Required Context Documents

**Multi-Platform Specification** (platform scope, decision framework, configuration matrix):
@thoughts/shared/plans/dotfiles-multi-platform-spec.md

**Theme System Architecture** (dual-track system, modular app pattern, color abstraction):
@thoughts/shared/research/2025-10-16_19-53-43_theme-system-implementation-analysis.md

**Apps Catalog** (existing app patterns, YAML schema for documentation):
@.chezmoidata/apps.yaml

## Variables

### Dynamic Variables

- ARGUMENTS = $ARGUMENTS
  argument-hint: "[app-name] [optional: additional-questions]"

APP_NAME: [app-name from first argument]
USER_QUESTIONS: [additional questions from remaining arguments, if provided]

## Instructions

You are conducting a comprehensive configuration research analysis for **{{APP_NAME}}** to determine platform scope, cross-platform needs, and optimal theming integration.

### Research Objectives

1. **Platform Scope**: Determine which platforms need {{APP_NAME}} and how config differs across them
2. **Theming Method**: Determine the best method to apply themes (static and dynamic)
3. **Implementation Spec**: Provide paste-ready code and configuration entries

**Additional Objective** (if provided):
Address the user's specific questions: "{{USER_QUESTIONS}}"

### Research Workflow

#### Phase 0: Platform Scope Assessment

**Determine where {{APP_NAME}} fits in the multi-platform dotfiles system.**

Reference the multi-platform spec's decision framework and target systems.

1. **App Classification**:
   - **Type**: Is {{APP_NAME}} a GUI app, TUI app, or CLI tool?
   - **Category**: Terminal emulator, editor, shell tool, status bar, window manager, media app, etc.

2. **Platform Availability**:
   
   | Platform | Available? | Notes |
   |----------|------------|-------|
   | macOS | ✅/❌ | |
   | Windows | ✅/❌ | |
   | Arch Linux (GUI) | ✅/❌ | |
   | Arch Linux (headless) | ✅/❌ | Relevant for CLI/TUI only |
   | Android (Termux) | ✅/❌ | |

3. **Theming Capability Per Platform**:
   - **Dynamic theming** (wallpaper-based): Which platforms support this? (Requires GUI + wallpaper)
   - **Static theming** (predefined palettes): All platforms where app is available
   - **No theming**: Headless systems where app inherits terminal colors

4. **Cross-Platform Config Considerations**:
   - Does the config format differ per platform?
   - Are there platform-specific settings (paths, commands, integrations)?
   - Will this need a `.tmpl` file with platform conditionals?
   - Should this be excluded from certain platforms via `.chezmoiignore`?

**Deliverable**: Platform scope summary that determines which subsequent phases apply and what the implementation complexity will be.

#### Phase 1: Codebase Analysis (Use codebase-analyzer subagent)

**Locate and analyze the existing config files in the chezmoi source.**

1. **Find Config Files**:
   - Search in `dot_config/{{APP_NAME}}/` or related paths
   - Identify all config files added via `chezmoi add`
   - Note which files are already templated (`.tmpl` extension)
   - Check if app appears in `.chezmoiignore`

2. **Analyze Config Structure**:
   - **Format**: Identify file format (Lua, TOML, YAML, JSON, INI, conf, plain text)
   - **Existing Colors**: Look for current color/theme configuration sections
   - **Import Mechanisms**: Search for include/import/require/source statements
   - **Structure**: Determine if config is structured (parseable) or plain text
   - **Comments**: Check if config has comments (preservation matters for surgical edits)

3. **Cross-Platform Analysis**:
   - Are there platform-specific paths or commands in the config?
   - Would config need conditionals for different platforms?
   - Reference existing templated configs (e.g., `wezterm.lua.tmpl`) for patterns

4. **Extract Config Samples**:
   - Include relevant snippets showing structure
   - Highlight any existing theme/color sections
   - Note any import/include statements

**Deliverable**: Codebase analysis with file structure, format, import capability, and cross-platform templating needs.

#### Phase 2: Web Research (Use web-search-researcher subagent)

**Research {{APP_NAME}} capabilities systematically.**

1. **Official Documentation Research**:
   - Configuration file format and syntax
   - Color/theme configuration options
   - Include/import/source mechanisms (if any)
   - Plugin/extension system (if any)
   - Opacity/transparency support
   - Auto-reload capabilities

2. **Theme Ecosystem Research**:
   - **Builtin theme support**: Does the app have native theme switching?
   - **Popular theme ports**: Check for existing ports of common palettes:
     - Catppuccin: <https://github.com/catppuccin/{{APP_NAME}}>
     - Tokyo Night: <https://github.com/tokyo-night/{{APP_NAME}}>
     - Gruvbox, Nord, Dracula, One Dark, Solarized, etc.
   - **Community themes**: Are there theme generators or community collections?
   - **Theme format**: How do existing themes define colors? (This informs our implementation)

3. **Terminal Colors Inheritance** (Critical for TUI apps):
   - Can {{APP_NAME}} use terminal's ANSI color palette?
   - Does it respect terminal colors by default or require explicit configuration?
   - Is it a terminal emulator, TUI app, or GUI app?
   - Terminal colors fallback viability

4. **Reload Behavior**:
   - Does {{APP_NAME}} watch config files for changes?
   - Does it require restart or can it reload (signals, commands)?
   - Hot-reload capabilities?
   - What signal or command triggers reload? (e.g., SIGUSR1, SIGUSR2, `:reload`)

5. **Additional User Questions** (if {{USER_QUESTIONS}} provided):
   Research the user's specific questions with same rigor as above.

**Deliverable**: Comprehensive capability analysis with documentation links, theme ecosystem overview, and reload behavior.

#### Phase 3: Theming Method Decision Tree

**Systematically evaluate {{APP_NAME}} against the theming method decision tree.**

The goal is to determine HOW to apply themes (the method), not WHICH themes to apply (the palette). The method stays constant regardless of whether applying Catppuccin, Tokyo Night, or dynamic Material Design 3 colors.

```
Decision Tree:
1. Has builtin theme plugin/support?
   → YES: Method = builtin
   → Check: Does it support multiple palettes? Can we switch programmatically?
   → NO: Continue to 2

2. Supports external file loading (import/include/require/source)?
   → YES: Method = external_file (RECOMMENDED)
   → Best for: Fast updates, clean separation, comment preservation
   → NO: Continue to 3

3. Config format is structured (TOML/YAML/JSON/INI/Lua)?
   → YES: Method = inline (surgical swap)
   → Tools: tomlkit, ruamel.yaml, json, configparser
   → NO: Continue to 4

4. Plain text config?
   → YES: Method = inline (full template regeneration - last resort)
   → Downside: Loses comments, harder to maintain

5. Can inherit terminal colors?
   → Evaluate as fallback option for TUI apps
   → Note: Only relevant for apps running inside a terminal
```

**For each question, provide**:
- Clear YES/NO answer
- Evidence from codebase or web research
- Relevant code examples or documentation quotes

**Method Characteristics Reference**:

| Method | Speed | Comment Preservation | Complexity | Best For |
|--------|-------|---------------------|------------|----------|
| builtin | Fast | Yes | Low | Apps with theme plugins |
| external_file | Very Fast | Yes | Medium | Apps supporting includes |
| inline (surgical) | Fast | Yes (with right lib) | Medium-High | Structured configs |
| inline (template) | Fast | No | High | Last resort |
| terminal_colors | Instant | N/A | None | TUI fallback |

**Deliverable**: Step-by-step evaluation with evidence and recommended method.

#### Phase 4: Implementation Specification

**Based on all previous phases, provide a complete implementation specification.**

1. **Method Recommendation**:
   - **Primary Method**: [builtin / external_file / inline]
   - **Confidence**: High / Medium / Low
   - **Rationale**: [Evidence-based explanation]

2. **Platform Configuration**:

   Based on Phase 0 platform scope:
   
   | Platform | Theming | Config Approach |
   |----------|---------|-----------------|
   | macOS | Dynamic + Static | [approach] |
   | Windows | Dynamic + Static | [approach] |
   | Arch (GUI) | Dynamic + Static | [approach] |
   | Dev-Box | Static only | [approach or N/A] |
   | Termux | Static only | [approach or N/A] |

3. **Files to Create/Modify**:

   **Chezmoi Source Files**:
   - `dot_config/{{APP_NAME}}/[files]` - Main config (template if cross-platform)
   - `dot_config/{{APP_NAME}}/colors-{{APP_NAME}}.[ext].tmpl` - Color template (if external_file)
   - `dot_config/{{APP_NAME}}/opacity-{{APP_NAME}}.[ext].tmpl` - Opacity template (if supported)

   **Theme System Files**:
   - `dot_config/theme-system/scripts/apps/{{APP_NAME}}.py` - App module class

   **Ignore Files** (if platform-specific):
   - `.chezmoiignore.tmpl` entries needed

4. **Modular App Class Skeleton**:

   Following the `BaseApp` pattern from the theme system architecture:

   ```python
   """{{APP_NAME}} theme generator"""

   from pathlib import Path
   from .base import BaseApp
   from utils import get_material_colors, get_catppuccin_colors, is_dynamic_theme

   class {{AppName}}Theme(BaseApp):
       """{{APP_NAME}} theme generator
       
       Method: [external_file / inline / builtin]
       Reload: [auto / signal / manual / none]
       """
       
       def __init__(self, config_home: Path):
           super().__init__("{{APP_NAME}}", config_home)
           self.config_file = config_home / "{{APP_NAME}}/config.[ext]"
           # Add other file paths as needed
       
       def apply_theme(self, theme_data: dict) -> None:
           """Apply theme - called automatically by theme-manager.py"""
           self.log_progress("Updating {{APP_NAME}} theme")
           
           if is_dynamic_theme(theme_data):
               colors = self._generate_dynamic_colors(theme_data)
           else:
               colors = self._generate_static_colors(theme_data)
           
           self._apply_colors(colors)
           self._reload()  # If needed
           self.log_success(f"Updated {{APP_NAME}}")
       
       def _generate_dynamic_colors(self, theme_data: dict) -> dict:
           """Generate colors from Material Design 3 palette"""
           mat = get_material_colors(theme_data)
           return {
               # Map MD3 colors to app's color slots
               'foreground': mat.get('on_surface'),
               'background': mat.get('background'),
               'primary': mat.get('primary'),
               # ... more mappings based on app's color slots
           }
       
       def _generate_static_colors(self, theme_data: dict) -> dict:
           """Generate colors from static palette (Catppuccin, etc.)"""
           ctp = get_catppuccin_colors(theme_data)
           return {
               # Map palette colors to app's color slots
               'foreground': ctp.get('text'),
               'background': ctp.get('base'),
               'primary': ctp.get('mauve'),  # or user's accent preference
               # ... more mappings based on app's color slots
           }
       
       def _apply_colors(self, colors: dict) -> None:
           """Apply colors using the determined method"""
           # Implementation depends on method:
           # - external_file: Write to colors file
           # - inline: Surgical update with tomlkit/configparser/etc.
           # - builtin: Update config to reference theme name
           pass
       
       def _reload(self) -> None:
           """Reload app to apply changes"""
           # Implementation depends on app:
           # - signal: self.run_command("pkill -USR2 {{APP_NAME}}")
           # - command: self.run_command("{{APP_NAME}} --reload")
           # - auto: pass (app watches files)
           pass
   ```

5. **Registration**:

   In `apps/__init__.py`:
   ```python
   from .{{APP_NAME}} import {{AppName}}Theme
   
   def get_all_apps(config_home: Path) -> list:
       return [
           # ... existing apps ...
           {{AppName}}Theme(config_home),
       ]
   ```

6. **Color Mapping Specification**:

   Document how the app's color slots map to both static and dynamic palettes:

   | App Color Slot | Static (Catppuccin) | Dynamic (MD3) |
   |----------------|---------------------|---------------|
   | foreground | text | on_surface |
   | background | base | background |
   | primary/accent | mauve (or user pref) | primary |
   | ... | ... | ... |

7. **Opacity Support** (if applicable):
   - Supported: Yes / No
   - Method: external_file / inline / compositor
   - Config key: [specific key name]
   - Value format: 0-100 / 0.0-1.0 / hex alpha

8. **Reload Mechanism**:
   - Type: auto / signal / command / manual / none
   - Signal: [if applicable, e.g., SIGUSR2]
   - Command: [if applicable]
   - Reload time: [estimated]

**Deliverable**: Complete implementation specification with ready-to-use class skeleton.

#### Phase 5: Additional Questions (If Applicable)

{{- if USER_QUESTIONS is provided }}

**Address the user's specific questions**: "{{USER_QUESTIONS}}"

Provide:
1. Direct answer to each question
2. Code examples or configuration snippets
3. Integration considerations with the theme system and cross-platform setup
4. Best practices or recommendations
5. Potential conflicts or dependencies

**Deliverable**: Comprehensive answers to user's questions.

{{- end }}

### Research Output Structure

Create a comprehensive research document in `thoughts/shared/research/` with filename format:
`YYYY-MM-DD_HH-MM-SS_app-config-analysis-{{APP_NAME}}.md`

**Document Structure**:

````markdown
---
date: [ISO timestamp]
researcher: [agent name]
topic: "{{APP_NAME}} Configuration Integration Analysis"
app: {{APP_NAME}}
app_type: [gui/tui/cli]
platforms: [mac, windows, arch, dev-box, termux]
recommended_method: [method name]
confidence: [High/Medium/Low]
tags: [research, app-config, theming, {{APP_NAME}}]
status: complete
---

# Research: {{APP_NAME}} Configuration Integration

## Summary

[2-3 paragraph executive summary with platform scope, theming method recommendation, and key findings]

## Research Questions

1. How should {{APP_NAME}} be integrated into the chezmoi-managed dotfiles?
2. What is the optimal theming method?
3. Which platforms need this app?

{{- if USER_QUESTIONS is provided }}
4. {{USER_QUESTIONS}}
{{- end }}

---

## Platform Assessment

### App Classification

- **Type**: [GUI / TUI / CLI]
- **Category**: [terminal emulator / editor / status bar / etc.]

### Platform Availability

| Platform | Available | Theming | Notes |
|----------|-----------|---------|-------|
| macOS | ✅/❌ | Dynamic + Static | |
| Windows | ✅/❌ | Dynamic + Static | |
| Arch (GUI) | ✅/❌ | Dynamic + Static | |
| Dev-Box (headless) | ✅/❌ | Static only | |
| Android (Termux) | ✅/❌ | Static only | |

### Cross-Platform Considerations

- **Template needed**: Yes/No - [reason]
- **Platform conditionals**: [list any needed]
- **chezmoiignore entries**: [list any needed]

---

## Codebase Analysis

### Existing Configuration Files

[List files found in dot_config/ with paths]

### Configuration Structure

- **Format**: [Lua / TOML / YAML / JSON / INI / etc.]
- **Import mechanism**: [require / source / include / none]
- **Comment preservation**: [important / not important]

### Configuration Samples

[Relevant code snippets with analysis]

---

## Application Capabilities

### Official Documentation Findings

[Key findings from docs with links]

### Theme Ecosystem

| Theme | Port Exists | Link |
|-------|-------------|------|
| Catppuccin | ✅/❌ | [link] |
| Tokyo Night | ✅/❌ | [link] |
| Gruvbox | ✅/❌ | [link] |
| Nord | ✅/❌ | [link] |
| Other | ... | ... |

### Terminal Colors Support

[For TUI apps: inheritance capability analysis]

### Reload Behavior

- **Auto-reload**: Yes/No
- **Method**: [file_watch / signal / command / manual]
- **Signal/Command**: [specific signal or command]
- **Reload time**: [estimated]

### Opacity/Transparency Support

[Capability and configuration method]

---

## Theming Method Decision

### Decision Tree Evaluation

#### Question 1: Builtin Theme Support?
**Answer**: [YES/NO]
**Evidence**: [documentation, links, examples]

#### Question 2: External File Support?
**Answer**: [YES/NO]
**Evidence**: [import/include/require syntax and examples]

#### Question 3: Structured Config Format?
**Answer**: [YES/NO]
**Evidence**: [format analysis]

#### Question 4: Terminal Colors Inheritance?
**Answer**: [YES/NO/PARTIAL]
**Evidence**: [analysis for TUI apps]

### Recommendation

- **Primary Method**: [builtin / external_file / inline]
- **Confidence**: [High / Medium / Low]
- **Rationale**: [Detailed explanation]

---

## Implementation Specification

### Files to Create

#### Chezmoi Source
- `dot_config/{{APP_NAME}}/[main config]`
- `dot_config/{{APP_NAME}}/colors-{{APP_NAME}}.[ext].tmpl` (if external_file)

#### Theme System
- `dot_config/theme-system/scripts/apps/{{APP_NAME}}.py`

### Color Mapping

| App Slot | Static Palette | Dynamic (MD3) |
|----------|----------------|---------------|
| foreground | text | on_surface |
| background | base | background |
| primary | mauve | primary |
| [etc.] | | |

### App Class Skeleton

```python
[Complete skeleton from Phase 4]
```

### Registration

```python
# In apps/__init__.py
from .{{APP_NAME}} import {{AppName}}Theme

# Add to get_all_apps():
{{AppName}}Theme(config_home),
```

---

## Configuration Matrix Entry

**Add to `dotfiles-multi-platform-spec.md` Configuration Matrix:**

```markdown
| {{APP_NAME}} | ✅ | [dev-box] | [arch] | [windows] | [termux] | [notes] |
```

---

## apps.yaml Entry

**Add to `.chezmoidata/apps.yaml`:**

```yaml
  {{APP_NAME}}:
    display_name: {{DisplayName}}
    config_file: ~/.config/{{APP_NAME}}/config.[ext]
    config_format: [lua/toml/yaml/json/ini]
    app_type: [terminal_emulator/tui/gui/etc.]
    platform: [cross_platform/macos/linux]
    
    static_theme:
      priority:
        - method: [method]
          enabled: true
          notes: "[description]"
    
    dynamic_theme:
      priority:
        - method: [method]
          enabled: true
          notes: "[description]"
    
    external_files:  # If using external_file method
      colors:
        path: ~/.config/{{APP_NAME}}/colors-{{APP_NAME}}.[ext]
        format: [format]
        load_mechanism: "[how app loads it]"
    
    opacity:
      supported: [true/false]
      method: [method]
    
    reload:
      automatic: [true/false]
      method: [file_watch/signal/manual]
      signal: [if applicable]
      manual_command: [if applicable]
    
    generator:
      class: {{AppName}}Theme
      module: apps.{{APP_NAME}}
      method: [method]
      location: dot_config/theme-system/scripts/apps/{{APP_NAME}}.py
      apply_method: apply_theme
    
    status:
      implemented: false
      tested: false
      date_researched: "[date]"
```

---

{{- if USER_QUESTIONS is provided }}

## Additional Analysis

### User Question: {{USER_QUESTIONS}}

[Comprehensive answer]

{{- end }}

---

## Implementation Checklist

- [ ] Config added to chezmoi (`chezmoi add ~/.config/{{APP_NAME}}/`)
- [ ] Create app module: `apps/{{APP_NAME}}.py`
- [ ] Register in `apps/__init__.py`
- [ ] Create color template (if external_file method)
- [ ] Create opacity template (if supported)
- [ ] Update main config to load external files (if applicable)
- [ ] Add platform conditionals to config (if cross-platform differences)
- [ ] Update `.chezmoiignore.tmpl` (if platform-specific)
- [ ] Bootstrap: `chezmoi apply`
- [ ] Test: `theme set mocha`, `theme set dynamic`, `theme opacity 85`
- [ ] Update Configuration Matrix in spec
- [ ] Add entry to `apps.yaml`

## Next Steps

1. [Prioritized implementation steps]
2. [Testing recommendations]
3. [Potential gotchas]

## References

- [Official documentation links]
- [Theme port links]
- [Community resources]
- [Codebase file references]
````

### Execution Notes

1. **Use subagents appropriately**:
   - **codebase-analyzer**: For deep analysis of config structure and existing patterns
   - **web-search-researcher**: For documentation, theme ecosystem, and capability research
   - **codebase-locator**: If you need to find config files first

2. **Start with platform scope**: Phase 0 determines which subsequent phases are relevant. Don't skip it.

3. **Be systematic**: Work through phases in order. Each phase builds on previous findings.

4. **Be specific**: Include actual code examples, documentation quotes, and file paths. Avoid generic statements.

5. **Prioritize external_file method**: This is the recommended approach when the app supports it - fastest updates, cleanest separation.

6. **Use modular architecture**: All new apps must use the `BaseApp` class pattern in `apps/` directory. Do NOT suggest standalone generator functions.

7. **Terminal colors for TUI**: For terminal apps, always evaluate terminal colors inheritance as a fallback option.

8. **Document uncertainty**: If evidence is unclear or conflicting, state confidence level and explain why.

9. **Produce paste-ready output**: The apps.yaml entry and Configuration Matrix entry should be copy-paste ready.

10. **Reference existing patterns**: Look at existing apps in `apps.yaml` and `apps/*.py` for consistent patterns.

## Remember

Your goal is to provide a **complete, actionable research document** that allows implementation to proceed without additional research. The document should include:
- Platform scope determination
- Theming method recommendation with evidence
- Ready-to-use app class skeleton
- Paste-ready apps.yaml entry
- Paste-ready Configuration Matrix entry
