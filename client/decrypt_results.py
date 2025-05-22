import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.he_utils import load_secret_key, load_ciphertext, decrypt_allele_count
from shared.config import PARAMS

def main():
    # Check if result file is provided
    if len(sys.argv) < 2:
        result_file = "../server/results/allele_sums.bin"
    else:
        result_file = sys.argv[1]
    
    # Load secret key
    print("Loading secret key...")
    cc, secret_key = load_secret_key("keys/secret.key")
    
    # Load encrypted results
    print(f"Loading encrypted results from {result_file}")
    encrypted_sums = load_ciphertext(result_file)
    
    # Decrypt and calculate allele frequencies
    print("Decrypting and calculating allele frequencies:")
    
    # Define the total number of samples (this should be known to the client)
    num_samples = 3  # From our sample VCF
    
    for i, encrypted_sum in enumerate(encrypted_sums):
        # Decrypt the sum
        allele_sum = decrypt_allele_count(cc, secret_key, encrypted_sum)
        
        # Calculate allele frequency
        # Each sample contributes 2 alleles (diploid organism)
        total_alleles = num_samples * 2
        allele_frequency = allele_sum / total_alleles
        
        print(f"Variant {i+1}: Sum={allele_sum}, Frequency={allele_frequency:.4f}")

if __name__ == "__main__":
    main() 