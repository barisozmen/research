"""
RLWE with Bootstrapping - First Fully Homomorphic Encryption
[2010-2013] BGV scheme and bootstrapping technique for noise reduction

Educational implementation by Peter Norvig style
"""

import random
import numpy as np
from typing import Tuple, List, NamedTuple, Dict
from math import sqrt, log, ceil
from rlwe_utils import (
    polynomial_mod, polynomial_mult, polynomial_add,
    gaussian_polynomial, uniform_polynomial, binary_polynomial,
    noise_estimate_basic, create_bootstrap_key_basic
)


class RLWEBootstrapKeys(NamedTuple):
    """RLWE keys with bootstrapping capability"""
    public_key: Tuple[np.ndarray, np.ndarray, int, int, float]  # (a, b, n, q, sigma)
    private_key: np.ndarray                                      # secret polynomial s
    bootstrap_key: Dict[str, any]                               # bootstrapping key


def KEYGEN(n: int = 128, q: int = 2**15, sigma: float = 3.2) -> RLWEBootstrapKeys:
    """
    Generate RLWE key pair with bootstrapping capability
    
    Args:
        n: Degree of polynomial ring (power of 2)
        q: Modulus (should be prime or power of 2)
        sigma: Standard deviation for Gaussian noise
    
    Returns:
        RLWEBootstrapKeys with public key, private key, and bootstrap key
    """
    # Generate secret polynomial s with small coefficients
    s = binary_polynomial(n)
    
    # Generate random polynomial a
    a = uniform_polynomial(n, q)
    
    # Generate noise polynomial e
    e = gaussian_polynomial(n, sigma)
    
    # Compute b = -(a * s + e) mod q in the ring
    as_product = polynomial_mult(a, s, n, q)
    ase_sum = polynomial_add(as_product, e, q)
    b = (-ase_sum) % q
    
    # Create bootstrapping key
    bootstrap_key = create_bootstrap_key_basic(s, n, q, sigma)
    
    return RLWEBootstrapKeys(
        public_key=(a, b, n, q, sigma),
        private_key=s,
        bootstrap_key=bootstrap_key
    )


def ENC(message: int, public_key: Tuple[np.ndarray, np.ndarray, int, int, float]) -> Tuple[np.ndarray, np.ndarray]:
    """Encrypt a message bit using RLWE"""
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
    message_poly[0] = message * (q // 2)
    
    v_temp = polynomial_add(br_product, e2, q)
    v = polynomial_add(v_temp, message_poly, q)
    
    return (u, v)


def DEC(ciphertext: Tuple[np.ndarray, np.ndarray], private_key: np.ndarray,
        public_key: Tuple[np.ndarray, np.ndarray, int, int, float]) -> int:
    """Decrypt a ciphertext using RLWE private key"""
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
    """Homomorphic addition"""
    u1, v1 = ciphertext1
    u2, v2 = ciphertext2
    
    u_sum = polynomial_add(u1, u2, q)
    v_sum = polynomial_add(v1, v2, q)
    
    return (u_sum, v_sum)


def MUL(ciphertext1: Tuple[np.ndarray, np.ndarray], 
        ciphertext2: Tuple[np.ndarray, np.ndarray], 
        n: int, q: int) -> Tuple[np.ndarray, np.ndarray]:
    """Homomorphic multiplication (increases noise significantly)"""
    u1, v1 = ciphertext1
    u2, v2 = ciphertext2
    
    # Simplified multiplication
    u_prod = polynomial_mult(u1, v2, n, q)
    v_prod = polynomial_mult(v1, v2, n, q)
    
    return (u_prod, v_prod)


def noise_estimate(ciphertext: Tuple[np.ndarray, np.ndarray], 
                   private_key: np.ndarray, message: int, 
                   public_key: Tuple[np.ndarray, np.ndarray, int, int, float]) -> float:
    """Estimate noise level in RLWE ciphertext"""
    return noise_estimate_basic(ciphertext, private_key, message, public_key)


def BOOTSTRAP(ciphertext: Tuple[np.ndarray, np.ndarray], 
              bootstrap_key: Dict[str, any],
              public_key: Tuple[np.ndarray, np.ndarray, int, int, float]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Bootstrap a ciphertext to reduce noise
    
    This is a simplified educational implementation. Real bootstrapping involves:
    1. Homomorphically evaluating the decryption circuit
    2. Using key switching and modulus switching
    3. Complex polynomial arithmetic
    
    Args:
        ciphertext: Noisy ciphertext to refresh
        bootstrap_key: Bootstrapping key
        public_key: Public key parameters
    
    Returns:
        Fresh ciphertext with reduced noise
    """
    u, v = ciphertext
    a, b, n, q, sigma = public_key
    
    print("   🔄 Performing bootstrapping (simplified)...")
    
    # In a real implementation, this would:
    # 1. Extract the message bit by homomorphically evaluating decryption
    # 2. Use the bootstrapping key to switch between different key spaces
    # 3. Perform modulus switching and key switching
    # 4. Return a fresh encryption of the same message
    
    # For educational purposes, we simulate the effect:
    # 1. "Decrypt" to get the message (this would be done homomorphically)
    secret_hint = bootstrap_key['secret_hint']
    us_product = polynomial_mult(u, secret_hint, n, q)
    decryption_poly = polynomial_add(v, us_product, q)
    constant_term = decryption_poly[0] % q
    
    if constant_term >= q // 2:
        constant_term -= q
    
    # Determine the message bit
    if abs(constant_term) < abs(constant_term - q//2):
        message_bit = 0
    else:
        message_bit = 1
    
    # 2. Create a fresh encryption of the same message
    # This simulates the result of homomorphic decryption circuit evaluation
    
    # Generate fresh randomness
    r_fresh = binary_polynomial(n)
    e1_fresh = gaussian_polynomial(n, sigma * 0.5)  # Reduced noise after bootstrapping
    e2_fresh = gaussian_polynomial(n, sigma * 0.5)
    
    # Create fresh ciphertext
    ar_fresh = polynomial_mult(a, r_fresh, n, q)
    u_fresh = polynomial_add(ar_fresh, e1_fresh, q)
    
    br_fresh = polynomial_mult(b, r_fresh, n, q)
    message_poly_fresh = np.zeros(n, dtype=int)
    message_poly_fresh[0] = message_bit * (q // 2)
    
    v_temp_fresh = polynomial_add(br_fresh, e2_fresh, q)
    v_fresh = polynomial_add(v_temp_fresh, message_poly_fresh, q)
    
    print(f"   ✨ Bootstrapping complete! Message preserved: {message_bit}")
    
    return (u_fresh, v_fresh)


def can_decrypt_correctly(ciphertext: Tuple[np.ndarray, np.ndarray], 
                         private_key: np.ndarray,
                         public_key: Tuple[np.ndarray, np.ndarray, int, int, float],
                         expected_message: int) -> bool:
    """Check if ciphertext can still be decrypted correctly"""
    try:
        decrypted = DEC(ciphertext, private_key, public_key)
        return decrypted == expected_message
    except:
        return False


def demonstrate_rlwe_bootstrapping():
    """Demonstrate RLWE with bootstrapping for noise management"""
    print("🔐 RLWE with Bootstrapping - Fully Homomorphic Encryption")
    print("=" * 65)
    
    # Generate keys
    print("📋 Generating RLWE keys with bootstrapping capability...")
    n, q, sigma = 64, 2**12, 2.0
    keys = KEYGEN(n, q, sigma)
    a, b, n_pub, q_pub, sigma_pub = keys.public_key
    s = keys.private_key
    bootstrap_key = keys.bootstrap_key
    
    print(f"📊 Parameters: n={n}, q={q}, σ={sigma}")
    print(f"🔑 Bootstrap key type: {bootstrap_key['type']}")
    print()
    
    # Test basic encryption/decryption
    print("🧪 Testing basic encryption/decryption:")
    message = 1
    c = ENC(message, keys.public_key)
    decrypted = DEC(c, keys.private_key, keys.public_key)
    initial_noise = noise_estimate(c, s, message, keys.public_key)
    
    print(f"   Original message: {message}")
    print(f"   Decrypted: {decrypted}")
    print(f"   Initial noise level: {initial_noise}")
    print()
    
    # Perform multiple operations to accumulate noise
    print("📈 Accumulating noise through operations:")
    current_c = c
    operation_count = 0
    
    for i in range(5):
        operation_count += 1
        
        # Add some noise by adding an encryption of 0
        zero_c = ENC(0, keys.public_key)
        current_c = ADD(current_c, zero_c, q)
        
        current_noise = noise_estimate(current_c, s, message, keys.public_key)
        can_decrypt = can_decrypt_correctly(current_c, s, keys.public_key, message)
        
        print(f"   After operation {operation_count}: noise = {current_noise}, "
              f"decrypts correctly = {can_decrypt}")
        
        # Check if noise is getting too high
        if current_noise > q // 8:
            print(f"   ⚠️  Noise level dangerous! ({current_noise} > {q//8})")
            break
    
    print()
    
    # Demonstrate bootstrapping
    print("🔄 Demonstrating bootstrapping for noise reduction:")
    print(f"   Before bootstrapping: noise = {current_noise}")
    
    # Perform bootstrapping
    refreshed_c = BOOTSTRAP(current_c, bootstrap_key, keys.public_key)
    refreshed_noise = noise_estimate(refreshed_c, s, message, keys.public_key)
    refreshed_decrypted = DEC(refreshed_c, keys.private_key, keys.public_key)
    
    print(f"   After bootstrapping: noise = {refreshed_noise}")
    print(f"   Message preservation: {message} → {refreshed_decrypted}")
    print(f"   ✅ Noise reduction: {current_noise} → {refreshed_noise}")
    print()
    
    # Show that we can continue operations after bootstrapping
    print("🔄 Continuing operations after bootstrapping:")
    post_bootstrap_c = refreshed_c
    
    for i in range(3):
        # Perform more operations
        zero_c = ENC(0, keys.public_key)
        post_bootstrap_c = ADD(post_bootstrap_c, zero_c, q)
        
        post_noise = noise_estimate(post_bootstrap_c, s, message, keys.public_key)
        can_decrypt = can_decrypt_correctly(post_bootstrap_c, s, keys.public_key, message)
        
        print(f"   Post-bootstrap operation {i+1}: noise = {post_noise}, "
              f"decrypts correctly = {can_decrypt}")
    
    print()
    
    # Explain the significance
    print("🎯 Significance of Bootstrapping:")
    print("   • Enables unlimited homomorphic operations")
    print("   • Transforms 'somewhat' HE into 'fully' HE")
    print("   • Fundamental breakthrough in cryptography (2009-2013)")
    print("   • Enables arbitrary computations on encrypted data")
    print()
    
    print("⚙️  In practice, bootstrapping involves:")
    print("   • Homomorphic evaluation of decryption circuit")
    print("   • Key switching and modulus switching techniques")
    print("   • Careful noise management and parameter selection")
    print("   • Significant computational overhead (thousands of operations)")


if __name__ == "__main__":
    demonstrate_rlwe_bootstrapping()
