#!/usr/bin/env python3
import sys
import csv

reader = csv.reader(sys.stdin)
header = next(reader)  # skip header row

item_id_idx = header.index('pizza_id')
quantity_idx = header.index('quantity')

for fields in reader:
    if len(fields) > max(item_id_idx, quantity_idx):
        item_id = fields[item_id_idx]
        quantity = fields[quantity_idx]
        print(f"{item_id}\t{quantity}")