#!/usr/bin/env python3
"""Run with the hook environment's Python; never execute the inspected commands."""
import copy
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / 'dot_claude/hooks/executable_prefer-modern-cli.py'
detect = runpy.run_path(str(HOOK))['discouraged_commands']
setup = runpy.run_path(str(ROOT / 'dot_local/bin/executable_claude-mixed-setup'))


class BashHookTests(unittest.TestCase):
    def test_commands_in_pipelines_compounds_and_substitutions(self):
        cases = {
            'grep -n needle file': {'grep'},
            'cd repo && /usr/bin/grep needle file | head -5': {'grep'},
            "'grep' needle file": {'grep'},
            'env LANG=C command grep needle file': {'grep'},
            'command -- find . -name a': {'find'},
            'if true; then curl localhost:8787; fi': {'curl'},
            'for f in *.txt; do sed -i s/a/b/ "$f"; done': {'sed'},
            "bash -lc 'grep needle file'": {'grep'},
            'echo "$(grep needle file)"': {'grep'},
            'diff <(grep a file) <(rg b file)': {'grep'},
            'fgrep x file; egrep y file; http :8787; https example.com':
                {'fgrep', 'egrep', 'http', 'https'},
        }
        for command, expected in cases.items():
            with self.subTest(command=command):
                self.assertEqual(detect(command), expected)

    def test_data_is_not_a_command(self):
        cases = [
            'echo "grep sed curl find"',
            "jq '.grep | .find' report.json",
            "rg -n 'grep|sed|curl|find' docs",
            'sd grep rg example.txt',
            'fd -g grep.txt',
            'xh :8787 search==grep',
            "cat <<'EOF'\ngrep something\ncurl url\nEOF\nrg something file",
            "python3 - <<'PY'\nprint('grep')\nPY",
            '# grep ignored\nrg actual file',
            'command -v grep',
            'printf "%s" "a; grep file"',
        ]
        for command in cases:
            with self.subTest(command=command):
                self.assertEqual(detect(command), set())

    def test_command_after_heredoc_is_checked(self):
        self.assertEqual(detect("cat <<'EOF'\nrg data\nEOF\ngrep x file"), {'grep'})

    def test_unsupported_shell_syntax_does_not_block_work(self):
        self.assertEqual(detect('echo $((1 + 2))'), set())
        self.assertEqual(detect("echo 'unterminated"), set())

    def invoke(self, event):
        result = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(event),
                                text=True, capture_output=True, check=True)
        self.assertEqual(result.stderr, '')
        return json.loads(result.stdout) if result.stdout else None

    def test_denial_returns_actionable_feedback_without_executing(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / 'must-not-exist'
            result = self.invoke({'tool_name': 'Bash', 'tool_input': {
                'command': f'touch {marker}; grep secret file'}})
            output = result['hookSpecificOutput']
            self.assertEqual(output['hookEventName'], 'PreToolUse')
            self.assertEqual(output['permissionDecision'], 'deny')
            self.assertIn('Use rg', output['permissionDecisionReason'])
            self.assertNotIn('secret', output['permissionDecisionReason'])
            self.assertFalse(marker.exists())

    def test_allowed_calls_do_not_override_permissions(self):
        self.assertIsNone(self.invoke({'tool_name': 'Bash', 'tool_input': {'command': 'rg x file'}}))
        self.assertIsNone(self.invoke({'tool_name': 'Read', 'tool_input': {'command': 'grep x'}}))


class HookMergeTests(unittest.TestCase):
    def test_preserves_existing_hooks_and_settings_and_is_idempotent(self):
        existing = {'env': {'LOCAL': 'keep'}, 'model': 'local-model', 'hooks': {
            'PreToolUse': [{'matcher': 'Bash', 'hooks': [{'type': 'command', 'command': 'local-check'}]}],
            'PostToolUse': [{'matcher': 'Bash', 'hooks': [{'type': 'command', 'command': 'local-post'}]}],
        }}
        before = copy.deepcopy(existing)
        shared = json.loads((ROOT / 'dot_config/private_ai-setup/cli-preferences.json').read_text())['claude']['hooks']
        merge = setup['merge_claude_preferences']
        result = merge(existing, {'hooks': shared})
        self.assertEqual(existing, before)
        self.assertEqual(result['env'], existing['env'])
        self.assertEqual(result['model'], existing['model'])
        self.assertEqual(result['hooks']['PostToolUse'], existing['hooks']['PostToolUse'])
        self.assertEqual(result['hooks']['PreToolUse'][0], existing['hooks']['PreToolUse'][0])
        self.assertEqual(len(result['hooks']['PreToolUse']), 2)
        self.assertEqual(merge(result, {'hooks': shared}), result)
        changed = copy.deepcopy(shared)
        changed['PreToolUse'][0]['hooks'][0]['timeout'] = 9
        updated = merge(result, {'hooks': changed})
        self.assertEqual(len(updated['hooks']['PreToolUse']), 2)
        self.assertEqual(updated['hooks']['PreToolUse'][1]['hooks'][0]['timeout'], 9)


if __name__ == '__main__':
    unittest.main()
