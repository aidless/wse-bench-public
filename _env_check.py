"""环境检查脚本：GPU + Python deps + 磁盘。"""
import subprocess
import sys
import os
import shutil

print("=== Python ===")
print(f"version: {sys.version}")

print()
print("=== GPU ===")
try:
    out = subprocess.run(
        ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
        capture_output=True, text=True, timeout=10,
    )
    print(out.stdout.strip() or "no GPU detected")
except Exception as e:
    print(f"nvidia-smi not available: {e}")

print()
print("=== Disk ===")
for drive in ["C", "D", "F"]:
    path = drive + ":\\"
    try:
        u = shutil.disk_usage(path)
        free_gb = u.free / 1e9
        total_gb = u.total / 1e9
        print(f"  {drive}: free {free_gb:.1f} GB / total {total_gb:.1f} GB")
    except Exception as e:
        print(f"  {drive}: error {e}")

print()
print("=== Python deps ===")
for pkg in ["torch", "transformers", "peft", "trl", "bitsandbytes", "accelerate"]:
    try:
        m = __import__(pkg)
        v = getattr(m, "__version__", "unknown")
        print(f"  {pkg}: {v}")
    except Exception as e:
        print(f"  {pkg}: NOT installed ({e})")

print()
print("=== HF cache ===")
hf_home = os.environ.get("HF_HOME", "(unset, default ~/.cache/huggingface)")
print(f"  HF_HOME: {hf_home}")
print(f"  HF_HUB_CACHE: {os.environ.get('HF_HUB_CACHE', '(unset)')}")
print(f"  TRANSFORMERS_CACHE: {os.environ.get('TRANSFORMERS_CACHE', '(unset)')}")
