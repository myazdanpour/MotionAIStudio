#!/bin/bash
cd "$(dirname "$0")" || exit 1
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.npm-global/bin:$PATH"
export PORT=8100
export MOTION_OPEN_BROWSER=1
exec ./start.sh
