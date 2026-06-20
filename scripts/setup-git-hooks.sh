#!/bin/sh
set -e
cd "$(git rev-parse --show-toplevel)"
git config core.hooksPath .githooks
chmod +x .githooks/commit-msg
echo "Git hooks ativados: core.hooksPath=.githooks"
