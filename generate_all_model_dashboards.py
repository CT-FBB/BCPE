import subprocess
import os
import shutil
import time

def run_in_parallel(scripts):
    print(f"Starting {len(scripts)} scripts in parallel...")
    start = time.time()
    processes = []
    for s in scripts:
        print(f"🚀 Spawning: {s}")
        p = subprocess.Popen(["python3", s], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        processes.append((s, p))

    # Wait for all processes to complete
    for s, p in processes:
        stdout, stderr = p.communicate()
        duration = time.time() - start
        if p.returncode == 0:
            print(f"✅ Finished: {s} ({duration:.1f}s)")
        else:
            print(f"❌ Failed: {s} ({duration:.1f}s)")
            print(stderr)

def run_sequentially(scripts):
    for s in scripts:
        print(f"Running: {s}")
        start = time.time()
        res = subprocess.run(["python3", s], capture_output=True, text=True)
        duration = time.time() - start
        if res.returncode == 0:
            print(f"✅ Success ({duration:.1f}s)")
        else:
            print(f"❌ Failed ({duration:.1f}s)")
            print(res.stderr)

def main():
    scrip_dir = "/Users/bbae/GPTCodex/scrip"
    gpt_root = "/Users/bbae/GPTCodex"
    bcpe_dir = "/Users/bbae/BCPE/onu_model"

    # Step 1: Run dashboard data generation in parallel (CPU-heavy sheet loading)
    dash_scripts = [
        os.path.join(scrip_dir, "full_onu_diff_report.py"),
        os.path.join(scrip_dir, "generate_f688_dashboard_data.py"),
        os.path.join(scrip_dir, "generate_gn542vf_dashboard_data.py"),
        os.path.join(scrip_dir, "generate_hg8247w_dashboard_data.py")
    ]
    run_in_parallel(dash_scripts)

    # Step 2: Run trend computations sequentially
    trend_scripts = [
        os.path.join(scrip_dir, "compute_st244f_trends.py"),
        os.path.join(scrip_dir, "compute_f688_trends.py"),
        os.path.join(scrip_dir, "compute_gn542vf_trends.py"),
        os.path.join(scrip_dir, "compute_hg8247w_trends.py"),
        os.path.join(scrip_dir, "update_st244f_trend.py")
    ]
    run_sequentially(trend_scripts)

    # Step 3: Copy files to BCPE directory
    json_files = [
        "st244f_dashboard_data.json",
        "st244f_trend_data.json",
        "f688_dashboard_data.json",
        "f688_trend_data.json",
        "gn542vf_dashboard_data.json",
        "gn542vf_trend_data.json",
        "hg8247w_dashboard_data.json",
        "hg8247w_trend_data.json",
        "onu_dashboard_data.json",
        "onu_raw_changes.json"
    ]

    print("Copying updated JSON files to BCPE...")
    os.makedirs(bcpe_dir, exist_ok=True)
    copied_count = 0
    for jfile in json_files:
        src = os.path.join(gpt_root, jfile)
        if not os.path.exists(src):
            src = os.path.join(scrip_dir, jfile)
            
        if os.path.exists(src):
            dest = os.path.join(bcpe_dir, jfile)
            shutil.copy2(src, dest)
            print(f"✅ Copied {jfile} to BCPE")
            copied_count += 1
        else:
            print(f"⚠️ Source file not found: {jfile}")

    print(f"All done! Copied {copied_count} files to BCPE.")

if __name__ == "__main__":
    main()
