"""
Goldwasser-Micali Cryptosystem with Homomorphic Addition (mod 2)
[1982] First semantically secure public-key cryptosystem with additive homomorphism

Educational implementation by Peter Norvig style
"""

import random
from math import gcd
from typing import Tuple, NamedTuple, List
from crypto_utils import is_prime, generate_prime, jacobi_symbol, find_quadratic_non_residue


class GMKeys(NamedTuple):
    """Goldwasser-Micali key pair"""
    public_key: Tuple[int, int]   # (n, x) where x is quadratic non-residue
    private_key: Tuple[int, int]  # (p, q) the prime factors


def KEYGEN(bits: int = 512) -> GMKeys:
    """
    Generate Goldwasser-Micali key pair
    
    Args:
        bits: Bit length for each prime
    
    Returns:
        GMKeys with public key (n, x) and private key (p, q)
    """
    # Generate two distinct primes p, q ≡ 3 (mod 4)
    while True:
        p = generate_prime(bits)
        if p % 4 == 3:
            break
    
    while True:
        q = generate_prime(bits)
        if q % 4 == 3 and q != p:
            break
    
    n = p * q
    
    # Find quadratic non-residue x modulo n
    x = find_quadratic_non_residue(n)
    
    return GMKeys(
        public_key=(n, x),
        private_key=(p, q)
    )


def ENC(bit: int, public_key: Tuple[int, int]) -> int:
    """
    Encrypt a single bit using Goldwasser-Micali
    
    Args:
        bit: Plaintext bit (0 or 1)
        public_key: (n, x) tuple
    
    Returns:
        Ciphertext c = r^2 * x^bit mod n (where r is random)
    """
    if bit not in [0, 1]:
        raise ValueError("GM can only encrypt bits (0 or 1)")
    
    n, x = public_key
    
    # Choose random r
    while True:
        r = random.randrange(1, n)
        if gcd(r, n) == 1:
            break
    
    # c = r^2 * x^bit mod n
    return (pow(r, 2, n) * pow(x, bit, n)) % n


def DEC(ciphertext: int, private_key: Tuple[int, int], public_key: Tuple[int, int]) -> int:
    """
    Decrypt a ciphertext using Goldwasser-Micali private key
    
    Args:
        ciphertext: Encrypted bit
        private_key: (p, q) tuple
        public_key: (n, x) tuple (needed for n)
    
    Returns:
        Plaintext bit (0 or 1)
    """
    p, q = private_key
    n, x = public_key
    
    # Use quadratic residuosity test
    # If c is a quadratic residue mod n, then bit = 0, else bit = 1
    jacobi_p = jacobi_symbol(ciphertext, p)
    jacobi_q = jacobi_symbol(ciphertext, q)
    
    # Since p, q ≡ 3 (mod 4), Jacobi symbol equals Legendre symbol
    if jacobi_p == 1 and jacobi_q == 1:
        return 0  # Quadratic residue
    else:
        return 1  # Quadratic non-residue


def ADD(ciphertext1: int, ciphertext2: int, n: int) -> int:
    """
    Homomorphic addition modulo 2: XOR two encrypted bits
    
    Property: ENC(b1) * ENC(b2) = ENC(b1 ⊕ b2) mod n
    
    Args:
        ciphertext1: First encrypted bit
        ciphertext2: Second encrypted bit
        n: GM modulus
    
    Returns:
        Product of ciphertexts (representing XOR)
    """
    return (ciphertext1 * ciphertext2) % n


def encrypt_message(message: str, public_key: Tuple[int, int]) -> List[int]:
    """Encrypt a binary string bit by bit"""
    return [ENC(int(bit), public_key) for bit in message]


def decrypt_message(ciphertexts: List[int], private_key: Tuple[int, int], 
                   public_key: Tuple[int, int]) -> str:
    """Decrypt a list of ciphertexts to binary string"""
    return ''.join(str(DEC(c, private_key, public_key)) for c in ciphertexts)


def demonstrate_goldwasser_micali():
    """Demonstrate Goldwasser-Micali cryptosystem with homomorphic XOR"""
    print("🔐 Goldwasser-Micali Cryptosystem with Homomorphic Addition (mod 2)")
    print("=" * 75)
    
    # Generate keys
    print("📋 Generating GM keys...")
    keys = KEYGEN(bits=256)  # Smaller for demo
    n, x = keys.public_key
    p, q = keys.private_key
    
    print(f"📊 Public key:  (n={n}, x={x})")
    print(f"🔑 Private key: (p={p}, q={q})")
    print(f"   Verification: n = p × q = {p * q == n}")
    print()
    
    # Test basic encryption/decryption
    print("🧪 Testing basic bit encryption/decryption:")
    bit1, bit2 = 1, 0
    c1 = ENC(bit1, keys.public_key)
    c2 = ENC(bit2, keys.public_key)
    
    print(f"   Bit 1: {bit1}")
    print(f"   Encrypted: {c1}")
    print(f"   Decrypted: {DEC(c1, keys.private_key, keys.public_key)}")
    print()
    
    print(f"   Bit 2: {bit2}")
    print(f"   Encrypted: {c2}")
    print(f"   Decrypted: {DEC(c2, keys.private_key, keys.public_key)}")
    print()
    
    # Demonstrate homomorphic XOR (addition mod 2)
    print("✨ Demonstrating homomorphic XOR (addition mod 2):")
    print(f"   b1 = {bit1}, b2 = {bit2}")
    print(f"   b1 ⊕ b2 = {bit1 ^ bit2}")
    print()
    
    # XOR ciphertexts (multiply them)
    c_xor = ADD(c1, c2, n)
    b_xor = DEC(c_xor, keys.private_key, keys.public_key)
    
    print(f"   ENC({bit1}) = {c1}")
    print()
    print(f"   ENC({bit2}) = {c2}")
    print()
    print(f"   ENC({bit1}) × ENC({bit2}) = {c_xor}")
    print()
    print(f"   DEC(ENC({bit1}) × ENC({bit2})) = {b_xor}")
    print()
    
    # Verify homomorphic property
    success = (bit1 ^ bit2) == b_xor
    print(f"✅ Homomorphic XOR verified: {success}")
    print(f"   Expected: {bit1 ^ bit2}")
    print(f"   Got:      {b_xor}")
    print()
    
    # Test with binary string
    print("📝 Testing with binary messages:")
    msg1 = "1010"
    msg2 = "1100"
    
    print(f"   Message 1: {msg1}")
    print(f"   Message 2: {msg2}")
    
    # Encrypt messages
    c_msg1 = encrypt_message(msg1, keys.public_key)
    c_msg2 = encrypt_message(msg2, keys.public_key)
    
    # Homomorphic XOR
    c_result = [ADD(c1, c2, n) for c1, c2 in zip(c_msg1, c_msg2)]
    result = decrypt_message(c_result, keys.private_key, keys.public_key)
    
    expected = ''.join(str(int(b1) ^ int(b2)) for b1, b2 in zip(msg1, msg2))
    
    print(f"   Expected XOR: {expected}")
    print(f"   Computed XOR: {result}")
    print(f"✅ Message XOR verified: {expected == result}")


if __name__ == "__main__":
    demonstrate_goldwasser_micali()
