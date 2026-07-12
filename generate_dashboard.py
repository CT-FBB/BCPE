import csv
import json
import os
from datetime import datetime

def main():
    csv_path = "/Users/bbae/BCPE/CPE Total.csv"
    html_path = "/Users/bbae/BCPE/onu_model/index.html"

    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return

    raw_data = []
    total_devices = 0
    product_class_totals = {}
    product_class_versions = {}
    unique_versions = set()

    # Read and parse CSV (using utf-8-sig to strip BOM)
    with open(csv_path, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Safely handle keys, stripping potential whitespace
            pc = (row.get("ProductClass") or row.get("\ufeffProductClass") or "").strip()
            sv = (row.get("SoftwareVersion") or "").strip()
            dev_str = (row.get("Total devices") or row.get("TotalDevices") or "0").strip()
            pc_type = (row.get("type") or "Unknown").strip()

            # Clean numeric string (e.g. "722,766" -> 722766)
            dev_str = dev_str.replace('"', '').replace(',', '')
            try:
                count = int(dev_str)
            except ValueError:
                count = 0

            # Process ALL models in this CSV
            if pc:
                raw_data.append({
                    "ProductClass": pc,
                    "SoftwareVersion": sv,
                    "TotalDevices": count,
                    "Type": pc_type
                })
                total_devices += count
                
                # Aggregate by ProductClass
                product_class_totals[pc] = product_class_totals.get(pc, 0) + count
                
                # Track versions per ProductClass
                if pc not in product_class_versions:
                    product_class_versions[pc] = {}
                product_class_versions[pc][sv] = product_class_versions[pc].get(sv, 0) + count
                
                unique_versions.add(sv)

    # Sort Product Classes by device counts descending
    sorted_pcs = sorted(product_class_totals.items(), key=lambda x: x[1], reverse=True)
    
    # Calculate detailed stats for each Product Class
    product_class_summary = []
    for pc, total in sorted_pcs:
        versions_dict = product_class_versions[pc]
        # Sort versions descending by device count
        sorted_versions = sorted(versions_dict.items(), key=lambda x: x[1], reverse=True)
        
        # Calculate percentage share of total devices
        pc_share = (total / total_devices) * 100 if total_devices > 0 else 0
        
        # Resolve model type (using the first occurrence of model in raw_data)
        model_type = "Unknown"
        for row in raw_data:
            if row["ProductClass"] == pc:
                model_type = row["Type"]
                break

        product_class_summary.append({
            "ProductClass": pc,
            "Type": model_type,
            "TotalDevices": total,
            "VersionCount": len(versions_dict),
            "Share": pc_share,
            "Versions": [{"SoftwareVersion": sv, "Count": c, "Share": (c / total) * 100} for sv, c in sorted_versions]
        })

    # Prepare JS data object
    js_data = {
        "TotalDevices": total_devices,
        "TotalProductClasses": len(product_class_totals),
        "TotalVersions": len(unique_versions),
        "ProductClassSummary": product_class_summary,
        "RawData": raw_data,
        "GeneratedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # Serialize data to JSON string for embedding
    data_json = json.dumps(js_data, indent=2, ensure_ascii=False)

    # Generate HTML content by replacing the placeholder in the template
    template = get_html_template()
    html_content = template.replace("{{DATA_JSON}}", data_json)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Successfully generated standalone dashboard HTML at: {html_path}")
    print(f"Total devices processed: {total_devices:,}")
    print(f"Unique product classes: {len(product_class_totals)}")
    print(f"Unique software versions: {len(unique_versions)}")


def get_html_template():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BCPE Standalone CPE Device & Software Version Dashboard</title>
    
    <!-- External libraries -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"></script>
    
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <style>
        /* ── Top Navigation Bar CSS ── */
        .topnav {
            height: 60px;
            background: rgba(13, 18, 34, 0.85);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            display: grid;
            grid-template-columns: 250px 1fr 250px;
            align-items: center;
            padding: 0 2rem;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 9999;
        }
        .topnav-logo {
            font-family: 'Outfit', sans-serif;
            font-size: 1.25rem;
            color: #f8fafc;
            font-weight: 800;
            display: flex;
            align-items: center;
            gap: 10px;
            justify-self: start;
        }
        @media (max-width: 900px) {
            .topnav {
                grid-template-columns: 1fr;
                justify-items: center;
                padding: 0 1rem;
            }
            .topnav-logo {
                display: none !important;
            }
            .topnav-links {
                justify-self: center;
            }
        }
        .topnav-logo span {
            background: linear-gradient(135deg, #06b6d4, #6366f1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .topnav-links {
            display: flex;
            gap: 8px;
            height: 100%;
            align-items: center;
            justify-self: center;
        }
        .topnav-right {
            justify-self: end;
            display: flex;
            align-items: center;
        }
        .topnav-links a {
            display: flex;
            align-items: center;
            height: 40px;
            padding: 0 16px;
            color: #94a3b8;
            text-decoration: none;
            font-size: 0.95rem;
            font-weight: 500;
            transition: all 0.2s ease;
            border-radius: 8px;
            box-sizing: border-box;
        }
        .topnav-links a:hover {
            color: #f8fafc;
            background: rgba(255,255,255,0.03);
        }
        .topnav-links a.active {
            color: #f8fafc;
            background: rgba(6, 182, 212, 0.15);
            font-weight: 600;
            border: 1px solid rgba(6, 182, 212, 0.2);
        }

        /* ── Standard CSS for Standalone Glassmorphism Dashboard ── */
        :root {
            --bg-color: #030712;
            --card-bg: rgba(17, 24, 39, 0.65);
            --card-bg-hover: rgba(31, 41, 55, 0.75);
            --border-color: rgba(255, 255, 255, 0.06);
            --border-color-hover: rgba(99, 102, 241, 0.25);
            --text-primary: #f9fafb;
            --text-secondary: #9ca3af;
            --text-muted: #6b7280;
            --cyan: #06b6d4;
            --indigo: #6366f1;
            --violet: #8b5cf6;
            --emerald: #10b981;
            --rose: #f43f5e;
            --font-display: 'Outfit', sans-serif;
            --font-body: 'Inter', sans-serif;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background: radial-gradient(circle at top, #0b0f19 0%, #030712 100%);
            color: var(--text-primary);
            font-family: var(--font-body);
            min-height: 100vh;
            padding: 24px;
            line-height: 1.5;
        }

        .dashboard-container {
            max-width: 1400px;
            margin: 0 auto;
        }

        /* ── Header ── */
        .header {
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(3, 7, 18, 0.4) 100%);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 28px 36px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
        }

        .header-title h1 {
            font-family: var(--font-display);
            font-size: 2.1rem;
            font-weight: 800;
            background: linear-gradient(135deg, #38bdf8, #818cf8, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.02em;
        }

        .header-title .sub {
            color: var(--text-secondary);
            font-size: 0.95rem;
            margin-top: 4px;
        }

        .badge-container {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }

        .badge {
            padding: 6px 14px;
            border-radius: 30px;
            font-size: 0.8rem;
            font-weight: 600;
            font-family: var(--font-display);
            border: 1px solid rgba(255,255,255,0.08);
            background: rgba(255,255,255,0.04);
            color: var(--text-primary);
        }

        .badge.cyan {
            background: rgba(6, 182, 212, 0.12);
            border-color: rgba(6, 182, 212, 0.3);
            color: #22d3ee;
        }

        .badge.violet {
            background: rgba(139, 92, 246, 0.12);
            border-color: rgba(139, 92, 246, 0.3);
            color: #c084fc;
        }

        .badge.emerald {
            background: rgba(16, 185, 129, 0.12);
            border-color: rgba(16, 185, 129, 0.3);
            color: #34d399;
        }

        /* ── KPI Grid ── */
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }

        .kpi-card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 20px 24px;
            position: relative;
            overflow: hidden;
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
        }

        .kpi-card:hover {
            transform: translateY(-2px);
            border-color: var(--border-color-hover);
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.3);
        }

        .kpi-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 4px;
        }

        .kpi-card.cyan::before { background: linear-gradient(90deg, #06b6d4, #22d3ee); }
        .kpi-card.violet::before { background: linear-gradient(90deg, #8b5cf6, #c084fc); }
        .kpi-card.indigo::before { background: linear-gradient(90deg, #6366f1, #818cf8); }
        .kpi-card.emerald::before { background: linear-gradient(90deg, #10b981, #34d399); }

        .kpi-label {
            font-size: 0.78rem;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 6px;
        }

        .kpi-value {
            font-family: var(--font-display);
            font-size: 2.2rem;
            font-weight: 800;
            line-height: 1.1;
            margin-bottom: 4px;
        }
        
        .kpi-value.cyan { color: #22d3ee; }
        .kpi-value.violet { color: #c084fc; }
        .kpi-value.indigo { color: #818cf8; }
        .kpi-value.emerald { color: #34d399; }

        .kpi-sub {
            font-size: 0.78rem;
            color: var(--text-muted);
        }

        .kpi-icon {
            position: absolute;
            top: 20px;
            right: 20px;
            font-size: 1.8rem;
            opacity: 0.15;
        }

        /* ── Layout Grid ── */
        .layout-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 20px;
            margin-bottom: 24px;
        }

        @media (max-width: 1024px) {
            .layout-grid {
                grid-template-columns: 1fr;
            }
        }

        .card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 24px;
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            position: relative;
            display: flex;
            flex-direction: column;
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 12px;
        }

        .card-title {
            font-family: var(--font-display);
            font-size: 1.1rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .card-title .dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }

        .card-title .dot.cyan { background-color: var(--cyan); }
        .card-title .dot.violet { background-color: var(--violet); }
        .card-title .dot.indigo { background-color: var(--indigo); }

        /* ── Chart Container ── */
        .chart-container {
            position: relative;
            height: 320px;
            width: 100%;
        }

        .chart-placeholder {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100%;
            color: var(--text-muted);
            font-size: 0.9rem;
        }

        /* ── Dropdown / Controls ── */
        .select-control {
            padding: 8px 16px;
            border-radius: 8px;
            border: 1px solid var(--border-color);
            background: rgba(17, 24, 39, 0.8);
            color: var(--text-primary);
            font-family: var(--font-body);
            font-size: 0.85rem;
            cursor: pointer;
            outline: none;
            min-width: 180px;
        }

        .select-control:focus {
            border-color: var(--indigo);
        }

        /* ── Interactive Tables ── */
        .table-container {
            width: 100%;
            overflow-x: auto;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            background: rgba(3, 7, 18, 0.2);
            max-height: 400px;
            overflow-y: auto;
            scrollbar-width: thin;
        }

        .table-container::-webkit-scrollbar {
            width: 5px; height: 5px;
        }

        .table-container::-webkit-scrollbar-thumb {
            background: var(--border-color); border-radius: 4px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
            text-align: left;
        }

        th {
            background: rgba(17, 24, 39, 0.9);
            color: var(--text-secondary);
            font-family: var(--font-display);
            font-weight: 600;
            font-size: 0.76rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            padding: 12px 16px;
            border-bottom: 1px solid var(--border-color);
            position: sticky;
            top: 0;
            z-index: 10;
            cursor: pointer;
            user-select: none;
            transition: color 0.2s ease;
        }

        th:hover {
            color: var(--text-primary);
        }

        th .sort-indicator {
            margin-left: 4px;
            font-size: 0.7rem;
            color: var(--text-muted);
        }

        td {
            padding: 11px 16px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.03);
            color: var(--text-primary);
            transition: background 0.15s ease;
        }

        tr.clickable {
            cursor: pointer;
        }

        tr.clickable:hover td {
            background: rgba(99, 102, 241, 0.08);
        }

        tr.active-row td {
            background: rgba(6, 182, 212, 0.12) !important;
            border-left: 4px solid var(--cyan);
            color: #22d3ee;
        }

        tr:last-child td {
            border-bottom: none;
        }

        /* ── Progress bar indicator ── */
        .progress-bar-container {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .progress-bar {
            flex-grow: 1;
            height: 6px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            overflow: hidden;
            min-width: 60px;
        }

        .progress-bar-fill {
            height: 100%;
            border-radius: 10px;
            background: linear-gradient(90deg, var(--indigo), var(--cyan));
        }

        .progress-val {
            font-weight: 600;
            min-width: 38px;
            text-align: right;
            font-size: 0.8rem;
        }

        /* ── Controls Section ── */
        .controls-section {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            gap: 16px;
            flex-wrap: wrap;
        }

        .search-container {
            position: relative;
            flex-grow: 1;
            max-width: 360px;
        }

        .search-container input {
            width: 100%;
            padding: 10px 16px 10px 40px;
            border-radius: 10px;
            border: 1px solid var(--border-color);
            background: rgba(17, 24, 39, 0.7);
            color: var(--text-primary);
            font-family: var(--font-body);
            font-size: 0.85rem;
            outline: none;
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }

        .search-container input:focus {
            border-color: var(--indigo);
            box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.15);
        }

        .search-container::before {
            content: '🔍';
            position: absolute;
            left: 14px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 0.95rem;
            opacity: 0.6;
        }

        .btn-export {
            background: linear-gradient(135deg, #10b981, #059669);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 10px;
            font-weight: 700;
            font-family: var(--font-display);
            font-size: 0.85rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: opacity 0.2s ease, transform 0.15s ease;
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25);
        }

        .btn-export:hover {
            opacity: 0.9;
            transform: translateY(-1px);
        }

        .btn-export:active {
            transform: translateY(0);
        }

        /* ── Full Detail Card ── */
        .detail-card {
            margin-top: 24px;
        }

        /* ── Footer ── */
        .footer {
            text-align: center;
            color: var(--text-muted);
            font-size: 0.78rem;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid var(--border-color);
        }

        /* ── Scrollbars ── */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: transparent;
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.18);
        }
    </style>

    <!-- FORCE LAYOUT LOCK as required by Rule 10 -->
    <style>
    /* === FORCE LAYOUT LOCK — ห้ามแก้ไข === */
    html { scrollbar-gutter: stable !important; overflow-y: scroll !important; }
    body { 
        margin: 0 !important;
        padding: 80px 2rem 2rem 2rem !important;
        overflow-x: hidden !important;
    }
    .topnav {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        height: 60px !important;
        z-index: 9999 !important;
    }
    </style>
</head>
<body>
    
    <!-- TOP NAVIGATION BAR -->
    <nav class="topnav">
        <div class="topnav-logo">📦 <span>BCPE Monitor</span></div>
        <div class="topnav-links">
            <a href="index.html" class="active">CPE Dashboard</a>
            <a href="onu_model_dashboard.html" id="nav-onumodel">ONU Model</a>
        </div>
        <div class="topnav-right"></div>
    </nav>

    <div class="dashboard-container">
        
        <!-- HEADER -->
        <header class="header">
            <div class="header-title">
                <h1>BCPE Standalone CPE Device Dashboard</h1>
                <div class="sub">Total devices breakdown by Product Class and Software Version (All Models)</div>
            </div>
            <div class="badge-container" style="align-items: center; display: flex; gap: 12px;">
                <span style="font-size: 0.85rem; font-weight: 600; color: var(--text-secondary);">Device Type:</span>
                <select id="typeFilter" class="select-control" onchange="onTypeFilterChange(this.value)" style="min-width: 140px; padding: 6px 12px; height: 32px; border-radius: 8px;">
                    <option value="ALL">All Types</option>
                </select>
                <span class="badge violet">📅 Compiled: <span id="compile-date">-</span></span>
                <span class="badge cyan">📦 Standalone Version</span>
            </div>
        </header>

        <!-- KPI GRID -->
        <section class="kpi-grid">
            <div class="kpi-card cyan">
                <div class="kpi-icon">📦</div>
                <div class="kpi-label">Total Devices</div>
                <div class="kpi-value cyan" id="kpi-total-devices">0</div>
                <div class="kpi-sub">Across all product models</div>
            </div>
            <div class="kpi-card violet">
                <div class="kpi-icon">🛠️</div>
                <div class="kpi-label">Product Models</div>
                <div class="kpi-value violet" id="kpi-total-models">0</div>
                <div class="kpi-sub">Active ProductClasses</div>
            </div>
            <div class="kpi-card indigo">
                <div class="kpi-icon">💾</div>
                <div class="kpi-label">Software Versions</div>
                <div class="kpi-value indigo" id="kpi-total-versions">0</div>
                <div class="kpi-sub">Distinct active versions</div>
            </div>
            <div class="kpi-card emerald">
                <div class="kpi-icon">🏆</div>
                <div class="kpi-label">Top Model & Share</div>
                <div class="kpi-value emerald" id="kpi-top-model">N/A</div>
                <div class="kpi-sub" id="kpi-top-model-sub">0 devices (0%)</div>
            </div>
        </section>

        <!-- CHARTS SECTION -->
        <section class="layout-grid">
            
            <!-- LEFT CARD: TOP PRODUCT CLASSES -->
            <div class="card">
                <div class="card-header">
                    <div class="card-title">
                        <span class="dot violet"></span>
                        Top Product Classes Share
                    </div>
                </div>
                <div class="chart-container">
                    <canvas id="topModelsChart"></canvas>
                </div>
            </div>

            <!-- MIDDLE CARD: SOFTWARE VERSIONS FOR SELECTED -->
            <div class="card">
                <div class="card-header">
                    <div class="card-title">
                        <span class="dot cyan"></span>
                        <span id="bar-chart-title">Software Version Distribution</span>
                    </div>
                    <select id="modelSelector" class="select-control" onchange="onModelSelect(this.value)">
                        <!-- Populated by JS -->
                    </select>
                </div>
                <div class="chart-container">
                    <canvas id="versionDistChart"></canvas>
                    <div id="no-version-msg" class="chart-placeholder" style="display: none;">Select a model to view versions</div>
                </div>
            </div>

            <!-- RIGHT CARD: SOFTWARE VERSION PIE CHART FOR SELECTED -->
            <div class="card">
                <div class="card-header">
                    <div class="card-title">
                        <span class="dot indigo"></span>
                        <span id="pie-chart-title">Selected Model Version Share</span>
                    </div>
                </div>
                <div class="chart-container">
                    <canvas id="versionPieChart"></canvas>
                    <div id="no-pie-msg" class="chart-placeholder" style="display: none;">Select a model to view versions</div>
                </div>
            </div>

        </section>

        <!-- TABLE SECTION 1: PRODUCT CLASS SUMMARY -->
        <section class="card" style="margin-bottom: 24px;">
            <div class="card-header">
                <div class="card-title">
                    <span class="dot indigo"></span>
                    Product Class summary (Click row to view details & update chart above)
                </div>
            </div>
            <div class="table-container">
                <table id="summaryTable">
                    <thead>
                        <tr>
                            <th onclick="sortSummaryTable(0)">Product Class <span class="sort-indicator" id="summary-sort-0">↕</span></th>
                            <th onclick="sortSummaryTable(1)">Type <span class="sort-indicator" id="summary-sort-1">↕</span></th>
                            <th onclick="sortSummaryTable(2)" style="text-align: right;">Total Devices <span class="sort-indicator" id="summary-sort-2">▼</span></th>
                            <th onclick="sortSummaryTable(3)" style="text-align: right;">Versions Count <span class="sort-indicator" id="summary-sort-3">↕</span></th>
                            <th style="min-width: 160px; text-align: left; padding-left: 24px;">Device Share</th>
                        </tr>
                    </thead>
                    <tbody id="summaryTableBody">
                        <!-- Populated by JS -->
                    </tbody>
                </table>
            </div>
        </section>

        <!-- TABLE SECTION 2: DETAILED DATA TABLE -->
        <section class="card detail-card">
            <div class="card-header" style="margin-bottom: 12px;">
                <div class="card-title">
                    <span class="dot cyan"></span>
                    Full Raw Data Breakdown
                </div>
            </div>
            
            <!-- Controls (Search + Export) -->
            <div class="controls-section">
                <div class="search-container">
                    <input type="text" id="searchInput" placeholder="Search product model or software version..." onkeyup="filterDetailedTable()">
                </div>
                <button class="btn-export" onclick="exportToExcel()">
                    <span>📥</span> Export to Excel
                </button>
            </div>

            <div class="table-container" style="max-height: 480px;">
                <table id="detailedTable">
                    <thead>
                        <tr>
                            <th onclick="sortDetailedTable(0)">Product Class <span class="sort-indicator" id="detail-sort-0">↕</span></th>
                            <th onclick="sortDetailedTable(1)">Type <span class="sort-indicator" id="detail-sort-1">↕</span></th>
                            <th onclick="sortDetailedTable(2)">Software Version <span class="sort-indicator" id="detail-sort-2">↕</span></th>
                            <th onclick="sortDetailedTable(3)" style="text-align: right;">Total Devices <span class="sort-indicator" id="detail-sort-3">▼</span></th>
                            <th onclick="sortDetailedTable(4)" style="text-align: right;">Model Share % <span class="sort-indicator" id="detail-sort-4">↕</span></th>
                        </tr>
                    </thead>
                    <tbody id="detailedTableBody">
                        <!-- Populated by JS -->
                    </tbody>
                </table>
            </div>
        </section>

        <!-- FOOTER -->
        <footer class="footer">
            BCPE Standalone CPE Device Dashboard &copy; 2026 · Standalone Project view
        </footer>

    </div>

    <!-- JS LOGIC -->
    <script>
        // EMBEDDED DATA INJECTED BY PYTHON SCRIPT
        const DashboardData = {{DATA_JSON}};

        // GLOBAL CHARTS AND STATES
        let topModelsChartObj = null;
        let versionChartObj = null;
        let versionPieChartObj = null;
        
        let selectedModel = "";
        let activeType = "ALL";
        
        // Active Aggregated Data
        let activeSummary = [];
        let activeRawData = [];
        let activeTotalDevices = 0;
        let activeTotalModels = 0;
        let activeTotalVersions = 0;
        let activeTopModel = "N/A";
        let activeTopModelSub = "0 devices (0%)";
        
        // Sorting States
        let summarySortCol = 2; // Default Sort by Total Devices (Col 2)
        let summarySortAsc = false;
        
        let detailedSortCol = 3; // Default Sort by Total Devices (Col 3)
        let detailedSortAsc = false;

        // Render Helpers
        function fmt(n) {
            return n == null ? '-' : Number(n).toLocaleString('en-US');
        }

        // Helper to show placeholders when Chart.js fails to load
        function showChartPlaceholder(msg) {
            const topChartContainer = document.getElementById("topModelsChart").parentNode;
            topChartContainer.innerHTML = `<div class="chart-placeholder" style="color: var(--text-secondary); text-align: center; padding: 40px; border: 1px dashed rgba(255,255,255,0.1); border-radius: 8px; display: flex; justify-content: center; align-items: center; height: 100%;">📊 ${msg}</div>`;
            
            const verChartContainer = document.getElementById("versionDistChart").parentNode;
            verChartContainer.innerHTML = `<div class="chart-placeholder" style="color: var(--text-secondary); text-align: center; padding: 40px; border: 1px dashed rgba(255,255,255,0.1); border-radius: 8px; display: flex; justify-content: center; align-items: center; height: 100%;">📊 ${msg}</div>`;

            const pieChartContainer = document.getElementById("versionPieChart").parentNode;
            pieChartContainer.innerHTML = `<div class="chart-placeholder" style="color: var(--text-secondary); text-align: center; padding: 40px; border: 1px dashed rgba(255,255,255,0.1); border-radius: 8px; display: flex; justify-content: center; align-items: center; height: 100%;">📊 ${msg}</div>`;
        }

        // Initialization
        window.onload = function() {
            document.getElementById("compile-date").innerText = DashboardData.GeneratedAt;
            
            // Populate Type Filter Dropdown
            populateTypeFilter();
            
            // Initial aggregation and render
            onTypeFilterChange("ALL");
        };

        function populateTypeFilter() {
            const types = new Set();
            DashboardData.RawData.forEach(row => {
                if (row.Type) types.add(row.Type);
            });
            const filter = document.getElementById("typeFilter");
            filter.innerHTML = '<option value="ALL">All Types (All Devices)</option>';
            Array.from(types).sort().forEach(t => {
                const opt = document.createElement("option");
                opt.value = t;
                opt.innerText = t + " Devices";
                filter.appendChild(opt);
            });
        }

        function onTypeFilterChange(typeVal) {
            activeType = typeVal;
            filterAndAggregateData(typeVal);

            // Populate Model Selector for Dropdown (sorted alphabetically)
            const selector = document.getElementById("modelSelector");
            selector.innerHTML = "";
            
            const sortedModelsForDropdown = [...activeSummary].sort((a, b) => {
                return String(a.ProductClass).localeCompare(String(b.ProductClass), 'en', { sensitivity: 'base' });
            });
            
            sortedModelsForDropdown.forEach(item => {
                const opt = document.createElement("option");
                opt.value = item.ProductClass;
                opt.innerText = item.ProductClass;
                selector.appendChild(opt);
            });

            // Set top model as active selection
            if (activeSummary.length > 0) {
                selectedModel = activeSummary[0].ProductClass;
                selector.value = selectedModel;
            } else {
                selectedModel = "";
            }

            // Update KPIs
            document.getElementById("kpi-total-devices").innerText = fmt(activeTotalDevices);
            document.getElementById("kpi-total-models").innerText = fmt(activeTotalModels);
            document.getElementById("kpi-total-versions").innerText = fmt(activeTotalVersions);
            document.getElementById("kpi-top-model").innerText = activeTopModel;
            document.getElementById("kpi-top-model-sub").innerText = activeTopModelSub;

            // Render Tables
            renderSummaryTable();
            renderDetailedTable();

            // Render Charts
            updateCharts();
        }

        function filterAndAggregateData(selectedType) {
            activeTotalDevices = 0;
            const modelTotals = {};
            const modelTypes = {};
            const modelVersions = {};
            const uniqueVersions = new Set();
            activeRawData = [];

            DashboardData.RawData.forEach(row => {
                if (selectedType === "ALL" || row.Type === selectedType) {
                    activeRawData.push(row);
                    activeTotalDevices += row.TotalDevices;
                    modelTotals[row.ProductClass] = (modelTotals[row.ProductClass] || 0) + row.TotalDevices;
                    modelTypes[row.ProductClass] = row.Type;
                    
                    if (!modelVersions[row.ProductClass]) {
                        modelVersions[row.ProductClass] = {};
                    }
                    modelVersions[row.ProductClass][row.SoftwareVersion] = (modelVersions[row.ProductClass][row.SoftwareVersion] || 0) + row.TotalDevices;
                    uniqueVersions.add(row.SoftwareVersion);
                }
            });

            activeTotalModels = Object.keys(modelTotals).length;
            activeTotalVersions = uniqueVersions.size;

            activeSummary = [];
            const sortedModels = Object.entries(modelTotals).sort((a, b) => b[1] - a[1]);
            sortedModels.forEach(([pc, total]) => {
                const versionsDict = modelVersions[pc];
                const sortedVers = Object.entries(versionsDict).sort((a, b) => b[1] - a[1]);
                const pcShare = activeTotalDevices > 0 ? (total / activeTotalDevices) * 100 : 0;
                
                activeSummary.push({
                    ProductClass: pc,
                    Type: modelTypes[pc],
                    TotalDevices: total,
                    VersionCount: sortedVers.length,
                    Share: pcShare,
                    Versions: sortedVers.map(([sv, count]) => ({
                        SoftwareVersion: sv,
                        Count: count,
                        Share: (count / total) * 100
                    }))
                });
            });

            if (activeSummary.length > 0) {
                const topModel = activeSummary[0];
                activeTopModel = topModel.ProductClass;
                activeTopModelSub = fmt(topModel.TotalDevices) + " devices (" + topModel.Share.toFixed(1) + "%)";
            } else {
                activeTopModel = "N/A";
                activeTopModelSub = "0 devices (0%)";
            }
        }

        function updateCharts() {
            if (selectedModel) {
                document.getElementById("pie-chart-title").innerText = selectedModel + " Version Share";
                document.getElementById("bar-chart-title").innerText = selectedModel + " Version Distribution";
            } else {
                document.getElementById("pie-chart-title").innerText = "Selected Model Version Share";
                document.getElementById("bar-chart-title").innerText = "Selected Model Version Distribution";
            }

            try {
                if (typeof Chart !== 'undefined') {
                    renderTopModelsChart();
                    renderVersionChart(selectedModel);
                    renderVersionPieChart(selectedModel);
                } else {
                    showChartPlaceholder("Chart.js failed to load.");
                }
            } catch (e) {
                console.error("Failed to render charts:", e);
                showChartPlaceholder("Error rendering charts: " + e.message);
            }
        }

        // Render Top Models Doughnut Chart
        function renderTopModelsChart() {
            const ctx = document.getElementById('topModelsChart').getContext('2d');
            
            // Get top 8 models, group others
            const labels = [];
            const data = [];
            let othersTotal = 0;

            activeSummary.forEach((item, idx) => {
                if (idx < 8) {
                    labels.push(item.ProductClass);
                    data.push(item.TotalDevices);
                } else {
                    othersTotal += item.TotalDevices;
                }
            });

            if (othersTotal > 0) {
                labels.push("Others");
                data.push(othersTotal);
            }

            if (topModelsChartObj) {
                topModelsChartObj.destroy();
            }

            const colors = [
                '#6366f1', // Indigo
                '#06b6d4', // Cyan
                '#8b5cf6', // Violet
                '#10b981', // Emerald
                '#f59e0b', // Amber
                '#ec4899', // Pink
                '#ef4444', // Red
                '#3b82f6', // Blue
                '#4b5563'  // Dark Gray
            ];

            topModelsChartObj = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: data,
                        backgroundColor: colors.slice(0, labels.length),
                        borderWidth: 2,
                        borderColor: '#0b0f19',
                        hoverOffset: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: {
                                color: '#9ca3af',
                                font: { family: 'Inter', size: 11 },
                                boxWidth: 10,
                                padding: 10
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const val = context.raw;
                                    const pct = activeTotalDevices > 0 ? (val / activeTotalDevices) * 100 : 0;
                                    return ` ${context.label}: ${fmt(val)} (${pct.toFixed(1)}%)`;
                                }
                            }
                        }
                    },
                    cutout: '70%'
                }
            });
        }

        // Render Version Bar Chart for selected Product Class
        function renderVersionChart(modelName) {
            const ctx = document.getElementById('versionDistChart').getContext('2d');
            const modelData = activeSummary.find(item => item.ProductClass === modelName);
            const msgEl = document.getElementById("no-version-msg");
            const canvasEl = document.getElementById("versionDistChart");

            if (!modelData) {
                msgEl.style.display = "flex";
                canvasEl.style.display = "none";
                if (versionChartObj) versionChartObj.destroy();
                return;
            }

            msgEl.style.display = "none";
            canvasEl.style.display = "block";

            const sortedVersions = modelData.Versions;
            const labels = [];
            const counts = [];
            let othersTotal = 0;

            sortedVersions.forEach((v, idx) => {
                if (idx < 10) {
                    labels.push(v.SoftwareVersion);
                    counts.push(v.Count);
                } else {
                    othersTotal += v.Count;
                }
            });

            if (othersTotal > 0) {
                labels.push("Others");
                counts.push(othersTotal);
            }

            if (versionChartObj) {
                versionChartObj.destroy();
            }

            versionChartObj = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Devices',
                        data: counts,
                        backgroundColor: 'rgba(6, 182, 212, 0.65)',
                        borderColor: '#06b6d4',
                        borderWidth: 1.5,
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    scales: {
                        x: {
                            ticks: { color: '#9ca3af', font: { family: 'Inter', size: 9 } },
                            grid: { color: 'rgba(255, 255, 255, 0.04)' }
                        },
                        y: {
                            ticks: { color: '#e5e7eb', font: { family: 'Inter', size: 10, weight: 'bold' } },
                            grid: { display: false }
                        }
                    },
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const val = context.raw;
                                    const pct = (val / modelData.TotalDevices) * 100;
                                    return ` ${fmt(val)} (${pct.toFixed(1)}% of Model)`;
                                }
                            }
                        }
                    }
                }
            });
        }

        // Render Version Pie Chart for selected Product Class
        function renderVersionPieChart(modelName) {
            const ctx = document.getElementById('versionPieChart').getContext('2d');
            const modelData = activeSummary.find(item => item.ProductClass === modelName);
            const msgEl = document.getElementById("no-pie-msg");
            const canvasEl = document.getElementById("versionPieChart");

            if (!modelData) {
                msgEl.style.display = "flex";
                canvasEl.style.display = "none";
                if (versionPieChartObj) versionPieChartObj.destroy();
                return;
            }

            msgEl.style.display = "none";
            canvasEl.style.display = "block";

            const sortedVersions = modelData.Versions;
            const labels = [];
            const counts = [];
            let othersTotal = 0;

            sortedVersions.forEach((v, idx) => {
                if (idx < 6) {
                    labels.push(v.SoftwareVersion);
                    counts.push(v.Count);
                } else {
                    othersTotal += v.Count;
                }
            });

            if (othersTotal > 0) {
                labels.push("Others");
                counts.push(othersTotal);
            }

            if (versionPieChartObj) {
                versionPieChartObj.destroy();
            }

            const colors = [
                '#06b6d4', // Cyan
                '#8b5cf6', // Violet
                '#6366f1', // Indigo
                '#10b981', // Emerald
                '#f59e0b', // Amber
                '#ec4899', // Pink
                '#4b5563'  // Gray
            ];

            versionPieChartObj = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: labels,
                    datasets: [{
                        data: counts,
                        backgroundColor: colors.slice(0, labels.length),
                        borderWidth: 1.5,
                        borderColor: '#0b0f19'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: '#9ca3af',
                                font: { family: 'Inter', size: 9 },
                                boxWidth: 8,
                                padding: 6
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const val = context.raw;
                                    const pct = (val / modelData.TotalDevices) * 100;
                                    return ` ${context.label}: ${fmt(val)} (${pct.toFixed(1)}% of Model)`;
                                }
                            }
                        }
                    }
                }
            });
        }

        // Handle dropdown selection
        function onModelSelect(val) {
            selectedModel = val;
            updateCharts();
            
            // Sync selected row in summary table
            const rows = document.querySelectorAll("#summaryTableBody tr");
            rows.forEach(row => {
                if (row.getAttribute("data-model") === val) {
                    row.classList.add("active-row");
                    // Prevent page jumps, scroll inside table container
                    const container = row.closest('.table-container');
                    if (container) {
                        container.scrollTo({
                            top: row.offsetTop - container.offsetTop,
                            behavior: 'smooth'
                        });
                    }
                } else {
                    row.classList.remove("active-row");
                }
            });
        }

        // Handle table row click
        function onSummaryRowClick(row, modelName) {
            document.getElementById("modelSelector").value = modelName;
            onModelSelect(modelName);
        }

        // Render Product Class Summary Table
        function renderSummaryTable() {
            const summary = [...activeSummary];
            
            // Sort logic
            summary.sort((a, b) => {
                let valA, valB;
                
                if (summarySortCol === 0) {
                    valA = String(a.ProductClass).toLowerCase();
                    valB = String(b.ProductClass).toLowerCase();
                } else if (summarySortCol === 1) {
                    valA = String(a.Type).toLowerCase();
                    valB = String(b.Type).toLowerCase();
                } else if (summarySortCol === 2) {
                    valA = a.TotalDevices;
                    valB = b.TotalDevices;
                } else if (summarySortCol === 3) {
                    valA = a.VersionCount;
                    valB = b.VersionCount;
                }

                if (valA < valB) return summarySortAsc ? -1 : 1;
                if (valA > valB) return summarySortAsc ? 1 : -1;
                return 0;
            });

            const tbody = document.getElementById("summaryTableBody");
            tbody.innerHTML = "";

            summary.forEach(item => {
                const row = document.createElement("tr");
                row.className = "clickable" + (item.ProductClass === selectedModel ? " active-row" : "");
                row.setAttribute("data-model", item.ProductClass);
                row.onclick = function() { onSummaryRowClick(this, item.ProductClass); };

                row.innerHTML = `
                    <td style="font-weight: 600;">${item.ProductClass}</td>
                    <td style="color: var(--text-secondary); font-weight: 500;">${item.Type}</td>
                    <td style="text-align: right; font-weight: 700; font-family: monospace;">${fmt(item.TotalDevices)}</td>
                    <td style="text-align: right; font-family: monospace; color: var(--text-secondary);">${item.VersionCount}</td>
                    <td style="padding-left: 24px;">
                        <div class="progress-bar-container">
                            <div class="progress-bar">
                                <div class="progress-bar-fill" style="width: ${item.Share}%"></div>
                            </div>
                            <span class="progress-val" style="color: ${item.ProductClass === selectedModel ? '#22d3ee' : '#818cf8'}">${item.Share.toFixed(1)}%</span>
                        </div>
                    </td>
                `;
                tbody.appendChild(row);
            });

            // Update header sort indicators
            for (let i = 0; i <= 3; i++) {
                const indicator = document.getElementById("summary-sort-" + i);
                if (i === summarySortCol) {
                    indicator.innerText = summarySortAsc ? "▲" : "▼";
                    indicator.style.color = "var(--cyan)";
                } else {
                    indicator.innerText = "↕";
                    indicator.style.color = "var(--text-muted)";
                }
            }
        }

        // Render Detailed Breakdown Table
        function renderDetailedTable() {
            const detailed = [];
            
            activeSummary.forEach(pc => {
                pc.Versions.forEach(v => {
                    detailed.push({
                        ProductClass: pc.ProductClass,
                        Type: pc.Type,
                        SoftwareVersion: v.SoftwareVersion,
                        TotalDevices: v.Count,
                        Share: v.Share
                    });
                });
            });

            // Sort logic
            detailed.sort((a, b) => {
                let valA, valB;
                
                if (detailedSortCol === 0) {
                    valA = String(a.ProductClass).toLowerCase();
                    valB = String(b.ProductClass).toLowerCase();
                } else if (detailedSortCol === 1) {
                    valA = String(a.Type).toLowerCase();
                    valB = String(b.Type).toLowerCase();
                } else if (detailedSortCol === 2) {
                    valA = String(a.SoftwareVersion).toLowerCase();
                    valB = String(b.SoftwareVersion).toLowerCase();
                } else if (detailedSortCol === 3) {
                    valA = a.TotalDevices;
                    valB = b.TotalDevices;
                } else if (detailedSortCol === 4) {
                    valA = a.Share;
                    valB = b.Share;
                }

                if (valA < valB) return detailedSortAsc ? -1 : 1;
                if (valA > valB) return detailedSortAsc ? 1 : -1;
                return 0;
            });

            const tbody = document.getElementById("detailedTableBody");
            tbody.innerHTML = "";

            detailed.forEach(item => {
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td style="font-weight: 600; color: #a5b4fc;">${item.ProductClass}</td>
                    <td style="color: var(--text-secondary); font-size: 0.8rem; font-weight: 500;">${item.Type}</td>
                    <td style="font-family: monospace; color: var(--text-primary); font-size: 0.8rem;">${item.SoftwareVersion}</td>
                    <td style="text-align: right; font-weight: 700; font-family: monospace; color: #34d399;">${fmt(item.TotalDevices)}</td>
                    <td style="text-align: right; font-family: monospace; color: var(--text-secondary);">${item.Share.toFixed(1)}%</td>
                `;
                tbody.appendChild(row);
            });

            // Update header sort indicators
            for (let i = 0; i <= 4; i++) {
                const indicator = document.getElementById("detail-sort-" + i);
                if (i === detailedSortCol) {
                    indicator.innerText = detailedSortAsc ? "▲" : "▼";
                    indicator.style.color = "var(--cyan)";
                } else {
                    indicator.innerText = "↕";
                    indicator.style.color = "var(--text-muted)";
                }
            }
        }

        function sortSummaryTable(colIdx) {
            if (summarySortCol === colIdx) {
                summarySortAsc = !summarySortAsc;
            } else {
                summarySortCol = colIdx;
                summarySortAsc = true;
            }
            renderSummaryTable();
        }

        function sortDetailedTable(colIdx) {
            if (detailedSortCol === colIdx) {
                detailedSortAsc = !detailedSortAsc;
            } else {
                detailedSortCol = colIdx;
                detailedSortAsc = true;
            }
            renderDetailedTable();
        }

        // Filter Table on Search Input
        function filterDetailedTable() {
            const filter = document.getElementById("searchInput").value.toLowerCase();
            const rows = document.querySelectorAll("#detailedTableBody tr");

            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.includes(filter)) {
                    row.style.display = "";
                } else {
                    row.style.display = "none";
                }
            });
        }

        // Export Detailed Data to Excel using SheetJS
        function exportToExcel() {
            if (typeof XLSX === 'undefined') {
                alert("SheetJS library is not loaded. Please connect to the internet to export to Excel.");
                return;
            }
            const exportData = [["Product Class", "Type", "Software Version", "Total Devices", "Share of Model (%)"]];

            activeSummary.forEach(pc => {
                pc.Versions.forEach(v => {
                    exportData.push([
                        pc.ProductClass,
                        pc.Type,
                        v.SoftwareVersion,
                        v.Count,
                        v.Share
                    ]);
                });
            });

            const wb = XLSX.utils.book_new();
            const ws = XLSX.utils.aoa_to_sheet(exportData);
            ws['!cols'] = [{wch:20}, {wch:12}, {wch:25}, {wch:15}, {wch:18}];
            XLSX.utils.book_append_sheet(wb, ws, "BCPE Devices Breakdown");
            
            const dateStr = new Date().toISOString().slice(0, 10);
            XLSX.writeFile(wb, `BCPE_Device_Breakdown_${activeType}_${dateStr}.xlsx`);
        }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
