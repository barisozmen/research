"""
Cryptographic Utilities for FHE Milestones
Common functions used across different FHE implementations

Educational implementation by Peter Norvig style
"""

import random
from math import gcd
from typing import Tuple


def is_prime(n: int, k: int = 20) -> bool:
    """
    Miller-Rabin primality test
    
    Args:
        n: Number to test for primality
        k: Number of rounds (higher = more accurate)
    
    Returns:
        True if n is probably prime, False if composite
    """
    if n < 2: 
        return False
    if n == 2 or n == 3: 
        return True
    if n % 2 == 0: 
        return False
    
    # Write n-1 as d * 2^r
    r = 0
    d = n - 1
    while d % 2 == 0:
        d //= 2
        r += 1
    
    # Miller-Rabin test
    for _ in range(k):
        a = random.randrange(2, n - 1)
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def generate_prime(bits: int) -> int:
    """
    Generate a random prime of specified bit length
    
    Args:
        bits: Desired bit length of the prime
    
    Returns:
        A random prime number of the specified bit length
    """
    while True:
        candidate = random.getrandbits(bits) | (1 << bits - 1) | 1
        if is_prime(candidate):
            return candidate


def extended_gcd(a: int, b: int) -> Tuple[int, int, int]:
    """
    Extended Euclidean algorithm
    
    Args:
        a, b: Integers
    
    Returns:
        Tuple (gcd, x, y) such that ax + by = gcd(a, b)
    """
    if a == 0:
        return b, 0, 1
    gcd_val, x1, y1 = extended_gcd(b % a, a)
    x = y1 - (b // a) * x1
    y = x1
    return gcd_val, x, y


def mod_inverse(a: int, m: int) -> int:
    """
    Compute modular inverse of a modulo m
    
    Args:
        a: Number to find inverse of
        m: Modulus
    
    Returns:
        x such that (a * x) ≡ 1 (mod m)
    
    Raises:
        ValueError: If modular inverse does not exist
    """
    gcd_val, x, _ = extended_gcd(a, m)
    if gcd_val != 1:
        raise ValueError("Modular inverse does not exist")
    return (x % m + m) % m


def lcm(a: int, b: int) -> int:
    """
    Compute least common multiple of two integers
    
    Args:
        a, b: Integers
    
    Returns:
        LCM of a and b
    """
    return abs(a * b) // gcd(a, b)


def jacobi_symbol(a: int, n: int) -> int:
    """
    Compute Jacobi symbol (a/n)
    
    Args:
        a: Numerator
        n: Denominator (must be odd)
    
    Returns:
        Jacobi symbol value (-1, 0, or 1)
    """
    if gcd(a, n) != 1:
        return 0
    
    result = 1
    a = a % n
    
    while a != 0:
        while a % 2 == 0:
            a //= 2
            if n % 8 in [3, 5]:
                result = -result
        
        a, n = n, a
        if a % 4 == 3 and n % 4 == 3:
            result = -result
        a = a % n
    
    return result if n == 1 else 0


def find_quadratic_non_residue(n: int) -> int:
    """
    Find a quadratic non-residue modulo n
    
    Args:
        n: Modulus
    
    Returns:
        Integer x such that x is a quadratic non-residue mod n
    """
    while True:
        x = random.randrange(2, n)
        if gcd(x, n) == 1 and jacobi_symbol(x, n) == -1:
            return x
