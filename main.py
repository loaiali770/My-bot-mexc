import streamlit as st
import ccxt
import pandas as pd
import pandas_ta as ta
import time
from datetime import datetime

# إعدادات الواجهة
st.set_page_config(page_title="Crypto Penny Radar", page_icon="💰", layout="wide")

st.title("🚀 رادار ومحاكي التداول اللحظي")
st.markdown("---")

# إعدادات الشريط الجانبي
with st.sidebar:
    st.header("⚙️ الإعدادات")
    START_BALANCE = st.number_input("الميزانية الابتدائية ($)", value=100.0)
    TRADE_AMOUNT = st.number_input("مبلغ كل صفقة ($)", value=10.0)
    TRAILING_STOP = st.slider("وقف الخسارة المتحرك (%)", 0.5, 5.0, 2.0)
    st.info("هذا البوت يبحث عن العملات التي سعرها أقل من 0.001$")

# إعداد حالة الجلسة (Session State)
if 'v_balance' not in st.session_state:
    st.session_state.v_balance = START_BALANCE
    st.session_state.positions = {} 
    st.session_state.logs = []
    st.session_state.running = False

# دالة جلب البيانات
def get_data(symbol):
    try:
        ex = ccxt.mexc({'enableRateLimit': True})
        bars = ex.fetch_ohlcv(symbol, timeframe='1m', limit=50)
        df = pd.DataFrame(bars, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
        df['EMA_8'] = ta.ema(df['c'], length=8)
        df['EMA_21'] = ta.ema(df['c'], length=21)
        return df
    except Exception as e:
        return None

# عرض الرصيد والصفقات المفتوحة في أعمدة
m1, m2 = st.columns(2)
balance_metric = m1.empty()
positions_metric = m2.empty()

# أزرار التحكم
col1, col2, col3 = st.columns([1, 1, 2])
if col1.button("▶️ تشغيل"): 
    st.session_state.running = True
if col2.button("🛑 إيقاف"): 
    st.session_state.running = False
if col3.button("🗑️ مسح السجل"): 
    st.session_state.logs = []
    st.rerun()

status_text = st.empty()
log_box = st.empty()

# حلقة العمل الرئيسية
if st.session_state.running:
    while st.session_state.running:
        # تحديث المتركس (الأرقام)
        balance_metric.metric("الحساب الوهمي", f"${st.session_state.v_balance:.2f}", 
                              f"{st.session_state.v_balance - START_BALANCE:.2f}$")
        positions_metric.metric("الصفقات المفتوحة", len(st.session_state.positions))

        status_text.info(f"🔎 فحص السوق: {datetime.now().strftime('%H:%M:%S')}")
        
        try:
            ex = ccxt.mexc()
            tickers = ex.fetch_tickers()
            # تصفية العملات أقل من 0.001
            symbols = [s for s, t in tickers.items() 
                       if '/USDT' in s and t['last'] is not None and t['last'] <= 0.001][:10]
        except Exception as e:
            status_text.error(f"خطأ في الاتصال بالمنصة: {e}")
            time.sleep(10)
            continue

        for symbol in symbols:
            # تجنب فحص العملات إذا توقف البوت فجأة
            if not st.session_state.running: break
            
            df = get_data(symbol)
            if df is None or len(df) < 21: continue
            
            curr_price = df.iloc[-1]['c']
            
            # 1. منطق الخروج
            if symbol in st.session_state.positions:
                pos = st.session_state.positions[symbol]
                if curr_price > pos['max_price']:
                    st.session_state.positions[symbol]['max_price'] = curr_price
                
                drop = (pos['max_price'] - curr_price) / pos['max_price']
                if drop >= (TRAILING_STOP / 100):
                    profit_pct = (curr_price - pos['entry']) / pos['entry']
                    final_return = TRADE_AMOUNT * (1 + profit_pct)
                    st.session_state.v_balance += final_return
                    st.session_state.logs.append(f"🔴 خروج: {symbol} | ربح: {profit_pct*100:.2f}% | سعر: {curr_price:.6f}")
                    del st.session_state.positions[symbol]

            # 2. منطق الدخول
            else:
                ema_cross = df.iloc[-1]['EMA_8'] > df.iloc[-1]['EMA_21'] and \
                            df.iloc[-2]['EMA_8'] <= df.iloc[-2]['EMA_21']
                
                if ema_cross and st.session_state.v_balance >= TRADE_AMOUNT:
                    st.session_state.positions[symbol] = {'entry': curr_price, 'max_price': curr_price}
                    st.session_state.v_balance -= TRADE_AMOUNT
                    st.session_state.logs.append(f"🟢 دخول: {symbol} | سعر: {curr_price:.6f}")
            
            time.sleep(0.1) # تقليل الضغط على API

        # تحديث السجل في الواجهة
        log_display = "\n".join(st.session_state.logs[-15:][::-1])
        log_box.text_area("سجل العمليات الأخير", value=log_display, height=300)
        
        time.sleep(5) # انتظار بسيط قبل الدورة التالية
        # ملاحظة: أزلنا st.rerun() واستبدلناها بتحديث العناصر مباشرة عبر الـ empty containers
