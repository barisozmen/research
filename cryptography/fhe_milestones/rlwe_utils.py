"""
RLWE Utilities for Ring Learning With Errors based cryptosystems
Common functions used across RLWE-based FHE implementations

Educational implementation by Peter Norvig style
"""

import random
import numpy as np
from typing import Tuple, List, Dict


def polynomial_mod(poly: np.ndarray, n: int, q: int) -> np.ndarray:
    """
    Reduce polynomial modulo x^n + 1 and coefficients modulo q
    
    Args:
        poly: Input polynomial coefficients
        n: Degree bound (x^n + 1 reduction)
        q: Coefficient modulus
    
    Returns:
        Reduced polynomial
    """
    # First reduce coefficients modulo q
    poly = poly % q
    
    # Then reduce modulo x^n + 1 (cyclotomic polynomial)
    if len(poly) > n:
        result = np.zeros(n, dtype=int)
        for i, coeff in enumerate(poly):
            pos = i % (2 * n)
            if pos < n:
                result[pos] = (result[pos] + coeff) % q
            else:
                # x^{n+k} = -x^k in x^n + 1
                result[pos - n] = (result[pos - n] - coeff) % q
        return result % q
    else:
        # Pad with zeros if needed
        result = np.zeros(n, dtype=int)
        result[:len(poly)] = poly
        return result % q


def polynomial_mult(a: np.ndarray, b: np.ndarray, n: int, q: int) -> np.ndarray:
    """
    Multiply two polynomials in R_q = Z_q[x]/(x^n + 1)
    
    Args:
        a, b: Input polynomials
        n: Degree bound
        q: Modulus
    
    Returns:
        Product polynomial in the ring
    """
    # Use convolution for polynomial multiplication
    result = np.convolve(a, b)
    return polynomial_mod(result, n, q)


def polynomial_add(a: np.ndarray, b: np.ndarray, q: int) -> np.ndarray:
    """
    Add two polynomials in R_q
    
    Args:
        a, b: Input polynomials
        q: Modulus
    
    Returns:
        Sum polynomial
    """
    n = max(len(a), len(b))
    result = np.zeros(n, dtype=int)
    result[:len(a)] += a
    result[:len(b)] += b
    return result % q


def gaussian_polynomial(n: int, sigma: float) -> np.ndarray:
    """
    Generate polynomial with Gaussian coefficients
    
    Args:
        n: Degree of polynomial
        sigma: Standard deviation for Gaussian distribution
    
    Returns:
        Polynomial with Gaussian noise coefficients
    """
    return np.array([int(round(random.gauss(0, sigma))) for _ in range(n)])


def uniform_polynomial(n: int, q: int) -> np.ndarray:
    """
    Generate polynomial with uniform random coefficients
    
    Args:
        n: Degree of polynomial
        q: Modulus (coefficients will be in [0, q))
    
    Returns:
        Polynomial with uniform random coefficients
    """
    return np.random.randint(0, q, n)


def binary_polynomial(n: int) -> np.ndarray:
    """
    Generate polynomial with binary coefficients {0,1}
    
    Args:
        n: Degree of polynomial
    
    Returns:
        Polynomial with binary coefficients
    """
    return np.random.randint(0, 2, n)


def create_modulus_chain(q_start: int, levels: int) -> List[int]:
    """
    Create a chain of moduli for modulus switching
    
    Args:
        q_start: Starting (largest) modulus
        levels: Number of modulus levels
    
    Returns:
        List of moduli in decreasing order
    """
    q_chain = []
    current_q = q_start
    
    for i in range(levels):
        q_chain.append(current_q)
        # Each level reduces modulus (simplified approach)
        current_q = max(current_q // 2, 2**8)  # Don't go too small
    
    return q_chain


def noise_estimate_basic(ciphertext: Tuple[np.ndarray, np.ndarray], 
                        private_key: np.ndarray, message: int, 
                        public_key: Tuple[np.ndarray, np.ndarray, int, int, float]) -> float:
    """
    Estimate noise level in basic RLWE ciphertext (2-element, no modulus tracking)
    
    Args:
        ciphertext: (u, v) ciphertext tuple
        private_key: Secret polynomial s
        message: Expected plaintext message
        public_key: (a, b, n, q, sigma) tuple
    
    Returns:
        Estimated noise level
    """
    u, v = ciphertext
    s = private_key
    a, b, n, q, sigma = public_key
    
    # Compute decryption polynomial
    us_product = polynomial_mult(u, s, n, q)
    decryption_poly = polynomial_add(v, us_product, q)
    
    # Expected value (message in constant term)
    expected = message * (q // 2)
    
    # Noise is the deviation from expected
    actual = decryption_poly[0] % q
    if actual >= q // 2:
        actual -= q
    
    noise = abs(actual - expected)
    return noise


def noise_estimate_modulus(ciphertext: Tuple[np.ndarray, np.ndarray, int], 
                          private_key: np.ndarray, message: int) -> float:
    """
    Estimate noise level in RLWE ciphertext with modulus tracking (3-element)
    
    Args:
        ciphertext: (u, v, q) ciphertext tuple with modulus
        private_key: Secret polynomial s
        message: Expected plaintext message
    
    Returns:
        Estimated noise level
    """
    u, v, q = ciphertext
    s = private_key
    n = len(s)
    
    # Compute decryption polynomial
    us_product = polynomial_mult(u, s, n, q)
    decryption_poly = polynomial_add(v, us_product, q)
    
    # Expected value
    expected = message * (q // 2)
    
    # Actual value
    actual = decryption_poly[0] % q
    if actual >= q // 2:
        actual -= q
    
    noise = abs(actual - expected)
    return noise


def create_switch_keys(secret: np.ndarray, q_chain: List[int], n: int, sigma: float) -> Dict[int, Dict[str, any]]:
    """
    Create modulus switching keys for transitioning between modulus levels
    
    Args:
        secret: Secret polynomial
        q_chain: Chain of moduli
        n: Polynomial degree
        sigma: Noise parameter
    
    Returns:
        Dictionary mapping source modulus to switching key information
    """
    switch_keys = {}
    
    for i in range(len(q_chain) - 1):
        from_q = q_chain[i]
        to_q = q_chain[i + 1]
        
        switch_keys[from_q] = {
            'to_q': to_q,
            'ratio': from_q / to_q,
            'secret_hint': secret.copy(),  # Simplified for educational purposes
            'n': n,
            'sigma': sigma
        }
    
    return switch_keys


def create_bootstrap_key_basic(secret: np.ndarray, n: int, q: int, sigma: float) -> Dict[str, any]:
    """
    Create basic bootstrapping key
    
    Args:
        secret: Secret polynomial
        n: Polynomial degree
        q: Modulus
        sigma: Noise parameter
    
    Returns:
        Basic bootstrapping key (simplified for education)
    """
    bootstrap_key = {
        'type': 'simplified',
        'n': n,
        'q': q,
        'sigma': sigma,
        # In practice, this would contain:
        # - Key switching keys
        # - Evaluation keys for homomorphic evaluation of decryption circuit
        # - Various auxiliary keys for different operations
        'secret_hint': secret.copy(),  # Simplified for educational purposes
    }
    
    return bootstrap_key


def create_bootstrap_key_modswitch(secret: np.ndarray, n: int, q_chain: List[int], sigma: float) -> Dict[str, any]:
    """
    Create bootstrapping key with modulus switching support
    
    Args:
        secret: Secret polynomial
        n: Polynomial degree
        q_chain: Chain of moduli
        sigma: Noise parameter
    
    Returns:
        Bootstrapping key with modulus switching capabilities
    """
    bootstrap_key = {
        'type': 'with_modulus_switching',
        'n': n,
        'q_chain': q_chain,
        'sigma': sigma,
        'secret_hint': secret.copy(),
    }
    
    return bootstrap_key


def create_bootstrap_key_full(secret: np.ndarray, n: int, q_chain: List[int], sigma: float) -> Dict[str, any]:
    """
    Create full FHE bootstrapping key
    
    Args:
        secret: Secret polynomial
        n: Polynomial degree
        q_chain: Chain of moduli
        sigma: Noise parameter
    
    Returns:
        Full FHE bootstrapping key
    """
    bootstrap_key = {
        'type': 'full_fhe',
        'n': n,
        'q_chain': q_chain,
        'sigma': sigma,
        'secret_hint': secret.copy(),
    }
    
    return bootstrap_key


def create_relin_keys(secret: np.ndarray, q_chain: List[int], n: int, sigma: float) -> Dict[str, any]:
    """
    Create relinearization keys for reducing ciphertext size after multiplication
    
    In real FHE, these are much more complex and involve:
    - Key switching matrices
    - Decomposition parameters
    - Multiple auxiliary keys
    
    Args:
        secret: Secret polynomial
        q_chain: Chain of moduli
        n: Polynomial degree
        sigma: Noise parameter
    
    Returns:
        Simplified relinearization keys
    """
    relin_keys = {
        'type': 'simplified_relin',
        'n': n,
        'q_chain': q_chain,
        'sigma': sigma,
        'secret_squared_hint': polynomial_mult(secret, secret, n, q_chain[0]),
        'secret_hint': secret.copy(),
        # In practice, this would contain complex key switching matrices
    }
    
    return relin_keys
