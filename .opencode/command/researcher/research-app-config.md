---
description: Research app configuration and determine optimal theming method for integration
agent: researcher
argument-hint: "[app-name] [optional: additional-config-questions]"
---

## Context

You are researching how to integrate an application into the unified theme management system. The user has already added the app's config to chezmoi using `chezmoi add`, so the config files exist in the codebase under `dot_config/` or similar.

**Required Context Document**:
@thoughts/shared/research/2025-10-16_19-53-43_theme-system-implementation-analysis.md

## Variables

### Dynamic Variables

- ARGUMENTS = $ARGUMENTS
  argument-hint: "[app-name] [optional: additional-config-questions]"

APP_NAME: [app-name from first argument]
USER_REQUEST: [additional config questions/requests from remaining arguments, if provided]

## Instructions

You are conducting a comprehensive configuration research analysis for **{{APP_NAME}}** to determine the optimal theming integration method and answer any additional configuration questions.

### Research Objectives

**Core Objective (Always Required)**:
Determine the best theming method for {{APP_NAME}} by systematically evaluating it against the theme system's decision tree.

**Additional Objective (If Provided)**:
{{- if USER_REQUEST is provided }}
Address the user's specific configuration request: "{{USER_REQUEST}}"
{{- end }}

### Research Workflow

#### Phase 1: Codebase Analysis (Use codebase-analyzer subagent)

**Locate and analyze the existing config files**:

1. **Find Config Files**:
   - Search in `dot_config/{{APP_NAME}}/` or related paths
   - Identify all config files added via `chezmoi add`
   - Note config file paths and names

2. **Analyze Config Structure**:
   - **Format**: Identify file format (Lua, TOML, YAML, JSON, conf, plain text)
   - **Existing Colors**: Look for current color/theme configuration sections
   - **Import Mechanisms**: Search for include/import/require/source statements
   - **Structure**: Determine if config is structured (parseable) or plain text
   - **Comments**: Check if config has comments (preservation matters)

3. **Extract Config Samples**:
   - Include relevant snippets showing structure
   - Highlight any existing theme/color sections
   - Note any import/include statements

**Deliverable**: Codebase analysis findings with file structure, format, and import capability assessment.

#### Phase 2: Web Research (Use web-search-researcher subagent)

**Research {{APP_NAME}} capabilities systematically**:

1. **Official Documentation Research**:
   - Configuration file format and syntax
   - Color/theme configuration options
   - Include/import/source mechanisms (if any)
   - Plugin/extension system (if any)
   - Opacity/transparency support
   - Auto-reload capabilities

2. **Catppuccin Ecosystem Research**:
   - Does a Catppuccin plugin/theme exist for {{APP_NAME}}?
   - If yes: Installation method, activation syntax, dynamic theme support?
   - Check: <https://github.com/catppuccin> and <https://github.com/catppuccin/{{APP_NAME}}>
   - Community themes or ports

3. **Terminal Colors Inheritance** (Critical for terminal apps):
   - Can {{APP_NAME}} use terminal's ANSI color palette?
   - Does it respect terminal colors by default or require explicit configuration?
   - Is it a terminal emulator, TUI app, or GUI app?
   - Terminal colors fallback viability

4. **Reload Behavior**:
   - Does {{APP_NAME}} watch config files for changes?
   - Does it require restart or can it reload (signals, commands)?
   - Hot-reload capabilities?

5. **Additional User Request Research** (if applicable):
   {{- if USER_REQUEST is provided }}
   Research the user's specific question: "{{USER_REQUEST}}"
   - Find official documentation
   - Look for community best practices
   - Identify configuration examples
   - Note any integration considerations with the theme system
     {{- end }}

**Deliverable**: Comprehensive capability analysis with documentation links and examples.

#### Phase 3: Decision Tree Evaluation

**Systematically evaluate {{APP_NAME}} against the theming method decision tree**:

```
Decision Tree:
1. Has builtin Catppuccin plugin?
   → YES: Method = builtin
   → NO: Continue to 2

2. Supports external file loading (import/include/require/source)?
   → YES: Method = external_file (RECOMMENDED)
   → NO: Continue to 3

3. Config format is structured (TOML/YAML/JSON/Lua)?
   → YES: Method = inline (surgical swap)
   → NO: Continue to 4

4. Plain text config?
   → YES: Method = inline (full template - last resort)

5. Can inherit terminal colors?
   → Evaluate as fallback/priority 2 or 3 option
```

**For each question, provide**:

- Clear YES/NO answer
- Evidence from codebase or web research
- Relevant code examples or documentation quotes

**Deliverable**: Step-by-step evaluation with evidence and recommended method.

#### Phase 4: Method Recommendation and Implementation Requirements

**Based on the decision tree evaluation, provide**:

1. **Primary Method Recommendation**:
   - Method name (builtin, external_file, inline)
   - Confidence level (High/Medium/Low)
   - Rationale with supporting evidence

2. **Priority Order** (for apps.yaml documentation):

   ```yaml
   priority:
     - method: [primary_method]
       enabled: true
     - method: terminal_colors # If applicable
       enabled: [true/false]
   ```

3. **Implementation Requirements**:

   **For builtin method**:
   - Plugin name and installation method
   - Activation syntax
   - Dynamic theme handling approach

   **For external_file method** (recommended):
   - Suggested external file names (e.g., `colors-{{APP_NAME}}.lua`)
   - Load mechanism syntax (e.g., `require("colors-app")`)
   - Config format for external files
   - Template structure needed

   **For inline method**:
   - Parser library needed (tomlkit, ruamel.yaml, etc.)
   - Config sections to modify
   - Comment preservation strategy
   - Surgical swap approach

4. **Opacity Support Assessment**:
   - Does {{APP_NAME}} support opacity/transparency?
   - Method: external_file, inline, or compositor
   - Configuration syntax

5. **Reload Behavior**:
   - Automatic vs manual
   - Method: file_watch, signal, manual, instant
   - Required commands (if manual)

6. **Generator Function Requirements**:
   - Function names needed (e.g., `generate_{{APP_NAME}}_colors`)
   - MD3 color mappings needed
   - Special handling requirements

**Deliverable**: Complete implementation specification ready for development.

#### Phase 5: Additional Configuration Analysis (If Applicable)

{{- if USER_REQUEST is provided }}

**Address the user's specific configuration request**: "{{USER_REQUEST}}"

Provide:

1. Direct answer to the configuration question
2. Code examples or configuration snippets
3. Integration considerations with the theme system
4. Best practices or recommendations
5. Potential conflicts or dependencies

**Deliverable**: Comprehensive answer to user's configuration question.

{{- end }}

### Research Output Structure

Create a comprehensive research document in `thoughts/shared/research/` with filename format:
`YYYY-MM-DD_HH-MM-SS_app-config-analysis-{{APP_NAME}}.md`

**Document Structure**:

````markdown
---
date: [ISO timestamp]
researcher: [your name]
topic: "{{APP_NAME}} Configuration and Theming Integration Analysis"
app: { { APP_NAME } }
recommended_method: [method name]
confidence: [High/Medium/Low]
tags: [research, app-config, theming, { { APP_NAME } }]
status: complete
---

# Research: {{APP_NAME}} Configuration and Theming Integration

## Summary

[2-3 paragraph executive summary with method recommendation and key findings]

## Research Question

How should {{APP_NAME}} be integrated into the unified theme management system? What is the optimal theming method?

{{- if USER_REQUEST is provided }}
Additional Question: {{USER_REQUEST}}
{{- end }}

## Codebase Analysis

### Existing Configuration Files

[List files found in dot_config/ with paths]

### Configuration Structure

[Format, structure, import mechanisms]

### Configuration Samples

[Relevant code snippets with analysis]

## Application Capabilities Research

### Official Documentation Findings

[Key findings from docs with links]

### Catppuccin Ecosystem

[Plugin availability, community themes]

### Terminal Colors Support

[Inheritance capability for terminal apps]

### Reload Behavior

[Auto-reload, signals, manual]

### Opacity/Transparency Support

[Capability and configuration method]

## Decision Tree Evaluation

### Question 1: Builtin Catppuccin Plugin?

**Answer**: [YES/NO]
**Evidence**: [documentation, links, examples]

### Question 2: External File Support?

**Answer**: [YES/NO]
**Evidence**: [import/include/require syntax and examples]

### Question 3: Structured Config Format?

**Answer**: [YES/NO]
**Evidence**: [format analysis]

### Question 4: Terminal Colors Inheritance?

**Answer**: [YES/NO/PARTIAL]
**Evidence**: [terminal app type, color handling]

## Method Recommendation

### Primary Method: [method_name]

**Confidence**: [High/Medium/Low]

**Rationale**:
[Detailed explanation with pros/cons]

**Priority Configuration**:

```yaml
static_theme:
  priority:
    - method: [primary]
      enabled: true
    - method: [fallback]
      enabled: [true/false]

dynamic_theme:
  priority:
    - method: [primary]
      enabled: true
```
````

## Implementation Specification

### Files to Create

#### Bootstrap Templates (chezmoi)

- `dot_config/{{APP_NAME}}/[template files needed]`

#### Generator Functions (theme-manager.py)

- `generate_{{APP_NAME}}_colors(theme_data: dict)`
- `generate_{{APP_NAME}}_opacity(theme_data: dict)` [if applicable]

### Configuration Integration

[Specific code examples showing how to load colors]

### Material Design 3 Color Mapping

[Map MD3 semantic colors to app's color scheme]

- foreground: `{{ .theme.material.on_surface }}`
- background: `{{ .theme.material.background }}`
- primary: `{{ .theme.material.primary }}`
  [etc.]

### Generator Function Skeleton

```python
def generate_{{APP_NAME}}_colors(theme_data: dict):
    """Generate colors for {{APP_NAME}}"""
    theme = theme_data.get('theme', {})
    theme_name = theme.get('name', 'mocha')

    if theme_name == 'dynamic':
        mat = theme.get('material', {})
        # Use MD3 colors
        [implementation details]
    else:
        ctp = theme.get('colors', {})
        # Use Catppuccin colors
        [implementation details]

    # Write to config
    [write logic]
```

### Opacity Support (If Applicable)

[Opacity implementation details]

### Reload Mechanism

[How to reload the app after config changes]

{{- if USER_REQUEST is provided }}

## Additional Configuration Analysis

### User Request: {{USER_REQUEST}}

[Comprehensive answer to the user's configuration question with examples and best practices]

{{- end }}

## Implementation Checklist

- [ ] Add config to chezmoi (already done via `chezmoi add`)
- [ ] Create color template: `dot_config/{{APP_NAME}}/colors-{{APP_NAME}}.[ext].tmpl`
- [ ] Create opacity template (if applicable)
- [ ] Write `generate_{{APP_NAME}}_colors()` in theme-manager.py
- [ ] Write `generate_{{APP_NAME}}_opacity()` (if applicable)
- [ ] Call generators in `set()` command (after line ~334)
- [ ] Update main config to load external files (if using external_file method)
- [ ] Bootstrap: Run `chezmoi apply`
- [ ] Test: `theme set mocha`, `theme set dynamic`, `theme opacity 85`
- [ ] Document in `.chezmoidata/apps.yaml` (optional)

## Next Steps

1. [Step-by-step implementation guidance]
2. [Testing recommendations]
3. [Potential gotchas to watch for]

## References

- [Links to official documentation]
- [Links to Catppuccin resources]
- [Links to community resources]
- [Code references in codebase]

```

### Execution Notes

1. **Use subagents appropriately**:
   - **codebase-analyzer**: For deep analysis of config structure and patterns
   - **web-search-researcher**: For thorough documentation and capability research
   - **codebase-locator**: If you need to find config files first

2. **Be systematic**: Work through the decision tree in order, providing clear evidence for each decision point.

3. **Be specific**: Include actual code examples, documentation quotes, and file paths. Avoid generic statements.

4. **Prioritize external_file method**: This is the recommended approach when possible - emphasize if the app supports it.

5. **Terminal colors matter**: For terminal apps, always evaluate terminal colors inheritance as a fallback option.

6. **Document uncertainty**: If evidence is unclear or conflicting, state confidence level and explain why.

7. **Integration focus**: Always consider how the solution integrates with the existing dual-track (bootstrap/runtime) architecture.

## Remember

Your goal is to provide a **complete, actionable research document** that allows the user to implement {{APP_NAME}} theming integration with confidence. The document should be thorough enough that implementation can proceed without additional research.
```
