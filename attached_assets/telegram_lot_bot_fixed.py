
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import re

# === CONFIGURATION ===
CAPITAL = 20000  # capital en $
RISQUE_POURCENT = 0.5  # % de risque
VALEUR_PIP_PAR_LOT = 10  # $ par pip pour 1 lot sur XAUUSD

# === LOGIQUE DU CALCUL ===
def calculer_lot(sl_pips, capital, risque_pct):
    risque_usd = capital * (risque_pct / 100)
    lot = risque_usd / (sl_pips * VALEUR_PIP_PAR_LOT)
    return round(lot, 2)

# === RÉPONSE AUTOMATIQUE ===
def handle_message(update, context):
    text = update.message.text.lower()
    match = re.search(r"xauusd\s+(buy|sell)\s+(\d+\.?\d*)\s+sl\s+(\d+\.?\d*)\s+tp\s+(\d+\.?\d*)", text)

    if match:
        direction = match.group(1)
        entry = float(match.group(2))
        sl = float(match.group(3))
        tp = float(match.group(4))

        sl_pips = abs(entry - sl)
        lot = calculer_lot(sl_pips, CAPITAL, RISQUE_POURCENT)

        response = f"**Calcul XAUUSD**\nDirection : {{direction.upper()}}\nEntrée : {{entry}}\nSL : {{sl}} (⛔ {{sl_pips}} pips)\n\n" +                    f"Capital : {{CAPITAL}} $\nRisque : {{RISQUE_POURCENT}}% = {{int(CAPITAL * (RISQUE_POURCENT / 100))}} $\n" +                    f"→ Taille de lot recommandée : **{{lot}} lot**"
    else:
        response = "Format attendu :\n`xauusd buy/sell 2700 sl 2708 tp 2690`"

    update.message.reply_text(response, parse_mode='Markdown')

# === MAIN ===
def main():
    TOKEN = "7794523794:AAHXCtvJvzQ9KD6P7CfV1byBRjkYalp3e3s"

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)

    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
