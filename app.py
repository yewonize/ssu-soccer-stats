import streamlit as st
import pandas as pd
import re
import io

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 CSS 스타일링
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SSU DATA CENTER", 
    layout="wide"
)

# 커스텀 CSS
st.markdown("""
    <style>
    /* 폰트 설정 및 전체 글자 크기 축소 */
    html, body, [class*="css"] {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif;
        font-size: 13px;
    }
    
    /* 메인 컨테이너 패딩 조절 */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    
    /* 헤더 스타일 (파란색 배경) */
    .header-box {
        background-color: #00467F; /* SSU Blue */
        padding: 25px;
        border-radius: 10px;
        margin-bottom: 15px;
        color: white;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .header-text-group {
        display: flex;
        flex-direction: column;
    }
    
    .main-title { 
        font-size: 24px; 
        font-weight: 800; 
        color: white; 
        line-height: 1.2;
        margin-bottom: 4px;
    }
    
    .sub-title { 
        font-size: 14px; 
        font-weight: 500; 
        color: #e0e0e0; 
        margin: 0;
    }
    
    /* 데이터 카드 스타일 */
    .data-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        border: 1px solid #eee;
    }
    
    /* 커스텀 메트릭 박스 스타일 */
    .custom-metric-box {
        background-color: #f8f9fa;
        padding: 12px 10px;
        border-radius: 8px;
        border: 1px solid #eee;
        text-align: center;
    }
    .metric-label {
        font-size: 11px;
        color: #666;
        margin-bottom: 4px;
        font-weight: 500;
    }
    .metric-value {
        font-size: 18px;
        font-weight: 700;
        color: #333;
    }
    .metric-unit {
        font-size: 11px;
        font-weight: normal;
        color: #777;
        margin-left: 1px;
    }
    
    /* 득실 색상 클래스 */
    .val-blue { color: #00467F; }
    .val-red { color: #D32F2F; }
    
    /* 테이블 스타일 조정 */
    thead tr th {
        font-size: 12px !important;
        background-color: #f8f9fa !important;
    }
    tbody td {
        font-size: 12px !important;
    }
    thead tr th:first-child {display:none}
    tbody th {display:none}
    
    /* 버튼 스타일 */
    div.stButton > button {
        border-radius: 6px;
        font-size: 12px;
        padding: 0.25rem 0.75rem;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 데이터 처리 및 세션 관리
# -----------------------------------------------------------------------------

# 초기 데이터 로드
if 'player_csv' not in st.session_state:
    try:
        with open("player_records.csv", "r", encoding="utf-8") as f:
            st.session_state['player_csv'] = f.read()
    except FileNotFoundError:
        st.session_state['player_csv'] = ""

if 'match_csv' not in st.session_state:
    try:
        with open("match_records.csv", "r", encoding="utf-8") as f:
            st.session_state['match_csv'] = f.read()
    except FileNotFoundError:
        st.session_state['match_csv'] = ""

def preprocess_data(df_p, df_m):
    """데이터 전처리 공통 함수"""
    df_p['날짜'] = df_p['날짜'].astype(str)
    df_m['날짜'] = df_m['날짜'].astype(str)
    df_p['연도'] = df_p['연도'].astype(int)
    df_m['연도'] = df_m['연도'].astype(int)
    
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
# 3. 헤더 구성 및 데이터 입력창 (Expander 사용)
# -----------------------------------------------------------------------------

# 헤더 섹션
st.markdown("""
<div class="header-box">
    <div class="header-text-group">
        <div class="main-title">SSU DATA CENTER</div>
        <div class="sub-title">SSU FOOTBALL TEAM</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 데이터 등록/수정 섹션 (st.dialog 대신 st.expander 사용)
with st.expander("데이터 일괄 등록/수정 (클릭하여 열기)", expanded=False):
    st.info("엑셀이나 CSV 파일의 내용을 복사해서 아래 입력창에 붙여넣으세요. (첫 줄 헤더 포함)")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### 1. 경기기록 (Match Data)")
        st.caption("필수 컬럼: 연도, 대회명, 라운드, 날짜, 상대팀, 스코어...")
        new_match_csv = st.text_area(
            "match_input", 
            value=st.session_state.match_csv, 
            height=200, 
            label_visibility="collapsed"
        )
    with c2:
        st.markdown("##### 2. 선수기록 (Player Data)")
        st.caption("필수 컬럼: 연도, 대회명, 라운드, 날짜, 상대팀, 선수명, 선발/교체...")
        new_player_csv = st.text_area(
            "player_input", 
            value=st.session_state.player_csv, 
            height=200, 
            label_visibility="collapsed"
        )
    
    if st.button("데이터 업데이트", type="primary"):
        st.session_state.match_csv = new_match_csv
        st.session_state.player_csv = new_player_csv
        st.rerun()

# 데이터 로드
if st.session_state.player_csv and st.session_state.match_csv:
    try:
        df_p_raw = pd.read_csv(io.StringIO(st.session_state.player_csv))
        df_m_raw = pd.read_csv(io.StringIO(st.session_state.match_csv))
        df_player, df_match = preprocess_data(df_p_raw, df_m_raw)
    except Exception as e:
        st.error(f"데이터 형식 오류: {e}")
        st.stop()
else:
    st.warning("데이터가 없습니다. 위 입력창에서 데이터를 입력해주세요.")
    st.stop()

st.write("") # 여백

# -----------------------------------------------------------------------------
# 4. 가로형 필터바
# -----------------------------------------------------------------------------
st.markdown("##### 기록 검색 필터")

def reset_filters():
    st.session_state.year = []
    st.session_state.tour = []
    st.session_state.opp = []
    st.session_state.player = []

f_col1, f_col2, f_col3, f_col4, f_col5 = st.columns([1.5, 1.5, 1.5, 1.5, 0.5])

all_years = sorted(df_player['연도'].unique(), reverse=True)
all_tournaments = sorted(df_player['대회명'].unique())
all_opponents = sorted(df_player['상대팀'].unique())

with f_col1:
    selected_years = st.multiselect("연도", all_years, key='year', format_func=lambda x: str(x))
with f_col2:
    selected_tournaments = st.multiselect("대회명", all_tournaments, key='tour')
with f_col3:
    selected_opponents = st.multiselect("상대팀", all_opponents, key='opp')

temp_player_df = df_player.copy()
if selected_years:
    temp_player_df = temp_player_df[temp_player_df['연도'].isin(selected_years)]
available_players = sorted(temp_player_df['선수명'].unique())

with f_col4:
    selected_players = st.multiselect("선수명", available_players, key='player')
with f_col5:
    st.write("") 
    st.write("") 
    st.button("초기화", on_click=reset_filters)

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

if selected_players:
    filtered_p_match_subset = filtered_p[filtered_p['선수명'].isin(selected_players)]
else:
    filtered_p_match_subset = filtered_p

relevant_matches = filtered_p_match_subset[['날짜', '상대팀']].drop_duplicates()
final_match_df = df_match.merge(relevant_matches, on=['날짜', '상대팀'], how='inner')

# -----------------------------------------------------------------------------
# 6. 메인 콘텐츠 (카드형 디자인)
# -----------------------------------------------------------------------------

# HTML로 커스텀 메트릭을 그리는 함수
def render_metric(label, value_html):
    st.markdown(f"""
    <div class="custom-metric-box">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value_html}</div>
    </div>
    """, unsafe_allow_html=True)

# [Case 1] 전체 선수 보기 (Team Record)
if not selected_players:
    with st.container():
        st.markdown('<div class="data-card">', unsafe_allow_html=True)
        st.subheader("TEAM RECORDS")
        
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
            mom_text = f"{top_mom_player} <span class='metric-unit'>({top_mom_count}회)</span>"

        # 커스텀 메트릭 렌더링
        mc1, mc2, mc3, mc4 = st.columns(4)
        
        with mc1:
            render_metric("총 경기수", f"{total_games}<span class='metric-unit'>경기</span>")
        with mc2:
            render_metric("전적", f"{wins}<span class='metric-unit'>승</span> {draws}<span class='metric-unit'>무</span> {losses}<span class='metric-unit'>패</span>")
        with mc3:
            render_metric("팀 득실", f"<span class='val-blue'>{team_goals}</span><span class='metric-unit'>득</span> / <span class='val-red'>{team_conceded}</span><span class='metric-unit'>실</span>")
        with mc4:
            render_metric("최다 MOM", mom_text)
        
        st.divider()

        t1, t2 = st.tabs(["전체 경기 일정", "선수 랭킹"])
        
        with t1:
            view_cols = ['대회명', '라운드', '날짜', '상대팀', '스코어', '득점자', '비고']
            view_cols = [c for c in view_cols if c in final_match_df.columns]
            display_match = final_match_df[view_cols].copy()
            st.dataframe(display_match.fillna(""), use_container_width=True, hide_index=True)
            
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
        st.markdown('</div>', unsafe_allow_html=True)

# [Case 2] 선수 지정 보기 (Player Stats)
else:
    player_list_str = ", ".join(selected_players)
    
    with st.container():
        st.markdown('<div class="data-card">', unsafe_allow_html=True)
        st.subheader(f"PLAYER STATS : {player_list_str}")
        
        p_df = filtered_p[filtered_p['선수명'].isin(selected_players)]
        is_goalkeeper = p_df['실점'].sum() > 0
        
        p_apps = len(p_df)
        p_starts = len(p_df[p_df['선발/교체'] == '선발'])
        p_subs = len(p_df[p_df['선발/교체'] == '교체'])
        stat_val_1 = int(p_df['득점'].sum())
        p_mom_count = int(p_df['MOM'].sum())
        
        if is_goalkeeper:
            # 골키퍼인 경우 실점 표시 (빨간색)
            stat_val_2 = int(p_df['실점'].sum())
            val2_html = f"<span class='val-red'>{stat_val_2}</span><span class='metric-unit'>실</span>"
            stat2_label = "득점 / 실점(GK)"
            val1_html = f"<span class='val-blue'>{stat_val_1}</span><span class='metric-unit'>득</span>"
        else:
            # 필드 플레이어인 경우 도움 표시
            stat_val_2 = int(p_df['도움'].sum())
            val2_html = f"{stat_val_2}<span class='metric-unit'>도</span>"
            stat2_label = "득점 / 도움"
            val1_html = f"<span class='val-blue'>{stat_val_1}</span><span class='metric-unit'>득</span>"

        pc1, pc2, pc3, pc4 = st.columns(4)
        with pc1:
            render_metric("출전 경기", f"{p_apps}<span class='metric-unit'>경기</span>")
        with pc2:
            render_metric("선발 / 교체", f"{p_starts}<span class='metric-unit'>선</span> / {p_subs}<span class='metric-unit'>교</span>")
        with pc3:
            render_metric(stat2_label, f"{val1_html} / {val2_html}")
        with pc4:
            render_metric("MOM 선정", f"{p_mom_count}<span class='metric-unit'>회</span>")
        
        st.divider()
        
        st.markdown("##### Match Log")
        if not p_df.empty:
            view_df = p_df.copy()
            view_df['MOM'] = view_df['MOM'].apply(lambda x: 'O' if x == 1 else '')
            view_df['출전시간'] = view_df['출전시간'].astype(int).astype(str) + "'"
            
            cols = ['날짜', '대회명', '상대팀', '선발/교체', '출전시간', '득점']
            if is_goalkeeper:
                cols.append('실점')
            else:
                cols.append('도움')
            cols.extend(['MOM', '경고', '비고'])
            
            view_cols = [c for c in cols if c in view_df.columns]
            view_df = view_df.sort_values('날짜', ascending=False)
            
            st.dataframe(view_df[view_cols].fillna(""), use_container_width=True, hide_index=True)
        else:
            st.warning("선택된 조건의 기록이 없습니다.")
            
        st.markdown('</div>', unsafe_allow_html=True)
