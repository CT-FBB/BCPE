import subprocess
import os
import shutil
import time

def run_script(script_path):
    print(f"Running: {script_path}")
    start = time.time()
    res = subprocess.run(["python3", script_path], capture_output=True, text=True)
    duration = time.time() - start
    if res.returncode == 0:
        print(f"✅ Success ({duration:.1f}s)")
        print(res.stdout)
    else:
        print(f"❌ Failed ({duration:.1f}s)")
        print(res.stderr)
    return res.returncode == 0

def main():
    scrip_dir = "/Users/bbae/GPTCodex/scrip"
    gpt_root = "/Users/bbae/GPTCodex"
    bcpe_dir = "/Users/bbae/BCPE/onu_model"

    # Wait for the current running ST-244F script to finish if it is still running
    # (Checking via ps aux)
    print("Waiting for any existing compute_st244f_trends.py to finish...")
    while True:
        res = subprocess.run(["pgrep", "-f", "compute_st244f_trends.py"], capture_output=True)
        if res.returncode != 0:
            break
        print("Existing process still running... waiting 10s")
        time.sleep(10)

    # Run trend computation for other models
    run_script(os.path.join(scrip_dir, "compute_f688_trends.py"))
    run_script(os.path.join(scrip_dir, "compute_gn542vf_trends.py"))
    run_script(os.path.join(scrip_dir, "compute_hg8247w_trends.py"))
    run_script(os.path.join(scrip_dir, "update_st244f_trend.py"))

    # Copy files to BCPE directory
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
        # Some JSON files might be generated in scrip folder, check both
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
