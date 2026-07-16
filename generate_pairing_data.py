import json
import os
import glob
import pandas as pd
import re
from collections import Counter

def main():
    export_files = glob.glob('/Users/bbae/BCPE/device_export_*.csv')
    if not export_files:
        raise FileNotFoundError("No device_export_*.csv found in /Users/bbae/BCPE/")
    file_path = max(export_files, key=os.path.getmtime)
    output_json = '/Users/bbae/BCPE/onu_model/cpe_pairing_data.json'
    
    print(f"Reading raw data from {file_path}...")
    df = pd.read_csv(file_path)
    
    # Clean data
    df_valid = df.dropna(subset=['UserID']).copy()
    df_valid['UserID'] = df_valid['UserID'].astype(str)
    
    # 1. Load Updated Mapping
    mapping_path = '/Users/bbae/BCPE/cpe_model_type_mapping.json'
    with open(mapping_path, 'r') as f:
        mapping = json.load(f)
        
    legacy_ont_patterns = [
        r'^HG8247H$', r'^HG8247W5$', r'^HG8122$', r'^HG6145', r'^F612C$', r'^H662GR$', 
        r'^GN2000', r'^H660', r'^HT803', r'^AN5506', r'^F668$', r'^HG624', r'^AN5121'
    ]

    def is_legacy_ont(model):
        model_str = str(model).strip()
        for pattern in legacy_ont_patterns:
            if re.search(pattern, model_str, re.IGNORECASE):
                return True
        return False

    def is_routing_ont(model):
        model_str = str(model).strip()
        if re.search(r'^T[5678]\d+', model_str, re.IGNORECASE):
            return True
        routing_brands = {
            'GN542VF', 'F6600P', 'F6600R', 'F6620', 'F688', 
            'HG8247W5-6T', 'HG8245W5-6T', 'ST-244F', 'ST-244FV2', 'ST-245F', 'ST-GPON'
        }
        return model_str in routing_brands

    ap_models = {'WR6221-T', 'RE1200R4GC-V3', 'T3ATv2', 'ST-R4D', 'HG180Ev2', 'ZXHN H198A V3.0', 'SR120-A', 'BiPAC 3301DL-T', 'IGD'}

    print("Analyzing subscriber groups...")
    groups = df_valid.groupby('UserID')
    
    roles = {}
    pairing_types = {}
    
    # To collect pairings
    pairings_list = []
    
    # Grouping counts
    sub_1 = 0
    sub_2 = 0
    sub_3_plus = 0
    
    for name, grp in groups:
        indexes = grp.index.tolist()
        num_devices = len(indexes)
        
        if num_devices == 1:
            sub_1 += 1
            roles[indexes[0]] = 'HGW'
            continue
        elif num_devices == 2:
            sub_2 += 1
        else:
            sub_3_plus += 1
            
        idx_model = {idx: str(grp.loc[idx, 'Product Class']).strip() for idx in indexes}
        models = list(idx_model.values())
        
        # 1. Same model
        if len(set(models)) == 1:
            pairing_types[name] = 'as_mesh'
            roles[indexes[0]] = 'HGW'
            for idx in indexes[1:]:
                roles[idx] = 'Mesh'
                pairings_list.append((models[0], models[0], 'as_mesh'))
            continue
            
        # 2. 2-box (Legacy ONT + AP)
        has_legacy = any(is_legacy_ont(m) for m in models)
        if has_legacy:
            pairing_types[name] = '2-box'
            hgw_candidates = []
            for idx, model in idx_model.items():
                if is_legacy_ont(model):
                    roles[idx] = 'HGW'
                    hgw_candidates.append(model)
                else:
                    roles[idx] = 'AP'
            
            # Resolve HGW in group
            hgw_in_group = [idx for idx in indexes if roles.get(idx) == 'HGW']
            if len(hgw_in_group) == 0:
                roles[indexes[0]] = 'HGW'
                hgw_model = idx_model[indexes[0]]
            else:
                hgw_model = idx_model[hgw_in_group[0]]
                if len(hgw_in_group) > 1:
                    for idx in hgw_in_group[1:]:
                        roles[idx] = 'AP'
            
            # Collect pairings
            for idx, model in idx_model.items():
                if roles.get(idx) != 'HGW':
                    pairings_list.append((hgw_model, model, '2-box'))
            continue
            
        # 3. Routing ONT + Mesh AP
        has_routing_ont = any(is_routing_ont(m) for m in models)
        if has_routing_ont:
            pairing_types[name] = 'routing_ont_mesh'
            hgw_candidates = []
            for idx, model in idx_model.items():
                if is_routing_ont(model):
                    roles[idx] = 'HGW'
                    hgw_candidates.append(model)
                else:
                    if model in ap_models:
                        roles[idx] = 'AP'
                    else:
                        roles[idx] = 'Mesh'
            
            # Resolve HGW in group
            hgw_in_group = [idx for idx in indexes if roles.get(idx) == 'HGW']
            if len(hgw_in_group) == 0:
                roles[indexes[0]] = 'HGW'
                hgw_model = idx_model[indexes[0]]
            else:
                hgw_model = idx_model[hgw_in_group[0]]
                if len(hgw_in_group) > 1:
                    for idx in hgw_in_group[1:]:
                        roles[idx] = 'Mesh'
            
            # Collect pairings
            for idx, model in idx_model.items():
                if roles.get(idx) != 'HGW':
                    p_type = '2-box' if model in ap_models else 'routing_ont_mesh'
                    pairings_list.append((hgw_model, model, p_type))
            continue
            
        # Default Fallback (other_pairing)
        pairing_types[name] = 'other_pairing'
        roles[indexes[0]] = 'HGW'
        hgw_model = idx_model[indexes[0]]
        for idx in indexes[1:]:
            roles[idx] = 'Mesh'
            pairings_list.append((hgw_model, idx_model[idx], 'other_pairing'))

    # Set roles back in DataFrame
    df_valid['Device_Role'] = df_valid.index.map(roles).fillna('Mesh')
    
    total_devices = int(len(df_valid))
    total_subs = int(len(groups))
    
    hgw_count = int((df_valid['Device_Role'] == 'HGW').sum())
    mesh_count = int((df_valid['Device_Role'] == 'Mesh').sum())
    ap_count = int((df_valid['Device_Role'] == 'AP').sum())
    
    print("Aggregating model counts by physical type...")
    model_counts = df_valid['Product Class'].value_counts()
    
    # Calculate group totals based on physical type
    hgw_total = 0
    mesh_total = 0
    ap_total = 0
    
    for pc, val in model_counts.items():
        pc_str = str(pc).strip()
        m_type = mapping.get(pc_str, 'Unknown')
        if m_type == 'HGW':
            hgw_total += val
        elif m_type == 'Mesh':
            mesh_total += val
        elif m_type == 'AP':
            ap_total += val
            
    top_hgw_models = []
    top_mesh_models = []
    top_ap_models = []
    
    for pc, val in model_counts.items():
        pc_str = str(pc).strip()
        m_type = mapping.get(pc_str, 'Unknown')
        
        item_data = {
            'ProductClass': pc_str,
            'Type': m_type,
            'TotalDevices': int(val),
            'Share': 0.0
        }
        
        if m_type == 'HGW':
            item_data['Share'] = float(val / hgw_total * 100) if hgw_total > 0 else 0
            top_hgw_models.append(item_data)
        elif m_type == 'Mesh':
            item_data['Share'] = float(val / mesh_total * 100) if mesh_total > 0 else 0
            top_mesh_models.append(item_data)
        elif m_type == 'AP':
            item_data['Share'] = float(val / ap_total * 100) if ap_total > 0 else 0
            top_ap_models.append(item_data)

    print("Analyzing pairing types distribution...")
    pt_counts = Counter(pairing_types.values())
    pairing_types_dist = {
        'routing_ont_mesh': int(pt_counts.get('routing_ont_mesh', 0)),
        '2-box': int(pt_counts.get('2-box', 0)),
        'as_mesh': int(pt_counts.get('as_mesh', 0)),
        'other_pairing': int(pt_counts.get('other_pairing', 0))
    }
    
    print("Analyzing physical model pairings...")
    pairing_counts = Counter(pairings_list)
    total_pairings_count = len(pairings_list)
    top_pairings = []
    for (hgw, sub, ptype), count in pairing_counts.most_common(100):
        top_pairings.append({
            'HGW': str(hgw),
            'SubDevice': str(sub),
            'Type': str(ptype),
            'Count': int(count),
            'Percentage': float(count / total_pairings_count * 100) if total_pairings_count > 0 else 0
        })

    print("Analyzing FTTR Lead candidates (3+ devices)...")
    fttr_loids = [name for name, grp in groups if len(grp) >= 3]
    df_fttr = df_valid[df_valid['UserID'].isin(fttr_loids)]
    
    fttr_hgw_counts = df_fttr[df_fttr['Device_Role'] == 'HGW']['Product Class'].value_counts()
    fttr_leads_profile = []
    for pc, val in fttr_hgw_counts.items():
        fttr_leads_profile.append({
            'HGW': str(pc),
            'HouseholdCount': int(val),
            'Share': float(val / len(fttr_loids) * 100) if len(fttr_loids) > 0 else 0
        })

    data_json = {
        'total_devices': int(total_devices),
        'total_subscribers': int(total_subs),
        'device_roles': {
            'HGW': int(hgw_count),
            'Mesh': int(mesh_count),
            'AP': int(ap_count)
        },
        'household_devices_dist': {
            '1_device': int(sub_1),
            '2_devices': int(sub_2),
            '3_plus_devices': int(sub_3_plus)
        },
        'pairing_types_dist': pairing_types_dist,
        'top_hgw_models': top_hgw_models,
        'top_mesh_models': top_mesh_models,
        'top_ap_models': top_ap_models,
        'top_pairings': top_pairings,
        'fttr_leads_profile': fttr_leads_profile,
        'generated_at': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    print(f"Writing statistics to {output_json}...")
    with open(output_json, 'w') as f:
        json.dump(data_json, f, indent=2)
        
    print("Analysis and serialization complete!")

if __name__ == "__main__":
    main()
