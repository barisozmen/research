"""
RSA Cryptosystem with Homomorphic Multiplication
[1978] The first public-key cryptosystem with multiplicative homomorphism

Educational implementation by Peter Norvig style
"""

import random
from math import gcd
from typing import Tuple, NamedTuple
from crypto_utils import is_prime, generate_prime, extended_gcd, mod_inverse


class RSAKeys(NamedTuple):
    """RSA key pair"""
    public_key: Tuple[int, int]   # (n, e)
    private_key: Tuple[int, int]  # (n, d)


def KEYGEN(bits: int = 512) -> RSAKeys:
    """
    Generate RSA key pair
    
    Args:
        bits: Bit length for each prime (total key size will be 2*bits)
    
    Returns:
        RSAKeys with public key (n, e) and private key (n, d)
    """
    # Generate two distinct primes
    p = generate_prime(bits)
    q = generate_prime(bits)
    while q == p:
        q = generate_prime(bits)
    
    n = p * q
    phi_n = (p - 1) * (q - 1)
    
    # Choose e (commonly 65537)
    e = 65537
    while gcd(e, phi_n) != 1:
        e = random.randrange(3, phi_n, 2)
    
    # Compute d = e^(-1) mod φ(n)
    d = mod_inverse(e, phi_n)
    
    return RSAKeys(
        public_key=(n, e),
        private_key=(n, d)
    )


def ENC(message: int, public_key: Tuple[int, int]) -> int:
    """
    Encrypt a message using RSA public key
    
    Args:
        message: Plaintext integer (must be < n)
        public_key: (n, e) tuple
    
    Returns:
        Ciphertext c = m^e mod n
    """
    n, e = public_key
    if message >= n:
        raise ValueError(f"Message {message} must be less than n={n}")
    return pow(message, e, n)


def DEC(ciphertext: int, private_key: Tuple[int, int]) -> int:
    """
    Decrypt a ciphertext using RSA private key
    
    Args:
        ciphertext: Encrypted integer
        private_key: (n, d) tuple
    
    Returns:
        Plaintext m = c^d mod n
    """
    n, d = private_key
    return pow(ciphertext, d, n)


def MUL(ciphertext1: int, ciphertext2: int, n: int) -> int:
    """
    Homomorphic multiplication: multiply two ciphertexts
    
    Property: ENC(m1) * ENC(m2) = ENC(m1 * m2) mod n
    
    Args:
        ciphertext1: First encrypted value
        ciphertext2: Second encrypted value
        n: RSA modulus
    
    Returns:
        Product of ciphertexts modulo n
    """
    return (ciphertext1 * ciphertext2) % n


def demonstrate_rsa():
    """Demonstrate RSA cryptosystem with homomorphic multiplication"""
    print("🔐 RSA Cryptosystem with Homomorphic Multiplication")
    print("=" * 60)
    
    # Generate keys
    print("📋 Generating RSA keys...")
    keys = KEYGEN(bits=256)  # Smaller for demo
    n, e = keys.public_key
    _, d = keys.private_key
    
    print(f"📊 Public key:  (n={n}, e={e})")
    print(f"🔑 Private key: (n={n}, d={d})")
    print()
    
    # Test basic encryption/decryption
    print("🧪 Testing basic encryption/decryption:")
    m1, m2 = 42, 17
    c1 = ENC(m1, keys.public_key)
    c2 = ENC(m2, keys.public_key)
    
    print(f"   Message 1: {m1}")
    print(f"   Encrypted: {c1}")
    print(f"   Decrypted: {DEC(c1, keys.private_key)}")
    print()
    
    print(f"   Message 2: {m2}")
    print(f"   Encrypted: {c2}")
    print(f"   Decrypted: {DEC(c2, keys.private_key)}")
    print()
    
    # Demonstrate homomorphic multiplication
    print("✨ Demonstrating homomorphic multiplication:")
    print(f"   m1 = {m1}, m2 = {m2}")
    print(f"   m1 × m2 = {m1 * m2}")
    print()
    
    # Multiply ciphertexts
    c_product = MUL(c1, c2, n)
    m_product = DEC(c_product, keys.private_key)
    
    print(f"   ENC({m1}) = {c1}")
    print()
    print(f"   ENC({m2}) = {c2}")
    print()
    print(f"   ENC({m1}) × ENC({m2}) = {c_product}")
    print()
    print(f"   DEC(ENC({m1}) × ENC({m2})) = {m_product}")
    print()
    
    # Verify homomorphic property
    success = (m1 * m2) % n == m_product
    print(f"✅ Homomorphic property verified: {success}")
    print(f"   Expected: {(m1 * m2) % n}")
    print(f"   Got:      {m_product}")
    
    if not success:
        print("   Note: Product may exceed modulus, causing wraparound")


if __name__ == "__main__":
    demonstrate_rsa()
