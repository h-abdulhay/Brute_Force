"""
NexaBank local security lab — based on the supplied SecureVault app.
LOCALHOST ONLY. Educational demo, not production banking software.
Preserves honeypot, per-username escalating lockout, image CAPTCHA,
/ captcha.png endpoint, and the original CAPTCHA refresh lifecycle.
"""
import io
import random
import time
import logging
from pathlib import Path
from functools import wraps

from flask import Flask, request, render_template_string, session, Response, redirect, url_for, abort
from PIL import Image, ImageDraw, ImageFont
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "demo-secret-key-faqat-local-uchun"

USERS = {
    "admin": {"password": generate_password_hash("AdminDemo2026!"), "email": "admin@nexabank.local", "role": "ADMIN", "balance": 12450000},
    "j.miller": {"password": generate_password_hash("MillerDemo2026!"), "email": "j.miller@nexabank.local", "role": "USER", "balance": 3200000},
    "a.karimov": {"password": generate_password_hash("KarimovDemo2026!"), "email": "a.karimov@nexabank.local", "role": "USER", "balance": 7800000},
    "n.yusupova": {"password": generate_password_hash("YusupovaDemo2026!"), "email": "n.yusupova@nexabank.local", "role": "USER", "balance": 1500000},
}
attempts = {}
MAX_FAILS_PER_CYCLE = 4
LOCKOUT_STAGES = [5, 10, 20, 40,999999]
CAPTCHA_CHARS = "23456789"
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
BASE_DIR = Path(__file__).resolve().parent
LOG_PATH = BASE_DIR / "nexabank_lab.log"

logger = logging.getLogger("nexabank_lab")
logger.setLevel(logging.INFO)
if not logger.handlers:
    fh = logging.FileHandler(LOG_PATH, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
    logger.addHandler(fh)

DEMO_TOKEN = "nx_demo_local_only_7F3A9C2D"  # display-only placeholder


def log_event(event, username="-", detail="-"):
    logger.info("%s | user=%s | %s", event, str(username)[:80], str(detail)[:180])


def new_captcha_text(length=4):
    return "".join(random.choice(CAPTCHA_CHARS) for _ in range(length))


def render_captcha_png(text):
    img = Image.new("RGB", (200, 70), color=(248, 248, 255))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(FONT_PATH, 44)
    except Exception:
        font = ImageFont.load_default()
    for i, ch in enumerate(text):
        draw.text((12 + i * 46, random.randint(6, 14)), ch, font=font,
                  fill=(random.randint(0, 60), random.randint(0, 60), random.randint(30, 100)))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        if USERS.get(session.get("username", ""), {}).get("role") != "ADMIN":
            abort(403)
        return view(*args, **kwargs)
    return wrapped


LOGIN_PAGE = """
<!doctype html><html lang="uz"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>NexaBank — Kirish</title>
<style>
*{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;padding:20px;
font-family:Segoe UI,sans-serif;background:linear-gradient(135deg,#071b33,#0c3152 60%,#17617b)}
.card{width:min(420px,100%);background:#fff;border-radius:20px;padding:36px;box-shadow:0 25px 70px #00152b88}
.brand{text-align:center;font-size:29px;font-weight:800;color:#123d63}.brand span{color:#1b9c83}
.sub{text-align:center;color:#8492a2;font-size:11px;letter-spacing:2px;margin:6px 0 27px}
label{display:block;margin:16px 0 7px;font-size:12px;font-weight:700;color:#40546a}
input[type=text],input[type=password]{width:100%;padding:13px;border:1px solid #dce4ec;border-radius:9px;outline:none}
input:focus{border-color:#218b91}.hp-field{position:absolute;left:-9999px;top:-9999px}
button{width:100%;margin-top:23px;padding:14px;border:0;border-radius:9px;background:#123e64;color:white;font-weight:700;cursor:pointer}
.message{margin-top:16px;padding:11px;border-radius:8px;text-align:center;font-size:13px}
.msg-error{background:#fff0ef;color:#ad352d}.msg-lock{background:#fff4e6;color:#a65a0a}
.captcha-box{text-align:center;margin-top:16px}.captcha-box img{display:block;margin:auto;border:1px solid #e4e9ef;border-radius:7px}
.note{text-align:center;color:#8795a5;font-size:11px;margin-top:22px;line-height:1.6}
</style></head><body><main class="card"><div class="brand">Nexa<span>Bank</span></div>
<div class="sub">SECURE DIGITAL BANKING</div>
<form method="POST">
<label>FOYDALANUVCHI NOMI</label><input type="text" name="username" autocomplete="off" required>
<label>PAROL</label><input type="password" name="password" required>
<div class="hp-field"><label>Email</label><input type="text" name="confirm_email" tabindex="-1" autocomplete="off"></div>
{% if captcha_required %}<div class="captcha-box"><img src="/captcha.png?v={{ cache_bust }}" alt="CAPTCHA">
<label>Rasmdagi kodni kiriting</label><input type="text" name="captcha" autocomplete="off"></div>{% endif %}
<button type="submit">Tizimga kirish</button></form>
{% if message %}<div class="message {{ msg_class }}">{{ message }}</div>{% endif %}
<div class="note">LOCALHOST SECURITY LAB · Faqat o‘quv maqsadida</div></main></body></html>
"""

DASHBOARD_PAGE = """
<!doctype html><html lang="uz"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>NexaBank — Dashboard</title><style>
*{box-sizing:border-box}body{margin:0;background:#f3f6fa;color:#18344e;font-family:Segoe UI,sans-serif}
header{height:70px;background:white;border-bottom:1px solid #e6edf3;display:flex;align-items:center;justify-content:space-between;padding:0 5%}
.brand{font-size:23px;font-weight:850;color:#123d63}.brand span{color:#1b9c83}.right{display:flex;gap:18px;align-items:center;color:#738397;font-size:13px}
a{text-decoration:none;color:inherit}.logout{padding:9px 14px;border:1px solid #dce5ed;border-radius:9px;color:#24516f;font-weight:650}
main{width:min(1120px,92%);margin:32px auto}.muted{color:#8291a1;font-size:13px}.hello h1{margin:7px 0;color:#1a3d5c;font-size:27px}
.grid{display:grid;grid-template-columns:1.5fr 1fr;gap:18px;margin-top:22px}
.balance{background:linear-gradient(120deg,#10385e,#17678b);color:white;border-radius:17px;padding:27px;min-height:190px}
.balance small{color:#c9dce8}.amount{font-size:34px;font-weight:800;margin:13px 0}.pill{display:inline-block;background:#ffffff22;padding:7px 11px;border-radius:18px;font-size:11px}
.panel,.action{background:white;border:1px solid #e7edf2;border-radius:16px;padding:21px}.panel h3{margin:0 0 13px}
.row{display:flex;justify-content:space-between;padding:11px 0;border-bottom:1px solid #edf1f5;font-size:13px}.row:last-child{border:0}.row span{color:#8492a1}
.actions{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:19px}.action b{display:block;margin:9px 0 5px;color:#244b69}
.action small{color:#8392a1;line-height:1.5}.notice{margin-top:20px;padding:15px;background:#eaf4f8;border:1px solid #d9e9ef;border-radius:12px;color:#49677c;font-size:13px;line-height:1.6}
@media(max-width:720px){.grid{grid-template-columns:1fr}.actions{grid-template-columns:1fr}.right .email{display:none}.amount{font-size:28px}}
</style></head><body><header><div class="brand">Nexa<span>Bank</span></div>
<div class="right"><span class="email">{{ email }}</span><span>{{ username }}</span><a class="logout" href="/logout">Chiqish</a></div></header>
<main><div class="hello"><small class="muted">SHAXSIY KABINET / BOSH SAHIFA</small>
<h1>Xush kelibsiz, {{ username }}!</h1><p class="muted">Moliyaviy ma’lumotlaringiz va demo xizmatlaringiz.</p></div>
<div class="grid"><section class="balance"><small>JAMI HISOB BALANSI</small>
<div class="amount">{{ balance }} UZS</div><small>NexaBank demo hisob raqami</small><br><br><span class="pill">● Hisob faol</span></section>
<section class="panel"><h3>Hisob ma’lumotlari</h3>
<div class="row"><span>Foydalanuvchi</span><b>{{ username }}</b></div>
<div class="row"><span>Email</span><b>{{ email }}</b></div>
<div class="row"><span>Hisob turi</span><b>{{ role }}</b></div>
<div class="row"><span>Valyuta</span><b>UZS</b></div></section></div>
<div class="actions"><a class="action" href="/token">◈<b>Demo token</b><small>Namuna API tokenini ko‘rish</small></a>
<a class="action" href="/logs">▤<b>Xavfsizlik loglari</b><small>Laboratoriyadagi hodisalar tarixi</small></a>
{% if is_admin %}<a class="action" href="/admin">⚙<b>Admin panel</b><small>Foydalanuvchilar va himoya sozlamalari</small></a>
{% else %}<div class="action">◉<b>Profil xavfsizligi</b><small>Hisobingiz himoyasi faol</small></div>{% endif %}</div>
<div class="notice">Bu lokal o‘quv laboratoriyasi. Balanslar va token namuna uchun; haqiqiy bank operatsiyalari bajarilmaydi.</div>
</main></body></html>
"""

TOKEN_PAGE = """<!doctype html><html lang="uz"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Demo token</title><style>body{font-family:Segoe UI;background:#f3f6fa;color:#183650;margin:0}
main{max-width:760px;margin:50px auto;padding:22px}.card{background:white;border:1px solid #e5ebf1;border-radius:16px;padding:26px}
a{color:#147b83;text-decoration:none;font-weight:700}.token{background:#102f4d;color:#b9f3df;padding:17px;border-radius:9px;
font:15px monospace;overflow-wrap:anywhere}.muted{color:#7c8c9c;font-size:13px;line-height:1.7}</style></head>
<body><main><p><a href="/dashboard">← Dashboard</a></p><section class="card"><h1>Demo API token</h1>
<p class="muted">Bu faqat interfeys va API autentifikatsiyasini o‘rganish uchun. Hech qanday real xizmatga ruxsat bermaydi.</p>
<div class="token">{{ token }}</div><p class="muted">DEMO · LOCALHOST · Haqiqiy maxfiy kalit emas.</p></section></main></body></html>"""

ADMIN_PAGE = """<!doctype html><html lang="uz"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Admin panel</title><style>body{font-family:Segoe UI;background:#f3f6fa;color:#183650;margin:0}
main{max-width:1000px;margin:38px auto;padding:20px}.card{background:white;border:1px solid #e5ebf1;border-radius:14px;padding:22px;margin-top:17px}
a{color:#147b83;text-decoration:none;font-weight:700}table{width:100%;border-collapse:collapse;font-size:13px}
td,th{text-align:left;padding:12px 9px;border-bottom:1px solid #edf1f5}th{font-size:11px;color:#7b8b9a}
.note{font-size:13px;color:#7b8b9a}</style></head><body><main><p><a href="/dashboard">← Dashboard</a></p>
<h1>Administrator paneli</h1><p class="note">Faqat ADMIN roliga ega foydalanuvchi kira oladi.</p>
<section class="card"><h3>Foydalanuvchilar</h3><table><tr><th>Username</th><th>Email</th><th>Role</th><th>Demo balans (UZS)</th></tr>
{% for name,u in users %}<tr><td>{{ name }}</td><td>{{ u.email }}</td><td>{{ u.role }}</td><td>{{ "{:,}".format(u.balance).replace(",", " ") }}</td></tr>{% endfor %}
</table></section><section class="card"><h3>Himoya sozlamalari</h3>
<p class="note">Har siklda {{ max_fails }} urinish · 5s → 10s → 20s → doimiy bloklash · birinchi blokdan keyin CAPTCHA.</p>
</section></main></body></html>"""

LOGS_PAGE = """<!doctype html><html lang="uz"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Xavfsizlik loglari</title><style>body{font-family:Segoe UI;background:#f3f6fa;color:#183650;margin:0}
main{max-width:1000px;margin:38px auto;padding:20px}.card{background:white;border:1px solid #e5ebf1;border-radius:14px;padding:22px}
a{color:#147b83;text-decoration:none;font-weight:700}.muted{color:#7b8b9a;font-size:13px}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#102f4d;color:#d6e8f3;padding:17px;border-radius:9px;max-height:600px;overflow:auto}</style>
</head><body><main><p><a href="/dashboard">← Dashboard</a></p><h1>Xavfsizlik loglari</h1>
<p class="muted">Login urinishlari va muhim hodisalar. Parollar logga yozilmaydi.</p><section class="card"><pre>{{ log_text }}</pre></section></main></body></html>"""


@app.route("/captcha.png")
def captcha_image():
    text = session.get("captcha_text")
    if not text:
        text = new_captcha_text()
        session["captcha_text"] = text
    return Response(render_captcha_png(text), mimetype="image/png")


@app.route("/", methods=["GET", "POST"])
def login():
    message = None
    msg_class = "msg-error"
    if "needs_captcha" not in session:
        session["needs_captcha"] = False

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        honeypot = request.form.get("confirm_email", "")

        if honeypot.strip():
            message = "Xatolik yuz berdi, qayta urinib ko'ring"
            log_event("HONEYPOT_TRIGGERED", username)
        else:
            record = attempts.setdefault(username, {"fails": 0, "locked_until": 0, "lockout_count": 0})
            now = time.time()
            if now < record["locked_until"]:
                remaining = int(record["locked_until"] - now)
                if remaining > 3600:
                    message = "Hisobingiz xavfsizlik siyosati asosida bloklangan. Administrator bilan bog'laning."
                else:
                    message = f"Hisob bloklangan. {remaining} soniyadan keyin qayta urinib ko'ring."
                msg_class = "msg-lock"
                log_event("LOGIN_WHILE_LOCKED", username, f"remaining={remaining}")
            elif session.get("needs_captcha") and request.form.get("captcha", "").strip().upper() != session.get("captcha_text", "").upper():
                message = "CAPTCHA noto'g'ri kiritildi"
                log_event("CAPTCHA_FAILED", username)
            else:
                delay = min(record["fails"] * 0.3, 3)
                if delay:
                    time.sleep(delay)
                user_record = USERS.get(username)
                if user_record and check_password_hash(user_record["password"], password):
                    record["fails"] = 0
                    session["logged_in"] = True
                    session["username"] = username
                    log_event("LOGIN_SUCCESS", username)
                    return redirect(url_for("dashboard"))

                record["fails"] += 1
                # Local-lab-only username enumeration response, matching the supplied test client.
                message = "Bunday foydalanuvchi topilmadi" if user_record is None else "Login yoki parol noto'g'ri"
                log_event("LOGIN_FAILED", username, f"known_user={user_record is not None}")
                if record["fails"] >= MAX_FAILS_PER_CYCLE:
                    stage = min(record["lockout_count"], len(LOCKOUT_STAGES) - 1)
                    lock_seconds = LOCKOUT_STAGES[stage]
                    record["locked_until"] = now + lock_seconds
                    record["lockout_count"] += 1
                    record["fails"] = 0
                    session["needs_captcha"] = True
                    if lock_seconds > 3600:
                        message = "Juda ko'p noto'g'ri urinish. Hisobingiz bloklandi."
                    else:
                        message = f"Noto'g'ri urinishlar soni oshib ketdi. {lock_seconds} soniyaga bloklandi."
                    msg_class = "msg-lock"
                    log_event("ACCOUNT_LOCKED", username, f"duration={lock_seconds}s")

    # Intentionally preserved from the original app for CAPTCHA/OCR client compatibility.
    session["captcha_text"] = new_captcha_text()
    return render_template_string(LOGIN_PAGE, message=message, msg_class=msg_class,
        captcha_required=session.get("needs_captcha", False), cache_bust=random.randint(1, 10**9))


@app.route("/dashboard")
@login_required
def dashboard():
    username = session.get("username", "foydalanuvchi")
    user = USERS.get(username)
    if not user:
        session.clear()
        return redirect(url_for("login"))
    return render_template_string(DASHBOARD_PAGE, username=username, email=user["email"],
        role=user["role"], balance=f'{user["balance"]:,}'.replace(",", " "),
        is_admin=user["role"] == "ADMIN")


@app.route("/token")
@login_required
def token_page():
    return render_template_string(TOKEN_PAGE, token=DEMO_TOKEN)


@app.route("/admin")
@admin_required
def admin():
    return render_template_string(ADMIN_PAGE, users=sorted(USERS.items()), max_fails=MAX_FAILS_PER_CYCLE)


@app.route("/logs")
@login_required
def logs():
    try:
        lines = LOG_PATH.read_text(encoding="utf-8").splitlines()
        log_text = "\\n".join(lines[-100:]) if lines else "Hozircha log mavjud emas."
    except OSError:
        log_text = "Log faylini o‘qib bo‘lmadi."
    return render_template_string(LOGS_PAGE, log_text=log_text)


@app.route("/logout")
def logout():
    username = session.get("username", "-")
    if session.get("logged_in"):
        log_event("LOGOUT", username)
    session.pop("logged_in", None)
    session.pop("username", None)
    return redirect(url_for("login"))


@app.errorhandler(403)
def forbidden(_error):
    return ('<h2>403 — Ruxsat yo‘q</h2><p>Bu sahifa faqat administrator uchun.</p>'
            '<p><a href="/dashboard">Dashboardga qaytish</a></p>', 403)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5004, debug=False)
