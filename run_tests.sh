#!/bin/sh
if [ -x "$(which python)" ]; then
    ./py2/bin/python -m cone.tile.tests
fi
if [ -x "$(which python3)" ]; then
    ./py3/bin/python -m cone.tile.tests
fi
if [ -x "$(which pypy)" ]; then
    ./pypy/bin/python -m cone.tile.tests
fi
