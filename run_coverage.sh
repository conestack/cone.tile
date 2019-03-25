#!/bin/sh
./$1/bin/coverage run --source src/cone/tile -m cone.tile.tests
./$1/bin/coverage report
./$1/bin/coverage html
