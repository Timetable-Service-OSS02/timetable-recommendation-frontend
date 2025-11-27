# visualizer.py
import matplotlib.pyplot as plt
import pandas as pd

# 한글 폰트 설정 (Windows: Malgun Gothic, Mac: AppleGothic)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def draw_timetable(timetable):
    """
    Timetable 객체를 받아 matplotlib figure 반환
    (다중 요일/시간대 지원 버전)
    """
    days = ["월", "화", "수", "목", "금"]
    # 9시부터 18시(오후 6시)까지 표시
    times = range(9, 19)

    # 빈 시간표 프레임 생성
    df_table = pd.DataFrame(index=times, columns=days).fillna("")

    # 색상 팔레트
    colors = ['#FF9999', '#66B2FF', '#99FF99', '#FFCC99', '#FFD700', 
              '#DDA0DD', '#8FBC8F', '#F08080', '#AFEEEE', '#FFE4B5']
    color_map = {}
    
    # 시간표 채우기 로직
    for idx, subj in enumerate(timetable.subjects):
        # 과목별 고유 색상 지정
        color = colors[idx % len(colors)]
        color_map[subj.name] = color
        
        # [핵심 변경] times 리스트를 순회하며 모든 시간대를 칠함
        # 예: [('월', 11, 13), ('수', 11, 12)]
        for day_str, start_h, end_h in subj.times:
            
            # 요일이 우리가 표시하는 범위(월~금)에 없으면 패스 (토요수업 등)
            if day_str not in days:
                continue

            # 해당 시간 칸 채우기
            for t in range(start_h, end_h):
                if t in df_table.index:
                    # 셀에 들어갈 텍스트: 과목명 + (교수님) + 강의실
                    prof_info = f"\n({subj.professor})" if subj.professor else ""
                    room_info = f"\n{subj.room}" if subj.room else ""
                    
                    text = f"{subj.name}{prof_info}{room_info}"
                    df_table.loc[t, day_str] = text

    # Matplotlib 그리기 설정
    fig, ax = plt.subplots(figsize=(10, 8)) # 세로 길이 조금 늘림
    ax.axis("off")
    ax.axis("tight")
    
    # 테이블 셀 색상 적용
    cell_colours = []
    for r in range(len(df_table)):
        row_colors = []
        for c in range(len(df_table.columns)):
            val = df_table.iloc[r, c]
            color = "white"
            # 텍스트가 있으면(수업이 있으면) 색칠
            if val != "":
                # 텍스트에서 과목명만 추출해서 색상 매핑 찾기
                subj_name = val.split("\n")[0]
                color = color_map.get(subj_name, "white")
            row_colors.append(color)
        cell_colours.append(row_colors)

    # 테이블 생성
    table = ax.table(cellText=df_table.values,
                     rowLabels=[f"{t}:00" for t in df_table.index],
                     colLabels=df_table.columns,
                     cellLoc='center',
                     loc='center',
                     cellColours=cell_colours)
    
    # 스타일 조정
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.0, 1.8) # 셀 높이 조정
    
    plt.title("🎓 2025학년도 추천 시간표", fontsize=15, pad=20)
    plt.tight_layout()
    
    return fig