#!/bin/bash

if [ -x "$(which python)" ]; then
    rm -r py2

    virtualenv -p python py2

    ./py2/bin/pip install coverage
    ./py2/bin/pip install -e .[test]
fi
if [ -x "$(which python3)" ]; then
    rm -r py3

    virtualenv -p python3 py3

    ./py3/bin/pip install coverage
    ./py3/bin/pip install -e .[test]
fi
