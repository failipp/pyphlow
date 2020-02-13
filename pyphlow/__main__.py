#! /usr/bin/env python3

import os
import sys

from pyphlow.app import run_app

if sys.argv[1]:
    run_app(sys.argv[1])
else:
    print("python -m pyphlow <path>")
