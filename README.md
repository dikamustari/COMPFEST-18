# COMPFEST 18 CTF - Cryptography

## Challenge: hello

**Category:** Cryptography

### Description

This challenge utilizes an RSA scheme modified with a polynomial quotient ring. The objective is to recover the plaintext from the given ciphertext.

### Solution

1. **Source Code Analysis**

   Analyze `chall.sage` to understand the encryption process and identify a relationship between the public exponent and the private exponent that can be exploited.

2. **Generalized Wiener Attack**

   Apply a Continued Fraction-based approach to recover the private exponent and determine the prime factors `p` and `q` of the modulus `N`.

3. **Polynomial Factorization**

   Standard decryption using the recovered private exponent fails because the polynomial `x^10 - 2` is not irreducible modulo `p` or `q`.

4. **Recovering the True Decryption Exponent**

   Perform Distinct Degree Factorization (DDF) to determine the factorization structure of the polynomial, then calculate the correct decryption exponent.

5. **Decryption**

   Use the calculated exponent to decrypt the ciphertext, then convert the resulting coefficients back into the plaintext.

### Usage

Run the solver using:

```bash
python3 solevrr.py chall.sage
```

### Flag

```text
COMPFEST18{c0ngr4tzzz_h3ngk3rrrr_g3n3r4l1Zed_w13n3R_4ttacK}
```
