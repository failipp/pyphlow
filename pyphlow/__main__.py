#! /usr/bin/env python3

import sys
from pyphlow.app import main

if sys.argv[1]:
    main(sys.argv[1])
else:
    print("python -m pyphlow <path>")
