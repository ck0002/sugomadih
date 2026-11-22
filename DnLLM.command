#!/usr/bin/env bash
# Double-click in Finder to play DnLLM.
cd "$(dirname "$0")" && ./play "$@"
status=$?
if [ $status -ne 0 ] && [ $status -ne 130 ]; then
  read -r -p "Press enter to close..."
fi
