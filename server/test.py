# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

def feb(m):
    if m==1:
        return 0
    elif m==2:
        return 1
    return feb(m-1)+feb(m-2)

def fib2(max):
    n, a, b, sum2 = 0, 0, 1, 0
    while n < max:
        print(a)
        sum2+=a
        a, b = b, a + b
        n = n + 1
        
    return sum2
 
m=int(input('输入项数:'))
print('斐波那契数列前',m,'项和为',sum(feb(i) for i in range(1,m+1)))
print('递归：斐波那契数列前',m,'项和为',sum(map(feb,range(1,m+1))))
print('迭代：斐波那契数列前',m,'项和为',fib2(m))
        