---
name: command-creator
description: |
  Authoritative templates and scaffolding for creating slash commands. This skill should be used
  when creating new commands, reviewing existing commands for template compliance, or understanding
  command structure. Contains YAML templates with section instructions and scaffolding scripts
  for generating command skeleton files.
---

# Command Creator

This skill provides authoritative templates and tools for creating slash commands.

## When to Use This Skill

- **Creating** new slash commands
- **Reviewing** existing commands for template compliance
- **Understanding** command structure and patterns

## What Commands Are

Commands are task instructions that tell agents WHAT to do. They are:
- **Declarative** - Specify the task, not the implementation
- **Agent-executed** - Run by a specific agent (defined in frontmatter)
- **User-invoked** - Triggered via `/command-name` syntax
- **Parameterized** - Can accept arguments via `$ARGUMENTS`

Commands live in `.opencode/command/` (local) or `~/.config/opencode/command/` (global).

## Command Structure

Commands are simpler than agents. A minimal command needs only:
- **Frontmatter**: `description` and `agent`
- **Instructions**: What the agent should do

Optional sections add power when needed:
- **Variables**: Reusable values and argument handling
- **Context**: Runtime file/command injection
- **Workflow**: Multi-phase execution
- **Output Template**: Structured output generation

## Scripts

Execute scaffolding via justfile or directly with uv:

### Via Justfile (Recommended)

```bash
just -f {base_dir}/justfile <recipe> [args...]
```

| Recipe | Arguments | Description |
|--------|-----------|-------------|
| `scaffold` | `name path agent` | Create command skeleton |

### Direct Execution

```bash
uv run {base_dir}/scripts/scaffold_command.py <name> --path <path> --agent <agent>
```

### Examples

```bash
# Create a command for the build agent
just -f {base_dir}/justfile scaffold run-tests .opencode/command build

# Create a command for prompter
just -f {base_dir}/justfile scaffold review-code .opencode/command/prompter prompter

# Direct execution
uv run {base_dir}/scripts/scaffold_command.py my-command --path .opencode/command --agent build
```

## Domain Patterns

### Argument Handling Pattern

Commands accept user input via `$ARGUMENTS`. Handle based on usage:

**Single-use** (argument referenced once):
```yaml
## Variables
### Dynamic Variables
FILE_PATH: $ARGUMENTS

## Instructions
Process the file at {{FILE_PATH}}.
```

Or use `{{ARGUMENTS}}` directly if simpler.

**Multi-use** (argument referenced 2+ times):
```yaml
## Variables
### Dynamic Variables
FILE_PATH: $ARGUMENTS

## Instructions
Read {{FILE_PATH}}, analyze it, and save results to {{FILE_PATH}}.output.
```

**Why?** Only the first `$ARGUMENTS` gets programmatically swapped. Extract to semantic variable for clarity.

**Multiple arguments**:
```yaml
## Variables
### Dynamic Variables
- ARGUMENTS = $ARGUMENTS
  argument-hint: "[component-name] [optional-variant]"

COMPONENT: [component-name]
VARIANT: [optional-variant]

## Instructions
Generate {{COMPONENT}} with {{VARIANT}} styling.
```

### Freeform Input Pattern

For commands accepting either structured IDs OR freeform text:

```yaml
## Variables
### Dynamic Variables
USER_INPUT: $ARGUMENTS

## Instructions
**If {{USER_INPUT}} matches pattern (e.g., ENG-1234)**:
- Execute structured workflow with ID

**If {{USER_INPUT}} provided but doesn't match**:
- Treat as context/filtering criteria

**If no {{USER_INPUT}}**:
- Default behavior (e.g., list recent items)
```

Benefits: Single variable, maximum flexibility, elegant branching.

### Context Injection Pattern

Gather runtime information before execution:

```yaml
## Context
Current git status:
!`git status --short`

Project configuration:
@package.json

## Instructions
Based on the current state, ...
```

- `@file` - Inject file contents
- `!`command`` - Inject command output

## Template Reference

The YAML template in `references/command.yaml` is the authoritative source for command structure.

Each section contains:
- `id`: Unique section identifier
- `title`: Section heading
- `type`: Content type
- `instruction`: Detailed guidance
- `template`: Example format
- `optional`: Whether section can be omitted

## Workflow Integration

When Prompter creates a command:

1. **Understand the task** - What should the command accomplish?
2. **Identify the agent** - Which agent executes this? (build, prompter, etc.)
3. **Scaffold** - Run scaffolding script to create skeleton
4. **Reference template** - Read YAML for section instructions
5. **Fill sections** - Add only needed sections (keep commands minimal)
6. **Handle arguments** - Apply appropriate argument pattern if needed
