import json
import os

def main():
    json_path = '/Users/bbae/BCPE/onu_model/cpe_pairing_data.json'
    html_path = '/Users/bbae/BCPE/onu_model/cpe_pairing_dashboard.html'
    
    print(f"Loading data from {json_path}...")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    # Serialize data to embed directly in JS
    data_json = json.dumps(data, indent=2, ensure_ascii=False)
    
    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CPE Pairing & Roles (ACS) Dashboard</title>
    
    <script>
    if (window.self !== window.top) document.documentElement.classList.add('in-iframe');
    </script>
    
    <!-- External libraries -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"></script>
    
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <style>
        /* ── CSS VARIABLES & DESIGN SYSTEM ── */
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
            --amber: #f59e0b;
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
            padding-top: 84px; /* offset for nav bar */
            line-height: 1.5;
        }

        /* iframe exceptions */
        html.in-iframe { overflow-y: auto !important; }
        html.in-iframe body { padding: 0 !important; }
        html.in-iframe nav.topnav { display: none !important; }

        .dashboard-container {
            max-width: 1400px;
            margin: 0 auto;
        }

        /* ── TOP NAV BAR ── */
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
            font-family: var(--font-display);
            font-size: 1.25rem;
            color: #f8fafc;
            font-weight: 800;
            display: flex;
            align-items: center;
            gap: 10px;
            justify-self: start;
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

        /* ── HEADER ── */
        .header {
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(3, 7, 18, 0.4) 100%);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 24px 32px;
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
            font-size: 2.0rem;
            font-weight: 800;
            background: linear-gradient(135deg, #06b6d4, #6366f1, #a855f7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.02em;
        }

        .header-title .sub {
            color: var(--text-secondary);
            font-size: 0.92rem;
            margin-top: 4px;
        }

        .compile-badge {
            padding: 6px 14px;
            border-radius: 30px;
            font-size: 0.8rem;
            font-weight: 600;
            font-family: var(--font-display);
            border: 1px solid rgba(139, 92, 246, 0.3);
            background: rgba(139, 92, 246, 0.12);
            color: #c084fc;
        }

        /* ── KPI GRID ── */
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }

        .kpi-card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 20px 24px;
            display: flex;
            flex-direction: column;
            position: relative;
            overflow: hidden;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            backdrop-filter: blur(10px);
        }

        .kpi-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: var(--indigo);
            opacity: 0.8;
        }

        .kpi-card:hover {
            transform: translateY(-4px);
            border-color: var(--border-color-hover);
            background: var(--card-bg-hover);
            box-shadow: 0 10px 20px -10px rgba(99, 102, 241, 0.15);
        }

        /* Card color modifiers */
        .kpi-card.blue::before { background: #3b82f6; }
        .kpi-card.purple::before { background: #8b5cf6; }
        .kpi-card.emerald::before { background: #10b981; }
        .kpi-card.cyan::before { background: #06b6d4; }
        .kpi-card.rose::before { background: #f43f5e; }
        .kpi-card.amber::before { background: #f59e0b; }

        .kpi-card.amber {
            background: rgba(245, 158, 11, 0.04);
            border-color: rgba(245, 158, 11, 0.15);
        }
        .kpi-card.amber:hover {
            background: rgba(245, 158, 11, 0.08);
            border-color: rgba(245, 158, 11, 0.3);
        }

        .kpi-title {
            font-size: 0.82rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-secondary);
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .kpi-value {
            font-family: var(--font-display);
            font-size: 1.8rem;
            font-weight: 800;
            color: var(--text-primary);
            line-height: 1.2;
        }

        .kpi-sub {
            font-size: 0.78rem;
            color: var(--text-muted);
            margin-top: 6px;
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .kpi-badge {
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.65rem;
            font-weight: 700;
            background: rgba(245, 158, 11, 0.15);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.2);
        }

        /* Tooltip style */
        .tooltip-icon {
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 14px;
            height: 14px;
            border-radius: 50%;
            background: rgba(255,255,255,0.15);
            font-size: 0.65rem;
            color: var(--text-primary);
            position: relative;
        }
        
        .tooltip-icon:hover::after {
            content: attr(data-tooltip);
            position: absolute;
            bottom: 24px;
            right: -20px;
            width: 220px;
            background: #111827;
            border: 1px solid rgba(255,255,255,0.1);
            color: #e5e7eb;
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 0.75rem;
            line-height: 1.3;
            z-index: 1000;
            white-space: normal;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
            text-transform: none;
            font-weight: normal;
            letter-spacing: normal;
        }

        /* ── CHARTS CONTAINER ── */
        .charts-row {
            display: grid;
            grid-template-columns: 1.2fr 0.8fr;
            gap: 20px;
            margin-bottom: 24px;
        }

        @media (max-width: 900px) {
            .charts-row {
                grid-template-columns: 1fr;
            }
        }

        .chart-card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 24px;
            display: flex;
            flex-direction: column;
            backdrop-filter: blur(10px);
        }

        .chart-header {
            margin-bottom: 16px;
        }

        .chart-title {
            font-family: var(--font-display);
            font-size: 1.15rem;
            font-weight: 700;
            color: var(--text-primary);
        }

        .chart-subtitle {
            font-size: 0.82rem;
            color: var(--text-secondary);
            margin-top: 2px;
        }

        .canvas-container {
            position: relative;
            flex-grow: 1;
            min-height: 260px;
            max-height: 320px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        /* ── DATA SECTION & TABS ── */
        .data-section {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 24px;
            backdrop-filter: blur(10px);
            margin-bottom: 30px;
        }

        .tabs-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 14px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 16px;
        }

        .tabs-list {
            display: flex;
            gap: 6px;
        }

        .tab-btn {
            background: transparent;
            border: 1px solid transparent;
            color: var(--text-secondary);
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 0.9rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .tab-btn:hover {
            color: var(--text-primary);
            background: rgba(255, 255, 255, 0.03);
        }

        .tab-btn.active {
            color: var(--text-primary);
            background: rgba(99, 102, 241, 0.15);
            border-color: rgba(99, 102, 241, 0.25);
            font-weight: 600;
        }

        /* Controls: Search & Export */
        .table-controls {
            display: flex;
            gap: 10px;
            align-items: center;
            flex-wrap: wrap;
        }

        .search-control {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 8px 14px;
            border-radius: 8px;
            font-size: 0.88rem;
            outline: none;
            width: 260px;
            transition: all 0.2s ease;
        }

        .search-control:focus {
            border-color: var(--indigo);
            background: rgba(255, 255, 255, 0.06);
            box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.25);
        }

        .btn {
            background: var(--indigo);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 0.88rem;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s ease;
        }

        .btn:hover {
            background: #4f46e5;
            transform: translateY(-1px);
        }

        .btn-secondary {
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
        }

        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.08);
            border-color: var(--text-secondary);
        }

        /* ── TABLE STYLES ── */
        .table-container {
            overflow-x: auto;
            border-radius: 12px;
            border: 1px solid var(--border-color);
            background: rgba(3, 7, 18, 0.2);
        }

        table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 0.9rem;
        }

        th {
            background: rgba(13, 18, 34, 0.5);
            color: var(--text-secondary);
            font-weight: 600;
            padding: 14px 18px;
            border-bottom: 1px solid var(--border-color);
            cursor: pointer;
            user-select: none;
            transition: background 0.2s ease;
        }

        th:hover {
            background: rgba(13, 18, 34, 0.8);
            color: var(--text-primary);
        }

        td {
            padding: 14px 18px;
            border-bottom: 1px solid var(--border-color);
            color: var(--text-primary);
        }

        tr:last-child td {
            border-bottom: none;
        }

        tr {
            transition: background 0.15s ease;
        }

        tr:hover td {
            background: rgba(255, 255, 255, 0.02);
        }

        /* Badges inside tables */
        .table-badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.72rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        .table-badge.hgw {
            background: rgba(16, 185, 129, 0.12);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.2);
        }
        .table-badge.mesh {
            background: rgba(6, 182, 212, 0.12);
            color: #22d3ee;
            border: 1px solid rgba(6, 182, 212, 0.2);
        }
        .table-badge.ap {
            background: rgba(244, 63, 94, 0.12);
            color: #fb7185;
            border: 1px solid rgba(244, 63, 94, 0.2);
        }
        .table-badge.routing-ont-mesh {
            background: rgba(99, 102, 241, 0.12);
            color: #818cf8;
            border: 1px solid rgba(99, 102, 241, 0.2);
        }
        .table-badge.two-box {
            background: rgba(139, 92, 246, 0.12);
            color: #c084fc;
            border: 1px solid rgba(139, 92, 246, 0.2);
        }
        .table-badge.as-mesh {
            background: rgba(6, 182, 212, 0.12);
            color: #22d3ee;
            border: 1px solid rgba(6, 182, 212, 0.2);
        }
        .table-badge.other-pairing {
            background: rgba(244, 63, 94, 0.12);
            color: #fb7185;
            border: 1px solid rgba(244, 63, 94, 0.2);
        }
        .table-badge.potential {
            background: rgba(245, 158, 11, 0.15);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.25);
            font-size: 0.68rem;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { opacity: 0.8; }
            50% { opacity: 1; }
            100% { opacity: 0.8; }
        }

        .sort-indicator {
            margin-left: 4px;
            font-size: 0.75rem;
            color: var(--text-muted);
        }

        .empty-row {
            text-align: center;
            color: var(--text-secondary);
            padding: 30px !important;
            font-style: italic;
        }
    </style>
</head>
<body>

    <!-- TOP NAVIGATION BAR -->
    <nav class="topnav">
        <div class="topnav-logo">📦 <span>BCPE Monitor</span></div>
        <div class="topnav-links">
            <a href="index.html">Device (ACS)</a>
            <a href="onu_model_dashboard.html" id="nav-onumodel">ONU (QRUN)</a>
            <a href="cpe_pairing_dashboard.html" class="active" id="nav-cpepairing">CPE Pairing (ACS)</a>
        </div>
        <div class="topnav-right"></div>
    </nav>

    <div class="dashboard-container">
        
        <!-- HEADER -->
        <header class="header">
            <div class="header-title">
                <h1>CPE Pairing & Network Roles Summary</h1>
                <div class="sub">วิเคราะห์การพ่วงขยายสัญญาณตามรหัสลูกค้า (HGW, Mesh, AP และโอกาสทางการตลาดสำหรับ FTTR)</div>
            </div>
            <div class="compile-badge">
                📅 Generated: <span id="generation-time">-</span>
            </div>
        </header>

        <!-- KPI GRID -->
        <div class="kpi-grid">
            <div class="kpi-card blue">
                <div class="kpi-title">Active Subscribers</div>
                <div class="kpi-value" id="kpi-subscribers">-</div>
                <div class="kpi-sub">จำนวนครัวเรือน (LOIDs) ทั้งหมดในระบบ</div>
            </div>
            
            <div class="kpi-card purple">
                <div class="kpi-title">Multi-device Homes</div>
                <div class="kpi-value" id="kpi-multi-homes">-</div>
                <div class="kpi-sub" id="kpi-multi-share">บ้านที่พ่วงอุปกรณ์ &ge; 2 เครื่อง</div>
            </div>
            
            <div class="kpi-card amber">
                <div class="kpi-title">
                    <span>FTTR Leads (3+ Devices)</span>
                    <span class="kpi-badge">High Value</span>
                </div>
                <div class="kpi-value" id="kpi-fttr-leads">-</div>
                <div class="kpi-sub" id="kpi-fttr-share">บ้านใหญ่ที่มีความต้องการ AP สูง</div>
            </div>
            
            <div class="kpi-card cyan">
                <div class="kpi-title">Mesh Access Points</div>
                <div class="kpi-value" id="kpi-mesh">-</div>
                <div class="kpi-sub" id="kpi-mesh-share">ตัวเสริมสัญญาณแบบ Smart Mesh</div>
            </div>
            
            <div class="kpi-card rose">
                <div class="kpi-title">
                    <span>2-Box / Standalone APs</span>
                    <span class="tooltip-icon" data-tooltip="อุปกรณ์ AP ที่ลงทะเบียนเดี่ยวใน ACS (กล่อง ONT หลักบริดจ์โปร่งใส / สัญญาณตกหล่น) หรือตัวพ่วงในชุด 2-box">?</span>
                </div>
                <div class="kpi-value" id="kpi-ap">-</div>
                <div class="kpi-sub" id="kpi-ap-share">ตัวกระจายสัญญาณเสริมชั้นที่สอง</div>
            </div>
        </div>

        <!-- CHARTS SECTION -->
        <div class="charts-row">
            <div class="chart-card">
                <div class="chart-header">
                    <div class="chart-title">Pairing Configuration Type Distribution</div>
                    <div class="chart-subtitle">สัดส่วนของรูปแบบชุดอุปกรณ์กระจายสัญญาณ Wi-Fi ของบ้านที่มีอุปกรณ์ขยายสัญญาณ</div>
                </div>
                <div class="canvas-container">
                    <canvas id="pairingChart"></canvas>
                </div>
            </div>
            
            <div class="chart-card">
                <div class="chart-header">
                    <div class="chart-title">Devices Count per Household</div>
                    <div class="chart-subtitle">สัดส่วนจำนวนอุปกรณ์ต่อหนึ่งสายผู้ใช้งานอินเทอร์เน็ต</div>
                </div>
                <div class="canvas-container">
                    <canvas id="devCountChart"></canvas>
                </div>
            </div>
        </div>

        <!-- DATA SECTION -->
        <div class="data-section">
            <div class="tabs-header">
                <div class="tabs-list">
                    <button class="tab-btn active" onclick="switchTab('pairings')">Model Pairings (การจับคู่ยอดนิยม)</button>
                    <button class="tab-btn" onclick="switchTab('roles')">Device Roles (สถิติแยกตามรุ่น)</button>
                    <button class="tab-btn" onclick="switchTab('fttr')">FTTR Upgrade Potentials (โอกาสทางการขาย)</button>
                </div>
                <div class="table-controls">
                    <input type="text" id="tableSearch" class="search-control" placeholder="ค้นหาข้อมูล..." onkeyup="onSearchInput()">
                    <button class="btn btn-secondary" onclick="exportDataExcel()">📥 Export Excel</button>
                </div>
            </div>

            <!-- TAB CONTENT: Pairings -->
            <div id="tab-pairings" class="tab-content">
                <div class="table-container">
                    <table id="pairings-table">
                        <thead>
                            <tr>
                                <th onclick="sortTabTable('pairings', 0)">HGW Model (กล่องหลัก) <span class="sort-indicator">↕</span></th>
                                <th onclick="sortTabTable('pairings', 1)">Secondary Model (กล่องเสริม) <span class="sort-indicator">↕</span></th>
                                <th onclick="sortTabTable('pairings', 2)">Pairing Type <span class="sort-indicator">↕</span></th>
                                <th onclick="sortTabTable('pairings', 3)">Count (จำนวนคู่) <span class="sort-indicator">↕</span></th>
                                <th onclick="sortTabTable('pairings', 4)">Share of Pairings (%) <span class="sort-indicator">↕</span></th>
                            </tr>
                        </thead>
                        <tbody id="pairings-table-body">
                            <!-- Populated by JS -->
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- TAB CONTENT: Roles -->
            <div id="tab-roles" class="tab-content" style="display: none;">
                <!-- Nested role-type selector -->
                <div style="margin-bottom: 16px; display: flex; gap: 8px;">
                    <button id="subtab-hgw-btn" class="tab-btn active" onclick="switchRoleSubTab('HGW')">HGW Models</button>
                    <button id="subtab-mesh-btn" class="tab-btn" onclick="switchRoleSubTab('Mesh')">Mesh Models</button>
                    <button id="subtab-ap-btn" class="tab-btn" onclick="switchRoleSubTab('AP')">AP Models</button>
                </div>
                <div class="table-container">
                    <table id="roles-table">
                        <thead>
                            <tr>
                                <th onclick="sortTabTable('roles', 0)">Product Class (โมเดล) <span class="sort-indicator">↕</span></th>
                                <th onclick="sortTabTable('roles', 1)">Network Role <span class="sort-indicator">↕</span></th>
                                <th onclick="sortTabTable('roles', 2)">Total Devices <span class="sort-indicator">↕</span></th>
                                <th onclick="sortTabTable('roles', 3)">Share of Role (%) <span class="sort-indicator">↕</span></th>
                            </tr>
                        </thead>
                        <tbody id="roles-table-body">
                            <!-- Populated by JS -->
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- TAB CONTENT: FTTR Opportunities -->
            <div id="tab-fttr" class="tab-content" style="display: none;">
                <div style="background: rgba(245,158,11,0.06); border: 1px solid rgba(245,158,11,0.15); border-radius: 12px; padding: 16px; margin-bottom: 20px; font-size: 0.9rem;">
                    💡 <strong>โอกาสการขายอัปเกรด FTTR:</strong> รายชื่อโมเดลเกตเวย์ HGW หลักที่พบในบ้านกลุ่ม 3+ Devices (จำนวน 15,012 ครัวเรือน) ซึ่งมีพฤติกรรมความต้องการ Wi-Fi ความครอบคลุมสูง เหมาะสำหรับการทำการตลาดนำเสนอแพ็กเกจ Fiber-to-the-Room (FTTR) เป็นอันดับแรก ๆ
                </div>
                <div class="table-container">
                    <table id="fttr-table">
                        <thead>
                            <tr>
                                <th onclick="sortTabTable('fttr', 0)">HGW Model (กล่องหลักปัจจุบัน) <span class="sort-indicator">↕</span></th>
                                <th onclick="sortTabTable('fttr', 1)">FTTR Candidate Households (ราย) <span class="sort-indicator">↕</span></th>
                                <th onclick="sortTabTable('fttr', 2)">Share of FTTR Pool (%) <span class="sort-indicator">↕</span></th>
                                <th>Sales Potential <span class="sort-indicator">↕</span></th>
                            </tr>
                        </thead>
                        <tbody id="fttr-table-body">
                            <!-- Populated by JS -->
                        </tbody>
                    </table>
                </div>
            </div>

        </div>

    </div>

    <!-- DATA BLOCK -->
    <script>
        const dashboardData = {data_json};
    </script>

    <!-- LOGIC SCRIPT -->
    <script>
        let currentTab = 'pairings';
        let currentRoleSubTab = 'HGW';
        let sortDirections = {
            pairings: [1, 1, 1, -1, -1],
            roles: [1, 1, -1, -1],
            fttr: [1, -1, -1]
        };
        
        let filteredPairings = [];
        let filteredRoles = [];
        let filteredFttr = [];

        window.onload = function() {
            initDashboard();
        };

        function initDashboard() {
            document.getElementById('generation-time').innerText = dashboardData.generated_at;
            
            // Populate KPIs
            document.getElementById('kpi-subscribers').innerText = Number(dashboardData.total_subscribers).toLocaleString();
            document.getElementById('kpi-multi-homes').innerText = Number(dashboardData.household_devices_dist['2_devices'] + dashboardData.household_devices_dist['3_plus_devices']).toLocaleString();
            
            const multiShare = ((dashboardData.household_devices_dist['2_devices'] + dashboardData.household_devices_dist['3_plus_devices']) / dashboardData.total_subscribers) * 100;
            document.getElementById('kpi-multi-share').innerText = `สัดส่วน: ${multiShare.toFixed(2)}% ของครัวเรือนรวม`;
            
            document.getElementById('kpi-fttr-leads').innerText = Number(dashboardData.household_devices_dist['3_plus_devices']).toLocaleString();
            const fttrShare = (dashboardData.household_devices_dist['3_plus_devices'] / dashboardData.total_subscribers) * 100;
            document.getElementById('kpi-fttr-share').innerText = `สัดส่วน: ${fttrShare.toFixed(2)}% ของครัวเรือนรวม`;
            
            document.getElementById('kpi-mesh').innerText = Number(dashboardData.device_roles.Mesh).toLocaleString();
            document.getElementById('kpi-mesh-share').innerText = `สัดส่วน: ${(dashboardData.device_roles.Mesh / dashboardData.total_devices * 100).toFixed(2)}% ของเครื่องทั้งหมด`;
            
            document.getElementById('kpi-ap').innerText = Number(dashboardData.device_roles.AP).toLocaleString();
            document.getElementById('kpi-ap-share').innerText = `สัดส่วน: ${(dashboardData.device_roles.AP / dashboardData.total_devices * 100).toFixed(2)}% ของเครื่องทั้งหมด`;

            // Prepare filtered arrays
            filteredPairings = [...dashboardData.top_pairings];
            filteredFttr = [...dashboardData.fttr_leads_profile];
            updateFilteredRoles();

            // Populate Tables
            renderPairingsTable();
            renderRolesTable();
            renderFttrTable();

            // Render Charts
            renderCharts();
        }

        function updateFilteredRoles() {
            if (currentRoleSubTab === 'HGW') {
                filteredRoles = [...dashboardData.top_hgw_models];
            } else if (currentRoleSubTab === 'Mesh') {
                filteredRoles = [...dashboardData.top_mesh_models];
            } else {
                filteredRoles = [...dashboardData.top_ap_models];
            }
        }

        // Tab Switching
        function switchTab(tabId) {
            currentTab = tabId;
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.style.display = 'none');
            
            // Highlight current button (parent tab-btn only)
            const index = ['pairings', 'roles', 'fttr'].indexOf(tabId);
            document.querySelectorAll('.tabs-list .tab-btn')[index].classList.add('active');
            document.getElementById(`tab-${tabId}`).style.display = 'block';

            // Reset search bar on switch
            document.getElementById('tableSearch').value = '';
            onSearchInput();
        }

        function switchRoleSubTab(subTabId) {
            currentRoleSubTab = subTabId;
            document.getElementById('subtab-hgw-btn').classList.remove('active');
            document.getElementById('subtab-mesh-btn').classList.remove('active');
            document.getElementById('subtab-ap-btn').classList.remove('active');
            
            document.getElementById(`subtab-${subTabId.toLowerCase()}-btn`).classList.add('active');
            
            document.getElementById('tableSearch').value = '';
            updateFilteredRoles();
            renderRolesTable();
        }

        // Render Tables
        function renderPairingsTable() {
            const tbody = document.getElementById('pairings-table-body');
            tbody.innerHTML = '';
            
            if (filteredPairings.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="empty-row">ไม่พบข้อมูลการจับคู่ที่ค้นหา</td></tr>';
                return;
            }

            filteredPairings.forEach(item => {
                let typeBadge = item.Type;
                if (item.Type === 'routing_ont_mesh') typeBadge = 'ONT + Mesh';
                if (item.Type === '2-box') typeBadge = '2-Box';
                
                tbody.innerHTML += `
                    <tr>
                        <td style="font-weight: 600;">${item.HGW}</td>
                        <td style="color: var(--text-secondary);">${item.SubDevice}</td>
                        <td><span class="table-badge ${item.Type.replace('-','')}">${typeBadge}</span></td>
                        <td style="font-weight: 500; text-align: right; padding-right: 30px;">${Number(item.Count).toLocaleString()}</td>
                        <td style="color: var(--text-secondary); text-align: right; padding-right: 30px;">${Number(item.Percentage).toFixed(3)}%</td>
                    </tr>
                `;
            });
        }

        function renderRolesTable() {
            const tbody = document.getElementById('roles-table-body');
            tbody.innerHTML = '';
            
            if (filteredRoles.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" class="empty-row">ไม่พบข้อมูลโมเดลที่ค้นหา</td></tr>';
                return;
            }

            filteredRoles.forEach(item => {
                tbody.innerHTML += `
                    <tr>
                        <td style="font-weight: 600;">${item.ProductClass}</td>
                        <td><span class="table-badge ${item.Type.toLowerCase()}">${item.Type}</span></td>
                        <td style="font-weight: 500; text-align: right; padding-right: 30px;">${Number(item.TotalDevices).toLocaleString()}</td>
                        <td style="color: var(--text-secondary); text-align: right; padding-right: 30px;">${Number(item.Share).toFixed(2)}%</td>
                    </tr>
                `;
            });
        }

        function renderFttrTable() {
            const tbody = document.getElementById('fttr-table-body');
            tbody.innerHTML = '';
            
            if (filteredFttr.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" class="empty-row">ไม่พบข้อมูลเกตเวย์ที่ค้นหา</td></tr>';
                return;
            }

            filteredFttr.forEach(item => {
                let potBadge = 'Medium';
                if (item.HouseholdCount >= 1000) potBadge = 'Extreme (บ้านกลุ่มเป้าหมายใหญ่)';
                else if (item.HouseholdCount >= 100) potBadge = 'High';
                
                tbody.innerHTML += `
                    <tr>
                        <td style="font-weight: 600;">${item.HGW}</td>
                        <td style="font-weight: 500; text-align: right; padding-right: 60px;">${Number(item.HouseholdCount).toLocaleString()}</td>
                        <td style="color: var(--text-secondary); text-align: right; padding-right: 60px;">${Number(item.Share).toFixed(2)}%</td>
                        <td><span class="table-badge potential">${potBadge}</span></td>
                    </tr>
                `;
            });
        }

        // Search Control
        function onSearchInput() {
            const q = document.getElementById('tableSearch').value.toLowerCase().trim();
            
            if (currentTab === 'pairings') {
                if (!q) {
                    filteredPairings = [...dashboardData.top_pairings];
                } else {
                    filteredPairings = dashboardData.top_pairings.filter(item => 
                        item.HGW.toLowerCase().includes(q) || 
                        item.SubDevice.toLowerCase().includes(q) || 
                        item.Type.toLowerCase().includes(q)
                    );
                }
                renderPairingsTable();
            } else if (currentTab === 'roles') {
                let fullRoleList = [];
                if (currentRoleSubTab === 'HGW') fullRoleList = dashboardData.top_hgw_models;
                else if (currentRoleSubTab === 'Mesh') fullRoleList = dashboardData.top_mesh_models;
                else fullRoleList = dashboardData.top_ap_models;
                
                if (!q) {
                    filteredRoles = [...fullRoleList];
                } else {
                    filteredRoles = fullRoleList.filter(item => 
                        item.ProductClass.toLowerCase().includes(q)
                    );
                }
                renderRolesTable();
            } else {
                if (!q) {
                    filteredFttr = [...dashboardData.fttr_leads_profile];
                } else {
                    filteredFttr = dashboardData.fttr_leads_profile.filter(item => 
                        item.HGW.toLowerCase().includes(q)
                    );
                }
                renderFttrTable();
            }
        }

        // Sorting
        function sortTabTable(tabName, colIdx) {
            const dir = sortDirections[tabName][colIdx];
            sortDirections[tabName][colIdx] = -dir; // toggle next

            if (tabName === 'pairings') {
                filteredPairings.sort((a, b) => {
                    let valA, valB;
                    if (colIdx === 0) { valA = a.HGW; valB = b.HGW; }
                    else if (colIdx === 1) { valA = a.SubDevice; valB = b.SubDevice; }
                    else if (colIdx === 2) { valA = a.Type; valB = b.Type; }
                    else if (colIdx === 3) { valA = a.Count; valB = b.Count; }
                    else { valA = a.Percentage; valB = b.Percentage; }

                    if (typeof valA === 'string') {
                        return valA.localeCompare(valB) * dir;
                    }
                    return (valA - valB) * dir;
                });
                renderPairingsTable();
            } else if (tabName === 'roles') {
                filteredRoles.sort((a, b) => {
                    let valA, valB;
                    if (colIdx === 0) { valA = a.ProductClass; valB = b.ProductClass; }
                    else if (colIdx === 1) { valA = a.Type; valB = b.Type; }
                    else if (colIdx === 2) { valA = a.TotalDevices; valB = b.TotalDevices; }
                    else { valA = a.Share; valB = b.Share; }

                    if (typeof valA === 'string') {
                        return valA.localeCompare(valB) * dir;
                    }
                    return (valA - valB) * dir;
                });
                renderRolesTable();
            } else if (tabName === 'fttr') {
                filteredFttr.sort((a, b) => {
                    let valA, valB;
                    if (colIdx === 0) { valA = a.HGW; valB = b.HGW; }
                    else if (colIdx === 1) { valA = a.HouseholdCount; valB = b.HouseholdCount; }
                    else { valA = a.Share; valB = b.Share; }

                    if (typeof valA === 'string') {
                        return valA.localeCompare(valB) * dir;
                    }
                    return (valA - valB) * dir;
                });
                renderFttrTable();
            }
        }

        // Render charts
        function renderCharts() {
            const ctxPairing = document.getElementById('pairingChart').getContext('2d');
            const ctxDevCount = document.getElementById('devCountChart').getContext('2d');

            // Pairing Chart
            const dist = dashboardData.pairing_types_dist;
            new Chart(ctxPairing, {
                type: 'bar',
                data: {
                    labels: ['ONT + Mesh', '2-Box (Legacy + AP)', 'as_mesh (Same Model)', 'Other Pairing'],
                    datasets: [{
                        label: 'จำนวนชุดติดตั้ง (คู่)',
                        data: [dist.routing_ont_mesh, dist['2-box'], dist.as_mesh, dist.other_pairing],
                        backgroundColor: ['#6366f1', '#8b5cf6', '#06b6d4', '#f43f5e'],
                        borderColor: ['rgba(99, 102, 241, 0.4)', 'rgba(139, 92, 246, 0.4)', 'rgba(6, 182, 212, 0.4)', 'rgba(244, 63, 94, 0.4)'],
                        borderWidth: 1,
                        borderRadius: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const val = context.raw;
                                    const total = dist.routing_ont_mesh + dist['2-box'] + dist.as_mesh + dist.other_pairing;
                                    const pct = (val / total) * 100;
                                    return ` ${val.toLocaleString()} คู่อุปกรณ์ (${pct.toFixed(2)}%)`;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { color: 'rgba(255,255,255,0.04)' },
                            ticks: { color: '#9ca3af' }
                        },
                        x: {
                            grid: { display: false },
                            ticks: { color: '#9ca3af', font: { family: 'Outfit' } }
                        }
                    }
                }
            });

            // Device count distribution per subscriber
            const dd = dashboardData.household_devices_dist;
            new Chart(ctxDevCount, {
                type: 'pie',
                data: {
                    labels: ['1 Device', '2 Devices', '3+ Devices (FTTR Candidates)'],
                    datasets: [{
                        data: [dd['1_device'], dd['2_devices'], dd['3_plus_devices']],
                        backgroundColor: ['#10b981', '#6366f1', '#f59e0b'],
                        borderWidth: 0
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
                                font: { family: 'Outfit', size: 12 },
                                boxWidth: 12
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const val = context.raw;
                                    const total = dd['1_device'] + dd['2_devices'] + dd['3_plus_devices'];
                                    const pct = (val / total) * 100;
                                    return ` ${val.toLocaleString()} ครัวเรือน (${pct.toFixed(2)}%)`;
                                }
                            }
                        }
                    }
                }
            });
        }

        // Excel Export
        function exportDataExcel() {
            let exportHeaders = [];
            let exportRows = [];
            let filename = '';

            if (currentTab === 'pairings') {
                exportHeaders = ["HGW Model (กล่องหลัก)", "Secondary Model (กล่องเสริม)", "Pairing Type", "Count (จำนวน)", "Percentage (%)"];
                exportRows = filteredPairings.map(item => [item.HGW, item.SubDevice, item.Type, item.Count, item.Percentage]);
                filename = 'CPE_Pairing_Models_Breakdown';
            } else if (currentTab === 'roles') {
                exportHeaders = ["Product Class", "Network Role", "Total Devices", "Share of Role (%)"];
                exportRows = filteredRoles.map(item => [item.ProductClass, item.Type, item.TotalDevices, item.Share]);
                filename = `CPE_Device_Role_${currentRoleSubTab}`;
            } else {
                exportHeaders = ["HGW Model (กล่องหลัก)", "Candidate Households (จำนวนบ้าน)", "Share of Leads Pool (%)"];
                exportRows = filteredFttr.map(item => [item.HGW, item.HouseholdCount, item.Share]);
                filename = 'CPE_FTTR_Lead_Opportunities';
            }

            const worksheetData = [exportHeaders, ...exportRows];
            const wb = XLSX.utils.book_new();
            const ws = XLSX.utils.aoa_to_sheet(worksheetData);
            XLSX.utils.book_append_sheet(wb, ws, "Data");
            
            const dateStr = new Date().toISOString().slice(0, 10);
            XLSX.writeFile(wb, `${filename}_${dateStr}.xlsx`);
        }
    </script>
</body>
</html>
"""

    # Inject JSON data into template
    html_output = html_template.replace('{data_json}', data_json)
    
    print(f"Writing dashboard HTML to {html_path}...")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_output)
        
    print("Dashboard build complete!")

if __name__ == "__main__":
    main()
