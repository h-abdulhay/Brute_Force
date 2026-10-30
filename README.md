# NexaBank — Kiberxavfsizlik laboratoriyasi

Ushbu loyiha Python va Flask yordamida yaratilgan o‘quv laboratoriyasi bo‘lib, veb-ilovalarda autentifikatsiya va xavfsizlik mexanizmlarini o‘rganish hamda sinovdan o‘tkazish uchun mo‘ljallangan.

## Loyihaning imkoniyatlari

- **Flask autentifikatsiyasi:** Bir nechta foydalanuvchi va rollarga ega demo login tizimi.
- **CAPTCHA:** Rasm asosidagi CAPTCHA tekshiruvi.
- **Honeypot:** Avtomatlashtirilgan so‘rovlarni aniqlash uchun yashirin maydon.
- **Progressive Account Lockout:** Noto‘g‘ri parol bir necha marta kiritilganda hisobni bosqichma-bosqich vaqtincha bloklash.
- **Admin panel:** Administrator uchun maxsus boshqaruv sahifasi.
- **Faoliyat jurnali (Logs):** Login va xavfsizlik hodisalarini qayd etish.
- **Sinov skripti:** Lokal ilovada autentifikatsiya jarayonini tekshirish uchun Python skripti.
- **Wordlist:** Laboratoriya mashqlari uchun namunaviy parollar ro‘yxati.

## Loyiha tuzilishi

```text
NexaBank-Security-Lab/
│
├── app_v6_nexabank.py
├── brute_force_v5.py
├── wordlist_v5.txt
├── requirements.txt
├── .gitignore
└── README.md
```

## Kerakli dasturlar

- Python 3
- Flask
- Requests
- Pillow
- Pytesseract
- Tesseract OCR

## O‘rnatish

Repository'ni kompyuterga yuklab olish:

```bash
git clone https://github.com/YOUR_USERNAME/NexaBank-Security-Lab.git
cd NexaBank-Security-Lab
```

Virtual muhit yaratish:

```bash
python3 -m venv venv
source venv/bin/activate
```

Kerakli kutubxonalarni o‘rnatish:

```bash
pip install -r requirements.txt
```

Kali Linux tizimida Tesseract OCR o‘rnatish:

```bash
sudo apt update
sudo apt install tesseract-ocr
```

## Loyihani ishga tushirish

Flask ilovasini ishga tushirish:

```bash
python3 app_v6_nexabank.py
```

Ilova quyidagi manzilda ishlaydi:

```text
http://127.0.0.1:5004/
```

Ushbu manzilni brauzerda oching.

## Lokal xavfsizlik sinovlari

Flask ilovasi ishlayotgan paytda ikkinchi terminalni oching va sinov skriptini ishga tushiring:

```bash
python3 brute_force_v5.py
```

Sinov skriptidagi manzil lokal ilovaning 5004-portiga mos bo‘lishi va `wordlist_v5.txt` fayli shu papkada joylashgan bo‘lishi kerak.

## O‘rganish maqsadlari

Ushbu loyiha orqali quyidagilarni o‘rganish mumkin:

- Veb-ilovalarda autentifikatsiya qanday ishlashi.
- CAPTCHA mexanizmini login tizimiga integratsiya qilish.
- Honeypot orqali avtomatlashtirilgan so‘rovlarni aniqlash.
- Bosqichma-bosqich hisob bloklash mexanizmi.
- Xavfsizlik hodisalarini log orqali kuzatish.
- Lokal laboratoriyada nazorat ostidagi xavfsizlik sinovlarini bajarish.

## Xavfsizlik eslatmasi

- Loyiha faqat ta'lim va lokal laboratoriya sinovlari uchun mo‘ljallangan.
- Sinovlarni faqat o‘zingizga tegishli yoki ruxsat berilgan tizimlarda bajaring.
- Skriptni begona saytlar yoki foydalanuvchi hisoblariga qarshi ishlatmang.
- Ushbu demo ilovani haqiqiy bank tizimi sifatida ishlatmang.
- GitHub'ga yuklashdan oldin haqiqiy parollar, maxfiy kalitlar va shaxsiy ma'lumotlarni olib tashlang.

## Ogohlantirish

NexaBank — o‘quv maqsadida yaratilgan xayoliy bank ilovasi. U hech qanday haqiqiy bank yoki moliyaviy tashkilot bilan bog‘liq emas.

Ushbu repository kiberxavfsizlikni o‘rganish va ruxsat etilgan laboratoriya sinovlari uchun taqdim etilgan.
