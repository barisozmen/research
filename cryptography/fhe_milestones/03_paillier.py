"""
Paillier Cryptosystem with Homomorphic Addition (mod n)
[1999] Probabilistic public-key cryptosystem with additive homomorphism

Educational implementation by Peter Norvig style
"""

import random
from math import gcd
from typing import Tuple, NamedTuple
from crypto_utils import is_prime, generate_prime, extended_gcd, mod_inverse, lcm


class PaillierKeys(NamedTuple):
    """Paillier key pair"""
    public_key: Tuple[int, int]   # (n, g)
    private_key: Tuple[int, int]  # (lambda, mu)


def L_function(x: int, n: int) -> int:
    """L(x) = (x - 1) / n"""
    return (x - 1) // n


def KEYGEN(bits: int = 512) -> PaillierKeys:
    """
    Generate Paillier key pair
    
    Args:
        bits: Bit length for each prime
    
    Returns:
        PaillierKeys with public key (n, g) and private key (lambda, mu)
    """
    # Generate two distinct primes
    p = generate_prime(bits)
    q = generate_prime(bits)
    while q == p:
        q = generate_prime(bits)
    
    n = p * q
    n_squared = n * n
    
    # λ = lcm(p-1, q-1)
    lambda_val = lcm(p - 1, q - 1)
    
    # Choose g (simple choice: g = n + 1)
    g = n + 1
    
    # Verify g has correct order
    # μ = (L(g^λ mod n²))^(-1) mod n
    g_lambda = pow(g, lambda_val, n_squared)
    mu = mod_inverse(L_function(g_lambda, n), n)
    
    return PaillierKeys(
        public_key=(n, g),
        private_key=(lambda_val, mu)
    )


def ENC(message: int, public_key: Tuple[int, int]) -> int:
    """
    Encrypt a message using Paillier public key
    
    Args:
        message: Plaintext integer (must be < n)
        public_key: (n, g) tuple
    
    Returns:
        Ciphertext c = g^m * r^n mod n²
    """
    n, g = public_key
    
    if message >= n or message < 0:
        raise ValueError(f"Message {message} must be in range [0, {n})")
    
    n_squared = n * n
    
    # Choose random r
    while True:
        r = random.randrange(1, n)
        if gcd(r, n) == 1:
            break
    
    # c = g^m * r^n mod n²
    return (pow(g, message, n_squared) * pow(r, n, n_squared)) % n_squared


def DEC(ciphertext: int, private_key: Tuple[int, int], public_key: Tuple[int, int]) -> int:
    """
    Decrypt a ciphertext using Paillier private key
    
    Args:
        ciphertext: Encrypted integer
        private_key: (lambda, mu) tuple
        public_key: (n, g) tuple
    
    Returns:
        Plaintext m = L(c^λ mod n²) * μ mod n
    """
    lambda_val, mu = private_key
    n, _ = public_key
    n_squared = n * n
    
    # m = L(c^λ mod n²) * μ mod n
    c_lambda = pow(ciphertext, lambda_val, n_squared)
    return (L_function(c_lambda, n) * mu) % n


def ADD(ciphertext1: int, ciphertext2: int, n_squared: int) -> int:
    """
    Homomorphic addition: add two encrypted values
    
    Property: ENC(m1) * ENC(m2) = ENC(m1 + m2) mod n²
    
    Args:
        ciphertext1: First encrypted value
        ciphertext2: Second encrypted value
        n_squared: n² (Paillier modulus squared)
    
    Returns:
        Product of ciphertexts (representing addition)
    """
    return (ciphertext1 * ciphertext2) % n_squared


def SCALAR_MUL(ciphertext: int, scalar: int, n_squared: int) -> int:
    """
    Homomorphic scalar multiplication
    
    Property: ENC(m)^k = ENC(k * m) mod n²
    
    Args:
        ciphertext: Encrypted value
        scalar: Plaintext scalar
        n_squared: n² (Paillier modulus squared)
    
    Returns:
        Ciphertext raised to scalar power
    """
    return pow(ciphertext, scalar, n_squared)


def demonstrate_paillier():
    """Demonstrate Paillier cryptosystem with homomorphic addition"""
    print("🔐 Paillier Cryptosystem with Homomorphic Addition")
    print("=" * 60)
    
    # Generate keys
    print("📋 Generating Paillier keys...")
    keys = KEYGEN(bits=256)  # Smaller for demo
    n, g = keys.public_key
    lambda_val, mu = keys.private_key
    n_squared = n * n
    
    print(f"📊 Public key:  (n={n}, g={g})")
    print(f"🔑 Private key: (λ={lambda_val}, μ={mu})")
    print()
    
    # Test basic encryption/decryption
    print("🧪 Testing basic encryption/decryption:")
    m1, m2 = 42, 17
    c1 = ENC(m1, keys.public_key)
    c2 = ENC(m2, keys.public_key)
    
    print(f"   Message 1: {m1}")
    print(f"   Encrypted: {c1}")
    print(f"   Decrypted: {DEC(c1, keys.private_key, keys.public_key)}")
    print()
    
    print(f"   Message 2: {m2}")
    print(f"   Encrypted: {c2}")
    print(f"   Decrypted: {DEC(c2, keys.private_key, keys.public_key)}")
    print()
    
    # Demonstrate homomorphic addition
    print("✨ Demonstrating homomorphic addition:")
    print(f"   m1 = {m1}, m2 = {m2}")
    print(f"   m1 + m2 = {m1 + m2}")
    print()
    
    # Add ciphertexts
    c_sum = ADD(c1, c2, n_squared)
    m_sum = DEC(c_sum, keys.private_key, keys.public_key)
    
    print(f"   ENC({m1}) = {c1}")
    print()
    print(f"   ENC({m2}) = {c2}")
    print()
    print(f"   ENC({m1}) × ENC({m2}) = {c_sum}")
    print()
    print(f"   DEC(ENC({m1}) × ENC({m2})) = {m_sum}")
    print()
    
    # Verify homomorphic property
    success = (m1 + m2) % n == m_sum
    print(f"✅ Homomorphic addition verified: {success}")
    print(f"   Expected: {(m1 + m2) % n}")
    print(f"   Got:      {m_sum}")
    print()
    
    # Demonstrate scalar multiplication
    print("🔢 Demonstrating homomorphic scalar multiplication:")
    scalar = 5
    m3 = 23
    c3 = ENC(m3, keys.public_key)
    
    print(f"   Message: {m3}")
    print(f"   Scalar:  {scalar}")
    print(f"   Expected: {(scalar * m3) % n}")
    
    c_scaled = SCALAR_MUL(c3, scalar, n_squared)
    m_scaled = DEC(c_scaled, keys.private_key, keys.public_key)
    
    print(f"   ENC(m)^k = {c_scaled}")
    print(f"   DEC(ENC(m)^k) = {m_scaled}")
    print()
    
    success_scalar = (scalar * m3) % n == m_scaled
    print(f"✅ Scalar multiplication verified: {success_scalar}")
    print()
    
    # Compute (m1 + m2) * scalar using homomorphic operations
    print("🧮 Complex operation: (m1 + m2) × scalar")
    c_complex = SCALAR_MUL(c_sum, scalar, n_squared)
    m_complex = DEC(c_complex, keys.private_key, keys.public_key)
    expected_complex = ((m1 + m2) * scalar) % n
    
    print(f"   ((m1 + m2) × scalar) mod n = {expected_complex}")
    print(f"   Homomorphic result = {m_complex}")
    print(f"✅ Complex operation verified: {expected_complex == m_complex}")


if __name__ == "__main__":
    demonstrate_paillier()
