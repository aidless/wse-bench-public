"""下载 Qwen2.5-3B-Instruct 到 F:/hf_cache（用户环境已重定向）。
HF Hub 在国内被墙 → hf-mirror.com 也被 xet 401 → 改用 ModelScope 镜像。"""
import os
os.environ["HF_HOME"] = r"F:\hf_cache"
os.environ["TRANSFORMERS_CACHE"] = r"F:\hf_cache"

from modelscope import snapshot_download
import time

print("开始下载 Qwen2.5-3B-Instruct (via ModelScope)...")
t0 = time.time()
local_path = snapshot_download(
    "Qwen/Qwen2.5-3B-Instruct",
    cache_dir=r"F:\hf_cache",
    allow_patterns=["*.json", "*.safetensors", "tokenizer.*", "*.txt"],
)
print(f"下载完成 ({time.time()-t0:.0f}s)")
print(f"本地路径: {local_path}")
print()
total = 0
for root, _, files in os.walk(local_path):
    for f in files:
        fp = os.path.join(root, f)
        try:
            total += os.path.getsize(fp)
        except OSError:
            pass
print(f"总大小: {total/1e9:.2f} GB")
