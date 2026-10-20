#!/usr/bin/env python3
import sys

current_key = None
total = 0

for line in sys.stdin:
    key, quantity = line.strip().split("\t")
    quantity = int(quantity)

    if key == current_key:
        total += quantity
    else:
        if current_key is not None:
            print(f"{current_key}\t{total}")
        current_key = key
        total = quantity

if current_key is not None:
    print(f"{current_key}\t{total}")