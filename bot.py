import os
import random
import string
import re
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# --- RENDER ÜCRETSİZ PLAN İÇİN MİNİ WEB SUNUCUSU ---
app_flask = Flask('')

@app_flask.route('/')
def home():
    return "Bot 7/24 Aktif!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()
# ---------------------------------------------------

user_cards = {}
BANKANIN_ISIMLERI = ["Anadolu Titan Bank", "NeoKredi", "DemirBank", "Quantum Finans", "Birlik Bankası"]

def rastgele_kart_no():
    karakterler = string.ascii_letters + string.digits
    kod = ''.join(random.choice(karakterler) for _ in range(12))
    return f"TR{random.randint(10,99)}-{kod[:4]}-{kod[4:8]}-{kod[8:]}"

async def kartver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Az (100 - 500 TL)", callback_data="secim_az")],
        [InlineKeyboardButton("Orta (500 - 2.500 TL)", callback_data="secim_orta")],
        [InlineKeyboardButton("Çok (2.500 - 10.000 TL)", callback_data="secim_cok")],
        [InlineKeyboardButton("Lüks (10.000 - 50.000 TL)", callback_data="secim_luks")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("💳 Hangi bütçede bir sanal kart istiyorsun?", reply_markup=reply_markup)

async def buton_yakala(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "secim_az":
        bakiye = random.randint(100, 500)
    elif data == "secim_orta":
        bakiye = random.randint(500, 2500)
    elif data == "secim_cok":
        bakiye = random.randint(2500, 10000)
    elif data == "secim_luks":
        bakiye = random.randint(10000, 50000)
    else:
        bakiye = 1000

    banka = random.choice(BANKANIN_ISIMLERI)
    kart_no = rastgele_kart_no()

    user_cards[user_id] = {
        "banka": banka,
        "kart_no": kart_no,
        "bakiye": bakiye
    }

    await query.edit_message_text(
        text=f"🎉 **Yeni Kartın Hazır!**\n\n"
             f"🏛️ Banka: {banka}\n"
             f"🔢 Numara: `{kart_no}`\n"
             f"💰 Bakiye: {bakiye} TL\n\n"
             f"🛒 Artık dilediğin gibi harcama yapabilirsin! (Örn: *Kahve aldım (45 TL)*)"
    )

async def harcama_yap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    mesaj = update.message.text

    if user_id not in user_cards or user_cards[user_id]["bakiye"] <= 0:
        await update.message.reply_text("❌ Aktif bir kartın yok veya bakiyen bitti! Yeni kart almak için /kartver yazmalısın.")
        return

    tutar_bul = re.findall(r'\((\d+)\s*tl\)', mesaj.lower())

    if tutar_bul:
        harcama = int(tutar_bul[0])
        kart = user_cards[user_id]

        if kart["bakiye"] >= harcama:
            kart["bakiye"] -= harcama
            await update.message.reply_text(
                f"✅ Harcama onaylandı!\n"
                f"💸 Düşülen Tutar: {harcama} TL\n"
                f"💳 Kalan Bakiye: {kart['bakiye']} TL"
            )
            if kart["bakiye"] <= 0:
                await update.message.reply_text("⚠️ Kartındaki bakiye tükendi! Yeni bir kart almak için /kartver yazabilirsin.")
        else:
            await update.message.reply_text(f"❌ Yetersiz bakiye! Kartında sadece {kart['bakiye']} TL kaldı.")

if __name__ == '__main__':
    keep_alive()  # Arka planda web sunucusunu başlatır
    TOKEN = os.environ.get("TOKEN")  # Token'ı Render ayarlarından çekecek
    
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("kartver", kartver))
    app.add_handler(CallbackQueryHandler(buton_yakala))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), harcama_yap))

    print("Simülasyon botu bulutta çalışıyor...")
    app.run_polling()