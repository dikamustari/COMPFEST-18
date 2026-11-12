# COMPFEST 18 CTF - Cryptography

## Challenge: hello

**Category:** Cryptography

### Description

Challenge ini menggunakan skema RSA yang dimodifikasi dengan polynomial quotient ring. Tujuannya adalah menemukan kembali plaintext dari ciphertext yang diberikan.

### Solution

1. **Source Code Analysis**

   Melakukan analisis pada `chall.sage` untuk memahami proses enkripsi dan menemukan hubungan antara public exponent dan private exponent yang dapat dimanfaatkan.

2. **Generalized Wiener Attack**

   Menggunakan Continued Fraction untuk memulihkan private exponent serta mendapatkan faktor prima `p` dan `q` dari modulus `N`.

3. **Polynomial Factorization**

   Dekripsi menggunakan private exponent biasa ternyata tidak berhasil karena polynomial `x^10 - 2` tidak irreducible modulo `p` maupun `q`.

4. **Recovering the True Decryption Exponent**

   Melakukan Distinct Degree Factorization (DDF) untuk memperoleh struktur faktor polynomial, kemudian menghitung true decryption exponent yang sesuai.

5. **Decryption**

   Menggunakan exponent tersebut untuk mendekripsi ciphertext, kemudian mengonversi hasil koefisien menjadi plaintext.

### Usage

Jalankan solver dengan:

```bash
python3 solevrr.py chall.sage
```

### Flag

```text
COMPFEST18{c0ngr4tzzz_h3ngk3rrrr_g3n3r4l1Zed_w13n3R_4ttacK}
```
