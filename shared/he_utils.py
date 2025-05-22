from openfhe import *
import pickle

def generate_keys(params):
    """Generate encryption keys for homomorphic encryption"""
    cc = CryptoContextFactory.genCryptoContextBFV(
        params["plaintextModulus"],
        params["securityLevel"],
        8,  # Standard deviation
        4,  # Maximum depth
        0,  # Key switching technique
        2   # Ring dimension
    )
    
    cc.Enable(PKESchemeFeature.PKE)
    cc.Enable(PKESchemeFeature.KEYSWITCH)
    cc.Enable(PKESchemeFeature.LEVELEDSHE)
    
    # Generate key pair
    key_pair = cc.KeyGen()
    
    # Generate evaluation keys for homomorphic operations
    cc.EvalMultKeyGen(key_pair.secretKey)
    cc.EvalSumKeyGen(key_pair.secretKey)
    
    return cc, key_pair

def encrypt_allele_count(cc, public_key, count):
    """Encrypt a single allele count"""
    plaintext = Plaintext()
    plaintext.SetIntegerValue(count)
    ciphertext = cc.Encrypt(public_key, plaintext)
    return ciphertext

def decrypt_allele_count(cc, secret_key, ciphertext):
    """Decrypt an allele count"""
    plaintext = cc.Decrypt(secret_key, ciphertext)
    return plaintext.GetIntegerValue()

def homomorphic_allele_sum(cc, ciphertexts):
    """
    Compute the sum of encrypted allele counts.
    This correctly adds the ciphertexts together using homomorphic addition.
    """
    if not ciphertexts:
        raise ValueError("No ciphertexts provided")
    
    # Start with the first ciphertext
    result = ciphertexts[0]
    
    # Add the remaining ciphertexts
    for ct in ciphertexts[1:]:
        result = cc.EvalAdd(result, ct)
    
    return result

def save_ciphertext(filename, ciphertext):
    """Save a ciphertext to a file"""
    with open(filename, 'wb') as f:
        pickle.dump(ciphertext, f)

def load_ciphertext(filename):
    """Load a ciphertext from a file"""
    with open(filename, 'rb') as f:
        return pickle.load(f)

def save_keys(cc, key_pair, public_key_file, secret_key_file):
    """Save encryption keys to files"""
    with open(public_key_file, 'wb') as f:
        pickle.dump((cc, key_pair.publicKey), f)
    
    with open(secret_key_file, 'wb') as f:
        pickle.dump((cc, key_pair.secretKey), f)

def load_public_key(filename):
    """Load the public key from a file"""
    with open(filename, 'rb') as f:
        return pickle.load(f)

def load_secret_key(filename):
    """Load the secret key from a file"""
    with open(filename, 'rb') as f:
        return pickle.load(f) 