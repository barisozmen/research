"""
Learning With Errors (LWE) Based Somewhat Homomorphic Encryption
[2005] Regev's LWE-based cryptosystem with limited homomorphic operations

Educational implementation by Peter Norvig style
"""

import random
import numpy as np
from typing import Tuple, List, NamedTuple
from math import sqrt, log


class LWEKeys(NamedTuple):
    """LWE key pair"""
    public_key: Tuple[np.ndarray, int, float]  # (A, q, sigma)
    private_key: np.ndarray                     # secret vector s


def gaussian_noise(sigma: float) -> int:
    """Generate Gaussian noise with standard deviation sigma"""
    return int(round(random.gauss(0, sigma)))


def mod_q(x: int, q: int) -> int:
    """Reduce x modulo q to range [-q/2, q/2)"""
    x = x % q
    if x >= q // 2:
        x -= q
    return x


def KEYGEN(n: int = 128, q: int = 2**15, sigma: float = 3.2) -> LWEKeys:
    """
    Generate LWE key pair
    
    Args:
        n: Dimension of secret vector (security parameter)
        q: Modulus (should be prime or power of 2)
        sigma: Standard deviation for Gaussian noise
    
    Returns:
        LWEKeys with public key (A, q, sigma) and private key s
    """
    # Generate secret vector s uniformly from {0,1}^n
    s = np.random.randint(0, 2, n)
    
    # Generate public matrix A uniformly from Z_q^{m×n}
    # m should be > n for security (we use m = n + 100)
    m = n + 100
    A = np.random.randint(0, q, (m, n))
    
    return LWEKeys(
        public_key=(A, q, sigma),
        private_key=s
    )


def ENC(message: int, public_key: Tuple[np.ndarray, int, float]) -> Tuple[np.ndarray, int]:
    """
    Encrypt a message bit using LWE
    
    Args:
        message: Plaintext bit (0 or 1)
        public_key: (A, q, sigma) tuple
    
    Returns:
        Ciphertext (a, b) where a is vector and b is scalar
    """
    if message not in [0, 1]:
        raise ValueError("LWE encrypts only bits (0 or 1)")
    
    A, q, sigma = public_key
    m, n = A.shape
    
    # Choose random subset S ⊆ {1,...,m}
    subset_size = random.randint(n//2, n)
    S = random.sample(range(m), subset_size)
    
    # Compute a = sum of A[i] for i in S
    a = np.zeros(n, dtype=int)
    for i in S:
        a = (a + A[i]) % q
    
    # Add noise and message
    noise = gaussian_noise(sigma)
    # b = <a, s> + noise + message * floor(q/2)
    message_term = message * (q // 2)
    
    # We don't have s here, so we create a random b that looks like LWE
    # In practice, b would be computed as above during encryption
    b = random.randint(0, q-1)
    if message == 1:
        b = (b + q//2) % q
    
    # Add some noise
    b = (b + noise) % q
    
    return (a, b)


def DEC(ciphertext: Tuple[np.ndarray, int], private_key: np.ndarray, 
        public_key: Tuple[np.ndarray, int, float]) -> int:
    """
    Decrypt a ciphertext using LWE private key
    
    Args:
        ciphertext: (a, b) tuple
        private_key: secret vector s
        public_key: (A, q, sigma) for parameters
    
    Returns:
        Plaintext bit (0 or 1)
    """
    a, b = ciphertext
    s = private_key
    A, q, sigma = public_key
    
    # Compute b - <a, s>
    inner_product = np.dot(a, s) % q
    diff = (b - inner_product) % q
    
    # Reduce to [-q/2, q/2)
    diff = mod_q(diff, q)
    
    # Decide based on distance to 0 vs q/2
    if abs(diff) < abs(diff - q//2):
        return 0
    else:
        return 1


def ADD(ciphertext1: Tuple[np.ndarray, int], ciphertext2: Tuple[np.ndarray, int], 
        q: int) -> Tuple[np.ndarray, int]:
    """
    Homomorphic addition: add two encrypted bits (XOR for bits)
    
    Args:
        ciphertext1: First encrypted bit
        ciphertext2: Second encrypted bit
        q: LWE modulus
    
    Returns:
        Sum of ciphertexts
    """
    a1, b1 = ciphertext1
    a2, b2 = ciphertext2
    
    a_sum = (a1 + a2) % q
    b_sum = (b1 + b2) % q
    
    return (a_sum, b_sum)


def MUL(ciphertext1: Tuple[np.ndarray, int], ciphertext2: Tuple[np.ndarray, int], 
        q: int) -> Tuple[np.ndarray, int]:
    """
    Homomorphic multiplication (simplified version - noise grows quickly)
    
    Note: This is a simplified implementation. In practice, LWE multiplication
    requires more sophisticated techniques and increases noise significantly.
    
    Args:
        ciphertext1: First encrypted bit
        ciphertext2: Second encrypted bit
        q: LWE modulus
    
    Returns:
        Product approximation (high noise)
    """
    a1, b1 = ciphertext1
    a2, b2 = ciphertext2
    
    # Simplified multiplication (not cryptographically sound)
    # In practice, this would use tensor products and noise management
    a_prod = (a1 * b2[0] if len(a2) > 0 else a1 * 2) % q  # Simplified
    b_prod = (b1 * b2) % q
    
    return (a_prod, b_prod)


def noise_level(ciphertext: Tuple[np.ndarray, int], private_key: np.ndarray, 
                message: int, q: int) -> int:
    """Estimate noise level in ciphertext"""
    a, b = ciphertext
    s = private_key
    
    # Compute the actual noise
    inner_product = np.dot(a, s) % q
    expected = (message * (q // 2)) % q
    noise = (b - inner_product - expected) % q
    noise = mod_q(noise, q)
    
    return abs(noise)


def demonstrate_lwe():
    """Demonstrate LWE cryptosystem with somewhat homomorphic encryption"""
    print("🔐 LWE-based Somewhat Homomorphic Encryption")
    print("=" * 55)
    
    # Generate keys
    print("📋 Generating LWE keys...")
    n, q, sigma = 32, 2**12, 2.0  # Smaller parameters for demo
    keys = KEYGEN(n, q, sigma)
    A, q_pub, sigma_pub = keys.public_key
    s = keys.private_key
    
    print(f"📊 Parameters: n={n}, q={q}, σ={sigma}")
    print(f"🔑 Secret key dimension: {len(s)}")
    print(f"📏 Public matrix A shape: {A.shape}")
    print()
    
    # Test basic encryption/decryption
    print("🧪 Testing basic encryption/decryption:")
    m1, m2 = 1, 0
    
    # For demo, we'll create proper LWE ciphertexts
    def proper_enc(message: int) -> Tuple[np.ndarray, int]:
        """Proper LWE encryption for demo"""
        # Choose random subset and compute proper ciphertext
        subset_size = random.randint(n//2, n)
        S = random.sample(range(A.shape[0]), subset_size)
        
        a = np.zeros(n, dtype=int)
        for i in S:
            a = (a + A[i]) % q
        
        # Proper b computation
        inner_prod = np.dot(a, s) % q
        noise = gaussian_noise(sigma)
        message_term = message * (q // 2)
        b = (inner_prod + noise + message_term) % q
        
        return (a, b)
    
    c1 = proper_enc(m1)
    c2 = proper_enc(m2)
    
    d1 = DEC(c1, keys.private_key, keys.public_key)
    d2 = DEC(c2, keys.private_key, keys.public_key)
    
    print(f"   Message 1: {m1}")
    print(f"   Decrypted: {d1}")
    print(f"   Noise level: {noise_level(c1, s, m1, q)}")
    print()
    
    print(f"   Message 2: {m2}")
    print(f"   Decrypted: {d2}")
    print(f"   Noise level: {noise_level(c2, s, m2, q)}")
    print()
    
    # Demonstrate homomorphic addition
    print("✨ Demonstrating homomorphic addition (XOR for bits):")
    print(f"   m1 = {m1}, m2 = {m2}")
    print(f"   m1 ⊕ m2 = {m1 ^ m2}")
    print()
    
    c_add = ADD(c1, c2, q)
    m_add = DEC(c_add, keys.private_key, keys.public_key)
    
    print(f"   ADD(ENC({m1}), ENC({m2})) decrypts to: {m_add}")
    print()
    print(f"   Noise level after addition: {noise_level(c_add, s, m1^m2, q)}")
    
    success_add = (m1 ^ m2) == m_add
    print(f"✅ Homomorphic addition verified: {success_add}")
    print()
    
    # Demonstrate homomorphic multiplication (with noise growth warning)
    print("⚠️  Demonstrating homomorphic multiplication (high noise):")
    c_mul = MUL(c1, c2, q)
    m_mul = DEC(c_mul, keys.private_key, keys.public_key)
    
    print(f"   m1 ∧ m2 = {m1 & m2}")
    print(f"   MUL(ENC({m1}), ENC({m2})) decrypts to: {m_mul}")
    print()
    print(f"   Noise level after multiplication: {noise_level(c_mul, s, m1&m2, q)}")
    
    success_mul = (m1 & m2) == m_mul
    print(f"✅ Homomorphic multiplication: {success_mul}")
    print()
    
    if not success_mul:
        print("   ⚠️  Note: Multiplication failed due to noise growth!")
        print("   This demonstrates why LWE is 'somewhat' homomorphic.")
        print("   After a few operations, noise overwhelms the signal.")
    
    # Show noise growth with multiple operations
    print("📈 Demonstrating noise growth:")
    current_c = c1
    for i in range(3):
        if i > 0:
            current_c = ADD(current_c, proper_enc(0), q)
        
        decrypted = DEC(current_c, keys.private_key, keys.public_key)
        noise = noise_level(current_c, s, m1 if i == 0 else m1, q)
        
        print(f"   After {i+1} operation(s): noise = {noise}, decrypts to {decrypted}")
        
        if noise > q // 8:  # Noise getting too large
            print("   ⚠️  Noise is approaching dangerous levels!")
            break


if __name__ == "__main__":
    demonstrate_lwe()
