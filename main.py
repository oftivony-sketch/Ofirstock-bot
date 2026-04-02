import yfinance as yf
import requests
import pandas as pd
from datetime import datetime

# הגדרות הבוט (וודא שהפרטים נכונים!)
TOKEN = "8684266181:AAFFV9UPlU-Xen3EBOJ1dN_BgNJH2u3e4OU"
CHAT_ID = "448405777"

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, data=payload)
        res_data = response.json()
        if res_data.get("ok"):
            print("✅ Message sent successfully to Telegram!")
        else:
            print(f"❌ Telegram Error: {res_data.get('description')}")
    except Exception as e:
        print(f"💥 Connection Error: {e}")

def get_stock_data():
    stocks = ['NTLA', 'IONQ', 'MARA', 'RIOT', 'TSLA'] # רשימת המניות שלך
    results = []
    
    current_time = datetime.now().strftime("%d/%m/%Y %H:%M")
    msg = f"🚀 *דו''ח סריקת מניות* ({current_time})\n\n"
    
    for symbol in stocks:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2d")
            if len(hist) < 2: continue
            
            price = hist['Close'].iloc[-1]
            change = ((price - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
            
            arrow = "🔼" if change > 0 else "🔽"
            msg += f"*{symbol}*: {price:.2f}$ ({arrow} {change:.2f}%)\n"
        except:
            continue
    
    msg += "\nביצועי מערכת: תקין ✅"
    return msg

if __name__ == "__main__":
    report = get_stock_data()
    print("Sending report...")
    send_telegram_msg(report)
