import json
import os
import glob
import pandas as pd
import subprocess

def update_json_mapping():
    json_path = '/Users/bbae/BCPE/cpe_model_type_mapping.json'
    print(f"Reading mapping file: {json_path}...")
    with open(json_path, 'r', encoding='utf-8') as f:
        mapping = json.load(f)
        
    # Apply AP -> Mesh updates for A series and specific mesh APs
    mesh_models = {'A5258', 'A623', 'A625M', 'A6268', 'A626M', 'A662', 'RN510', 'ZXHN H3601P V9'}
    for m in mesh_models:
        if m in mapping:
            print(f"Updating {m}: {mapping[m]} -> Mesh")
            mapping[m] = 'Mesh'
            
    # Add missing models
    missing_models_mapping = {
        'F618': 'HGW',
        'RN104R4GC-A3': 'AP',
        'DefaultClass': 'Unknown',
        'HG8045H': 'HGW',
        'PE3102-00': 'AP',
        'T72Pro': 'HGW',
        'K251s-11': 'Mesh',
        'HG8245H5': 'HGW',
        'T72E': 'HGW',
        'SR1021F': 'AP',
        'Billion': 'AP',
        'ST-245F': 'HGW',
        'HG8245': 'HGW',
        'HG8045A': 'HGW',
        'GN630V': 'HGW',
        'T625L': 'HGW',
        'T528': 'HGW',
        'G2100': 'AP'
    }
    
    for m, t in missing_models_mapping.items():
        print(f"Adding new model {m} -> {t}")
        mapping[m] = t
        
    # FTTR overrides
    print("Applying FTTR model type overrides...")
    mapping['K251a-21'] = 'Mesh'
    mapping['K251s-11'] = 'Mesh'
    mapping['K153'] = 'Mesh'
    mapping['K153-10'] = 'Mesh'
    mapping['G1611'] = 'Mesh'
    mapping['V261a-20'] = 'HGW'
    mapping['V281s'] = 'HGW'
    mapping['V163'] = 'HGW'
    
    # MDU-FTTO overrides
    print("Applying MDU-FTTO model type overrides...")
    mapping['AN5121-4G'] = 'HGW'
    mapping['AN5121-4G-B05'] = 'HGW'
    
    # Convert all general FTTR types to HGW
    print("Converting all general FTTR types to HGW...")
    for model, t in list(mapping.items()):
        if t == 'FTTR':
            print(f"Mapping {model}: FTTR -> HGW")
            mapping[model] = 'HGW'
        
    print(f"Saving updated mapping to {json_path}...")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, indent=2)
        
    return mapping

def generate_cpe_total(mapping):
    export_files = glob.glob('/Users/bbae/BCPE/device_export_*.csv')
    if not export_files:
        raise FileNotFoundError("No device_export_*.csv found in /Users/bbae/BCPE/")
    raw_file = max(export_files, key=os.path.getmtime)
    output_file = '/Users/bbae/BCPE/CPE Total.csv'
    
    print(f"Reading raw data: {raw_file}...")
    df = pd.read_csv(raw_file, low_memory=False)
    df.columns = [c.strip() for c in df.columns]

    # ─── KPI Filter Rules (3 conditions must ALL be met) ────────────────────
    # 1. มี Firmware Version (ACS discovery สำเร็จ)
    # 2. มี homepassID / circuit (ผูกกับ circuit แล้ว)
    # 3. type ตรง = ไม่ใช่ Unknown (Product Class อยู่ใน mapping)
    # เหตุผล: device ที่ไม่มี version = ACS ยังไม่ discover (ไม่เคย online)
    #         device ที่ไม่มี circuit = ยังไม่ได้ provision
    #         device ที่ type = Unknown = ไม่รู้จัก model ยังไม่ควร count

    print("Applying KPI filter: must have Firmware Version + homepassID + known type...")

    # Step 1: filter Firmware Version and homepassID not null/empty
    df_clean = df[
        df['Firmware Version'].notna() & (df['Firmware Version'].str.strip() != '') &
        df['homepassID'].notna() & (df['homepassID'].astype(str).str.strip() != '') &
        (df['homepassID'].astype(str).str.strip() != 'nan')
    ].copy()

    # Step 2: map type per row so we can filter Unknown
    def get_type(model):
        model_str = str(model).strip()
        if model_str in mapping:
            return mapping[model_str]
        if model_str.startswith('T'):
            return 'HGW'
        if model_str.startswith('A'):
            return 'Mesh'
        return 'Unknown'

    df_clean['_type'] = df_clean['Product Class'].apply(get_type)

    # Step 3: drop Unknown type
    before = len(df_clean)
    df_clean = df_clean[df_clean['_type'] != 'Unknown']
    after = len(df_clean)
    print(f"  Raw rows: {len(df):,}")
    print(f"  After firmware+circuit filter: {before:,}")
    print(f"  After Unknown type filter: {after:,}  (KPI Count)")

    print("Aggregating device counts...")
    df_grouped = df_clean.groupby(['Product Class', 'Firmware Version']).size().reset_index(name='Total devices')

    print("Mapping device types...")
    df_grouped['type'] = df_grouped['Product Class'].apply(get_type)
    
    # Rename columns to match CPE Total.csv header format: ProductClass,SoftwareVersion,Total devices,type
    df_grouped.rename(columns={
        'Product Class': 'ProductClass',
        'Firmware Version': 'SoftwareVersion'
    }, inplace=True)
    
    # Reorder columns
    df_grouped = df_grouped[['ProductClass', 'SoftwareVersion', 'Total devices', 'type']]
    
    print(f"Saving output to {output_file}...")
    df_grouped.to_csv(output_file, index=False, encoding='utf-8-sig')
    print("Completed generating CPE Total.csv!")

def rebuild_dashboard():
    dashboard_script = '/Users/bbae/BCPE/generate_dashboard.py'
    print(f"Running dashboard builder: {dashboard_script}...")
    res = subprocess.run(['python3', dashboard_script], capture_output=True, text=True)
    print("STDOUT:")
    print(res.stdout)
    if res.stderr:
        print("STDERR:")
        print(res.stderr)

if __name__ == "__main__":
    mapping = update_json_mapping()
    generate_cpe_total(mapping)
    rebuild_dashboard()
