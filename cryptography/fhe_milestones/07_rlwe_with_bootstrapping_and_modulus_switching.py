"""
RLWE with Bootstrapping and Modulus Switching
[2012] Enhanced FHE with modulus switching for better noise management

Educational implementation by Peter Norvig style
"""

import random
import numpy as np
from typing import Tuple, List, NamedTuple, Dict
from math import sqrt, log, ceil, gcd
from rlwe_utils import (
    polynomial_mod, polynomial_mult, polynomial_add,
    gaussian_polynomial, uniform_polynomial, binary_polynomial,
    create_modulus_chain, create_switch_keys, create_bootstrap_key_modswitch,
    noise_estimate_modulus
)


class RLWEModSwitchKeys(NamedTuple):
    """RLWE keys with bootstrapping and modulus switching capability"""
    public_key: Tuple[np.ndarray, np.ndarray, List[int], float]  # (a, b, q_chain, sigma)
    private_key: np.ndarray                                       # secret polynomial s
    bootstrap_key: Dict[str, any]                                # bootstrapping key
    switch_keys: Dict[int, Dict[str, any]]                       # modulus switching keys


def KEYGEN(n: int = 128, q_start: int = 2**15, sigma: float = 3.2, levels: int = 5) -> RLWEModSwitchKeys:
    """
    Generate RLWE key pair with bootstrapping and modulus switching
    
    Args:
        n: Degree of polynomial ring
        q_start: Starting modulus
        sigma: Standard deviation for Gaussian noise
        levels: Number of modulus levels
    
    Returns:
        RLWEModSwitchKeys with all required keys
    """
    # Generate secret polynomial
    s = binary_polynomial(n)
    
    # Create modulus chain
    q_chain = create_modulus_chain(q_start, levels)
    
    # Generate public key for the largest modulus
    q = q_chain[0]
    a = uniform_polynomial(n, q)
    e = gaussian_polynomial(n, sigma)
    
    as_product = polynomial_mult(a, s, n, q)
    ase_sum = polynomial_add(as_product, e, q)
    b = (-ase_sum) % q
    
    # Create bootstrapping key
    bootstrap_key = create_bootstrap_key_modswitch(s, n, q_chain, sigma)
    
    # Create modulus switching keys
    switch_keys = create_switch_keys(s, q_chain, n, sigma)
    
    return RLWEModSwitchKeys(
        public_key=(a, b, q_chain, sigma),
        private_key=s,
        bootstrap_key=bootstrap_key,
        switch_keys=switch_keys
    )


def ENC(message: int, public_key: Tuple[np.ndarray, np.ndarray, List[int], float], 
        level: int = 0) -> Tuple[np.ndarray, np.ndarray, int]:
    """
    Encrypt a message bit using RLWE at specified modulus level
    
    Returns:
        Ciphertext (u, v, current_q) with current modulus
    """
    if message not in [0, 1]:
        raise ValueError("RLWE encrypts only bits (0 or 1)")
    
    a, b, q_chain, sigma = public_key
    
    if level >= len(q_chain):
        level = len(q_chain) - 1
    
    q = q_chain[level]
    n = len(a)
    
    # Scale public key to current modulus level if needed
    if level > 0:
        scale_factor = q / q_chain[0]
        a_scaled = (a * scale_factor).astype(int) % q
        b_scaled = (b * scale_factor).astype(int) % q
    else:
        a_scaled, b_scaled = a, b
    
    # Choose random polynomial r
    r = binary_polynomial(n)
    
    # Generate noise polynomials
    e1 = gaussian_polynomial(n, sigma)
    e2 = gaussian_polynomial(n, sigma)
    
    # Compute ciphertext
    ar_product = polynomial_mult(a_scaled, r, n, q)
    u = polynomial_add(ar_product, e1, q)
    
    br_product = polynomial_mult(b_scaled, r, n, q)
    message_poly = np.zeros(n, dtype=int)
    message_poly[0] = message * (q // 2)
    
    v_temp = polynomial_add(br_product, e2, q)
    v = polynomial_add(v_temp, message_poly, q)
    
    return (u, v, q)


def DEC(ciphertext: Tuple[np.ndarray, np.ndarray, int], private_key: np.ndarray) -> int:
    """Decrypt a ciphertext using RLWE private key"""
    u, v, q = ciphertext
    s = private_key
    n = len(s)
    
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


def ADD(ciphertext1: Tuple[np.ndarray, np.ndarray, int], 
        ciphertext2: Tuple[np.ndarray, np.ndarray, int]) -> Tuple[np.ndarray, np.ndarray, int]:
    """Homomorphic addition"""
    u1, v1, q1 = ciphertext1
    u2, v2, q2 = ciphertext2
    
    if q1 != q2:
        raise ValueError("Ciphertexts must have same modulus for addition")
    
    q = q1
    u_sum = polynomial_add(u1, u2, q)
    v_sum = polynomial_add(v1, v2, q)
    
    return (u_sum, v_sum, q)


def MUL(ciphertext1: Tuple[np.ndarray, np.ndarray, int], 
        ciphertext2: Tuple[np.ndarray, np.ndarray, int]) -> Tuple[np.ndarray, np.ndarray, int]:
    """Homomorphic multiplication"""
    u1, v1, q1 = ciphertext1
    u2, v2, q2 = ciphertext2
    
    if q1 != q2:
        raise ValueError("Ciphertexts must have same modulus for multiplication")
    
    q = q1
    n = len(u1)
    
    # Simplified multiplication
    u_prod = polynomial_mult(u1, v2, n, q)
    v_prod = polynomial_mult(v1, v2, n, q)
    
    return (u_prod, v_prod, q)


def MOD_SWITCH(ciphertext: Tuple[np.ndarray, np.ndarray, int], 
               switch_keys: Dict[int, Dict[str, any]]) -> Tuple[np.ndarray, np.ndarray, int]:
    """
    Switch ciphertext to lower modulus for noise management
    
    Args:
        ciphertext: Input ciphertext
        switch_keys: Modulus switching keys
    
    Returns:
        Ciphertext with reduced modulus
    """
    u, v, current_q = ciphertext
    
    if current_q not in switch_keys:
        raise ValueError(f"No switching key for modulus {current_q}")
    
    switch_key = switch_keys[current_q]
    new_q = switch_key['to_q']
    ratio = switch_key['ratio']
    
    print(f"   🔄 Switching modulus: {current_q} → {new_q}")
    
    # Scale down the ciphertext (simplified)
    # Real modulus switching involves more sophisticated rounding and key switching
    
    # Scale coefficients
    u_scaled = np.round(u / ratio).astype(int) % new_q
    v_scaled = np.round(v / ratio).astype(int) % new_q
    
    # Add some controlled noise to simulate proper modulus switching
    n = len(u)
    sigma = switch_key['sigma']
    noise_u = gaussian_polynomial(n, sigma * 0.1)
    noise_v = gaussian_polynomial(n, sigma * 0.1)
    
    u_switched = (u_scaled + noise_u) % new_q
    v_switched = (v_scaled + noise_v) % new_q
    
    return (u_switched, v_switched, new_q)


def BOOTSTRAP(ciphertext: Tuple[np.ndarray, np.ndarray, int], 
              bootstrap_key: Dict[str, any],
              public_key: Tuple[np.ndarray, np.ndarray, List[int], float]) -> Tuple[np.ndarray, np.ndarray, int]:
    """Bootstrap with modulus switching support"""
    u, v, current_q = ciphertext
    a, b, q_chain, sigma = public_key
    
    print("   🔄 Performing bootstrapping with modulus switching...")
    
    # Simulate bootstrapping to highest modulus
    secret_hint = bootstrap_key['secret_hint']
    n = len(secret_hint)
    fresh_q = q_chain[0]  # Bootstrap to highest modulus
    
    # Extract message (simplified)
    us_product = polynomial_mult(u, secret_hint, n, current_q)
    decryption_poly = polynomial_add(v, us_product, current_q)
    constant_term = decryption_poly[0] % current_q
    
    if constant_term >= current_q // 2:
        constant_term -= current_q
    
    message_bit = 0 if abs(constant_term) < abs(constant_term - current_q//2) else 1
    
    # Create fresh encryption at highest modulus
    r_fresh = binary_polynomial(n)
    e1_fresh = gaussian_polynomial(n, sigma * 0.5)
    e2_fresh = gaussian_polynomial(n, sigma * 0.5)
    
    ar_fresh = polynomial_mult(a, r_fresh, n, fresh_q)
    u_fresh = polynomial_add(ar_fresh, e1_fresh, fresh_q)
    
    br_fresh = polynomial_mult(b, r_fresh, n, fresh_q)
    message_poly_fresh = np.zeros(n, dtype=int)
    message_poly_fresh[0] = message_bit * (fresh_q // 2)
    
    v_temp_fresh = polynomial_add(br_fresh, e2_fresh, fresh_q)
    v_fresh = polynomial_add(v_temp_fresh, message_poly_fresh, fresh_q)
    
    print(f"   ✨ Bootstrapped to modulus {fresh_q}, message: {message_bit}")
    
    return (u_fresh, v_fresh, fresh_q)


def noise_estimate(ciphertext: Tuple[np.ndarray, np.ndarray, int], 
                   private_key: np.ndarray, message: int) -> float:
    """Estimate noise level in ciphertext"""
    return noise_estimate_modulus(ciphertext, private_key, message)


def demonstrate_rlwe_modulus_switching():
    """Demonstrate RLWE with bootstrapping and modulus switching"""
    print("🔐 RLWE with Bootstrapping and Modulus Switching")
    print("=" * 60)
    
    # Generate keys
    print("📋 Generating RLWE keys with modulus switching...")
    n, q_start, sigma = 64, 2**14, 2.0
    keys = KEYGEN(n, q_start, sigma, levels=4)
    
    a, b, q_chain, sigma_pub = keys.public_key
    s = keys.private_key
    switch_keys = keys.switch_keys
    bootstrap_key = keys.bootstrap_key
    
    print(f"📊 Parameters: n={n}, σ={sigma}")
    print(f"🔗 Modulus chain: {q_chain}")
    print(f"🔑 Available modulus switches: {list(switch_keys.keys())}")
    print()
    
    # Test encryption at different levels
    print("🧪 Testing encryption at different modulus levels:")
    message = 1
    
    for level in range(min(3, len(q_chain))):
        c = ENC(message, keys.public_key, level)
        decrypted = DEC(c, keys.private_key)
        noise = noise_estimate(c, s, message)
        
        print(f"   Level {level} (q={c[2]}): decrypted={decrypted}, noise={noise}")
    
    print()
    
    # Demonstrate modulus switching
    print("🔄 Demonstrating modulus switching:")
    
    # Start with encryption at highest level
    c_high = ENC(message, keys.public_key, level=0)
    print(f"   Initial: q={c_high[2]}, noise={noise_estimate(c_high, s, message)}")
    
    # Perform some operations to accumulate noise
    zero_c = ENC(0, keys.public_key, level=0)
    c_noisy = ADD(c_high, zero_c)
    c_noisy = ADD(c_noisy, zero_c)
    
    current_noise = noise_estimate(c_noisy, s, message)
    print(f"   After operations: q={c_noisy[2]}, noise={current_noise}")
    
    # Switch to lower modulus
    if c_noisy[2] in switch_keys:
        c_switched = MOD_SWITCH(c_noisy, switch_keys)
        switched_noise = noise_estimate(c_switched, s, message)
        switched_decrypted = DEC(c_switched, keys.private_key)
        
        print(f"   After mod switch: q={c_switched[2]}, noise={switched_noise}, "
              f"decrypted={switched_decrypted}")
        
        # Continue with more operations at lower modulus
        zero_c_low = ENC(0, keys.public_key, level=1)
        c_continued = ADD(c_switched, zero_c_low)
        continued_noise = noise_estimate(c_continued, s, message)
        
        print(f"   More operations: q={c_continued[2]}, noise={continued_noise}")
    
    print()
    
    # Demonstrate combined bootstrapping and modulus switching
    print("🔄 Demonstrating bootstrapping with modulus switching:")
    
    # Create a very noisy ciphertext
    c_very_noisy = c_high
    for _ in range(3):
        zero_c = ENC(0, keys.public_key, level=0)
        c_very_noisy = ADD(c_very_noisy, zero_c)
    
    very_noisy_noise = noise_estimate(c_very_noisy, s, message)
    print(f"   Very noisy: q={c_very_noisy[2]}, noise={very_noisy_noise}")
    
    # Bootstrap to refresh
    c_bootstrapped = BOOTSTRAP(c_very_noisy, bootstrap_key, keys.public_key)
    bootstrap_noise = noise_estimate(c_bootstrapped, s, message)
    bootstrap_decrypted = DEC(c_bootstrapped, keys.private_key)
    
    print(f"   After bootstrap: q={c_bootstrapped[2]}, noise={bootstrap_noise}, "
          f"decrypted={bootstrap_decrypted}")
    
    # Now switch to lower modulus for efficiency
    if c_bootstrapped[2] in switch_keys:
        c_final = MOD_SWITCH(c_bootstrapped, switch_keys)
        final_noise = noise_estimate(c_final, s, message)
        final_decrypted = DEC(c_final, keys.private_key)
        
        print(f"   Final state: q={c_final[2]}, noise={final_noise}, "
              f"decrypted={final_decrypted}")
    
    print()
    
    # Explain the benefits
    print("🎯 Benefits of Modulus Switching:")
    print("   • Reduces noise growth during operations")
    print("   • Improves computational efficiency")
    print("   • Enables longer computation chains")
    print("   • Better noise management than bootstrapping alone")
    print()
    
    print("⚙️  Strategy:")
    print("   • Start with large modulus for security")
    print("   • Switch to smaller moduli as operations proceed")
    print("   • Bootstrap when noise becomes too large")
    print("   • Balance between security, efficiency, and noise")


if __name__ == "__main__":
    demonstrate_rlwe_modulus_switching()
