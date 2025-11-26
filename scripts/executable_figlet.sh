#!/usr/bin/env bash

if [ -z "$1" ]; then
  figlet -d ~/.config/figlet/fonts -f "ANSI Shadow" "Figlet"
  echo
  read -p "Enter the text for ascii encoding: " mytext
else
  mytext="$*"
fi

output=$(figlet -d ~/.config/figlet/fonts -f "ANSI Shadow" "$mytext")
echo "$output"

if command -v pbcopy &> /dev/null; then
  echo "$output" | pbcopy
elif command -v clip.exe &> /dev/null; then
  echo "$output" | clip.exe
elif command -v wl-copy &> /dev/null; then
  echo "$output" | wl-copy
elif command -v xclip &> /dev/null; then
  echo "$output" | xclip -sel clip
fi

echo
echo "Text copied to clipboard!"
