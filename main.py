import streamlit as st
import ccxt
import pandas as pd
import pandas_ta as ta
import time
from datetime import datetime

# إعدادات الواجهة
st.set_page_config(page_title="Crypto Penny Radar", page_icon="💰")

# --- شرح الملفات المطلوبة للرفع للسحاب ---
# لكي يعمل هذا الكود مباشرة على الإنترنت، يجب وجود ملف requirements.txt
# يحتوي على: streamlit, ccxt, pandas, pandas-ta

st.title("🚀 رادار ومحاكي التداول اللحظي")

# إعدادات الشريط الجانبي
with st.sidebar:
    st.header("⚙️ الإعدادات")
    START_BALANCE = st.number_input("الميزانية الابتدائية ($)", value=100.0)
    TRADE_AMOUNT = st.number_input("مبلغ كل صفقة ($)", value=10.0)
    TRAILING_STOP = st.slider("وقف الخسارة المتحرك (%)", 0.5, 5.0, 2.0)
    
# حالة الجلسة
if 'v_balance' not in st.session_state:
    st.session_state.v_balance = START_BALANCE
    st.session_state.positions = {} 
    st.session_state.logs = []
    st.session_state.running = False

def get_data(symbol):
    try:
        ex = ccxt.mexc()
        bars = ex.fetch_ohlcv(symbol, timeframe='1m', limit=50)
        df = pd.DataFrame(bars, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
        # حساب المؤشرات
        df['EMA_8'] = ta.ema(df['c'], length=8)
        df['EMA_21'] = ta.ema(df['c'], length=21)
        return df
    except:
        return None

# أزرار التحكم
col1, col2 = st.columns(2)
if col1.button("▶️ تشغيل البوت"): st.session_state.running = True
if col2.button("🛑 إيقاف"): st.session_state.running = False

# عرض الرصيد بشكل جميل
st.metric("الحساب الوهمي", f"${st.session_state.v_balance:.2f}", 
          f"{st.session_state.v_balance - START_BALANCE:.2f}$")

# حلقة العمل
if st.session_state.running:
    status_text = st.empty()
    log_box = st.empty()
    
    while st.session_state.running:
        status_text.info("🔎 جارِ فحص السوق بحثاً عن فرص أقل من 0.001...")
        
        # البحث عن العملات الرخيصة
        try:
            ex = ccxt.mexc()
            tickers = ex.fetch_tickers()
            symbols = [s for s, t in tickers.items() 
                       if '/USDT' in s and t['last'] <= 0.001][:15] # فحص محدود للسرعة
        except:
            continue

        for symbol in symbols:
            df = get_data(symbol)
            if df is None: continue
            
            curr_price = df.iloc[-1]['c']
            
            # 1. فحص الخروج (وقف الخسارة المتحرك)
            if symbol in st.session_state.positions:
                entry_price = st.session_state.positions[symbol]['entry']
                max_price = st.session_state.positions[symbol]['max_price']
                
                # تحديث أعلى سعر وصل له السهم منذ الدخول
                if curr_price > max_price:
                    st.session_state.positions[symbol]['max_price'] = curr_price
                
                # إذا نزل السعر عن أعلى سعر بنسبة الـ Trailing Stop
                drop = (st.session_state.positions[symbol]['max_price'] - curr_price) / st.session_state.positions[symbol]['max_price']
                if drop >= (TRAILING_STOP / 100):
                    profit = (curr_price - entry_price) / entry_price
                    st.session_state.v_balance += TRADE_AMOUNT * (1 + profit)
                    st.session_state.logs.append(f"📉 خروج (وقف متحرك): {symbol} بربح/خسارة: {profit*100:.2f}%")
                    del st.session_state.positions[symbol]

            # 2. فحص الدخول (تقاطع المتوسطات)
            else:
                if df.iloc[-1]['EMA_8'] > df.iloc[-1]['EMA_21'] and df.iloc[-2]['EMA_8'] <= df.iloc[-2]['EMA_21']:
                    if st.session_state.v_balance >= TRADE_AMOUNT:
                        st.session_state.positions[symbol] = {'entry': curr_price, 'max_price': curr_price}
                        st.session_state.v_balance -= TRADE_AMOUNT
                        st.session_state.logs.append(f"✅ دخول صفقة: {symbol} بسعر {curr_price:.6f}")

        # تحديث الشاشة
        log_display = "\n".join(st.session_state.logs[-10:][::-1])
        log_box.text_area("سجل الصفقات المباشر", value=log_display, height=200)
        
        time.sleep(15) # انتظر 15 ثانية للتحديث التالي
        st.rerun()
