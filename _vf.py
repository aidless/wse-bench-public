def mul(a,b):
    return [
        (a[0]*b[0]+a[1]*b[2])%10000,
        (a[0]*b[1]+a[1]*b[3])%10000,
        (a[2]*b[0]+a[3]*b[2])%10000,
        (a[2]*b[1]+a[3]*b[3])%10000,
    ]
def fib_matrix(n):
    m=[1,1,1,0]; r=[1,0,0,1]; e=n-1
    while e>0:
        if e&1: r=mul(r,m)
        m=mul(m,m); e>>=1
    return r[0]
v=fib_matrix(120)
print("T059 fib(120)%10000 =", v, "OK" if v==1840 else "MISMATCH")

x=175971
print("T060 checks:", x%97==13, x%101==29, x%103==47, "OK" if (x%97==13 and x%101==29 and x%103==47) else "MISMATCH")
