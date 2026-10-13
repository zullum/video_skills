# usage: python3 raise_guides_spec.py base.png SPEC.json
# Example: a 4x2 in-between sheet for a straight arm raised sideways from hanging (cell 1) to
# horizontal (cell 8). Cells 2-7 get the hanging-arm base with the arm erased and a red guide line
# from the shoulder at the target angle plus a red circle where the fist goes. Put a finished
# key-frame image into cell 8 afterwards (or erase+guide it at 90 degrees too).
# Measure SHOULDER, ARM_LEN and ARM_ERASE on YOUR base after it is fitted into a 630x540 cell.
import sys, json, math
SHOULDER, ARM_LEN = (300, 258), 225
ARM_ERASE = [(303, 300), (352, 300), (352, 505), (303, 505)]   # the hanging arm below the deltoid
ANGLES = [17, 29, 41, 53, 66, 78, 90]                            # degrees out from the body, cells 2-8
cells = [{}]
for a in ANGLES:
    r = math.radians(a); end = (SHOULDER[0] + ARM_LEN * math.sin(r), SHOULDER[1] + ARM_LEN * math.cos(r))
    cells.append({"erase": [ARM_ERASE], "guide": [[SHOULDER, [round(end[0], 1), round(end[1], 1)]]],
                  "circle": [[round(end[0], 1), round(end[1], 1)]]})
json.dump({"base": sys.argv[1], "cols": 4, "rows": 2, "cell": [630, 540], "fit": {"height": 1.0},
           "trim": 10, "cells": cells}, open(sys.argv[2], "w"), indent=1)
print("wrote", sys.argv[2])
