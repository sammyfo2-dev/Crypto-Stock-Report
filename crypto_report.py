import requests
import pandas as pd
import yfinance as yf
import smtplib
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURATION ---
API_KEY = "CG-J4tDDnQxqUPkJdhsi45LyQco"
EMAIL_USER = "sammyfo2@gmail.com"
EMAIL_PASS = "djyf zeol njjt qtfj"

# Dates
REF_DATE_CG = "21-01-2026"  
REF_DATE_YF = "2026-01-21"  

# Added XRP and DOGE back in
CRYPTO_COINS = {
    "bitcoin": "BTC", "ethereum": "ETH", "solana": "SOL", 
    "hyperliquid": "HYPE", "ripple": "XRP", "dogecoin": "DOGE", 
    "zcash": "ZEC"
}

STOCK_TICKERS = [
    "AAPL", "AMD", "AMZN", "ARM", "ASML", "AVGO", "BABA", "BETR", 
    "BIDU", "BMNR", "CIFR", "COIN", "DOCN", "ENSG", "GEV", "GLXY", 
    "GOOG", "IREN", "JD", "META", "MSFT", "NBIS", "NFLX", "NVDA", 
    "OPEN", "PACS", "QQQ", "SBET", "SMCI", "SPY", "TSLA", "TSM"
]

def get_crypto_data():
    print("Step 1: Fetching Crypto data...")
    data_list = []
    ids_query = ",".join(CRYPTO_COINS.keys())
    date_30d = (datetime.now() - timedelta(days=30)).strftime("%d-%m-%Y")
    
    # Get Live Prices
    live_url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids_query}&vs_currencies=usd&include_24hr_change=true&x_cg_demo_api_key={API_KEY}"
    live_resp = requests.get(live_url).json()

    for cg_id, ticker in CRYPTO_COINS.items():
        print(f"  > Fetching {ticker}...")
        # Historical Price (1/21)
        h_url = f"https://api.coingecko.com/api/v3/coins/{cg_id}/history?date={REF_DATE_CG}&x_cg_demo_api_key={API_KEY}"
        h_data = requests.get(h_url).json()
        p_ref = h_data.get('market_data', {}).get('current_price', {}).get('usd', 0)
        
        # 30d Price
        h30_url = f"https://api.coingecko.com/api/v3/coins/{cg_id}/history?date={date_30d}&x_cg_demo_api_key={API_KEY}"
        h30_data = requests.get(h30_url).json()
        p_30d = h30_data.get('market_data', {}).get('current_price', {}).get('usd', 0)
        
        coin_data = live_resp.get(cg_id, {})
        p_curr = coin_data.get('usd', 0)
        chg_1d = coin_data.get('usd_24h_change', 0)

        data_list.append({
            "Asset": ticker,
            "Price (1/21)": p_ref,
            "Current Price": p_curr,
            "Total %": ((p_curr - p_ref) / p_ref * 100) if p_ref > 0 else 0,
            "1D %": chg_1d,
            "30D %": ((p_curr - p_30d) / p_30d * 100) if p_30d > 0 else 0
        })
        time.sleep(1) # Safety pause for API
        
    df = pd.DataFrame(data_list)
    df.index = df.index + 1
    return df

def get_stock_data():
    print("Step 2: Fetching Stock data...")
    stock_list = []
    for ticker in STOCK_TICKERS:
        try:
            s = yf.Ticker(ticker)
            h_ref = s.history(start=REF_DATE_YF, period="1d")
            p_ref = h_ref['Close'].iloc[0] if not h_ref.empty else 0
            h_30 = s.history(period="30d")
            p_30 = h_30['Close'].iloc[0] if not h_30.empty else 0
            p_curr = s.fast_info['last_price']
            p_prev = s.fast_info['previous_close']

            stock_list.append({
                "Asset": ticker,
                "Price (1/21)": p_ref,
                "Current Price": p_curr,
                "Total %": ((p_curr - p_ref) / p_ref * 100) if p_ref > 0 else 0,
                "1D %": ((p_curr - p_prev) / p_prev * 100) if p_prev > 0 else 0,
                "30D %": ((p_curr - p_30) / p_30 * 100) if p_30 > 0 else 0
            })
        except Exception as e:
            print(f"  ! Skipping {ticker}: {e}")
            
    df = pd.DataFrame(stock_list)
    df.index = df.index + 1
    return df

def build_table_html(df, title):
    rows_html = ""
    for idx, row in df.iterrows():
        bg = "#f2f2f2" if idx % 2 == 0 else "#ffffff"
        def get_style(val):
            color = "#008000" if val >= 0 else "#d10000"
            return f"color: {color}; font-weight: bold; border: 1px solid #cccccc;"
        
        rows_html += f"""
        <tr bgcolor="{bg}">
            <td align="center" style="padding: 8px; border: 1px solid #cccccc;">{idx}</td>
            <td style="padding: 8px; font-weight: bold; border: 1px solid #cccccc;">{row['Asset']}</td>
            <td style="padding: 8px; border: 1px solid #cccccc;">${row['Price (1/21)']:,.2f}</td>
            <td style="padding: 8px; border: 1px solid #cccccc;">${row['Current Price']:,.2f}</td>
            <td align="right" style="padding: 8px; {get_style(row['Total %'])}">{row['Total %']:+.2f}%</td>
            <td align="right" style="padding: 8px; {get_style(row['1D %'])}">{row['1D %']:+.2f}%</td>
            <td align="right" style="padding: 8px; {get_style(row['30D %'])}">{row['30D %']:+.2f}%</td>
        </tr>"""

    return f"""
    <h3 style="color: #007bff; font-family: Arial, sans-serif; margin-top: 25px;">{title}</h3>
    <table width="100%" border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; font-family: Arial, sans-serif; font-size: 12px; border: 1px solid #cccccc;">
        <tr bgcolor="#e6e6e6">
            <th style="border: 1px solid #cccccc;">#</th>
            <th style="border: 1px solid #cccccc;">Asset</th>
            <th style="border: 1px solid #cccccc;">Price (1/21)</th>
            <th style="border: 1px solid #cccccc;">Current Price</th>
            <th style="border: 1px solid #cccccc;">Total %</th>
            <th style="border: 1px solid #cccccc;">1D %</th>
            <th style="border: 1px solid #cccccc;">30D %</th>
        </tr>
        {rows_html}
    </table>"""

def send_combined_email(crypto_df, stock_df):
    print("Step 3: Preparing email...")
    crypto_html = build_table_html(crypto_df, "🪙 Crypto Performance")
    stock_html = build_table_html(stock_df, "📈 Stock Performance")
    
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
        <div style="max-width: 850px; margin: auto; background: white; border: 1px solid #007bff; padding: 25px; border-radius: 10px;">
            <h2 style="color: #333; border-bottom: 3px solid #007bff; padding-bottom: 10px; margin-top: 0;">📊 Daily Market Report</h2>
            <p style="color: #555;">Portfolio status as of <strong>{datetime.now().strftime('%B %d, %Y')}</strong></p>
            {crypto_html}
            {stock_html}
            <p style="font-size: 11px; color: #999; margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px;">
                Data Sources: CoinGecko API & Yahoo Finance. Report generated automatically via Python.
            </p>
        </div>
    </body>
    </html>
    """
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🚀 Portfolio Update: {datetime.now().strftime('%b %d, %Y')}"
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_USER
    msg.attach(MIMEText(html_content, 'html'))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)

# --- EXECUTION ---
try:
    c_df = get_crypto_data()
    s_df = get_stock_data()
    send_combined_email(c_df, s_df)
    print("✅ Success! Everything sent.")
except Exception as e:

    print(f"❌ Critical Error: {e}")
