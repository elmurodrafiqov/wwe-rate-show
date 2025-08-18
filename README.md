# WWE Rate Show

## Ishga tushirish (lokal)
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export ADMIN_PASSWORD=admin777  # Windows: set ADMIN_PASSWORD=admin777
export SECRET_KEY=anysecret
python app.py

## Muhit o'zgaruvchilari
- ADMIN_PASSWORD – admin paroli (majburiy)
- SECRET_KEY – Flask sessiya siri
- IP_SALT – IP hash uchun tuz (ixtiyoriy)

## Render sozlamalari
- Runtime: Python 3.11
- Start Command: python app.py (yoki gunicorn app:app)
- Disk persistensiya kerak emas (JSON fayllar repo’da)

## Foydalanish
- Bosh sahifa: header rasm, shou nomi, sana va baho kiritish.
- Admin panel: /admin → parol bilan kiring, sozlamalarni o'zgartiring, CSV eksport qiling, joriy reytinglarni tozalang.
- Har IP uchun 1 ovoz (hashlangan). Ovoz berish yopiq bo'lsa, forma ko'rinmaydi.