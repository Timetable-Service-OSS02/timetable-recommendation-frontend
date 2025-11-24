# -----------------------------------------------
# 1. 기본 라이브러리 임포트
# -----------------------------------------------
import streamlit as st
import pandas as pd
import sys
import os

# -----------------------------------------------
# 2. [핵심] 모듈 경로 문제 해결
# -----------------------------------------------
# 'core' 서브모듈 폴더를 파이썬의 모듈 검색 경로에 추가합니다.
# 이렇게 해야 'core' 폴더 안에 있는 models.py와 algorithms.py를
# app.py에서 정상적으로 불러올 수 있습니다.
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

# -----------------------------------------------
# 3. 프로젝트 모듈 임포트
# -----------------------------------------------
# 이제 'core' 폴더가 경로에 잡혔으므로, 정상적으로 임포트됩니다.
from core.models import Subject
from core.algorithms import base_strategy, credit_priority_strategy, generate_timetables
from visualizer import draw_timetable  # UI 폴더의 visualizer 임포트

# -----------------------------------------------
# 4. Streamlit 페이지 설정
# -----------------------------------------------
st.set_page_config(layout="wide")
st.title("🎓 전략 패턴 기반 시간표 자동 생성기")
st.info("이 앱은 `frontend` 레포지토리에서 실행되며, `backend` 레포지토리의 로직을 `core`라는 서브모듈로 불러와 사용합니다.")

# -----------------------------------------------
# 5. 데이터 로드 (경로 수정)
# -----------------------------------------------
# 엑셀 파일은 'core' 서브모듈 폴더 내에 위치합니다.
EXCEL_PATH = "core/subjects.xlsx"

@st.cache_data
def load_data(path):
    try:
        df = pd.read_excel(path)
        return df
    except FileNotFoundError:
        st.error(f"'{path}' 파일을 찾을 수 없습니다.")
        st.warning("Git Submodule이 올바르게 초기화되었는지 확인하세요.")
        st.code("git submodule update --init --recursive", language="bash")
        return None

df = load_data(EXCEL_PATH)

if df is None:
    st.stop() # 데이터 로드 실패 시 앱 실행 중지

# -----------------------------------------------
# 6. 사용자 입력 UI (사이드바)
# -----------------------------------------------
with st.sidebar:
    st.header("⚙️ 시간표 조건 설정")
    
    # 데이터프레임에서 고유값 추출
    years = df["학년"].unique()
    depts = df["학과"].unique()
    
    # UI 위젯
    year = st.selectbox("학년", years)
    dept = st.selectbox("학과", depts)
    free_days = st.multiselect("희망 공강 요일", ["월", "화", "수", "목", "금"])
    num_subjects = st.number_input("들을 과목 개수", min_value=1, max_value=10, value=5, step=1)

    # 7. 전략 선택 UI
    strategy_name = st.selectbox(
        "시간표 생성 전략", 
        ["기본 전략 (생성만)", "학점 우선 전략 (높은 학점 순 정렬)"]
    )
    
    if strategy_name == "학점 우선 전략":
        strategy_func = credit_priority_strategy
    else:
        strategy_func = base_strategy

# -----------------------------------------------
# 8. 메인 로직 실행
# -----------------------------------------------
if st.button("시간표 생성하기"):
    with st.spinner("최적의 시간표를 탐색 중입니다..."):
        
        # 8-1. 1차 필터링: 학과, 학년
        filtered_df = df[(df["학과"] == dept) & (df["학년"] == year)]
        
        # 8-2. 2차 필터링: 희망 공강일 제외
        if free_days:
            filtered_df = filtered_df[~filtered_df["요일"].isin(free_days)]

        # 8-3. DataFrame을 Subject 객체 리스트로 변환
        subjects_pool = [
            Subject(
                name=row["과목명"],
                day=row["요일"],
                start=row["시작시간"],
                end=row["종료시간"],
                credit=row["학점"],
                room=row["강의실"]
            )
            for _, row in filtered_df.iterrows()
        ]

        # 8-4. 핵심 알고리즘 실행 (core.algorithms 모듈 호출)
        results = list(generate_timetables(subjects_pool, num_subjects, strategy_func))

        # 9. 결과 출력
        if not results:
            st.warning("선택한 조건에 맞는 시간표를 찾을 수 없습니다. 조건을 변경해보세요.")
        else:
            st.success(f"총 {len(results)}개의 시간표를 찾았습니다!")
            
            # 전략에 따라 결과 정렬
            if strategy_name == "학점 우선 전략":
                results.sort(key=lambda x: x[1], reverse=True) # score 기준 내림차순

            for idx, (timetable, score) in enumerate(results):
                if strategy_name == "학점 우선 전략":
                    st.subheader(f"추천 시간표 {idx + 1} (총 학점: {score})")
                else:
                    st.subheader(f"추천 시간표 {idx + 1}")
                
                # 9-1. 시각화 모듈 호출 (visualizer.py)
                fig = draw_timetable(timetable)
                st.pyplot(fig)
                
                # 9-2. 텍스트 상세 정보
                with st.expander("텍스트로 상세 정보 보기"):
                    for subject in timetable:
                        st.write(f"- {subject}") # Subject 클래스의 __repr__ 호출

else:
    st.info("왼쪽 사이드바에서 조건을 설정하고 '시간표 생성하기' 버튼을 눌러주세요.")