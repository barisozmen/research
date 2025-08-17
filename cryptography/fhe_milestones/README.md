# FHE Milestones

[1978] RSA: Multiplicative homomorphism
[1982] Goldwasser-Micali: Additive homomorphism (mod 2)
[1999] Paillier: Additive homomorphism (mod n)
[2005] LWE: Lattice-based somewhat HE
[2009] RLWE: Ring-LWE
[2010-2013] BGV: RLWE-based FHE
[2012] modulus switching: RLWE-based FHE
[2014] relinearization: RLWE-based FHE


### Build from scratch implementation order
1. RSA
	1. homomorphic multiplication
2. Goldwasser-Micali
	1. homomorphic addition (mod 2)
3. Paillier
	1. homomorphic addition (mod n)
4. LWE
	1. somewhat HE
5. RLWE
6. RLWE + bootstrapping
7.  [ 6 ] + modulus switching
8.  [ 7 ] + relinearization

