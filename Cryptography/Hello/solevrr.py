import sys
import re
import json
import math

sys.set_int_max_str_digits(200000)

N_RING = 10   # ring degree "n" in x^n - r
R_CONST = 2   # "r" in x^n - r

def poly_mul(a, b, mod, n=N_RING, r=R_CONST):
    res = [0] * (2 * n - 1)
    for i in range(n):
        if a[i] == 0:
            continue
        ai = a[i]
        for j in range(n):
            if b[j] == 0:
                continue
            res[i + j] = (res[i + j] + ai * b[j]) % mod
    out = [0] * n
    for i in range(2 * n - 1):
        if res[i] == 0:
            continue
        if i < n:
            out[i] = (out[i] + res[i]) % mod
        else:
            out[i - n] = (out[i - n] + res[i] * r) % mod
    return out

def poly_pow(a, exp, mod, n=N_RING, r=R_CONST):
    result = [0] * n
    result[0] = 1
    base = a[:]
    e_ = exp
    while e_ > 0:
        if e_ & 1:
            result = poly_mul(result, base, mod, n, r)
        base = poly_mul(base, base, mod, n, r)
        e_ >>= 1
    return result

def trim(a):
    a = a[:]
    while len(a) > 1 and a[-1] == 0:
        a.pop()
    return a

def psub_full(a, b, mod):
    L = max(len(a), len(b))
    res = [0] * L
    for i in range(len(a)):
        res[i] = (res[i] + a[i]) % mod
    for i in range(len(b)):
        res[i] = (res[i] - b[i]) % mod
    return trim(res)

def pdivmod_generic(a, b, mod):
    a = trim(a)
    b = trim(b)
    inv_lead = pow(b[-1], mod - 2, mod)
    quo = [0] * (max(len(a) - len(b) + 1, 1))
    aa = a[:]
    while len(aa) >= len(b) and not (len(aa) == 1 and aa[0] == 0):
        shift = len(aa) - len(b)
        if shift < 0:
            break
        coef = (aa[-1] * inv_lead) % mod
        quo[shift] = coef
        sub = [0] * shift + [(coef * bi) % mod for bi in b]
        aa = psub_full(aa, sub, mod)
        aa = trim(aa)
        if aa == [0]:
            break
    return trim(quo), aa

def poly_gcd_generic(a, b, mod):
    a = trim(a)
    b = trim(b)
    while not (len(b) == 1 and b[0] == 0):
        _, r_ = pdivmod_generic(a, b, mod)
        a, b = b, r_
    return a

def distinct_degree_factorization(prime, n=N_RING, r=R_CONST):
    """Return list of (degree, multiplicity) for the irreducible factors
    of x^n - r over F_prime."""
    f = trim([(-r) % prime] + [0] * (n - 1) + [1])
    x_repr = [0, 1] + [0] * (n - 2)
    rem = f[:]
    factors = []
    for d in range(1, n + 1):
        if len(rem) - 1 < d:
            break
        h_d = poly_pow(x_repr, prime ** d, prime, n, r)
        _, h_d_mod_rem = pdivmod_generic(h_d, rem, prime)
        _, x_mod_rem = pdivmod_generic(x_repr, rem, prime)
        diff = psub_full(h_d_mod_rem, x_mod_rem, prime)
        g = poly_gcd_generic(rem, diff, prime)
        gdeg = len(trim(g)) - 1
        if gdeg > 0:
            mult = gdeg // d
            factors.append((d, mult))
            rem, remainder = pdivmod_generic(rem, g, prime)
            rem = trim(rem)
            assert remainder == [0]
        if len(rem) == 1:
            break
    if len(rem) > 1:
        factors.append((len(rem) - 1, 1))
    return factors

def parse_chall_file(path):
    with open(path) as f:
        content = f.read()
    m_n = re.search(r'#\s*N\s*=\s*(\d+)', content)
    m_e = re.search(r'#\s*e\s*=\s*(\d+)', content)
    m_c = re.search(r'#\s*c\s*=\s*(.+)', content)
    if not (m_n and m_e and m_c):
        raise ValueError("Could not find N/e/c in the given file. "
                          "If you got a fresh instance from `nc`, use "
                          "parse_from_strings() instead.")
    N = int(m_n.group(1))
    e = int(m_e.group(1))
    coeffs = parse_c_string(m_c.group(1))
    return N, e, coeffs

def parse_c_string(cstr):
    """Parse a Sage-printed ring element like '...*t^9 + ... + const' into
    a dict {power: coeff}."""
    cstr = cstr.strip()
    terms = cstr.split(' + ')
    coeffs = {}
    for term in terms:
        term = term.strip()
        if '*t^' in term:
            coef, pw = term.split('*t^')
            coeffs[int(pw)] = int(coef)
        elif '*t' in term:
            coef = term.split('*t')[0]
            coeffs[1] = int(coef)
        else:
            coeffs[0] = int(term)
    return coeffs

def cf_convergents(num, den):
    h_prev2, h_prev1 = 0, 1
    k_prev2, k_prev1 = 1, 0
    a, b = num, den
    while b:
        q = a // b
        a, b = b, a - q * b
        h = q * h_prev1 + h_prev2
        k = q * k_prev1 + k_prev2
        yield h, k
        h_prev2, h_prev1 = h_prev1, h
        k_prev2, k_prev1 = k_prev1, k

def nth_root_exact(x, n):
    if x < 0:
        return None
    if x == 0:
        return 0
    bl = x.bit_length()
    hi = 1 << (bl // n + 2)
    while hi ** n < x:
        hi <<= 1
    lo = 0
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if mid ** n <= x:
            lo = mid
        else:
            hi = mid - 1
    return lo if lo ** n == x else None

def recover_pq_and_d(N, e, n=N_RING):
    """Continued-fraction attack on e / N^n to find (k, d) with
    e*d + 1 = k*phi, then recover p, q from phi."""
    Nn = N ** n
    for k, d in cf_convergents(e, Nn):
        if k == 0 or d == 0:
            continue
        numerator = e * d + 1
        if numerator % k != 0:
            continue
        phi_cand = numerator // k
        if phi_cand <= 0:
            continue
        S = Nn - phi_cand + 1                     
        if S <= 0:
            continue
        disc = S * S - 4 * Nn
        if disc < 0:
            continue
        sq = math.isqrt(disc)
        if sq * sq != disc or (S - sq) % 2 != 0:
            continue
        z1, z2 = (S - sq) // 2, (S + sq) // 2
        p_cand = nth_root_exact(z1, n)
        q_cand = nth_root_exact(z2, n)
        if p_cand and q_cand and p_cand * q_cand == N:
            return p_cand, q_cand, d, k, phi_cand
    raise RuntimeError("Attack failed: no valid (p, q, d) found. "
                        "d may be outside the attack's bound.")

def true_decryption_exponent(p, q, e, n=N_RING, r=R_CONST):
    facs_p = distinct_degree_factorization(p, n, r)
    facs_q = distinct_degree_factorization(q, n, r)

    def group_exponent(prime, facs):
        L = 1
        for d, _mult in facs:
            L = L * (prime ** d - 1) // math.gcd(L, prime ** d - 1)
        return L

    Lp = group_exponent(p, facs_p)
    Lq = group_exponent(q, facs_q)
    L = Lp * Lq // math.gcd(Lp, Lq)

    if math.gcd(e, L) != 1:
        raise RuntimeError("e is not invertible mod the true group exponent")

    d_true = pow(e, -1, L)
    return d_true, facs_p, facs_q

def decrypt(N, coeffs, d_true, n=N_RING, r=R_CONST):
    c = [coeffs.get(i, 0) % N for i in range(n)]
    m = poly_pow(c, d_true, N, n, r)
    return m


def coeffs_to_flag(m_coeffs, chunk_size=6):
    raw = b''.join(x.to_bytes(chunk_size, 'big') for x in m_coeffs)
    if raw:
        pad_len = raw[-1]
        if 1 <= pad_len <= 16 and raw[-pad_len:] == bytes([pad_len]) * pad_len:
            raw = raw[:-pad_len]
    return raw

def solve(path):
    print("[*] Parsing challenge instance...")
    N, e, coeffs = parse_chall_file(path)
    print(f"    N: {N.bit_length()} bits, e: {e.bit_length()} bits")

    print("[*] Recovering d via generalized Wiener (continued fraction) attack...")
    p, q, d, k, phi = recover_pq_and_d(N, e)
    print(f"    Found p ({p.bit_length()} bits), q ({q.bit_length()} bits)")
    print(f"    d: {d.bit_length()} bits, k: {k.bit_length()} bits")
    assert p * q == N and phi == (p ** N_RING - 1) * (q ** N_RING - 1)

    print("[*] x^10 - 2 is not irreducible mod p / mod q -> computing the "
          "true unit-group exponent...")
    d_true, facs_p, facs_q = true_decryption_exponent(p, q, e)
    print(f"    factor degrees mod p: {facs_p}")
    print(f"    factor degrees mod q: {facs_q}")
    print(f"    true decryption exponent: {d_true.bit_length()} bits")

    print("[*] Decrypting...")
    m = decrypt(N, coeffs, d_true)

    flag = coeffs_to_flag(m)
    print("[+] Flag:", flag.decode(errors="replace"))
    return flag


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "chall.sage"
    solve(path)
