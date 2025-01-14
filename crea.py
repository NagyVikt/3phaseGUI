#!/usr/bin/env python3

"""
create_json_db.py

Reads the "3Phase-KSK-KW2-2025.xlsx" file and builds a JSON mapping
for each KSKNr -> { 'pmod': <Ident>, 'offset': <default or 0> }.

Usage:
    python create_json_db.py
"""

import pandas as pd
import json

def main():
    # 1) Read Excel
    excel_file = '3Phase-KSK-KW2-2025.xlsx'
    try:
        ksk_df = pd.read_excel(excel_file, sheet_name='KSK')
        pass_df = pd.read_excel(excel_file, sheet_name='3pass')
        pass_df.columns = pass_df.columns.str.strip()  # Remove whitespace from column headers
        print(f"Successfully read '{excel_file}' for sheets 'KSK' and '3pass'.")
    except Exception as e:
        print(f"Error reading Excel file '{excel_file}': {e}")
        return

    # 2) Create dictionary that will hold { KSKNr: { 'pmod': ..., 'offset': ... } }
    ksk_offsets = {}

    # 3) Iterate over each KSK row
    for idx, row in ksk_df.iterrows():
        ksk_nr = row.get('KSKNr')
        ident = row.get('Ident')

        if pd.isna(ksk_nr) or pd.isna(ident):
            # If either is empty, skip
            continue

        # Convert to string just in case
        ksk_nr_str = str(ksk_nr).strip()
        ident_str = str(ident).strip()

        # 4) (Optional) Check if this Ident also appears in 3pass's "P-mod"
        #    so you know whether it’s valid or not.
        pass_row = pass_df[pass_df['P-mod'] == ident_str]
        if pass_row.empty:
            # Not found in 3pass, but we’ll still store something
            print(f"[Warning] P-mod '{ident_str}' from KSKNr {ksk_nr_str} not found in '3pass' sheet.")

        # 5) Store the default offset as 0 (or any other default you like)
        ksk_offsets[ksk_nr_str] = {
            "pmod": ident_str,
            "offset": 0
        }

    # 6) Write out the JSON
    output_file = 'ksk_offsets.json'
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(ksk_offsets, f, indent=4, ensure_ascii=False)
        print(f"Successfully wrote JSON data to '{output_file}'.")
    except Exception as e:
        print(f"Error writing to '{output_file}': {e}")

if __name__ == "__main__":
    main()
