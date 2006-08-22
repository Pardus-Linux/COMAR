#!/bin/bash
valgrind --num-callers=20 --show-reachable=yes --leak-check=yes --tool=memcheck build/comar --print
