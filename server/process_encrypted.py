import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.he_utils import homomorphic_allele_sum, load_ciphertext, save_ciphertext
from shared.config import PARAMS
from openfhe import *

def calculate_allele_frequencies(cc, encrypted_counts):
    """
    Calculate allele frequencies from encrypted counts.
    Returns encrypted sum for each variant.
    """
    encrypted_sums = []
    
    for variant_counts in encrypted_counts:
        # Calculate the sum of allele counts for this variant
        encrypted_sum = homomorphic_allele_sum(cc, variant_counts)
        encrypted_sums.append(encrypted_sum)
    
    return encrypted_sums

def main():
    # Get the input file path
    if len(sys.argv) < 2:
        encrypted_file = "encrypted_data.bin"
    else:
        encrypted_file = sys.argv[1]
    
    # Initialize the crypto context
    cc = CryptoContextFactory.genCryptoContextBFV(
        PARAMS["plaintextModulus"],
        PARAMS["securityLevel"],
        8,  # Standard deviation
        4,  # Maximum depth
        0,  # Key switching technique
        2   # Ring dimension
    )
    
    cc.Enable(PKESchemeFeature.PKE)
    cc.Enable(PKESchemeFeature.KEYSWITCH)
    cc.Enable(PKESchemeFeature.LEVELEDSHE)
    
    # Load encrypted data
    print(f"Loading encrypted data from {encrypted_file}")
    encrypted_counts = load_ciphertext(encrypted_file)
    
    # Process the encrypted data
    print("Calculating allele frequencies...")
    encrypted_sums = calculate_allele_frequencies(cc, encrypted_counts)
    
    # Save results
    os.makedirs("results", exist_ok=True)
    save_ciphertext("results/allele_sums.bin", encrypted_sums)
    print("Encrypted results saved to results/allele_sums.bin")

if __name__ == "__main__":
    main() 