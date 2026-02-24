import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(page_title="프랜차이즈 매출 통합 대시보드", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for Premium Design (Forcing Clean Light Theme style)
st.markdown("""
<style>
    /* Main container and text */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        font-family: 'Pretendard', sans-serif;
    }
    
    /* Force Light Mode styling on elements if OS is dark */
    .stApp {
        background-color: #FAFAFA;
        color: #111827;
    }
    
    /* KPI Metrics Styling */
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 800;
        color: #1E3A8A;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 1.1rem;
        font-weight: 600;
        color: #4B5563;
    }
    
    /* Header Styling */
    h1 {
        color: #0F172A;
        font-weight: 900;
        margin-bottom: 2rem;
        border-bottom: 3px solid #3B82F6;
        padding-bottom: 1rem;
    }
    h2, h3 {
        color: #1E293B;
        font-weight: 700;
        margin-top: 2rem;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #F8FAFC;
        border-right: 1px solid #E2E8F0;
    }
    
    /* Hide specific unneeded elements */
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# -----------------
# 1. Data Loading (Relative Paths for Cloud)
# -----------------
@st.cache_data
def load_data():
    # Use relative path for cloud deployment
    base_path = "streamlit_data"
    
    # 1. 일별 매출/주문수 데이터
    df_daily = pd.DataFrame()
    daily_path = os.path.join(base_path, 'mart_daily_sales.csv')
    if os.path.exists(daily_path):
        df_daily = pd.read_csv(daily_path)
    
    # 2. 메뉴별 판매 데이터
    df_menu = pd.DataFrame()
    menu_path = os.path.join(base_path, 'mart_menu_sales.csv')
    if os.path.exists(menu_path):
        df_menu = pd.read_csv(menu_path)
        
    # 3. 배민 데이터 (NOW: 재주문율, Click: 광고비/클릭)
    df_bm_now = pd.DataFrame()
    now_path = os.path.join(base_path, 'mart_baemin_now.csv')
    if os.path.exists(now_path):
        try:
            df_bm_now = pd.read_csv(now_path, encoding='utf-8-sig')
        except:
            df_bm_now = pd.read_csv(now_path, encoding='cp949')
            
    df_bm_click = pd.DataFrame()
    click_path = os.path.join(base_path, 'mart_baemin_click.csv')
    if os.path.exists(click_path):
        try:
            df_bm_click = pd.read_csv(click_path, encoding='utf-8-sig')
        except:
            df_bm_click = pd.read_csv(click_path, encoding='cp949')

    return df_daily, df_menu, df_bm_now, df_bm_click

df_daily, df_menu, df_bm_now, df_bm_click = load_data()

# Data Parsing (Safety)
if not df_daily.empty:
    df_daily['h_orderdt'] = pd.to_datetime(df_daily['h_orderdt'])

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

# -----------------
# 2. Sidebar Filters
# -----------------
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3063/3063822.png", width=60)
st.sidebar.title("📊 통합 컨트롤 패널")
st.sidebar.markdown("---")

if not df_daily.empty:
    # 1. 매장 선택 (최대 5개)
    stores = sorted(list(df_daily['h_strnm'].unique()))
    selected_stores = st.sidebar.multiselect("🏪 매장 비교 선택 (최대 5개)", stores, default=[stores[0]], max_selections=5)
    
    # 2. 월 선택
    months = ["전체"] + sorted(list(df_daily['month'].unique()), reverse=True)
    selected_month = st.sidebar.selectbox("🗓️ 기간 (월별)", months, index=0)
    
    # 3. 플랫폼 다중 선택
    platforms = sorted(list(df_daily['platform'].unique()))
    selected_platforms = st.sidebar.multiselect("🛵 결제 플랫폼 선택", platforms, default=platforms)
    
    st.sidebar.markdown("---")
    st.sidebar.info("💡 사이드바의 필터를 변경하면 화면의 모든 차트와 지표가 실시간으로 업데이트됩니다.")
    
    if len(selected_stores) == 0:
        st.warning("⚠️ 좌측 메뉴에서 최소 1개의 매장을 선택해주세요.")
        st.stop()
        
    if len(selected_platforms) == 0:
        st.warning("⚠️ 좌측 메뉴에서 플랫폼을 1개 이상 선택해주세요.")
        st.stop()
        
    # -----------------
    # 3. Data Filtering
    # -----------------
    filtered_df = df_daily[df_daily['h_strnm'].isin(selected_stores)].copy()
    filtered_menu = df_menu[df_menu['h_strnm'].isin(selected_stores)].copy()
    
    f_now = df_bm_now.copy()
    f_click = df_bm_click.copy()
    
    if not f_now.empty:
        # Match any of the selected stores
        f_now = f_now[f_now['매장명'].apply(lambda x: any(store in str(x) for store in selected_stores))]
    if not f_click.empty:
        f_click = f_click[f_click['매장명'].apply(lambda x: any(store in str(x) for store in selected_stores))]
            
    if selected_month != "전체":
        filtered_df = filtered_df[filtered_df['month'] == selected_month]
        filtered_menu = filtered_menu[filtered_menu['month'] == selected_month]

    filtered_df = filtered_df[filtered_df['platform'].isin(selected_platforms)]

    # Calculate KPIs
    total_sales = filtered_df['total_sales'].sum()
    total_orders = filtered_df['order_count'].sum()
    avg_ticket = total_sales / total_orders if total_orders > 0 else 0
    
    # -----------------
    # 4. Main UI Layout
    # -----------------
    st.title("📈 프랜차이즈 매출 통합 비교 대시보드")
    
    # KPI Section
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="총 매출액", value=format_korean_currency(total_sales))
    with col2:
        st.metric(label="총 주문 건수", value=f"{int(total_orders):,}건")
    with col3:
        st.metric(label="평균 객단가", value=format_korean_currency(avg_ticket))
        
    with col4:
        if not f_now.empty and '최근재주문율_수치' in f_now.columns:
            # Average out the reorder rate if multiple stores are selected
            reorder_vals = pd.to_numeric(f_now['최근재주문율_수치'].astype(str).str.replace('%',''), errors='coerce').mean()
            if pd.notna(reorder_vals):
                st.metric(label="합산 평균 재주문율", value=f"{reorder_vals:.1f}%")
            else:
                st.metric(label="합산 평균 재주문율", value="데이터 없음")
        else:
            st.metric(label="합산 평균 재주문율", value="데이터 로딩 중 ⏳")

    st.markdown("---")
    
    # Charts Section 1: Sales Trends
    st.subheader("📊 매장별 일자 매출 비교 추이")
    if not filtered_df.empty:
        trend_df = filtered_df.groupby(['h_orderdt', 'h_strnm']).agg({'total_sales':'sum'}).reset_index()
        trend_df['hover_sales'] = trend_df['total_sales'].apply(format_korean_currency)
        
        fig = px.line(trend_df, x='h_orderdt', y='total_sales', color='h_strnm', markers=True, 
                      custom_data=['hover_sales', 'h_strnm'],
                      labels={'h_orderdt':'주문 날짜', 'total_sales':'총 매출액 (원)', 'h_strnm':'매장명'})
        
        if len(selected_stores) == 1:
             fig.update_traces(line_color='#3B82F6')
             
        fig.update_traces(
            mode='lines+markers',
            hovertemplate="<b>%{customdata[1]}</b><br>%{x}<br><b>%{customdata[0]}</b><extra></extra>",
            line_width=3, marker_size=8
        )
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', 
                          xaxis_title=None, yaxis_title=None, margin=dict(l=0, r=0, t=20, b=0))    
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#E5E7EB', tickformat='~s')
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("선택하신 조건에 해당하는 매출 데이터가 없습니다.")
        
    st.markdown("---")
    # Charts Section 2: Popular Menus & Ad Performance
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("🍗 합산 인기 메뉴 TOP 10")
        if not filtered_menu.empty:
            top_menus = filtered_menu.groupby('i_itemnm')['total_sales'].sum().reset_index().sort_values(by='total_sales', ascending=False).head(10)
            top_menus = top_menus[~top_menus['i_itemnm'].str.contains('배달팁|쇼핑백', na=False)]
            top_menus['hover_sales'] = top_menus['total_sales'].apply(format_korean_currency)
            
            fig = px.bar(top_menus, x='total_sales', y='i_itemnm', orientation='h',
                         color='total_sales', color_continuous_scale='Blues',
                         custom_data=['hover_sales'])
            fig.update_traces(
                hovertemplate="<b>%{y}</b><br>%{customdata[0]}<extra></extra>"
            )
            fig.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False, xaxis_title=None, yaxis_title=None, margin=dict(l=0, r=0, t=20, b=0), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("선택하신 기간의 메뉴 명세 데이터가 없습니다.")

    with col_chart2:
        st.subheader("🚀 배달의민족 '우리가게 클릭' ROAS 요약")
        if not f_click.empty and '총_광고비' in f_click.columns:
            total_spend = pd.to_numeric(f_click['총_광고비'], errors='coerce').sum()
            total_ad_sales = pd.to_numeric(f_click['총_광고매출'], errors='coerce').sum()
            total_clicks = pd.to_numeric(f_click['총_클릭수'], errors='coerce').sum()
            
            st.markdown(f"""
            <div style='background-color: #EFF6FF; padding: 20px; border-radius: 10px; border: 1px solid #BFDBFE; height: 100%; color: #1E3A8A;'>
                <h4 style='color: #1D4ED8; margin-top:0;'>💰 광고 합산 요약 ({selected_month})</h4>
                <ul style='font-size: 1.1rem; line-height: 1.8;'>
                    <li><b>총 광고 지출액:</b> {format_korean_currency(total_spend)}</li>
                    <li><b>광고 발생 배민매출:</b> {format_korean_currency(total_ad_sales)}</li>
                    <li><b>총 고객 클릭수:</b> {int(total_clicks):,} 회</li>
                </ul>
                <hr style='border-color: #93C5FD;'>
                <div style='text-align:center;'>
                    <span style='font-size: 1rem; color: #4B5563;'>월 광고비 대비 전환 매출액(ROAS)</span><br>
                    <span style='font-size: 2.5rem; font-weight: 800; color: #2563EB;'>
                        {round(total_ad_sales/total_spend*100, 1) if total_spend > 0 else 0}%
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("해당 지점/기간의 배민 광고 데이터가 발견되지 않았습니다.")
            
else:
    st.error("데이터가 비어있습니다. 'streamlit_data' 폴더 안에 데이터 파일들이 있는지 확인해주세요.")
