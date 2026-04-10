
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="FMCG Karar Destek İstihbaratı", page_icon="📊", layout="wide")

# --- VERİ TABANI BAĞLANTISI VE ÖNBELLEKLEME ---
# Streamlit'in veritabanını her tıklamada tekrar yormaması için cache (önbellek) kullanıyoruz
@st.cache_data(ttl=600)
def load_data():
    NEON_DATABASE_URL = "postgresql://neondb_owner:npg_PfY6QcNiy1dW@ep-purple-lab-an6w8s0d.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require"
    engine = create_engine(NEON_DATABASE_URL)
    
    # Kategori bazlı satışlar
    cat_query = "SELECT cat_id, SUM(sales_qty) as total_qty FROM sales_evaluation GROUP BY cat_id"
    df_cat = pd.read_sql(cat_query, engine)
    
    # Günlük toplam satış trendi
    trend_query = "SELECT day_id, SUM(sales_qty) as daily_qty FROM sales_evaluation GROUP BY day_id ORDER BY day_id"
    df_trend = pd.read_sql(trend_query, engine)
    
    return df_cat, df_trend

with st.spinner('Veri ambarından canlı metrikler çekiliyor...'):
    df_cat, df_trend = load_data()

# --- ARAYÜZ MİMARİSİ ---
st.title("📊 FMCG Executive Intelligence Dashboard")
st.markdown("*Lokasyon: Teksas Pilot Mağazası (TX_1) | Veri Aralığı: Son 365 Gün*")
st.markdown("---")

# 1. SATIR: TEMEL METRİKLER (KPIs)
col1, col2, col3 = st.columns(3)
total_sales = df_cat['total_qty'].sum()
avg_daily = df_trend['daily_qty'].mean()

col1.metric(label="Toplam Satış Hacmi (Adet)", value=f"{total_sales:,.0f}")
col2.metric(label="Günlük Ortalama Satış", value=f"{avg_daily:,.0f}")
col3.metric(label="En Güçlü Kategori", value=df_cat.loc[df_cat['total_qty'].idxmax()]['cat_id'])

st.markdown("---")

# 2. SATIR: GÖRSELLEŞTİRME VE SENARYO MOTORU
left_col, right_col = st.columns([2, 1])

with left_col:
    st.subheader("📈 Günlük Satış Trendi")
    fig_trend = px.line(df_trend, x='day_id', y='daily_qty', 
                        line_shape='spline', render_mode='svg',
                        color_discrete_sequence=['#1f77b4'])
    fig_trend.update_xaxes(showticklabels=False) # X eksenindeki d_1500 yazılarını gizleyip temiz bir görünüm sağlıyoruz
    st.plotly_chart(fig_trend, use_container_width=True)

with right_col:
    st.subheader("🎯 Kategori Dağılımı")
    fig_pie = px.pie(df_cat, values='total_qty', names='cat_id', hole=0.4,
                     color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("---")

# 3. SATIR: WHAT-IF (SENARYO) MOTORU
st.subheader("🛠️ Karar Destek: Fiyat/Talep Elastikiyet Simülasyonu")
st.markdown("Fiyat değişikliklerinin (elastikiyet varsayımı ile) tahmini toplam satış hacmine etkisini simüle edin.")

price_change = st.slider("Planlanan Fiyat Değişimi (%)", min_value=-20, max_value=20, value=0, step=1)

# Basit bir fiyat elastikiyeti katsayısı (Örn: -1.2 -> Fiyat %1 artarsa, talep %1.2 düşer)
elasticity = -1.2 
estimated_qty_change = price_change * elasticity
estimated_new_total = total_sales * (1 + (estimated_qty_change / 100))

sc1, sc2 = st.columns(2)
sc1.metric("Tahmini Hacim Etkisi", f"% {estimated_qty_change:.1f}")
sc2.metric("Yeni Tahmini Toplam Satış (Adet)", f"{estimated_new_total:,.0f}", delta=f"{estimated_new_total - total_sales:,.0f}")
