# app.py
import streamlit as st
import pandas as pd
import sys
import os
import glob

# ---------------------------------------------------------------
# [핵심 수정] 1. Core 모듈 경로를 '가장 먼저' 추가해야 함
# ---------------------------------------------------------------
# 현재 파일(app.py)이 있는 위치에서 'core' 폴더 경로를 찾음
core_path = os.path.join(os.path.dirname(__file__), 'core')

# 파이썬 검색 경로에 core 폴더 추가
# (이게 있어야 models, algorithms를 import 할 수 있음)
if core_path not in sys.path:
    sys.path.append(core_path)

# ---------------------------------------------------------------
# [핵심 수정] 2. 모듈 임포트 (core.algorithms 가 아니라 그냥 algorithms)
# ---------------------------------------------------------------
try:
    # 이제 core 폴더가 검색 경로에 있으므로, 'core.'을 빼고 바로 부릅니다.
    # 이렇게 해야 algorithms.py 내부에서 'from models import...'가 작동합니다.
    from data_loader import load_subjects
    from algorithms import base_strategy, credit_priority_strategy, generate_timetables
    from models import Subject
except ImportError as e:
    st.error(f"❌ Core 모듈 로딩 실패: {e}")
    st.info("💡 해결법: models.py, algorithms.py 등이 core 폴더 안에 있는지 확인하세요.")
    st.warning("혹시 core 폴더가 비어있다면: git submodule update --init --recursive")
    st.stop()

# 시각화 모듈은 frontend 폴더에 있으므로 그냥 임포트
from visualizer import draw_timetable

# ---------------------------------------------------------------
# 3. UI 설정 및 데이터 파일 찾기
# ---------------------------------------------------------------
st.set_page_config(page_title="시간표 추천 프로그램", layout="wide")
st.title("전략패턴 기반 시간표 추천")

# core 폴더 안에서 엑셀이나 CSV 파일 찾기
data_files = glob.glob(os.path.join(core_path, "Book1.*")) + glob.glob(os.path.join(core_path, "subjects.*"))

if not data_files:
    st.error("❌ 데이터 파일(Book1.csv 또는 Book1.xls)을 'core' 폴더에서 찾을 수 없습니다.")
    st.stop()

# 가장 첫 번째로 발견된 파일 사용
DATA_FILE_PATH = data_files[0]

# ---------------------------------------------------------------
# 4. 사이드바: 사용자 정보 입력
# ---------------------------------------------------------------
with st.sidebar:
    st.header("📝 내 정보 입력")
    
    # 학과/학년 목록을 가져오기 위해 깡통 데이터프레임을 잠시 읽음 (UI 표시용)
    try:
        if DATA_FILE_PATH.endswith('.csv'):
            try:
                pre_df = pd.read_csv(DATA_FILE_PATH, encoding='cp949')
            except:
                pre_df = pd.read_csv(DATA_FILE_PATH, encoding='utf-8')
        else:
            pre_df = pd.read_excel(DATA_FILE_PATH)
            
        all_depts = sorted(pre_df['개설학과'].dropna().unique())
        all_grades = sorted(pre_df['학년'].dropna().unique().astype(str))
        
    except Exception as e:
        st.error(f"데이터 미리보기 실패: {e}")
        st.stop()

    # 입력 폼
    dept = st.selectbox("학과", all_depts)
    year = st.selectbox("학년", all_grades)
    num_subjects = st.slider("듣고 싶은 과목 수", 3, 8, 5)
    
    st.markdown("---")
    st.header("⚙️ 추천 옵션")
    strategy_name = st.radio("우선순위", ["기본(랜덤)", "학점 꽉 채우기"])

# 전략 함수 매핑
if strategy_name == "학점 꽉 채우기":
    strategy_func = credit_priority_strategy
else:
    strategy_func = base_strategy

# ---------------------------------------------------------------
# 5. 메인 로직 실행
# ---------------------------------------------------------------
if st.button("🚀 시간표 생성 시작", type="primary"):
    
    with st.spinner(f"'{os.path.basename(DATA_FILE_PATH)}'에서 데이터를 불러오는 중..."):
        # [Backend 호출] 전처리 모듈을 통해 과목 리스트 로딩
        subjects_pool = load_subjects(DATA_FILE_PATH, dept, year)
    
    if not subjects_pool:
        st.error("조건에 맞는 개설 강좌가 하나도 없습니다. (학과/학년을 확인해주세요)")
    else:
        st.success(f"총 {len(subjects_pool)}개의 후보 강좌를 찾았습니다!")
        
        # [Backend 호출] 알고리즘을 통해 시간표 조합 생성
        with st.spinner("최적의 시간표를 굽는 중... (이름 중복 제거 & 시간 충돌 검사)"):
            results = list(generate_timetables(subjects_pool, num_subjects, strategy_func))
        
        if not results:
            st.warning("가능한 시간표 조합이 없습니다. 과목 수를 줄이거나 조건을 변경해보세요.")
        else:
            st.balloons()
            # 점수 높은 순 정렬
            results.sort(key=lambda x: x[1], reverse=True)
            
            st.markdown(f"### 🎯 추천 시간표 TOP {min(5, len(results))}")
            
            # 탭으로 결과 보여주기
            tabs = st.tabs([f"옵션 {i+1}" for i in range(min(5, len(results)))])
            
            for i, tab in enumerate(tabs):
                timetable, score = results[i]
                with tab:
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        # [Frontend] 시각화 모듈 호출
                        fig = draw_timetable(timetable)
                        st.pyplot(fig)
                        
                    with col2:
                        st.info(f"💡 전략 점수: {score}점")
                        st.markdown("**[포함된 과목]**")
                        for subj in timetable.subjects:
                            # 분반이나 교수님 정보가 있으면 같이 표시
                            section_info = f"- {subj.section}분반" if subj.section else ""
                            prof_info = f"({subj.professor})" if subj.professor else ""
                            st.write(f"- **{subj.name}** {prof_info} {section_info}")
                            st.caption(f"&nbsp;&nbsp; └ {subj.room} / {subj.credit}학점")