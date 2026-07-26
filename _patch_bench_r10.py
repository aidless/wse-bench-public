# -*- coding: utf-8 -*-
"""第十轮进化：把 T047-T060（cohort=2026Q3-hard）写入 build_bench.py"""
src = open('build_bench.py', encoding='utf-8').read()

ANCHOR = "请务必在最后一行以\u201c最终答案：xxx\u201d的格式（全角冒号）写出纯数字答案（不含逗号分隔符）。"

def task(tid, split, source, prompt, ans, reference):
    return (
        '    {"id": "%s", "split": "%s",\n'
        '     "source": "%s", "version": "hard-2026Q3-v1",\n'
        '     "prompt": "%s%s",\n'
        '     "rubric": {"type": "contains", "required": ["最终答案：%s"]},\n'
        '     "reference": "%s"},\n'
    ) % (tid, split, source, prompt, ANCHOR, ans, reference)

header = """
    # ---------- HARD 计算难题集（T047-T060，2026-07-24 第十轮进化，cohort=2026Q3-hard）----------
    # 目的：第九轮 2026Q3-reason 批直答即满分（无 headroom）→ 按 v9 headroom 预检铁律，
    #       本批先经 K=3 直答盲测预检：模幂/阶乘位数和/区间素数计数三族确认直答会滑错或拒答
    #       → 有真 headroom。ground truth 全部来自可复跑 python 命令（记录于 source）。
    #       评分锚定"最终答案：xxx"格式，防短数字误命中中间步骤（仪器假阳性）。
"""

tasks_new = [
    ("T047","dev","python: pow(3,200,9973) → 3136（可复跑）",
     "计算 3^200 mod 9973（9973 是素数）。","3136",
     "反复平方取模。python 复跑 pow(3,200,9973)=3136。"),
    ("T048","dev","python: pow(7,131,8191) → 5409（可复跑）",
     "计算 7^131 mod 8191（8191 是素数）。","5409",
     "python 复跑 pow(7,131,8191)=5409。"),
    ("T049","hidden","python: pow(5,177,7919) → 5471（可复跑）",
     "计算 5^177 mod 7919（7919 是素数）。","5471",
     "python 复跑 pow(5,177,7919)=5471。"),
    ("T050","hidden","python: pow(11,99,4999) → 1408（可复跑）",
     "计算 11^99 mod 4999（4999 是素数）。","1408",
     "python 复跑 pow(11,99,4999)=1408。"),
    ("T051","dev","python: digitsum(77!) → 432（可复跑）",
     "求 77!（77 的阶乘）的十进制表示中各位数字之和。","432",
     "python 复跑 sum(int(d) for d in str(math.factorial(77)))=432。"),
    ("T052","dev","python: digitsum(66!) → 351（可复跑）",
     "求 66!（66 的阶乘）的十进制表示中各位数字之和。","351",
     "python 复跑 digitsum(66!)=351。"),
    ("T053","hidden","python: digitsum(59!) → 324（可复跑）",
     "求 59!（59 的阶乘）的十进制表示中各位数字之和。","324",
     "python 复跑 digitsum(59!)=324。"),
    ("T054","hidden","python: digitsum(88!) → 531（可复跑）",
     "求 88!（88 的阶乘）的十进制表示中各位数字之和。","531",
     "python 复跑 digitsum(88!)=531。"),
    ("T055","dev","python: 素数计数(5001..5599) → 69（可复跑）",
     "5000 到 5600 之间（开区间，不含端点）有多少个素数？","69",
     "python 复跑 sum(1 for x in range(5001,5600) if isprime(x))=69。"),
    ("T056","dev","python: 素数计数(3001..3599) → 73（可复跑）",
     "3000 到 3600 之间（开区间，不含端点）有多少个素数？","73",
     "python 复跑 =73。"),
    ("T057","hidden","python: 素数计数(7001..7499) → 50（可复跑）",
     "7000 到 7500 之间（开区间，不含端点）有多少个素数？","50",
     "python 复跑 =50。"),
    ("T058","hidden","python: 素数计数(2001..2499) → 64（可复跑）",
     "2000 到 2500 之间（开区间，不含端点）有多少个素数？","64",
     "python 复跑 =64。"),
    ("T059","dev","python: 迭代 F(120) mod 10000 → 1840（可复跑；F(1)=F(2)=1）",
     "斐波那契数列 F(1)=1, F(2)=1, F(n)=F(n-1)+F(n-2)。求 F(120) 除以 10000 的余数。","1840",
     "F(120)=5358359254990966640871840，mod 10000=1840。python 迭代可复跑。"),
    ("T060","hidden","python: 穷举 CRT x≡13(97),29(101),47(103) → 175971（可复跑）",
     "求最小正整数 x，满足：x 除以 97 余 13，x 除以 101 余 29，x 除以 103 余 47。","175971",
     "CRT 唯一解 mod 97*101*103=1009091；最小正整数 175971。python 穷举可复跑。"),
]

block = header + "".join(task(*t) for t in tasks_new) + "]"

OLD_TAIL = '     "reference": "相向合速度 50+70=120 km/h；相遇用时 300/120=2.5 h；甲行 50×2.5=125 km。"},\n]'
NEW_TAIL = '     "reference": "相向合速度 50+70=120 km/h；相遇用时 300/120=2.5 h；甲行 50×2.5=125 km。"},\n' + block
assert OLD_TAIL in src, "tail not found"
src = src.replace(OLD_TAIL, NEW_TAIL)

OLD_C = 'REASON_IDS = {"T041", "T042", "T043", "T044", "T045", "T046"}\nfor t in tasks:\n    if t["id"] in REASON_IDS:'
NEW_C = ('REASON_IDS = {"T041", "T042", "T043", "T044", "T045", "T046"}\n'
         'HARD_IDS = {"T047", "T048", "T049", "T050", "T051", "T052", "T053",\n'
         '            "T054", "T055", "T056", "T057", "T058", "T059", "T060"}\n'
         'for t in tasks:\n'
         '    if t["id"] in HARD_IDS:\n'
         '        t["cohort"] = "2026Q3-hard"     # 第十轮：headroom 预检通过的计算难题批\n'
         '    elif t["id"] in REASON_IDS:')
assert OLD_C in src, "cohort block not found"
src = src.replace(OLD_C, NEW_C)

OLD_CAP = '"T044": "reasoning", "T045": "reasoning", "T046": "reasoning",'
NEW_CAP = ('"T044": "reasoning", "T045": "reasoning", "T046": "reasoning",\n'
           '    "T047": "reasoning", "T048": "reasoning", "T049": "reasoning",\n'
           '    "T050": "reasoning", "T051": "reasoning", "T052": "reasoning",\n'
           '    "T053": "reasoning", "T054": "reasoning", "T055": "reasoning",\n'
           '    "T056": "reasoning", "T057": "reasoning", "T058": "reasoning",\n'
           '    "T059": "reasoning", "T060": "reasoning",')
assert OLD_CAP in src, "cap map not found"
src = src.replace(OLD_CAP, NEW_CAP)

OLD_A = '"active_cohorts": ["2026Q3-core", "2026Q3-ext", "2026Q3-reason"],'
NEW_A = '"active_cohorts": ["2026Q3-core", "2026Q3-ext", "2026Q3-reason", "2026Q3-hard"],'
assert OLD_A in src, "active_cohorts not found"
src = src.replace(OLD_A, NEW_A)

open('build_bench.py', 'w', encoding='utf-8').write(src)
print("build_bench.py patched: +14 tasks (T047-T060), cohort 2026Q3-hard")
