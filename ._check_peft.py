"""Check if trl / peft are available."""
import sys
sys.path.insert(0, r'C:/Users/Administrator/.workbuddy/binaries/python/envs/default/lib/python3.13/site-packages')
sys.path.insert(0, r'F:/hf_cache/models')
try:
    import trl
    print('trl', trl.__version__)
except Exception as e:
    print('no trl:', e)
try:
    import peft
    print('peft', peft.__version__)
except Exception as e:
    print('no peft:', e)