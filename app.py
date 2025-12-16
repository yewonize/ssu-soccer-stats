import streamlit as st
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="숭실대학교 축구단 기록실", layout="wide")

# 데이터 로드 (캐싱 적용)
@st.cache_data
def load_data():
    df_p = pd.read_csv("player_records.csv")
    df_m = pd.read_csv("match_records.csv")
    return df_p, df_m

df_player, df_match = load_data()

st.title("⚽ 숭실대학교 축구단 기록 필터")
st.markdown("데이터를 **위에서부터 순서대로** 선택하세요. (탑다운 방식)")

# --- 사이드바 필터 (요청하신 순서 적용) ---
with st.sidebar:
    st.header("🔍 검색 조건")

    # 1. 연도 (Year)
    all_years = sorted(df_player['연도'].unique(), reverse=True)
    sel_year = st.multiselect("1. 연도 선택", all_years, default=all_years)
    
    # 데이터 1차 필터링
    df_temp = df_player[df_player['연도'].isin(sel_year)]

    # 2. 경기일자 (Date) - 연도에 맞는 날짜만 표시
    available_dates = sorted(df_temp['날짜'].unique(), reverse=True)
    sel_date = st.multiselect("2. 경기일자 선택 (선택 시 좁혀짐)", available_dates)
    
    if sel_date:
        df_temp = df_temp[df_temp['날짜'].isin(sel_date)]

    # 3. 대회/리그 (Tournament) - 남은 데이터 기준
    available_tournaments = sorted(df_temp['대회명'].unique())
    sel_tour = st.multiselect("3. 대회/리그 선택", available_tournaments)

    if sel_tour:
        df_temp = df_temp[df_temp['대회명'].isin(sel_tour)]

    # 4. 상대교 (Opponent)
    available_opponents = sorted(df_temp['상대팀'].unique())
    sel_opp = st.multiselect("4. 상대교 선택", available_opponents)

    if sel_opp:
        df_temp = df_temp[df_temp['상대팀'].isin(sel_opp)]

    # 5. 선수명 (Player)
    available_players = sorted(df_temp['선수명'].unique())
    sel_player = st.multiselect("5. 선수명 선택 (필수 아님)", available_players)

    # 최종 필터링
    df_final_player = df_temp.copy()
    if sel_player:
        df_final_player = df_final_player[df_final_player['선수명'].isin(sel_player)]

# --- 결과 데이터 매칭 ---
# 선수 기록에 해당하는 '경기 기록' 찾기
relevant_keys = df_final_player[['날짜', '상대팀']].drop_duplicates()
df_final_match = df_match.merge(relevant_keys, on=['날짜', '상대팀'], how='inner')

# --- 화면 출력 ---

# 요약
c1, c2, c3 = st.columns(3)
c1.metric("검색된 경기 수", f"{len(df_final_match)} 경기")
c2.metric("선수 득점 합계", f"{int(df_final_player['득점'].sum())} 골")
c3.metric("MOM 선정 횟수", f"{df_final_player[df_final_player['MOM']==1].shape[0]} 회")

st.divider()

# 탭으로 구분하여 보기
tab1, tab2 = st.tabs(["📋 선수 기록 (Player Stats)", "📅 경기 기록 (Match Stats)"])

with tab1:
    if not df_final_player.empty:
        # 보기 좋은 컬럼 순서
        cols = ['연도', '대회명', '날짜', '상대팀', '선수명', '선발/교체', '출전시간', '득점', '도움', 'MOM', '경고', '비고']
        view_df = df_final_player[[c for c in cols if c in df_final_player.columns]].copy()
        
        # MOM 시각화
        if 'MOM' in view_df.columns:
            view_df['MOM'] = view_df['MOM'].apply(lambda x: '⭐' if x == 1 else '')
            
        st.dataframe(view_df, use_container_width=True, hide_index=True)
    else:
        st.warning("조건에 맞는 선수 기록이 없습니다.")

with tab2:
    if not df_final_match.empty:
        cols = ['연도', '대회명', '라운드', '날짜', '상대팀', '스코어', '득점자', 'MOM', '비고']
        view_df = df_final_match[[c for c in cols if c in df_final_match.columns]]
        st.dataframe(view_df, use_container_width=True, hide_index=True)
    else:
        st.warning("조건에 맞는 경기 기록이 없습니다.")
