#!/usr/bin/env python3
"""Redirect legacy Bash commands without executing or rewriting the command."""
import json
from pathlib import PurePosixPath
import shlex
import sys

from tree_sitter import Language, Parser
import tree_sitter_bash

PARSER = Parser(Language(tree_sitter_bash.language()))


REPLACEMENTS = {
    'grep': 'Use rg for text searches, or jq to extract JSON values.',
    'egrep': 'Use rg for regex searches, or jq to extract JSON values.',
    'fgrep': 'Use rg -F for literal text searches.',
    'find': 'Use fd to locate files, or rg --files to list source files.',
    'sed': 'Use sd for replacements; use Read, head, or tail to read file ranges.',
    'curl': 'Use xh for HTTP requests.',
    'http': 'Use xh for HTTP requests.',
    'https': 'Use xh for HTTP requests.',
}


def command_words(words):
    """Unwrap common launch prefixes, without treating their arguments as commands."""
    while words:
        name = PurePosixPath(words[0]).name
        if name == 'command':
            words = words[1:]
            if any(w in ('-v', '-V') for w in words[:1]):
                return []  # Executable discovery does not run the named command.
            while words and words[0] in ('-p', '--'):
                words = words[1:]
        elif name == 'env':
            words = words[1:]
            while words:
                if words[0] == '--':
                    words = words[1:]
                    break
                if words[0] in ('-u', '--unset', '-C', '--chdir'):
                    words = words[2:]
                elif words[0].startswith('-') or '=' in words[0]:
                    words = words[1:]
                else:
                    break
        elif name in ('exec', 'nohup'):
            words = words[1:]
            if words and words[0].startswith('-'):
                return []
        else:
            return words
    return []


def discouraged_commands(command, depth=0):
    if depth > 4:
        return set()
    root = PARSER.parse(command.encode()).root_node
    if root.has_error:
        # This is a tooling preference, not a shell security boundary. Unsupported
        # shell syntax must not turn into a false accusation or prevent real work.
        return set()
    found = set()

    def word(node):
        try:
            parts = shlex.split(node.text.decode())
            return parts[0] if len(parts) == 1 else ''
        except ValueError:
            return ''

    pending = [root]
    while pending:
        node = pending.pop()
        pending.extend(node.named_children)
        if node.type == 'command':
            name_node = node.child_by_field_name('name')
            if name_node is None:
                continue
            words = command_words([word(name_node)] +
                                  [word(n) for n in node.children_by_field_name('argument')])
            if not words:
                continue
            name = PurePosixPath(words[0]).name
            if name in REPLACEMENTS:
                found.add(name)
            elif name in ('bash', 'sh', 'zsh'):
                for index, word in enumerate(words[1:], 1):
                    if not word.startswith('-'):
                        break
                    if not word.startswith('--') and 'c' in word[1:]:
                        if index + 1 < len(words):
                            found.update(discouraged_commands(words[index + 1], depth + 1))
                        break

    return found


def main():
    event = json.load(sys.stdin)
    if event.get('tool_name') != 'Bash':
        return
    command = event.get('tool_input', {}).get('command', '')
    if not isinstance(command, str):
        return
    found = discouraged_commands(command)
    if found:
        reason = ' '.join(f'{name}: {REPLACEMENTS[name]}' for name in sorted(found))
        print(json.dumps({'hookSpecificOutput': {
            'hookEventName': 'PreToolUse',
            'permissionDecision': 'deny',
            'permissionDecisionReason': reason,
        }}))


if __name__ == '__main__':
    main()
