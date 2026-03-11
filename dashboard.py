import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
import os  # 🌟 파일 존재 여부를 확인하기 위해 추가

# 1. 웹페이지 기본 설정
st.set_page_config(page_title="Samsung TV Global Dashboard", layout="wide")
st.title("📺 삼성 글로벌 TV 가격 모니터링 대시보드")
st.markdown("독일과 영국의 TV 모델 현황 및 **날짜별 가격 변동 추이**를 분석합니다.")

# --- 🌟 클라우드 전용 보안 키 세팅 ---
# 내 컴퓨터에는 secrets.json이 있지만, 클라우드에는 없으므로 클라우드 비밀금고에서 꺼내 임시로 만듭니다.
if not os.path.exists('secrets.json'):
    with open('secrets.json', 'w', encoding='utf-8') as f:
        # st.secrets에 저장해둔 텍스트를 파일로 기록합니다.
        f.write(st.secrets["GSPREAD_CREDENTIALS"])


# ----------------------------------------

@st.cache_data(ttl=600)
def load_data():
    try:
        gc = gspread.service_account(filename='secrets.json')
        sh = gc.open("Samsung_TV_Data")
        worksheet = sh.sheet1

        data = worksheet.get_all_records()
        df = pd.DataFrame(data)

        # 열 이름 공백 제거 보호막
        df.columns = df.columns.str.strip()
        df['Price_Raw'] = pd.to_numeric(df['Price_Raw'], errors='coerce')
        return df
    except Exception as e:
        st.error(f"데이터를 불러오는 데 실패했습니다. 에러: {e}")
        return pd.DataFrame()


df = load_data()

if not df.empty:
    st.sidebar.header("🔍 데이터 필터링")

    countries = df['Country'].dropna().unique()
    selected_country = st.sidebar.selectbox("국가 선택 (Country):", options=countries)

    categories = df['Category'].dropna().unique()
    selected_category = st.sidebar.multiselect("카테고리 선택 (Category):", options=categories, default=categories)

    family_names = df[df['Country'] == selected_country]['Family_Name'].dropna().unique()
    selected_family = st.sidebar.multiselect("제품 라인업 선택 (Family Name):", options=family_names)

    filtered_df = df[df['Country'] == selected_country]
    if selected_category:
        filtered_df = filtered_df[filtered_df['Category'].isin(selected_category)]
    if selected_family:
        filtered_df = filtered_df[filtered_df['Family_Name'].isin(selected_family)]

    st.subheader(f"💡 {selected_country} 요약 지표")
    latest_date = filtered_df['Date'].max()
    latest_df = filtered_df[filtered_df['Date'] == latest_date]

    total_models = len(latest_df)
    avg_price = latest_df['Price_Raw'].mean()
    currency_symbol = "£" if selected_country == "UK" else "€"

    col1, col2 = st.columns(2)
    col1.metric(label=f"선택된 모델 수 ({latest_date} 기준)", value=f"{total_models} 개")
    if pd.isna(avg_price):
        col2.metric(label="평균 가격", value="데이터 없음")
    else:
        col2.metric(label="평균 가격", value=f"{avg_price:,.0f} {currency_symbol}")

    st.markdown("---")

    st.subheader(f"📈 {selected_country} 날짜별 평균 가격 변동 추이")
    trend_data = filtered_df.groupby(['Date', 'Category'])['Price_Raw'].mean().reset_index().dropna()
    fig_line = px.line(
        trend_data, x='Date', y='Price_Raw', color='Category', markers=True,
        title=f"Price Trend Over Time ({currency_symbol})",
        labels={'Price_Raw': f'평균 가격 ({currency_symbol})', 'Date': '날짜'}
    )
    st.plotly_chart(fig_line, use_container_width=True)

    st.markdown("---")

    st.subheader(f"📊 {selected_country} 카테고리별 평균 가격 (최신 기준)")
    price_by_category = latest_df.groupby('Category')['Price_Raw'].mean().reset_index().dropna()
    fig_bar = px.bar(
        price_by_category, x='Category', y='Price_Raw', text_auto='.0f',
        title=f"Category vs Average Price ({currency_symbol})",
        labels={'Price_Raw': f'평균 가격 ({currency_symbol})'}, color='Category'
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")

    st.subheader("📋 세부 모델 리스트")
    st.dataframe(filtered_df, use_container_width=True)
else:
    st.warning("구글 시트에 데이터가 없습니다. 크롤러를 먼저 실행해 주세요!")
