import streamlit as st
import pandas as pd
import re
import io

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 CSS 스타일링
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SSU DATA CENTER", 
    page_icon="⚽", 
    layout="wide"
)

# 커스텀 CSS
st.markdown("""
    <style>
    /* 메인 컨테이너 패딩 조절 */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* 헤더 스타일 */
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        padding-bottom: 20px;
        border-bottom: 2px solid #eee;
    }
    .main-title { 
        font-size: 2.5rem; 
        font-weight: 800; 
        color: #00467F; 
        line-height: 1.2;
    }
    .sub-title { 
        font-size: 1.2rem; 
        font-weight: 600; 
        color: #666; 
    }
    
    /* 카드 스타일 (데이터 표시 영역) */
    .data-card {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        border: 1px solid #f0f0f0;
    }
    
    /* 메트릭 카드 스타일 */
    div[data-testid="stMetric"] {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #eee;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 데이터 처리 함수
# -----------------------------------------------------------------------------
@st.cache_data
def load_default_data():
    """기본 CSV 파일 로드 (GitHub 업로드용)"""
    try:
        df_p = pd.read_csv("player_records.csv")
        df_m = pd.read_csv("match_records.csv")
        return preprocess_data(df_p, df_m)
    except FileNotFoundError:
        return None, None

def preprocess_data(df_p, df_m):
    """데이터 전처리 공통 함수"""
    # 날짜/연도 타입 통일
    df_p['날짜'] = df_p['날짜'].astype(str)
    df_m['날짜'] = df_m['날짜'].astype(str)
    df_p['연도'] = df_p['연도'].astype(int)
    df_m['연도'] = df_m['연도'].astype(int)
    
    # 숫자형 데이터 결측치 처리 (NaN -> 0)
    numeric_cols = ['득점', '도움', '실점', '경고', 'MOM', '출전시간']
    for col in numeric_cols:
        if col in df_p.columns:
            df_p[col] = pd.to_numeric(df_p[col], errors='coerce').fillna(0)
            
    return df_p, df_m

def parse_match_result(score_str):
    """스코어 문자열 파싱"""
    if pd.isna(score_str) or score_str == '-':
        return None, 0, 0
    clean_score = re.sub(r'\(.*?\)', '', str(score_str))
    try:
        parts = clean_score.split(':')
        home = int(parts[0])
        away = int(parts[1])
        result = '무'
        if home > away: result = '승'
        elif home < away: result = '패'
        return result, home, away
    except:
        return None, 0, 0

# -----------------------------------------------------------------------------
# 3. 데이터 로드 및 헤더 구성
# -----------------------------------------------------------------------------

# 헤더 레이아웃 (좌: 타이틀, 우: 데이터 입력)
col_header_left, col_header_right = st.columns([3, 1])

with col_header_left:
    st.markdown('<div class="main-title">SSU DATA CENTER</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">SSU FOOTBALL TEAM</div>', unsafe_allow_html=True)

with col_header_right:
    # 데이터 입력 창 (Expander)
    with st.expander("📂 데이터 업로드/수정", expanded=False):
        st.info("CSV 내용을 붙여넣으세요.")
        csv_text_player = st.text_area("선수 기록 (Player)", height=100, help="player_records.csv 내용")
        csv_text_match = st.text_area("경기 기록 (Match)", height=100, help="match_records.csv 내용")

# 데이터 로드 로직
if csv_text_player and csv_text_match:
    try:
        df_p_raw = pd.read_csv(io.StringIO(csv_text_player))
        df_m_raw = pd.read_csv(io.StringIO(csv_text_match))
        df_player, df_match = preprocess_data(df_p_raw, df_m_raw)
        st.toast("✅ 데이터가 업데이트되었습니다.", icon="💾")
    except Exception as e:
        st.error(f"데이터 오류: {e}")
        df_player, df_match = load_default_data()
else:
    df_player, df_match = load_default_data()

if df_player is None or df_match is None:
    st.error("❌ 데이터를 찾을 수 없습니다. CSV 내용을 입력하거나 GitHub에 파일을 올려주세요.")
    st.stop()

st.divider()

# -----------------------------------------------------------------------------
# 4. 가로형 필터바
# -----------------------------------------------------------------------------
st.markdown("##### 🔍 기록 검색 필터")

# 필터 초기화 함수
def reset_filters():
    st.session_state.year = []
    st.session_state.tour = []
    st.session_state.opp = []
    st.session_state.player = []

# 필터 레이아웃
f_col1, f_col2, f_col3, f_col4, f_col5 = st.columns([1.5, 1.5, 1.5, 1.5, 0.5])

# 전체 데이터 기준 옵션
all_years = sorted(df_player['연도'].unique(), reverse=True)
all_tournaments = sorted(df_player['대회명'].unique())
all_opponents = sorted(df_player['상대팀'].unique())

# 1. 연도 선택
with f_col1:
    selected_years = st.multiselect(
        "📅 연도", 
        all_years, 
        key='year',
        format_func=lambda x: str(x) # 2,025 -> 2025 포맷팅
    )

# 2. 대회명 선택
with f_col2:
    selected_tournaments = st.multiselect("🏆 대회명", all_tournaments, key='tour')

# 3. 상대팀 선택
with f_col3:
    selected_opponents = st.multiselect("🆚 상대팀", all_opponents, key='opp')

# 4. 선수명 선택 (로직 개선: 선택된 연도에 기록이 있는 선수만 표시)
# 먼저 연도로 데이터를 임시 필터링하여 선수 목록을 추출
temp_player_df = df_player.copy()
if selected_years:
    temp_player_df = temp_player_df[temp_player_df['연도'].isin(selected_years)]

# 출전 시간이 0이거나 기록이 없는 경우는 제외할 수도 있으나, 명단에 있으면 포함하는 것이 일반적이므로 이름 기준으로 추출
available_players = sorted(temp_player_df['선수명'].unique())

with f_col4:
    selected_players = st.multiselect("🏃 선수명", available_players, key='player')

# 5. 초기화 버튼
with f_col5:
    st.write("") # 줄맞춤용 공백
    st.write("") 
    st.button("🔄", on_click=reset_filters, help="필터 초기화")

# -----------------------------------------------------------------------------
# 5. 데이터 필터링 적용
# -----------------------------------------------------------------------------
filtered_p = df_player.copy()

if selected_years:
    filtered_p = filtered_p[filtered_p['연도'].isin(selected_years)]
if selected_tournaments:
    filtered_p = filtered_p[filtered_p['대회명'].isin(selected_tournaments)]
if selected_opponents:
    filtered_p = filtered_p[filtered_p['상대팀'].isin(selected_opponents)]

# 선수 선택 여부에 따라 데이터 분기
if selected_players:
    filtered_p_match_subset = filtered_p[filtered_p['선수명'].isin(selected_players)]
else:
    filtered_p_match_subset = filtered_p

# 경기 기록 매칭
relevant_matches = filtered_p_match_subset[['날짜', '상대팀']].drop_duplicates()
final_match_df = df_match.merge(relevant_matches, on=['날짜', '상대팀'], how='inner')

# -----------------------------------------------------------------------------
# 6. 메인 콘텐츠 (카드형 디자인)
# -----------------------------------------------------------------------------

# [Case 1] 전체 선수 보기 (Team Record)
if not selected_players:
    # 카드 시작
    with st.container():
        st.markdown('<div class="data-card">', unsafe_allow_html=True)
        st.subheader("🛡️ TEAM RECORDS (전체 보기)")
        
        # (1) 요약 통계
        wins, draws, losses = 0, 0, 0
        team_goals, team_conceded = 0, 0
        
        for score in final_match_df['스코어']:
            res, h, a = parse_match_result(score)
            if res == '승': wins += 1
            elif res == '무': draws += 1
            elif res == '패': losses += 1
            team_goals += h
            team_conceded += a
        
        total_games = len(final_match_df)
        
        # 최다 MOM
        mom_stats = filtered_p.groupby('선수명')['MOM'].sum().sort_values(ascending=False)
        mom_text = "-"
        if not mom_stats.empty and mom_stats.iloc[0] > 0:
            top_mom_player = mom_stats.index[0]
            top_mom_count = int(mom_stats.iloc[0])
            mom_text = f"{top_mom_player} ({top_mom_count}회)"

        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("총 경기수", f"{total_games}전")
        mc2.metric("전적", f"{wins}승 {draws}무 {losses}패")
        mc3.metric("팀 득실", f"{team_goals}득 / {team_conceded}실")
        mc4.metric("최다 MOM", mom_text)
        
        st.divider()

        # (2) 탭 (전체 경기가 먼저)
        t1, t2 = st.tabs(["📅 전체 경기 일정", "📊 선수 랭킹"])
        
        with t1:
            view_cols = ['연도', '대회명', '라운드', '날짜', '상대팀', '스코어', '득점자', '비고']
            view_cols = [c for c in view_cols if c in final_match_df.columns]
            # 연도 포맷팅을 위해 문자열 변환 후 표시
            display_match = final_match_df[view_cols].copy()
            st.dataframe(display_match, use_container_width=True, hide_index=True)
            
        with t2:
            rank_df = filtered_p.groupby('선수명').agg({
                '득점': 'sum', '도움': 'sum', 'MOM': 'sum', '출전시간': 'count'
            }).reset_index().rename(columns={'출전시간': '경기수'})
            
            rank_df = rank_df.sort_values(['득점', '경기수'], ascending=[False, False])
            rank_df.index = range(1, len(rank_df)+1)
            
            st.dataframe(
                rank_df, use_container_width=True,
                column_config={
                    "득점": st.column_config.ProgressColumn(format="%d골", min_value=0, max_value=int(rank_df['득점'].max())),
                    "경기수": st.column_config.NumberColumn(format="%d경기")
                }
            )
        st.markdown('</div>', unsafe_allow_html=True) # 카드 끝

# [Case 2] 선수 지정 보기 (Player Stats)
else:
    player_list_str = ", ".join(selected_players)
    
    # 카드 시작
    with st.container():
        st.markdown('<div class="data-card">', unsafe_allow_html=True)
        st.subheader(f"🏃 PLAYER STATS : {player_list_str}")
        
        # 선택된 선수 데이터
        p_df = filtered_p[filtered_p['선수명'].isin(selected_players)]
        
        # 골키퍼 여부 (실점 기록 존재 시)
        is_goalkeeper = p_df['실점'].sum() > 0
        
        # 스탯 계산
        p_apps = len(p_df)
        p_starts = len(p_df[p_df['선발/교체'] == '선발'])
        p_subs = len(p_df[p_df['선발/교체'] == '교체'])
        
        stat_val_1 = int(p_df['득점'].sum())
        
        if is_goalkeeper:
            stat_label_2 = "실점 (GK)"
            stat_val_2 = int(p_df['실점'].sum())
        else:
            stat_label_2 = "도움"
            stat_val_2 = int(p_df['도움'].sum())
            
        p_mom_count = int(p_df['MOM'].sum())

        pc1, pc2, pc3, pc4 = st.columns(4)
        pc1.metric("출전 경기", f"{p_apps}경기")
        pc2.metric("선발 / 교체", f"{p_starts} / {p_subs}")
        pc3.metric(f"득점 / {stat_label_2}", f"{stat_val_1} / {stat_val_2}")
        pc4.metric("MOM 선정", f"{p_mom_count}회")
        
        st.divider()
        
        st.markdown("##### 📝 Match Log")
        if not p_df.empty:
            view_df = p_df.copy()
            view_df['MOM'] = view_df['MOM'].apply(lambda x: '⭐' if x == 1 else '')
            view_df['출전시간'] = view_df['출전시간'].astype(int).astype(str) + "'"
            
            cols = ['연도', '날짜', '대회명', '상대팀', '선발/교체', '출전시간', '득점']
            if is_goalkeeper:
                cols.append('실점')
            else:
                cols.append('도움')
            cols.extend(['MOM', '경고', '비고'])
            
            view_cols = [c for c in cols if c in view_df.columns]
            view_df = view_df.sort_values('날짜', ascending=False)
            
            st.dataframe(view_df[view_cols], use_container_width=True, hide_index=True)
        else:
            st.warning("선택된 조건의 기록이 없습니다.")
            
        st.markdown('</div>', unsafe_allow_html=True) # 카드 끝
