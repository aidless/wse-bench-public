import math, sympy

# 独立复核：用循环取模法验证幂模
def pow_mod_loop(a, e, m):
    r = 1
    for _ in range(e):
        r = (r * a) % m
    return r

# 独立复核：用 sympy 大整数直接取模
def pow_mod_direct(a, e, m):
    return pow(a, e) % m

checks = []
checks.append(("T047", pow_mod_loop(3,200,9973), pow_mod_direct(3,200,9973)))
checks.append(("T048", pow_mod_loop(7,131,8191), pow_mod_direct(7,131,8191)))
checks.append(("T049", pow_mod_loop(5,177,7919), pow_mod_direct(5,177,7919)))
checks.append(("T050", pow_mod_loop(11,99,4999), pow_mod_direct(11,99,4999)))

for name, lo, di in checks:
    print(name, "loop=", lo, "direct=", di, "OK" if lo==di else "MISMATCH")

# 阶乘各位和：独立再算一次
for n, expect in [(77,432),(66,351),(59,324),(88,531)]:
    s = sum(int(c) for c in str(math.factorial(n)))
    print(f"digit-sum {n} =", s, "OK" if s==expect else "MISMATCH")

# 素数计数：独立用另一种判定（试除法）复核区间
def is_prime_trial(n):
    if n < 2: return False
    if n%2==0: return n==2
    i=3
    while i*i<=n:
        if n%i==0: return False
        i+=2
    return True

for lo,hi,expect in [(5000,5600,69),(3000,3600,73),(7000,7500,50),(2000,2500,64)]:
    c = sum(1 for x in range(lo+1,hi) if is_prime_trial(x))
    print(f"primes ({lo},{hi}) =", c, "OK" if c==expect else "MISMATCH")

# 斐波那契：独立用矩阵法
def fib_matrix(n):
    def mul(a,b):
        return [(a[0][0]*b[0][0]+a[0][1]*b[1][0])%10000,
                (a[0][0]*b[0][1]+a[0][1]*b[1][1])%10000,
                (a[1][0]*b[0][0]+a[1][1]*b[1][0])%10000,
                (a[1][0]*b[0][1]+a[1][1]*b[1][1])%10000]
    m=[[1,1],[1,0]]; r=[[1,0],[0,1]]
    e=n-1
    while e>0:
        if e&1: r=mul(r,m)
        m=mul(m,m); e>>=1
    return r[0][0]
print("T059 fib(120)%10000 =", fib_matrix(120), "OK" if fib_matrix(120)==1840 else "MISMATCH")

# CRT 复核：验证 x 满足三式
x=175971
print("T060 checks:", x%97==13, x%101==29, x%103==47)
