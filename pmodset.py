#!/usr/bin/env python3

"""
create_json_db.py

Reads the "3Phase-KSK-KW2-2025.xlsx" file and builds two JSON mappings:
1. KSKNr to PMOD (`ksk_pmod.json`)
2. PMOD to settings (`pmod_settings.json`)

Usage:
    python create_json_db.py
"""

import pandas as pd
import json
import os

def main():
    excel_file = '3Phase-KSK-KW2-2025.xlsx'
    
    # Check if Excel file exists
    if not os.path.exists(excel_file):
        print(f"Error: Excel file '{excel_file}' not found.")
        return
    
    try:
        # Read the necessary sheets
        ksk_df = pd.read_excel(excel_file, sheet_name='KSK')
        pass_df = pd.read_excel(excel_file, sheet_name='3pass')
        pass_df.columns = pass_df.columns.str.strip()  # Remove any leading/trailing whitespace in column headers
        print(f"Successfully read '{excel_file}' for sheets 'KSK' and '3pass'.")
    except Exception as e:
        print(f"Error reading Excel file '{excel_file}': {e}")
        return
    
    # 1. Create KSKNr to PMOD mapping
    ksk_pmod = {}
    
    for idx, row in ksk_df.iterrows():
        ksk_nr = row.get('KSKNr')
        ident = row.get('Ident')
        
        if pd.isna(ksk_nr) or pd.isna(ident):
            # Skip rows with missing KSKNr or Ident
            continue
        
        ksk_nr_str = str(int(ksk_nr)).strip()  # Assuming KSKNr is numeric
        ident_str = str(ident).strip()
        
        ksk_pmod[ksk_nr_str] = {
            "pmod": ident_str
        }
    
    # Write KSKNr to PMOD mapping to JSON
    ksk_pmod_file = 'ksk_pmod.json'
    try:
        with open(ksk_pmod_file, 'w', encoding='utf-8') as f:
            json.dump(ksk_pmod, f, indent=4, ensure_ascii=False)
        print(f"Successfully wrote KSKNr to PMOD mapping to '{ksk_pmod_file}'.")
    except Exception as e:
        print(f"Error writing to '{ksk_pmod_file}': {e}")
    
    # 2. Create PMOD to settings mapping
    # Extract unique PMODs from ksk_pmod
    unique_pmods = set(entry['pmod'] for entry in ksk_pmod.values())
    
    # Initialize PMOD settings with placeholder values
    pmod_settings = {}
    for pmod in unique_pmods:
        pmod_settings[pmod] = {
            "offset": 0,   # Default offset, to be manually updated
            "steps": 1     # Default steps, to be manually updated
        }
    
    # Optionally, you can pre-populate some settings based on '3pass' sheet
    # For example, if '3pass' contains default offsets/steps for PMODs
    # Uncomment and modify the following block as needed:
    
    # for pmod in unique_pmods:
    #     pass_row = pass_df[pass_df['P-mod'] == pmod]
    #     if not pass_row.empty:
    #         default_offset = pass_row['DefaultOffset'].iloc[0] if 'DefaultOffset' in pass_df.columns else 0
    #         default_steps = pass_row['DefaultSteps'].iloc[0] if 'DefaultSteps' in pass_df.columns else 1
    #         pmod_settings[pmod]['offset'] = default_offset
    #         pmod_settings[pmod]['steps'] = default_steps
    
    # Write PMOD to settings mapping to JSON
    pmod_settings_file = 'pmod_settings.json'
    try:
        with open(pmod_settings_file, 'w', encoding='utf-8') as f:
            json.dump(pmod_settings, f, indent=4, ensure_ascii=False)
        print(f"Successfully wrote PMOD settings to '{pmod_settings_file}'.")
    except Exception as e:
        print(f"Error writing to '{pmod_settings_file}': {e}")

if __name__ == "__main__":
    main()
