import pandas as pd
import json
import os
import time
import serial

file_path='3Phase-KSK-KW2-2025.xlsx'
ksk_table=pd.read_excel(file_path, sheet_name='KSK')
table_3pass=pd.read_excel(file_path, sheet_name='3pass')
with open('db.json','r') as f:
    db_data=json.load(f)

# Nyitva tartjuk a soros portot program induláskor, nem zárjuk be.
ser = serial.Serial('/dev/cino', 9600, timeout=1)

def get_variant_and_offsets(ident_value):
    for item in db_data:
        if item["Ident"] == ident_value:
            return item["variant"], int(item["offset"]), int(item["steps/mili"])
    return None, 0, 1

def find_and_save_data(input_value):
    ksk_row = ksk_table[ksk_table['KSKNr'] == input_value]
    if not ksk_row.empty:
        pmod_val = str(ksk_row['Ident'].iloc[0])
        table_3pass.columns = table_3pass.columns.str.strip()
        pass_row = table_3pass[table_3pass['P-mod'] == pmod_val]
        if not pass_row.empty:
            ident_value = str(pass_row['Ident'].iloc[0])
            length = int(pass_row['Stripping length'].iloc[0])
            variant, base_offset, steps_mili = get_variant_and_offsets(ident_value)
            final_offset = (length + base_offset) * steps_mili

            data_to_save = {
                "Ident": ident_value,
                "Stripping length": length,
                "variant": variant,
                "final_offset": final_offset
            }
            with open('output.json', 'w') as json_file:
                json.dump(data_to_save, json_file, indent=4)

            print(f"KSKNr: {input_value} -> P-mod: {pmod_val} -> Ident: {ident_value}")
            print(f"Stripping length: {length}, variant: {variant}, final_offset: {final_offset}")

            # Küldendő JSON
            to_send = json.dumps({"V": str(variant), "S": str(final_offset)})
            print(f"Sending over serial: {to_send}")

            # Írás a már megnyitott soros portra
            ser.write(to_send.encode('utf-8'))

            time.sleep(0.1)
            response = ser.readline().decode('utf-8', errors='ignore').strip()
            if response:
                print(f"Received from serial: {response}")
        else:
            print(f"No matching P-mod in 3pass for {pmod_val}")
    else:
        print(f"No matching KSK row for KSKNr: {input_value}")

def run_home_sequence():
    # "HOME" parancs küldése a program indulásakor, és a válasz beolvasása
    ser.write("HOME".encode('utf-8'))
    time.sleep(0.1)
    response = ser.readline().decode('utf-8', errors='ignore').strip()
    if response:
        print(f"HOME response: {response}")

def read_from_scanner(scanner_device):
    print("Listening for input from scanner...")
    with open(scanner_device, 'rb') as scanner:
        while True:
            raw_line = scanner.readline()
            if raw_line:
                decoded_line = raw_line.decode('latin-1', errors='ignore').strip()
                digits = ''.join(ch for ch in decoded_line if ch.isdigit())
                if digits:
                    find_and_save_data(int(digits))
            else:
                time.sleep(0.1)

scanner_device = '/dev/ttyACM0'

# HOME lépések lefuttatása
run_home_sequence()

# Ha létezik a szkenner eszköz, akkor elindítjuk a beolvasást
if os.path.exists(scanner_device):
    read_from_scanner(scanner_device)
else:
    print(f"Scanner device not found: {scanner_device}")
