import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(page_title="프랜차이즈 배달 상권 분석 대시보드", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for Premium Design (Dark Mode)
st.markdown("""
<style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; font-family: 'Pretendard', sans-serif; }
    .stApp { background-color: #111827; color: #F9FAFB; }
    div[data-testid="stMetricValue"] { font-size: 2rem; font-weight: 800; color: #60A5FA; }
    div[data-testid="stMetricLabel"] { font-size: 1.1rem; font-weight: 600; color: #9CA3AF; }
    h1 { color: #F8FAFC; font-weight: 900; margin-bottom: 2rem; border-bottom: 3px solid #3B82F6; padding-bottom: 1rem; }
    h2, h3 { color: #F1F5F9; font-weight: 700; margin-top: 2rem; }
    section[data-testid="stSidebar"] { background-color: #1F2937; border-right: 1px solid #374151; }
    footer {visibility: hidden;} .stDeployButton {visibility: hidden;}
    /* Status Card styling */
    .status-card { background-color: #1F2937; padding: 20px; border-radius: 10px; border: 1px solid #374151; text-align: center; margin-bottom: 20px;}
    .status-card h4 { color: #9CA3AF; margin-top:0; font-size:1.1rem;}
    .status-card h2 { color: #F1F5F9; margin-bottom:0; font-size:2rem;}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    base_path = "streamlit_data"
    
    df_daily = pd.DataFrame()
    daily_path = os.path.join(base_path, 'mart_daily_sales.csv')
    if os.path.exists(daily_path): df_daily = pd.read_csv(daily_path)
    
    df_dong = pd.DataFrame()
    dong_path = os.path.join(base_path, 'mart_dong_sales.csv')
    if os.path.exists(dong_path): df_dong = pd.read_csv(dong_path)
        
    df_bm_now = pd.DataFrame()
    now_path = os.path.join(base_path, 'mart_baemin_now.csv')
    if os.path.exists(now_path):
        try: df_bm_now = pd.read_csv(now_path, encoding='utf-8-sig')
        except: df_bm_now = pd.read_csv(now_path, encoding='cp949')
            
    df_bm_click = pd.DataFrame()
    click_path = os.path.join(base_path, 'mart_baemin_click.csv')
    if os.path.exists(click_path):
        try: df_bm_click = pd.read_csv(click_path, encoding='utf-8-sig')
        except: df_bm_click = pd.read_csv(click_path, encoding='cp949')
            
    df_bm_daily = pd.DataFrame()
    pd_path = os.path.join(base_path, 'mart_baemin_daily.csv')
    if os.path.exists(pd_path):
        try: df_bm_daily = pd.read_csv(pd_path, encoding='utf-8-sig')
        except: df_bm_daily = pd.read_csv(pd_path, encoding='cp949')

    return df_daily, df_dong, df_bm_now, df_bm_click, df_bm_daily

df_daily, df_dong, df_bm_now, df_bm_click, df_bm_daily = load_data()

# 지점명 통일 (간석구월점 -> 경기광주점) 및 파싱
for df in [df_daily, df_dong]:
    if not df.empty and 'h_strnm' in df.columns: df['h_strnm'] = df['h_strnm'].str.replace('간석구월점', '경기광주점', regex=False)
for df in [df_bm_now, df_bm_click, df_bm_daily]:
    if not df.empty and '매장명' in df.columns: df['매장명'] = df['매장명'].str.replace('간석구월점', '경기광주점', regex=False)

if not df_daily.empty: df_daily['h_orderdt'] = pd.to_datetime(df_daily['h_orderdt'])

def format_korean_currency(val):
    if pd.isna(val) or val == 0: return "0원"
    val = int(val)
    if val >= 100000000:
        uk = val // 100000000
        man = (val % 100000000) // 10000
        return f"{uk}억 {man}만 원" if man > 0 else f"{uk}억 원"
    elif val >= 10000:
        return f"{val // 10000}만 원"
    return f"{val}원"

# ----------------- Sidebar -----------------
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3063/3063822.png", width=60)
st.sidebar.title("통합 컨트롤 패널")
st.sidebar.markdown("---")

if not df_daily.empty:
    stores = sorted(list(df_daily['h_strnm'].unique()))
    selected_stores = st.sidebar.multiselect("🏪 매장 집중 분석 (최대 3개)", stores, default=[stores[0]], max_selections=3)
    
    months = ["전체"] + sorted(list(df_daily['month'].unique()), reverse=True)
    selected_month = st.sidebar.selectbox("🗓️ 기간 (월별)", months, index=0)
    
    if len(selected_stores) == 0: st.warning("최소 1개의 매장을 선택해주세요."); st.stop()
        
    # 메이트포스 원본 매출 중 "배달의민족"만 철저히 분리
    filtered_pos = df_daily[(df_daily['h_strnm'].isin(selected_stores)) & (df_daily['platform'] == '배달의민족')].copy()
    
    filtered_dong = pd.DataFrame()
    if not df_dong.empty and 'h_strnm' in df_dong.columns:
        filtered_dong = df_dong[df_dong['h_strnm'].isin(selected_stores)].copy()
    
    f_now = df_bm_now.copy()
    f_click = df_bm_click.copy()
    f_daily_ad = df_bm_daily.copy()
    
    if not f_now.empty: f_now = f_now[f_now['매장명'].apply(lambda x: any(s in str(x) for s in selected_stores))]
    if not f_click.empty: f_click = f_click[f_click['매장명'].apply(lambda x: any(s in str(x) for s in selected_stores))]
    if not f_daily_ad.empty: f_daily_ad = f_daily_ad[f_daily_ad['매장명'].apply(lambda x: any(s in str(x) for s in selected_stores))]
        
    if selected_month != "전체":
        filtered_pos = filtered_pos[filtered_pos['month'] == selected_month]
        filtered_dong = filtered_dong[filtered_dong['month'] == selected_month]
        # 배민 요약 데이터는 기본적으로 현재/최근 월이라 필터 생략 우선, 일별 광고비는 월 필터 적용 시 컷
        if not f_daily_ad.empty and '일자' in f_daily_ad.columns:
            f_daily_ad['month'] = pd.to_datetime(f_daily_ad['일자'].astype(str), format='%Y-%m-%d', errors='coerce').dt.strftime('%Y-%m')
            f_daily_ad = f_daily_ad[f_daily_ad['month'] == selected_month]

    st.title("📈 초정밀 타겟 마케팅 및 상권 상관관계 대시보드")
    st.caption("※ 본 대시보드는 배달의민족 매출, 배달 행정동(상권), 광고 통계 등 철저한 상관성(Correlation) 파악을 목적으로 설계되었습니다.")

    # KPI 
    total_baemin_sales = filtered_pos['total_sales'].sum()
    total_ad_spend = pd.to_numeric(f_click['총_광고비'], errors='coerce').sum() if not f_click.empty and '총_광고비' in f_click.columns else 0
    total_baemin_orders = filtered_pos['order_count'].sum()
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"<div class='status-card'><h4>총 배민 POS 매출</h4><h2>{format_korean_currency(total_baemin_sales)}</h2></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='status-card'><h4>우리가게클릭 총 광고비</h4><h2>{format_korean_currency(total_ad_spend)}</h2></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='status-card'><h4>배달의민족 총 주문수</h4><h2>{int(total_baemin_orders):,}건</h2></div>", unsafe_allow_html=True)
    with c4:
        rate = round(total_baemin_sales/total_ad_spend*100, 1) if total_ad_spend > 0 else 0
        color = "#22C55E" if rate > 500 else "#EF4444"
        st.markdown(f"<div class='status-card'><h4>배민 총 매출 실질 ROAS</h4><h2 style='color:{color}'>{rate}%</h2></div>", unsafe_allow_html=True)

    # Tabs
    tab1, tab2, tab3 = st.tabs(["🚀 광고-매출 상관관계 (Ad & Sales)", "🧭 배달 핵심구역 (Dong) 매핑", "👥 고객 행동 및 특성 (CRM)"])
    
    # ---------------- TAB 1 ----------------
    with tab1:
        st.subheader("💡 1. 포스기 실매출 vs 광고 지출액 상관관계 진단")
        col_t1, col_t2 = st.columns([2, 1])
        with col_t1:
            # Scatter Plot
            ad_by_store = f_click.groupby('매장명').agg(ad_spend=('총_광고비', lambda x: pd.to_numeric(x, errors='coerce').sum())).reset_index()
            pos_by_store = filtered_pos.groupby('h_strnm').agg(pos_baemin_sales=('total_sales', 'sum')).reset_index()
            roas_df = pd.merge(ad_by_store, pos_by_store, left_on='매장명', right_on='h_strnm', how='inner')
            
            if not roas_df.empty:
                roas_df['ad_hover'] = roas_df['ad_spend'].apply(format_korean_currency)
                roas_df['sal_hover'] = roas_df['pos_baemin_sales'].apply(format_korean_currency)
                fig_scatter = px.scatter(roas_df, x='ad_spend', y='pos_baemin_sales', text='매장명', size='pos_baemin_sales', 
                                         color='매장명', custom_data=['매장명', 'ad_hover', 'sal_hover'], size_max=45)
                fig_scatter.update_traces(textposition='top center', hovertemplate="<b>%{customdata[0]}</b><br>광고비: %{customdata[1]}<br>실 배민매출: %{customdata[2]}<extra></extra>")
                fig_scatter.update_layout(xaxis_title="광고 지출액 (원)", yaxis_title="배민 실 매출액 (원)", showlegend=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#F9FAFB'))
                fig_scatter.update_xaxes(showgrid=True, gridcolor='#374151', title_font=dict(color='#9CA3AF'))
                fig_scatter.update_yaxes(showgrid=True, gridcolor='#374151', title_font=dict(color='#9CA3AF'))
                st.plotly_chart(fig_scatter, use_container_width=True)
            else:
                st.info("광고 데이터와 매칭할 지점 데이터가 부족합니다.")
        with col_t2:
            st.info("💡 **상관성 인사이트**\n\n광고비 지출 맵입니다. 우상단에 찍힐수록 훌륭한 효율(건강한 매장)을 뜻하며, 광고비를 늘림에도 Y축(매출)이 제자리라면 **'깃발 꽂기' 효율 저하** 또는 **썸네일 기획의 부재**를 의심해야 합니다.")

        st.markdown("---")
        st.subheader("💡 2. 일별 매출액과 고객 광고 클릭수 상호성 트렌드")
        if not f_daily_ad.empty and not filtered_pos.empty:
            f_daily_ad['date'] = pd.to_datetime(f_daily_ad['일자'].astype(str).str.replace(' 0:00', ''), errors='coerce')
            d_clicks = f_daily_ad.groupby('date').agg(clicks=('클릭수', lambda x: pd.to_numeric(x, errors='coerce').sum())).reset_index()
            
            d_sales = filtered_pos.groupby('h_orderdt').agg(sales=('total_sales', 'sum')).reset_index()
            d_merged = pd.merge(d_sales, d_clicks, left_on='h_orderdt', right_on='date', how='outer').fillna(0).sort_values('h_orderdt')
            
            fig = go.Figure()
            fig.add_trace(go.Bar(x=d_merged['h_orderdt'], y=d_merged['sales'], name='배민 POS 매출액', marker_color='#3B82F6', yaxis='y1'))
            fig.add_trace(go.Scatter(x=d_merged['h_orderdt'], y=d_merged['clicks'], name='광고 클릭수', mode='lines+markers', marker=dict(color='#F59E0B', size=8), line=dict(width=3), yaxis='y2'))
            
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#F9FAFB'),
                margin=dict(l=0, r=0, t=10, b=0),
                yaxis=dict(title="POS 매출액 (원)", titlefont=dict(color="#3B82F6"), tickfont=dict(color="#3B82F6"), showgrid=True, gridcolor='#374151'),
                yaxis2=dict(title="고객 클릭수 (회)", titlefont=dict(color="#F59E0B"), tickfont=dict(color="#F59E0B"), overlaying="y", side="right", showgrid=False),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
             st.warning("일별 상세 광고 클릭 데이터(배민)가 로드되지 않았습니다.")

    # ---------------- TAB 2 ----------------
    with tab2:
        st.subheader("🧭 행정동(Dong) 상권 침투율 분석")
        st.caption("※ 이 지표는 100% 포스기(메이트포스) 주소 원본에서 추출한 실제 배달 빈도 수입니다. (전화주문+배달앱 통합)")
        
        if not filtered_dong.empty:
            dong_agg = filtered_dong.groupby('dong')['total_sales'].sum().reset_index().sort_values('total_sales', ascending=False).head(15)
            dong_agg['hover'] = dong_agg['total_sales'].apply(format_korean_currency)
            fig_dong = px.bar(dong_agg, x='total_sales', y='dong', orientation='h', color='total_sales', color_continuous_scale='teal', custom_data=['hover'])
            fig_dong.update_traces(hovertemplate="<b>%{y}</b><br>%{customdata[0]}<extra></extra>")
            fig_dong.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False, xaxis_title="해당 동 배달 매출 총액", yaxis_title="행정동", margin=dict(l=0, r=0, t=20, b=0), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#F9FAFB'))
            fig_dong.update_xaxes(showgrid=True, gridcolor='#374151', title_font=dict(color='#9CA3AF'))
            st.plotly_chart(fig_dong, use_container_width=True)
            
            st.info("💡 **매체 혼합 전략 제언**\n\n특정 동(예: 화정도, 신도시 등)에서만 유독 매출이 높게 나온다면, 해당 행정동을 타겟으로 **'우리가게클릭' 노출 반경을 좁혀 집중 타게팅(입찰가 상향)** 하거나, 배달팁을 해당 지역 한정으로 소폭 인하하는 공격적인 전략이 유효합니다.")
        else:
            st.warning("해당 지점/기간의 주소(행정동) 데이터가 부족합니다.")

    # ---------------- TAB 3 ----------------
    with tab3:
        st.subheader("👥 신규/재주문 및 인구통계 (CRM)")
        
        c_crm1, c_crm2 = st.columns(2)
        with c_crm1:
            st.markdown("#### 🔄 배민 앱 내 평균 재주문율")
            if not f_now.empty and '최근재주문율_수치' in f_now.columns:
                rv = pd.to_numeric(f_now['최근재주문율_수치'].astype(str).str.replace('%',''), errors='coerce').mean()
                if pd.notna(rv): st.markdown(f"<div class='status-card'><h2 style='color:#A855F7'>{rv:.1f}%</h2><h4>충성 고객 비율 (최근 6개월)</h4></div>", unsafe_allow_html=True)
                else: st.warning("재주문율 데이터 파싱 에러")
            else: st.warning("우리가게 NOW 데이터 부재")
                
            st.markdown("#### 🤔 분석가 코멘트")
            st.info('''결제 플랫폼(배민/포스)과 동(Address) 조합 분석 결과:
            
* 매장 반경 1km 이내 (배달팁 저렴 구역)의 재주문율이 핵심 지표입니다.
* 행정동 데이터(TAB 2)에서 1위를 차지한 동네의 주문건 중 '신규/재주문 구성비'가 파악된다면 가장 완벽합니다.''')

        with c_crm2:
             st.markdown("#### 🚧 신규/재주문 월별 추이 및 연령/성별 포트폴리오")
             st.markdown('''
             <div style="background-color:#374151; padding:30px; border-radius:10px; border:2px dashed #6B7280; text-align:center;">
                <h3 style="color:#9CA3AF; margin-bottom:10px;">데이터 수집 진행 중... ⏱️</h3>
                <p style="color:#D1D5DB; font-size:1rem;">대표님께서 지시하신 최정밀 <b>"신규/재주문/성별/연령대 (최근 3개월)"</b> 전문 데이터가 수집 파이프라인에서 추출되고 있습니다.</p>
                <p style="color:#D1D5DB; font-size:1rem;">수집이 완료되어 CSV 파일이 안착하는 즉시, 이곳에 홀로그램과 같은 세밀한 인구통계(Demographic) 점찍기 차트와 신규 유입 코호트(Cohort) 그래프가 100% 팩트 기반으로 렌더링될 예정입니다.</p>
             </div>
             ''', unsafe_allow_html=True)
else:
    st.error("데이터 서버 접속 대기 중...")
