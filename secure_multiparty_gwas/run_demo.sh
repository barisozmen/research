#!/bin/bash

echo "=== VCF Homomorphic Encryption Demo ==="
echo

echo "1. Running client encryption..."
cd client
python encrypt_vcf.py sample.vcf
echo

echo "2. Copying encrypted data to server..."
cp encrypted_data.bin ../server/
cd ../server
echo

echo "3. Processing encrypted data on server..."
python process_encrypted.py
echo

echo "4. Decrypting results on client..."
cd ../client
python decrypt_results.py ../server/results/allele_sums.bin
echo

echo "Demo completed!" 