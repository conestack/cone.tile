#!/bin/sh
set -e
TEST="bin/python -m cone.tile.tests"

clear

if [ -x "$(which python)" ]; then
    ./py2/$TEST
fi

echo ""

if [ -x "$(which python3)" ]; then
    ./py3/$TEST
fi
