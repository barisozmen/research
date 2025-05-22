import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.he_utils import generate_keys, encrypt_allele_count, save_keys, save_ciphertext
from shared.config import PARAMS

def parse_gt_field(gt_field):
    """
    Parse the genotype field from a VCF file and convert to allele count:
    0/0 or 0|0 -> 0 (homozygous reference)
    0/1, 1/0, 0|1, or 1|0 -> 1 (heterozygous)
    1/1 or 1|1 -> 2 (homozygous alternate)
    """
    if gt_field in ['0/0', '0|0']:
        return 0
    elif gt_field in ['0/1', '1/0', '0|1', '1|0']:
        return 1
    elif gt_field in ['1/1', '1|1']:
        return 2
    else:
        # Handle missing or unknown genotypes
        return 0

def process_vcf_file(filename, cc, public_key):
    """
    Process a VCF file and encrypt allele counts.
    Returns a list of encrypted counts for each variant.
    """
    encrypted_counts = []
    
    with open(filename, 'r') as vcf_file:
        for line in vcf_file:
            # Skip header lines
            if line.startswith('#'):
                continue
                
            # Parse the VCF line
            fields = line.strip().split('\t')
            
            # Assuming FORMAT is at index 8 and the sample data starts at index 9
            format_field = fields[8].split(':')
            gt_index = format_field.index('GT') if 'GT' in format_field else 0
            
            # Process each sample in the VCF file
            sample_counts = []
            for sample_idx in range(9, len(fields)):
                sample_data = fields[sample_idx].split(':')
                if len(sample_data) > gt_index:
                    gt_field = sample_data[gt_index]
                    allele_count = parse_gt_field(gt_field)
                    
                    # Encrypt the allele count
                    encrypted_count = encrypt_allele_count(cc, public_key, allele_count)
                    sample_counts.append(encrypted_count)
            
            encrypted_counts.append(sample_counts)
    
    return encrypted_counts

def main():
    # Check if a VCF file is provided
    if len(sys.argv) < 2:
        print("Usage: python encrypt_vcf.py <vcf_file>")
        return
    
    vcf_file = sys.argv[1]
    
    # Generate encryption keys
    print("Generating encryption keys...")
    cc, key_pair = generate_keys(PARAMS)
    
    # Save keys
    os.makedirs("keys", exist_ok=True)
    save_keys(cc, key_pair, "keys/public.key", "keys/secret.key")
    print("Keys saved to keys/public.key and keys/secret.key")
    
    # Process the VCF file
    print(f"Processing VCF file: {vcf_file}")
    encrypted_counts = process_vcf_file(vcf_file, cc, key_pair.publicKey)
    
    # Save encrypted counts
    save_ciphertext("encrypted_data.bin", encrypted_counts)
    print("Encrypted data saved to encrypted_data.bin")

if __name__ == "__main__":
    main() 