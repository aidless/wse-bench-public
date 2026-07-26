import math
from functools import reduce
import sympy

def pmod(a, e, m):
    return pow(a, e, m)

def dsum_fact(n):
    f = math.factorial(n)
    return sum(int(c) for c in str(f))

def count_primes(lo, hi):
    return sum(1 for x in range(lo+1, hi) if sympy.isprime(x))

def fib_mod(n, m):
    a, b = 1, 1
    for _ in range(3, n+1):
        a, b = b, (a+b) % m
    return b

def crt(rems, mods):
    M = reduce(lambda x,y: x*y, mods)
    x = 0
    for r, m in zip(rems, mods):
        Mi = M // m
        inv = pow(Mi, -1, m)
        x += r * Mi * inv
    return x % M

print("T047", pmod(3, 200, 9973))
print("T048", pmod(7, 131, 8191))
print("T049", pmod(5, 177, 7919))
print("T050", pmod(11, 99, 4999))
print("T051", dsum_fact(77))
print("T052", dsum_fact(66))
print("T053", dsum_fact(59))
print("T054", dsum_fact(88))
print("T055", count_primes(5000, 5600))
print("T056", count_primes(3000, 3600))
print("T057", count_primes(7000, 7500))
print("T058", count_primes(2000, 2500))
print("T059", fib_mod(120, 10000))
print("T060", crt([13,29,47],[97,101,103]))
