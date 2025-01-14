#!/usr/bin/env python3

"""
create_json_db.py

Reads the "3Phase-KSK-KW2-2025.xlsx" file to build a JSON mapping
for each KSKNr -> { 'pmod': <Ident>, 'offset': <StrippingLength> }.

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

        # Convert to appropriate types
        ksk_nr_str = str(ksk_nr).strip()
        ident_str = str(ident).strip()

        # 4) Check if this Ident appears in 3pass's "P-mod"
        pass_row = pass_df[pass_df['P-mod'] == ident_str]
        if pass_row.empty:
            # Not found in 3pass, skip this row
            print(f"[Warning] P-mod '{ident_str}' from KSKNr {ksk_nr_str} not found in '3pass' sheet.")
            continue

        # 5) Get the stripping length value
        stripping_length = pass_row.iloc[0]['Stripping length']
        stripping_length = stripping_length if not pd.isna(stripping_length) else 0  # Default to 0 if missing

        # Convert stripping_length to a regular Python type (int/float)
        stripping_length = int(stripping_length) if pd.api.types.is_integer_dtype(stripping_length) else float(stripping_length)

        # 6) Store the pmod and stripping length
        ksk_offsets[ksk_nr_str] = {
            "pmod": ident_str,
            "stripping_length": stripping_length
        }

    # 7) Write out the JSON
    output_file = 'ksk_offsets.json'
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(ksk_offsets, f, indent=4, ensure_ascii=False)
        print(f"Successfully wrote JSON data to '{output_file}'.")
    except Exception as e:
        print(f"Error writing to '{output_file}': {e}")

if __name__ == "__main__":
    main()
