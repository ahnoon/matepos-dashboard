import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(page_title="프랜차이즈 경영 대시보드", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for Premium Design
st.markdown("""
<style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; font-family: 'Pretendard', sans-serif; }
    .stApp { background-color: #FAFAFA; color: #111827; }
    div[data-testid="stMetricValue"] { font-size: 2rem; font-weight: 800; color: #1E3A8A; }
    div[data-testid="stMetricLabel"] { font-size: 1.1rem; font-weight: 600; color: #4B5563; }
    h1 { color: #0F172A; font-weight: 900; margin-bottom: 2rem; border-bottom: 3px solid #3B82F6; padding-bottom: 1rem; }
    h2, h3 { color: #1E293B; font-weight: 700; margin-top: 2rem; }
    section[data-testid="stSidebar"] { background-color: #F8FAFC; border-right: 1px solid #E2E8F0; }
    footer {visibility: hidden;} .stDeployButton {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    base_path = "streamlit_data"
    
    df_daily = pd.DataFrame()
    daily_path = os.path.join(base_path, 'mart_daily_sales.csv')
    if os.path.exists(daily_path): df_daily = pd.read_csv(daily_path)
    
    df_menu = pd.DataFrame()
    menu_path = os.path.join(base_path, 'mart_menu_sales.csv')
    if os.path.exists(menu_path): df_menu = pd.read_csv(menu_path)
        
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

    return df_daily, df_menu, df_bm_now, df_bm_click

df_daily, df_menu, df_bm_now, df_bm_click = load_data()

# 지점명 통일
if not df_daily.empty: df_daily['h_strnm'] = df_daily['h_strnm'].str.replace('간석구월점', '경기광주점', regex=False)
if not df_menu.empty: df_menu['h_strnm'] = df_menu['h_strnm'].str.replace('간석구월점', '경기광주점', regex=False)
if not df_bm_now.empty and '매장명' in df_bm_now.columns: df_bm_now['매장명'] = df_bm_now['매장명'].str.replace('간석구월점', '경기광주점', regex=False)
if not df_bm_click.empty and '매장명' in df_bm_click.columns: df_bm_click['매장명'] = df_bm_click['매장명'].str.replace('간석구월점', '경기광주점', regex=False)

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
    selected_stores = st.sidebar.multiselect("🏪 매장 비교 (최대 5개)", stores, default=[stores[0]], max_selections=5)
    
    months = ["전체"] + sorted(list(df_daily['month'].unique()), reverse=True)
    selected_month = st.sidebar.selectbox("🗓️ 기간 (월별)", months, index=0)
    
    platforms = sorted(list(df_daily['platform'].unique()))
    selected_platforms = st.sidebar.multiselect("🛵 결제 플랫폼", platforms, default=platforms)
    
    if len(selected_stores) == 0: st.warning("최소 1개의 매장을 선택해주세요."); st.stop()
    if len(selected_platforms) == 0: st.warning("플랫폼을 1개 이상 선택해주세요."); st.stop()
        
    filtered_df = df_daily[df_daily['h_strnm'].isin(selected_stores)&df_daily['platform'].isin(selected_platforms)].copy()
    filtered_menu = df_menu[df_menu['h_strnm'].isin(selected_stores)].copy()
    
    if selected_month != "전체":
        filtered_df = filtered_df[filtered_df['month'] == selected_month]
        filtered_menu = filtered_menu[filtered_menu['month'] == selected_month]

    # Baemin Ad Filters
    f_now = df_bm_now.copy()
    f_click = df_bm_click.copy()
    if not f_now.empty: f_now = f_now[f_now['매장명'].apply(lambda x: any(s in str(x) for s in selected_stores))]
    if not f_click.empty:
        f_click = f_click[f_click['매장명'].apply(lambda x: any(s in str(x) for s in selected_stores))]
        # 배민 월별 데이터가 있다면 해당 월 필터 로직 적용 가능하지만, 현재는 csv 컬럼에 따라 요약만 진행

    st.title("📈 프랜차이즈 경영 통합 대시보드 (HQ용)")

    # Tabs
    tab1, tab2, tab3 = st.tabs(["📊 통합 매출 & 플랫폼 관제", "💡 배민 광고 효율(ROAS) 진단", "🍗 핵심 메뉴 분석"])
    
    # ---------------- TAB 1 ----------------
    with tab1:
        total_sales = filtered_df['total_sales'].sum()
        total_orders = filtered_df['order_count'].sum()
        avg_ticket = total_sales / total_orders if total_orders > 0 else 0
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("총 매출액", format_korean_currency(total_sales))
        c2.metric("총 주문 건수", f"{int(total_orders):,}건")
        c3.metric("평균 객단가", format_korean_currency(avg_ticket))
        with c4:
            if not f_now.empty and '최근재주문율_수치' in f_now.columns:
                rv = pd.to_numeric(f_now['최근재주문율_수치'].astype(str).str.replace('%',''), errors='coerce').mean()
                if pd.notna(rv): st.metric("합산 평균 재주문율", f"{rv:.1f}%")
                else: st.metric("합산 평균 재주문율", "데이터 부족")
            else: st.metric("합산 평균 재주문율", "-")
            
        st.markdown("---")
        col_t1, col_t2 = st.columns([2, 1])
        with col_t1:
            st.subheader("매장별 일자 매출 비교 추이")
            trend_df = filtered_df.groupby(['h_orderdt', 'h_strnm']).agg({'total_sales':'sum'}).reset_index()
            trend_df['hover_sales'] = trend_df['total_sales'].apply(format_korean_currency)
            fig1 = px.line(trend_df, x='h_orderdt', y='total_sales', color='h_strnm', markers=True, custom_data=['hover_sales', 'h_strnm'])
            if len(selected_stores) == 1: fig1.update_traces(line_color='#3B82F6')
            fig1.update_traces(hovertemplate="<b>%{customdata[1]}</b><br>%{x}<br><b>%{customdata[0]}</b><extra></extra>", line_width=3)
            fig1.update_layout(xaxis_title=None, yaxis_title=None, margin=dict(l=0, r=0, t=10, b=0), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig1, use_container_width=True)
            
        with col_t2:
            st.subheader("결제 플랫폼 점유율")
            pie_df = filtered_df.groupby('platform')['total_sales'].sum().reset_index()
            pie_df['hover_sales'] = pie_df['total_sales'].apply(format_korean_currency)
            fig_pie = px.pie(pie_df, values='total_sales', names='platform', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_pie.update_traces(textposition='inside', textinfo='percent+label', hovertemplate="<b>%{label}</b><br>%{customdata[0]}<extra></extra>", customdata=pie_df[['hover_sales']])
            fig_pie.update_layout(margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
            st.plotly_chart(fig_pie, use_container_width=True)

    # ---------------- TAB 2 ----------------
    with tab2:
        st.subheader("💡 광고 효율 진단 (배민 광고비 vs 실제 포스기 배민 매출)")
        st.caption("※ Y축은 포스팅된 포스기 원본 기준 '배달의민족' 총 매출이며, X축은 배민 우리가게클릭 지출액입니다.")
        
        if not f_click.empty and '총_광고비' in f_click.columns:
            # Aggregate ad data per store
            ad_by_store = f_click.groupby('매장명').agg(ad_spend=('총_광고비', lambda x: pd.to_numeric(x, errors='coerce').sum())).reset_index()
            
            # Aggregate MatePOS baemin data per store
            baemin_pos = df_daily[(df_daily['h_strnm'].isin(selected_stores)) & (df_daily['platform'] == '배달의민족')]
            if selected_month != "전체": baemin_pos = baemin_pos[baemin_pos['month'] == selected_month]
            pos_by_store = baemin_pos.groupby('h_strnm').agg(pos_baemin_sales=('total_sales', 'sum')).reset_index()
            
            # Merge
            roas_df = pd.merge(ad_by_store, pos_by_store, left_on='매장명', right_on='h_strnm', how='inner')
            
            if not roas_df.empty:
                roas_df['ad_hover'] = roas_df['ad_spend'].apply(format_korean_currency)
                roas_df['sales_hover'] = roas_df['pos_baemin_sales'].apply(format_korean_currency)
                
                c_roas1, c_roas2 = st.columns([2, 1])
                with c_roas1:
                    fig_scatter = px.scatter(roas_df, x='ad_spend', y='pos_baemin_sales', text='매장명', size='pos_baemin_sales', 
                                             color='매장명', custom_data=['매장명', 'ad_hover', 'sales_hover'], size_max=40)
                    fig_scatter.update_traces(textposition='top center', hovertemplate="<b>%{customdata[0]}</b><br>광고비: %{customdata[1]}<br>배민매출: %{customdata[2]}<extra></extra>")
                    fig_scatter.update_layout(xaxis_title="우리가게클릭 총 광고비 (원)", yaxis_title="포스기 실제 배달의민족 총매출 (원)", showlegend=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                    fig_scatter.update_xaxes(showgrid=True, gridcolor='#E5E7EB')
                    fig_scatter.update_yaxes(showgrid=True, gridcolor='#E5E7EB')
                    st.plotly_chart(fig_scatter, use_container_width=True)
                
                with c_roas2:
                    st.info("📊 **분석가 인사이트**\n\n산점도(동그라미)가 **오른쪽(광고비 높음) 아래(매출 낮음)**에 치우쳐있는 매장은 즉각적인 광고 중단 혹은 썸네일/리뷰 개선 등 매장 점검이 시급합니다.\n\n반대로 **왼쪽 위**에 있는 매장은 적은 비용으로 고수익을 내고 있는 우수 운영 매장입니다.")
            else:
                st.warning("선택된 매장의 배민 광고비 vs 포스기 매출 매칭 데이터가 없습니다.")
        else:
            st.warning("배달의민족 '우리가게클릭' 원본 데이터가 존재하지 않습니다.")

    # ---------------- TAB 3 ----------------
    with tab3:
        st.subheader("🍗 핵심 견인 메뉴 TOP 10 (합산)")
        if not filtered_menu.empty:
            top_menus = filtered_menu.groupby('i_itemnm')['total_sales'].sum().reset_index().sort_values(by='total_sales', ascending=False)
            top_menus = top_menus[~top_menus['i_itemnm'].str.contains('배달팁|쇼핑백', na=False)].head(10)
            top_menus['hover_sales'] = top_menus['total_sales'].apply(format_korean_currency)
            
            fig_bar = px.bar(top_menus, x='total_sales', y='i_itemnm', orientation='h', color='total_sales', color_continuous_scale='Blues', custom_data=['hover_sales'])
            fig_bar.update_traces(hovertemplate="<b>%{y}</b><br>%{customdata[0]}<extra></extra>")
            fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False, xaxis_title=None, yaxis_title=None, margin=dict(l=0, r=0, t=20, b=0), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("기간 내의 메뉴 데이터가 없습니다.")
else:
    st.error("데이터 로딩 중...")
