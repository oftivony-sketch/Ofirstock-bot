import yfinance as yf
import requests
import pandas as pd
import random
from datetime import datetime, timedelta

# --- הגדרות אישיות ---
TOKEN = "8684266181:AAFFV9UPlU-Xen3EBOJ1dN_BgNJH2u3e4OU"
CHAT_ID = "448405777"
MY_LIST = ["NTLA", "TNYA", "CI", "BEAM", "IONQ", "VKTX", "CMPS", "AVXL", "OCGN", "ORCL"]
SCREENER_LIST = ["AAPL", "NVDA", "AMD", "PLTR", "TSLA", "META", "AMZN", "MSFT", "COIN", "MARA", "RIOT", "SNOW", "U", "CRWD"]

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"שגיאה בשליחה לטלגרם: {e}")

def find_hot_growth_stock():
    """סורק רשימה ומוצא את המנייה עם המומנטום הכי חזק היום"""
    best_stock = None
    max_score = -1

    for ticker in SCREENER_LIST:
        try:
            s = yf.Ticker(ticker)
            hist = s.history(period="5d")
            if hist.empty: continue

            # חישוב שינוי באחוזים ב-5 ימים האחרונים
            growth = ((hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1) * 100

            if growth > max_score:
                max_score = growth
                best_stock = {
                    "ticker": ticker,
                    "growth": growth,
                    "price": hist['Close'].iloc[-1]
                }
        except: continue

    return best_stock

def find_high_potential_stock_of_the_day():
    """
    Screens SCREENER_LIST for stocks with:
    1. Over 100% upside potential based on median analyst target prices.
    2. Not in MY_LIST.
    3. At least two recent recommendations from distinct analyst firms.
    Returns one randomly selected stock from the qualifying candidates.
    """
    potential_candidates = []

    for ticker in SCREENER_LIST:
        if ticker in MY_LIST:
            continue # Skip stocks already in MY_LIST

        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            target_median_price = info.get('targetMedianPrice')
            current_price = info.get('currentPrice')

            # Check for valid price data and upside potential
            if target_median_price is None or current_price is None or current_price == 0:
                continue

            upside_potential = ((target_median_price / current_price) - 1) * 100

            if upside_potential <= 100:
                continue

            # Check for at least two distinct analyst recommendations
            recs = stock.recommendations
            if recs is not None and not recs.empty:
                # Get unique firms from the last few recommendations
                # Using a larger window to ensure we catch enough firms
                recent_firms = recs.tail(10)['Firm'].nunique()
                if recent_firms >= 2:
                    potential_candidates.append({
                        'ticker': ticker,
                        'currentPrice': current_price,
                        'targetMedianPrice': target_median_price,
                        'upsidePotential': upside_potential
                    })

        except Exception as e:
            print(f"Error screening {ticker}: {e}")
            continue

    if potential_candidates:
        # Return one randomly selected stock
        return random.choice(potential_candidates)
    else:
        return None

def get_my_list_performance_table():
    """
    Generates a Markdown-formatted table showing the performance of stocks in MY_LIST.
    For each stock, it displays yesterday's closing price, today's closing price,
    and the percentage change between them.
    """
    performance_data = []

    for ticker in MY_LIST:
        try:
            stock = yf.Ticker(ticker)
            # Fetch data for 2 days to get yesterday's and today's close
            hist = stock.history(period="2d")

            if len(hist) < 2:
                # Not enough data for comparison
                performance_data.append({
                    'ticker': ticker,
                    'yesterday_close': 'N/A',
                    'today_close': 'N/A',
                    'change_pct': 'N/A'
                })
                continue

            yesterday_close = hist['Close'].iloc[0]
            today_close = hist['Close'].iloc[-1]

            if yesterday_close == 0:
                change_pct = float('inf') if today_close > 0 else 0.0 # Handle division by zero
            else:
                change_pct = ((today_close - yesterday_close) / yesterday_close) * 100

            performance_data.append({
                'ticker': ticker,
                'yesterday_close': f"{yesterday_close:.2f}",
                'today_close': f"{today_close:.2f}",
                'change_pct': f"{change_pct:.2f}%" if change_pct != float('inf') else 'inf%'
            })

        except Exception as e:
            print(f"Error fetching performance for {ticker}: {e}")
            performance_data.append({
                'ticker': ticker,
                'yesterday_close': 'Error',
                'today_close': 'Error',
                'change_pct': 'Error'
            })

    # Format into Markdown table
    table_header = "| Ticker | Yesterday Close | Today Close | Change (%) |\n|---|---|---|---"
    table_rows = []
    for row in performance_data:
        table_rows.append(
            f"| {row['ticker']} | {row['yesterday_close']} | {row['today_close']} | {row['change_pct']} |"
        )

    return table_header + "\n" + "\n".join(table_rows)

def get_my_list_analyst_updates():
    """
    Checks for recent analyst recommendations (within the last 30 days) for stocks in MY_LIST.
    If found, it displays the recommending firm, the target price, and the calculated upside potential
    from the current price, formatted as a Markdown string.
    """
    updates = []
    today = datetime.now()
    thirty_days_ago = today - timedelta(days=30)

    for ticker in MY_LIST:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            recs = stock.recommendations

            current_price = info.get('currentPrice')
            if current_price is None or current_price == 0:
                print(f"Skipping {ticker}: Current price not available.")
                continue # Skip if current price is not available

            if recs is not None and not recs.empty:
                # Reset index to ensure 'Date' is a column. If 'Date' is already a column, this has no effect.
                # If the index is a DatetimeIndex, it will become a 'Date' column.
                # If the index is unnamed, it will become a column named 'index'. We'll handle this next.
                recs = recs.reset_index()

                # Ensure the date column is explicitly named 'Date'.
                # If reset_index created a column named 'index' that contains dates, rename it.
                if 'index' in recs.columns and 'Date' not in recs.columns:
                    try:
                        # Attempt to convert 'index' to datetime to see if it's actually the date
                        pd.to_datetime(recs['index'], errors='raise')
                        recs = recs.rename(columns={'index': 'Date'})
                    except (ValueError, TypeError):
                        # If 'index' is not a date, we can't proceed with date filtering
                        print(f"Skipping {ticker}: 'index' column is not a date and 'Date' column is missing.")
                        continue

                if 'Date' not in recs.columns:
                    print(f"Skipping {ticker}: 'Date' column not found in recommendations after processing index.")
                    continue

                recs['Date'] = pd.to_datetime(recs['Date'], errors='coerce')
                recs = recs.dropna(subset=['Date']) # Drop rows where date conversion failed

                if recs.empty:
                    print(f"Skipping {ticker}: No valid recommendation dates after cleaning.")
                    continue # No valid dates after cleaning

                # Filter for recommendations within the last 30 days
                recent_recs = recs[recs['Date'] >= thirty_days_ago]

                if not recent_recs.empty:
                    updates.append(f"**{ticker}**:")
                    for index, row in recent_recs.iterrows():
                        firm = row.get('Firm', 'N/A')
                        to_grade = row.get('To Grade', 'N/A')
                        # 'Target Price' might not always be in the recommendations DataFrame, fall back to median from info
                        target_price = row.get('Target Price', info.get('targetMedianPrice'))

                        upside = "N/A"
                        if target_price is not None and current_price is not None and current_price > 0:
                            upside_pct = ((target_price / current_price) - 1) * 100
                            upside = f"{upside_pct:.1f}%"

                        updates.append(f"- {firm}: {to_grade} (Target: {target_price:.2f}$, Upside: {upside})")

        except Exception as e:
            print(f"Error fetching analyst updates for {ticker}: {e}")
            continue

    if updates:
        return """*עדכוני אנליסטים מהחודש האחרון:*\n""" + "\n".join(updates)
    else:
        return "*אין עדכוני אנליסטים חדשים למניות ברשימה שלך.*"

def scan_market():
    report = "🚀 *דו''ח מניות צמיחה יומי*\n\n"

    # 1. בדיקת הרשימה הקבועה שלך
    report += "*סטטוס הרשימה שלך:*\n"
    for ticker in MY_LIST:
        try:
            s = yf.Ticker(ticker)
            price = s.history(period="1d")['Close'].iloc[-1]
            report += f"• {ticker}: {price:.2f}$\n"
        except: continue

    # 2. מציאת מניית הצמיחה היומית
    hot_stock = find_hot_growth_stock()
    if hot_stock:
        report += f"\n🔥 *מניית הצמיחה החמה להיום:*\n"
        report += f"סימול: `{hot_stock['ticker']}`\n"
        report += f"עלייה שבועית: {hot_stock['growth']:.1f}%\n"
        report += f"מחיר: {hot_stock['price']:.2f}$\n"
        report += "_(מומלץ לבדוק גרף וחדשות לפני החלטה)_"

    # 3. מציאת מניית פוטנציאל עלייה של מעל 100% מהמסך הרחב
    hot_potential_stock = find_high_potential_stock_of_the_day()
    if hot_potential_stock:
        report += "\n\n💡 *מניית פוטנציאל-על היום (מעל 100% יעד אנליסטים):*\n"
        report += (f"סימול: `{hot_potential_stock['ticker']}`\n"
                   f"מחיר נוכחי: {hot_potential_stock['currentPrice']:.2f}$\n"
                   f"יעד אנליסטים: {hot_potential_stock['targetMedianPrice']:.2f}$\n"
                   f"פוטנציאל עלייה: {hot_potential_stock['upsidePotential']:.1f}%\n")
        report += "_(לא ברשימה שלך, מומלץ לבדוק לעומק!)_"
    else:
        report += "\n\n💡 *לא נמצאו מניות פוטנציאל-על היום.*\n"

    # 4. הוספת טבלת ביצועים לרשימה שלך
    report += "\n\n*ביצועי הרשימה שלך מהיום לאתמול:*\n"
    report += get_my_list_performance_table()

    # 5. הוספת עדכוני אנליסטים מהחודש האחרון
    report += "\n\n" + get_my_list_analyst_updates()

    send_telegram_msg(report)
    print("נשלח!")

# הפעלת הסריקה
scan_market()