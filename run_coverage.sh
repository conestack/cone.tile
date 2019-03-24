#!/bin/sh
./$1/bin/coverage run --source src/cone/tile src/cone/tile/tests.py
./$1/bin/coverage report
./$1/bin/coverage html
