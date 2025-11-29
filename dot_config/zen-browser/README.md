# Zen Browser Configuration

This directory contains preferences for Zen Browser.

## Files

- `user.js` - Browser preferences (about:config settings)

## How It Works

The `user.js` file is automatically copied to your Zen Browser profile during `chezmoi apply` via `.chezmoiscripts/run_onchange_after_zen-browser.sh.tmpl`.

## Theming

Zen Browser with transparency enabled automatically inherits system theme colors. No additional theming is needed.
