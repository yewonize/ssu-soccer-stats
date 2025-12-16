import streamlit as st
import pandas as pd
import re
import io

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 디자인
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SSU DATA CENTER", 
    page_icon="⚽", 
    layout="wide"
)

# 메인 헤더 디자인
st.markdown("""
    <style>
    .main-title { font-size: 3rem; font-weight: 800; color: #00467F; margin-bottom: 0;}
    .sub-title { font-size: 1.5rem; font-weight: 600; color: #555; margin-top: -10px; margin-bottom: 20px;}
    .metric-card { background-color: #f0f2f6; padding: 15px; border-radius: 10px; text-align: center; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">SSU DATA CENTER</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">SSU FOOTBALL TEAM</div>', unsafe_allow_html=True)

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
    """스코어 문자열(예: '2:1', '1:1(4PSO3)')을 파싱하여 승무패 및 득실 계산"""
    if pd.isna(score_str) or score_str == '-':
        return None, 0, 0
    
    # (PSO) 등 괄호 제거
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
# 3. 사이드바: 데이터 업로드 & 필터
# -----------------------------------------------------------------------------
st.sidebar.header("📂 데이터 관리")

# 파일 업로드 대신 텍스트 입력 방식 적용
with st.sidebar.expander("📝 데이터 직접 입력 (CSV)", expanded=False):
    st.info("CSV 파일의 내용을 복사해서 아래 칸에 붙여넣으세요.")
    csv_text_player = st.text_area("선수 기록 (Player CSV)", height=150, help="player_records.csv 내용을 붙여넣으세요.")
    csv_text_match = st.text_area("경기 기록 (Match CSV)", height=150, help="match_records.csv 내용을 붙여넣으세요.")

# 데이터 로드 로직 (텍스트 입력 우선, 없으면 기본 파일)
if csv_text_player and csv_text_match:
    try:
        df_p_raw = pd.read_csv(io.StringIO(csv_text_player))
        df_m_raw = pd.read_csv(io.StringIO(csv_text_match))
        df_player, df_match = preprocess_data(df_p_raw, df_m_raw)
        st.sidebar.success("✅ 입력한 데이터가 적용되었습니다.")
    except Exception as e:
        st.sidebar.error(f"❌ 데이터 형식 오류: {e}")
        df_player, df_match = load_default_data()
else:
    # 텍스트 입력이 하나라도 비어있으면 기본 파일 로드
    df_player, df_match = load_default_data()
    if csv_text_player or csv_text_match:
        st.sidebar.warning("⚠️ 선수 기록과 경기 기록을 모두 입력해야 적용됩니다.")

if df_player is None or df_match is None:
    st.error("❌ 데이터를 찾을 수 없습니다. CSV 내용을 입력하거나 GitHub에 파일을 올려주세요.")
    st.stop()

st.sidebar.divider()
st.sidebar.header("🔍 기록 검색 필터")

# 필터 초기화 콜백 함수
def reset_filters():
    st.session_state.year = []
    st.session_state.tour = []
    st.session_state.opp = []
    st.session_state.player = []

st.sidebar.button("🔄 필터 초기화", on_click=reset_filters)

# 필터 옵션 (전체 데이터 기준)
all_years = sorted(df_player['연도'].unique(), reverse=True)
all_tournaments = sorted(df_player['대회명'].unique())
all_opponents = sorted(df_player['상대팀'].unique())
all_players = sorted(df_player['선수명'].unique())

# Multiselect 위젯 (key를 지정하여 초기화 가능하게 함)
selected_years = st.sidebar.multiselect("📅 연도", all_years, key='year')
selected_tournaments = st.sidebar.multiselect("🏆 대회명", all_tournaments, key='tour')
selected_opponents = st.sidebar.multiselect("🆚 상대팀", all_opponents, key='opp')
selected_players = st.sidebar.multiselect("🏃 선수명", all_players, key='player')

# -----------------------------------------------------------------------------
# 4. 데이터 필터링
# -----------------------------------------------------------------------------
filtered_p = df_player.copy()

if selected_years:
    filtered_p = filtered_p[filtered_p['연도'].isin(selected_years)]
if selected_tournaments:
    filtered_p = filtered_p[filtered_p['대회명'].isin(selected_tournaments)]
if selected_opponents:
    filtered_p = filtered_p[filtered_p['상대팀'].isin(selected_opponents)]
# 선수 필터는 '전체 보기' vs '개인 보기' 분기용으로 사용하되, 데이터 자체도 줄여놓음
if selected_players:
    filtered_p_for_match = filtered_p[filtered_p['선수명'].isin(selected_players)]
else:
    filtered_p_for_match = filtered_p

# 경기 기록 매칭
relevant_matches = filtered_p_for_match[['날짜', '상대팀']].drop_duplicates()
final_match_df = df_match.merge(relevant_matches, on=['날짜', '상대팀'], how='inner')

# -----------------------------------------------------------------------------
# 5. 화면 출력
# -----------------------------------------------------------------------------

# [Case 1] 전체 선수 보기 (Team View)
if not selected_players:
    st.subheader("🛡️ TEAM RECORDS (전체 보기)")
    
    # (1) 승무패 및 득실 계산
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
    
    # (2) 최다 MOM 계산
    mom_stats = filtered_p.groupby('선수명')['MOM'].sum().sort_values(ascending=False)
    if not mom_stats.empty and mom_stats.iloc[0] > 0:
        top_mom_player = mom_stats.index[0]
        top_mom_count = int(mom_stats.iloc[0])
        mom_text = f"{top_mom_player} ({top_mom_count}회)"
    else:
        mom_text = "-"

    # (3) 메트릭 표시
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("총 경기수", f"{total_games}전")
    c2.metric("전적", f"{wins}승 {draws}무 {losses}패")
    c3.metric("팀 득실", f"{team_goals}득점 / {team_conceded}실점")
    c4.metric("최다 MOM", mom_text)

    st.divider()

    # (4) 탭 구성
    t1, t2 = st.tabs(["📊 선수 랭킹", "📅 전체 경기 일정"])
    
    with t1:
        # 랭킹 데이터 생성
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
        
    with t2:
        view_cols = ['연도', '대회명', '라운드', '날짜', '상대팀', '스코어', '득점자', '비고']
        view_cols = [c for c in view_cols if c in final_match_df.columns]
        st.dataframe(final_match_df[view_cols], use_container_width=True, hide_index=True)

# [Case 2] 선수 지정 보기 (Player View)
else:
    player_list_str = ", ".join(selected_players)
    st.subheader(f"🏃 PLAYER STATS : {player_list_str}")
    
    # 선택된 선수들의 데이터만 다시 필터링
    p_df = filtered_p[filtered_p['선수명'].isin(selected_players)]
    
    # (1) 골키퍼 판별 로직 (실점이 하나라도 있으면 GK로 간주)
    is_goalkeeper = p_df['실점'].sum() > 0
    
    # (2) 개인 스탯 계산
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

    # (3) 메트릭 표시
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("출전 경기", f"{p_apps}경기")
    c2.metric("선발 / 교체", f"{p_starts} / {p_subs}")
    c3.metric(f"득점 / {stat_label_2}", f"{stat_val_1} / {stat_val_2}")
    c4.metric("MOM 선정", f"{p_mom_count}회")
    
    st.divider()
    
    # (4) 상세 로그
    st.markdown("##### 📝 Match Log")
    if not p_df.empty:
        view_df = p_df.copy()
        view_df['MOM'] = view_df['MOM'].apply(lambda x: '⭐' if x == 1 else '')
        view_df['출전시간'] = view_df['출전시간'].astype(int).astype(str) + "'"
        
        # GK면 실점 표시, 아니면 도움 표시
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
