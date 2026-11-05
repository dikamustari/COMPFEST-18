# COMPFEST 18 CTF — Cryptography Write-Up

## Challenge: hello

**Category:** Cryptography  
**Competition:** COMPFEST 18 CTF  
**Challenge Files:**
- `chall.sage` — Source code challenge.
- `solevrr.py` — Python solver.

---

## 1. Challenge Overview

Challenge `hello` merupakan soal cryptography yang menggunakan modifikasi dari skema RSA.

Pada soal ini, pesan dienkripsi menggunakan operasi perpangkatan dalam polynomial quotient ring:

\[
R = \mathbb{Z}_N[x]/(x^{10}-2)
\]

Challenge memberikan beberapa informasi penting, yaitu:
- Public modulus \(N = p \cdot q\).
- Public exponent \(e\).
- Ciphertext \(c\), berupa elemen polynomial quotient ring.

Tujuan utama adalah memperoleh kembali plaintext dengan memanfaatkan kelemahan matematis pada pembentukan private exponent dan struktur polynomial ring yang digunakan.

## 2. Vulnerability Identification

Setelah menganalisis source code `chall.sage`, ditemukan bahwa challenge membentuk:

\[
\phi = (p^{10}-1)(q^{10}-1)
\]

Private exponent kecil \(d\) dipilih terlebih dahulu, kemudian public exponent dibentuk menggunakan:

\[
e = (\phi-d)^{-1} \pmod{\phi}
\]

Dari persamaan tersebut diperoleh:

\[
ed \equiv -1 \pmod{\phi}
\]

Sehingga terdapat suatu bilangan bulat \(k\) yang memenuhi:

\[
ed+1=k\phi
\]

Hubungan ini menjadi titik utama untuk melakukan serangan terhadap private exponent.

## 3. Exploitation Strategy

### Step 1 — Generalized Wiener Attack

Karena nilai \(d\) relatif kecil terhadap modulus, hubungan antara \(e\) dan \(\phi\) dapat dimanfaatkan menggunakan pendekatan Continued Fraction.

Dengan pendekatan:

\[
\phi \approx N^{10}
\]

diperoleh:

\[
\frac{e}{N^{10}} \approx \frac{k}{d}
\]

Program kemudian menghitung continued fraction convergents dari:

\[
\frac{e}{N^{10}}
\]

Setiap pasangan kandidat \((k,d)\) diperiksa menggunakan:

\[
\phi = \frac{ed+1}{k}
\]

Jika kandidat \(\phi\) benar, maka:

\[
N^{10}-\phi+1=p^{10}+q^{10}
\]

Sementara itu:

\[
N^{10}=p^{10}q^{10}
\]

Dengan demikian, \(p^{10}\) dan \(q^{10}\) dapat diperoleh sebagai akar persamaan kuadrat:

\[
z^2-(p^{10}+q^{10})z+N^{10}=0
\]

Setelah itu, dilakukan exact integer tenth-root untuk mendapatkan nilai \(p\) dan \(q\).

Kandidat diverifikasi dengan:

\[
p \cdot q=N
\]

### Step 2 — Understanding the Polynomial Ring

Setelah memperoleh \(p\) dan \(q\), langkah selanjutnya adalah mendekripsi ciphertext.

Namun, penggunaan private exponent hasil serangan secara langsung tidak menghasilkan plaintext yang benar.

Penyebabnya adalah polynomial:

\[
f(x)=x^{10}-2
\]

tidak irreducible terhadap field modulo \(p\) maupun modulo \(q\).

Artinya, polynomial quotient ring yang digunakan bukanlah sebuah field sederhana. Oleh karena itu, rumus dekripsi standar dengan menggunakan satu nilai Euler totient tidak dapat langsung diterapkan.

### Step 3 — Computing the True Unit Group Exponent

Untuk mengatasi masalah tersebut, dilakukan factorization terhadap:

\[
x^{10}-2
\]

pada masing-masing field:

\[
\mathbb{F}_p \quad \text{dan} \quad \mathbb{F}_q
\]

Solver menggunakan Distinct Degree Factorization (DDF) untuk memperoleh derajat faktor-faktor irreducible.

Jika derajat faktor irreducible yang ditemukan adalah \(d_i\), exponent dari komponen field terkait membagi:

\[
p^{d_i}-1
\]

Kemudian dihitung least common multiple untuk mendapatkan exponent pada masing-masing modulus:

\[
L_p=\operatorname{lcm}(p^{d_1}-1,\ldots,p^{d_m}-1)
\]

\[
L_q=\operatorname{lcm}(q^{d_1}-1,\ldots,q^{d_n}-1)
\]

Selanjutnya, kedua nilai tersebut digabungkan:

\[
L=\operatorname{lcm}(L_p,L_q)
\]

Nilai \(L\) digunakan untuk menghitung true decryption exponent:

\[
d_{\text{true}}=e^{-1}\pmod L
\]

Dengan demikian, exponent yang digunakan sudah menyesuaikan struktur unit group dari polynomial quotient ring.

### Step 4 — Decrypting the Ciphertext

Setelah mendapatkan \(d_{\text{true}}\), ciphertext dapat didekripsi menggunakan modular polynomial exponentiation:

\[
m=c^{d_{\text{true}}}\pmod{N,\;x^{10}-2}
\]

Solver mengimplementasikan operasi perkalian dan perpangkatan polynomial secara manual menggunakan modular arithmetic.

Setiap hasil perkalian direduksi berdasarkan relasi:

\[
x^{10}=2
\]

Hasil dekripsi berupa sepuluh koefisien integer yang merepresentasikan potongan-potongan plaintext.

### Step 5 — Recovering the Flag

Plaintext sebelumnya diubah menjadi sepuluh integer menggunakan `int.from_bytes()` dengan pembagian pesan menjadi beberapa chunk.

Untuk mendapatkan kembali pesan asli, setiap koefisien dikonversi menjadi bytes menggunakan big-endian representation.

Terakhir, padding dihapus dan hasilnya didekode menjadi string.

## 4. Solver Implementation

Seluruh proses eksploitasi diimplementasikan dalam `solevrr.py`.

Berikut beberapa fungsi utama yang digunakan:

| Function | Description |
|---|---|
| `parse_chall_file()` | Membaca nilai N, e, dan ciphertext dari challenge file. |
| `cf_convergents()` | Menghasilkan continued fraction convergents. |
| `recover_pq_and_d()` | Memulihkan p, q, dan kandidat private exponent. |
| `distinct_degree_factorization()` | Melakukan factorization berdasarkan derajat faktor irreducible. |
| `true_decryption_exponent()` | Menghitung true unit group exponent dan decryption exponent. |
| `poly_mul()` | Melakukan perkalian polynomial modular. |
| `poly_pow()` | Melakukan perpangkatan polynomial modular. |
| `decrypt()` | Mendekripsi ciphertext. |
| `coeffs_to_flag()` | Mengonversi koefisien plaintext menjadi flag. |

### How to Run

Pastikan Python 3 sudah terinstal.

Jalankan solver dengan:

```bash
python3 solevrr.py chall.sage
```

Solver akan menjalankan seluruh tahapan secara otomatis, mulai dari parsing challenge, pemulihan private key, perhitungan exponent, hingga dekripsi plaintext.

## 5. Result

<details>
<summary>Recovered Flag</summary>

```text
COMPFEST18{c0ngr4tzzz_h3ngk3rrrr_g3n3r4l1Zed_w13n3R_4ttacK}
```

</details>

## 6. Conclusion

Challenge `hello` menggabungkan konsep RSA, Continued Fraction, Generalized Wiener Attack, polynomial factorization, dan modular arithmetic.

Poin penting dari penyelesaian challenge ini adalah:

1. Memanfaatkan hubungan \(ed \equiv -1 \pmod{\phi}\) untuk melakukan Generalized Wiener Attack.
2. Memulihkan faktor prima \(p\) dan \(q\) dari modulus \(N\).
3. Memahami bahwa polynomial \(x^{10}-2\) tidak irreducible pada field yang digunakan.
4. Menghitung true unit group exponent berdasarkan struktur polynomial quotient ring.
5. Melakukan dekripsi dan mengonversi hasilnya menjadi plaintext.

Challenge ini menunjukkan bahwa memahami struktur aljabar yang digunakan dalam proses enkripsi sama pentingnya dengan memahami algoritma RSA itu sendiri.

---

**Tools & Concepts:**
- Python 3
- SageMath (challenge source)
- RSA Cryptography
- Generalized Wiener Attack
- Continued Fractions
- Polynomial Factorization
- Distinct Degree Factorization
- Modular Arithmetic
