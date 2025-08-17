"""
Ring Learning With Errors (RLWE) Based Somewhat Homomorphic Encryption
[2009] Ring-LWE: More efficient lattice-based cryptography using polynomial rings

Educational implementation by Peter Norvig style
"""

import random
import numpy as np
from typing import Tuple, List, NamedTuple
from math import sqrt, log
from rlwe_utils import (
    polynomial_mod, polynomial_mult, polynomial_add,
    gaussian_polynomial, uniform_polynomial, binary_polynomial,
    noise_estimate_basic
)


class RLWEKeys(NamedTuple):
    """RLWE key pair"""
    public_key: Tuple[np.ndarray, np.ndarray, int, int, float]  # (a, b, n, q, sigma)
    private_key: np.ndarray                                      # secret polynomial s


def KEYGEN(n: int = 128, q: int = 2**15, sigma: float = 3.2) -> RLWEKeys:
    """
    Generate RLWE key pair
    
    Args:
        n: Degree of polynomial ring (power of 2)
        q: Modulus (should be prime or power of 2)
        sigma: Standard deviation for Gaussian noise
    
    Returns:
        RLWEKeys with public key (a, b, n, q, sigma) and private key s
    """
    # Generate secret polynomial s with small coefficients
    s = binary_polynomial(n)  # Secret with binary coefficients
    
    # Generate random polynomial a
    a = uniform_polynomial(n, q)
    
    # Generate noise polynomial e
    e = gaussian_polynomial(n, sigma)
    
    # Compute b = -(a * s + e) mod q in the ring
    as_product = polynomial_mult(a, s, n, q)
    ase_sum = polynomial_add(as_product, e, q)
    b = (-ase_sum) % q
    
    return RLWEKeys(
        public_key=(a, b, n, q, sigma),
        private_key=s
    )


def ENC(message: int, public_key: Tuple[np.ndarray, np.ndarray, int, int, float]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Encrypt a message bit using RLWE
    
    Args:
        message: Plaintext bit (0 or 1)
        public_key: (a, b, n, q, sigma) tuple
    
    Returns:
        Ciphertext (u, v) where both are polynomials
    """
    if message not in [0, 1]:
        raise ValueError("RLWE encrypts only bits (0 or 1)")
    
    a, b, n, q, sigma = public_key
    
    # Choose random polynomial r with small coefficients
    r = binary_polynomial(n)
    
    # Generate noise polynomials
    e1 = gaussian_polynomial(n, sigma)
    e2 = gaussian_polynomial(n, sigma)
    
    # Compute u = a * r + e1
    ar_product = polynomial_mult(a, r, n, q)
    u = polynomial_add(ar_product, e1, q)
    
    # Compute v = b * r + e2 + message * floor(q/2)
    br_product = polynomial_mult(b, r, n, q)
    message_poly = np.zeros(n, dtype=int)
    message_poly[0] = message * (q // 2)  # Encode message in constant term
    
    v_temp = polynomial_add(br_product, e2, q)
    v = polynomial_add(v_temp, message_poly, q)
    
    return (u, v)


def DEC(ciphertext: Tuple[np.ndarray, np.ndarray], private_key: np.ndarray,
        public_key: Tuple[np.ndarray, np.ndarray, int, int, float]) -> int:
    """
    Decrypt a ciphertext using RLWE private key
    
    Args:
        ciphertext: (u, v) tuple of polynomials
        private_key: secret polynomial s
        public_key: (a, b, n, q, sigma) for parameters
    
    Returns:
        Plaintext bit (0 or 1)
    """
    u, v = ciphertext
    s = private_key
    a, b, n, q, sigma = public_key
    
    # Compute v + u * s
    us_product = polynomial_mult(u, s, n, q)
    decryption_poly = polynomial_add(v, us_product, q)
    
    # Extract message from constant term
    constant_term = decryption_poly[0] % q
    
    # Reduce to [-q/2, q/2)
    if constant_term >= q // 2:
        constant_term -= q
    
    # Decide based on distance to 0 vs q/2
    if abs(constant_term) < abs(constant_term - q//2):
        return 0
    else:
        return 1


def ADD(ciphertext1: Tuple[np.ndarray, np.ndarray], 
        ciphertext2: Tuple[np.ndarray, np.ndarray], 
        q: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Homomorphic addition: add two encrypted bits
    
    Args:
        ciphertext1: First encrypted bit
        ciphertext2: Second encrypted bit
        q: RLWE modulus
    
    Returns:
        Sum of ciphertexts
    """
    u1, v1 = ciphertext1
    u2, v2 = ciphertext2
    
    u_sum = polynomial_add(u1, u2, q)
    v_sum = polynomial_add(v1, v2, q)
    
    return (u_sum, v_sum)


def MUL(ciphertext1: Tuple[np.ndarray, np.ndarray], 
        ciphertext2: Tuple[np.ndarray, np.ndarray], 
        n: int, q: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Homomorphic multiplication (simplified - increases noise significantly)
    
    Args:
        ciphertext1: First encrypted bit
        ciphertext2: Second encrypted bit
        n: Polynomial degree
        q: RLWE modulus
    
    Returns:
        Product approximation (high noise)
    """
    u1, v1 = ciphertext1
    u2, v2 = ciphertext2
    
    # Simplified multiplication (not cryptographically optimal)
    # Real RLWE multiplication requires key switching and more sophisticated noise management
    
    # Approximate multiplication by tensor product approach
    u_prod = polynomial_mult(u1, v2, n, q)  # Simplified
    v_prod = polynomial_mult(v1, v2, n, q)
    
    return (u_prod, v_prod)


def noise_estimate(ciphertext: Tuple[np.ndarray, np.ndarray], 
                   private_key: np.ndarray, message: int, 
                   public_key: Tuple[np.ndarray, np.ndarray, int, int, float]) -> float:
    """Estimate noise level in RLWE ciphertext"""
    return noise_estimate_basic(ciphertext, private_key, message, public_key)


def demonstrate_rlwe():
    """Demonstrate RLWE cryptosystem with somewhat homomorphic encryption"""
    print("🔐 RLWE-based Somewhat Homomorphic Encryption")
    print("=" * 55)
    
    # Generate keys
    print("📋 Generating RLWE keys...")
    n, q, sigma = 64, 2**12, 2.0  # Smaller parameters for demo
    keys = KEYGEN(n, q, sigma)
    a, b, n_pub, q_pub, sigma_pub = keys.public_key
    s = keys.private_key
    
    print(f"📊 Parameters: n={n}, q={q}, σ={sigma}")
    print(f"🔑 Secret polynomial degree: {len(s)}")
    print(f"📏 Public polynomials degree: {len(a)}")
    print()
    
    # Test basic encryption/decryption
    print("🧪 Testing basic encryption/decryption:")
    m1, m2 = 1, 0
    c1 = ENC(m1, keys.public_key)
    c2 = ENC(m2, keys.public_key)
    
    d1 = DEC(c1, keys.private_key, keys.public_key)
    d2 = DEC(c2, keys.private_key, keys.public_key)
    
    print(f"   Message 1: {m1}")
    print(f"   Decrypted: {d1}")
    print(f"   Noise estimate: {noise_estimate(c1, s, m1, keys.public_key)}")
    print()
    
    print(f"   Message 2: {m2}")
    print(f"   Decrypted: {d2}")
    print(f"   Noise estimate: {noise_estimate(c2, s, m2, keys.public_key)}")
    print()
    
    # Demonstrate homomorphic addition
    print("✨ Demonstrating homomorphic addition:")
    print(f"   m1 = {m1}, m2 = {m2}")
    print(f"   m1 ⊕ m2 = {m1 ^ m2}")
    print()
    
    c_add = ADD(c1, c2, q)
    m_add = DEC(c_add, keys.private_key, keys.public_key)
    
    print(f"   ADD(ENC(m1), ENC(m2)) decrypts to: {m_add}")
    print(f"   Noise estimate after addition: {noise_estimate(c_add, s, m1^m2, keys.public_key)}")
    
    success_add = (m1 ^ m2) == m_add
    print(f"✅ Homomorphic addition verified: {success_add}")
    print()
    
    # Demonstrate homomorphic multiplication
    print("⚠️  Demonstrating homomorphic multiplication (simplified):")
    c_mul = MUL(c1, c2, n, q)
    m_mul = DEC(c_mul, keys.private_key, keys.public_key)
    
    print(f"   m1 ∧ m2 = {m1 & m2}")
    print(f"   MUL(ENC(m1), ENC(m2)) decrypts to: {m_mul}")
    print(f"   Noise estimate after multiplication: {noise_estimate(c_mul, s, m1&m2, keys.public_key)}")
    
    success_mul = (m1 & m2) == m_mul
    print(f"✅ Homomorphic multiplication: {success_mul}")
    print()
    
    if not success_mul:
        print("   ⚠️  Note: Multiplication may fail due to noise growth!")
        print("   This simplified implementation doesn't use proper key switching.")
    
    # Show polynomial structure
    print("🔍 Examining polynomial structure:")
    u1, v1 = c1
    print(f"   Ciphertext u polynomial (first 8 coeffs): {u1[:8]}")
    print(f"   Ciphertext v polynomial (first 8 coeffs): {v1[:8]}")
    print(f"   Secret polynomial (first 8 coeffs): {s[:8]}")
    print()
    
    # Demonstrate RLWE efficiency advantage
    print("⚡ RLWE Efficiency Advantages:")
    print("   • Packs n bits into one ciphertext polynomial")
    print("   • More efficient than standard LWE")
    print("   • Enables SIMD (Single Instruction, Multiple Data) operations")
    print("   • Foundation for modern FHE schemes (BGV, BFV, CKKS)")


if __name__ == "__main__":
    demonstrate_rlwe()
