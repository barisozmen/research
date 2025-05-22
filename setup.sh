#!/bin/bash
# Create project directory structure
mkdir -p vcf-homomorphic-privacy/client/keys
mkdir -p vcf-homomorphic-privacy/server/results
mkdir -p vcf-homomorphic-privacy/shared

cd vcf-homomorphic-privacy

# Initialize git repository
git init
echo "# VCF Homomorphic Encryption Privacy Demo" > README.md
echo "__pycache__/" > .gitignore
echo "*.pyc" >> .gitignore
echo "venv/" >> .gitignore
echo "*.bin" >> .gitignore
echo "*.key" >> .gitignore
echo "*.ct" >> .gitignore

# Setup Python environment
python -m venv venv
source venv/bin/activate
pip install openfhe
pip freeze > requirements.txt 