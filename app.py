import io
import re
from collections import Counter
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from wordcloud import WordCloud

# =========================================================
# 0. 한글 폰트 설정 (OS 환경에 맞춰 자동 적용)
# =========================================================
plt.rcParams["axes.unicode_minus"] = False  # 마이너스(-) 부호 깨짐 방지
try:
    plt.rcParams["font.family"] = "Malgun Gothic"  # 윈도우 한글 폰트
except:
    plt.rcParams["font.family"] = "AppleGothic"  # 맥OS 한글 폰트

# =========================================================
# 1. 웹페이지 제목
# =========================================================
st.title("📊 캠퍼스 생활 설문조사 결과 분석 웹페이지")
st.write(
    "우리 학교 학생들의 생활 습관과 학교생활 만족도를 학과별로 확인해보세요!"
)

# =========================================================
# 2. CSV 파일 업로드
# =========================================================
uploaded_file = st.file_uploader(
    "campus_life.csv 파일을 업로드해주세요:", type=["csv"]
)

# 파일이 업로드되었을 때만 분석 실행
if uploaded_file is not None:
    # CSV 파일 읽기
    df = pd.read_csv(uploaded_file)

    # =====================================================
    # 3. 데이터 미리보기
    # =====================================================
    st.subheader("1. 데이터 미리보기")
    st.write("업로드된 설문조사 원본 데이터의 앞부분 5개 행입니다:")
    st.dataframe(df.head())

    # =====================================================
    # 4. 데이터 전처리 결과
    # =====================================================
    st.subheader("2. 전처리 결과")

    raw_count = len(df)

    # '만족도' 열에 포함된 '모름' 등의 텍스트를 결측치(NaN)로 변환 후 실수형으로 변환
    df["만족도"] = pd.to_numeric(df["만족도"], errors="coerce")

    # 결측치 제거
    cleaned_df = df.dropna().copy()
    clean_count = len(cleaned_df)

    st.success(
        f"✔️ 전처리 완료: 전체 **{raw_count}명** 응답 중 결측치 및 이상치 **{raw_count - clean_count}건**을 제외하여 총 **{clean_count}명**의 데이터를 분석에 사용합니다."
    )

    # =====================================================
    # 5. 학과 선택 필터 및 평균 만족도
    # =====================================================
    st.subheader("3. 학과 선택")

    dept_options = ["전체"] + sorted(list(cleaned_df["학과"].unique()))
    selected_dept = st.selectbox("조회하고 싶은 학과를 선택하세요:", dept_options)

    # 선택한 학과 데이터 필터링
    if selected_dept == "전체":
        dept_df = cleaned_df
    else:
        dept_df = cleaned_df[cleaned_df["학과"] == selected_dept]

    # 선택된 학과의 평균 만족도 표시
    avg_satisfaction = dept_df["만족도"].mean()
    st.metric(
        label=f"[{selected_dept}] 학생들의 평균 학교생활 만족도",
        value=f"{avg_satisfaction:.2f}점 / 10점 만점",
    )

    # =====================================================
    # 6. 설문 분석 그래프
    # =====================================================
    st.subheader("4. 설문 분석 그래프")

    # --- [그래프 1] 학생 구성 비율 (원그래프) ---
    st.write("#### 🥧 1) 학생 구성 분포 (원그래프)")
    grade_counts = dept_df["학년"].value_counts().sort_index()

    fig1, ax1 = plt.subplots(figsize=(5, 5))
    ax1.pie(
        grade_counts,
        labels=[f"{grade}학년" for grade in grade_counts.index],
        autopct="%1.1f%%",
        startangle=140,
        colors=["#A0C4FF", "#BDB2FF", "#FFC6FF", "#FDFFB6"],
    )
    ax1.set_title(f"[{selected_dept}] 학년별 비율", fontsize=12)
    st.pyplot(fig1)

    # --- [그래프 2] 생활 시간과 만족도 관계 (산점도) ---
    st.write("#### 📈 2) 생활 시간과 학교생활 만족도 관계 (산점도)")
    time_feature = st.radio(
        "비교할 항목을 선택하세요:",
        ["공부시간", "수면시간", "스마트폰", "통학시간"],
        horizontal=True,
    )

    fig2, ax2 = plt.subplots(figsize=(6, 4))
    ax2.scatter(
        dept_df[time_feature],
        dept_df["만족도"],
        color="#2b5c8f",
        s=80,
        alpha=0.75,
        edgecolor="black",
    )
    ax2.set_xlabel(f"{time_feature} (시간 / 분)", fontsize=11)
    ax2.set_ylabel("학교생활 만족도 (점수)", fontsize=11)
    ax2.set_title(f"{time_feature}과 만족도 간의 관계", fontsize=12)
    ax2.grid(True, linestyle="--", alpha=0.5)
    st.pyplot(fig2)

    # --- [그래프 3] 한 줄 의견 키워드 (워드 클라우드) ---
    st.write("#### ☁️ 3) 한 줄 의견 키워드 (워드 클라우드)")
    all_comments = " ".join(dept_df["한줄의견"].dropna().tolist())

    if len(all_comments.strip()) > 0:
        try:
            wc = WordCloud(
                font_path="malgun.ttf",
                width=700,
                height=350,
                background_color="white",
            ).generate(all_comments)
        except:
            wc = WordCloud(
                font_path="/System/Library/Fonts/Supplemental/AppleGothic.ttf",
                width=700,
                height=350,
                background_color="white",
            ).generate(all_comments)

        fig3, ax3 = plt.subplots(figsize=(8, 4))
        ax3.imshow(wc, interpolation="bilinear")
        ax3.axis("off")
        st.pyplot(fig3)
    else:
        st.info("해당 조건에 표시할 한 줄 의견 데이터가 없습니다.")

    # =====================================================
    # 7. [신규 추가] 한 줄 의견 심층 분석 (빈출 단어 & 감성 분석)
    # =====================================================
    st.subheader("5. 💬 한 줄 의견 심층 단어 분석")

    # (1) 한글 단어 추출 정규표현식 (공백, 문장부호 제거 후 한글 단어만 추출)
    words = re.findall(r"[가-힣]+", all_comments)

    if len(words) > 0:
        # 단어별 등장 횟수 계산
        word_counts = Counter(words)

        # -------------------------------------------------
        # 기능 1: 상위 10개 단어 막대그래프
        # -------------------------------------------------
        st.write("#### 📊 가장 많이 등장한 단어 TOP 10")
        top_10 = word_counts.most_common(10)
        top_words = [item[0] for item in top_10]
        top_freqs = [item[1] for item in top_10]

        # 가로 막대그래프 생성 (위에서부터 1위 순으로 보이게 reversed 적용)
        fig4, ax4 = plt.subplots(figsize=(7, 4))
        ax4.barh(
            list(reversed(top_words)),
            list(reversed(top_freqs)),
            color="#5B9BD5",
        )
        ax4.set_xlabel("등장 횟수 (회)")
        ax4.set_title(f"[{selected_dept}] 한 줄 의견 빈출 단어 상위 10개")

        # 막대 끝에 숫자 레이블 달아주기
        for i, val in enumerate(reversed(top_freqs)):
            ax4.text(val + 0.1, i, f"{val}회", va="center", fontsize=9)

        st.pyplot(fig4)

        # -------------------------------------------------
        # 기능 2: 긍정 / 부정 단어 등장 횟수 분석
        # -------------------------------------------------
        st.write("#### ⚖️ 긍정 vs 부정 단어 등장 횟수 비교")

        # 설문 데이터에 자주 나타나는 긍정/부정 단어 사전 정의
        positive_keywords = [
            "좋아요",
            "재미있어요",
            "맛있어요",
            "즐거워요",
            "친절해요",
            "도움이",
            "만족",
            "예뻐서",
            "좋습니다",
        ]
        negative_keywords = [
            "피곤해요",
            "부족해서",
            "불편해요",
            "비싸서",
            "아쉬워요",
            "부족해요",
            "힘들어요",
            "후회돼요",
            "어려워요",
        ]

        # 등장 횟수 합산
        pos_total = sum(word_counts[w] for w in positive_keywords)
        neg_total = sum(word_counts[w] for w in negative_keywords)

        # 나란히 카드(metric) 형태로 결과 표시
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                label="😊 긍정 단어 등장 횟수",
                value=f"{pos_total}회",
                help="예: 좋아요, 재미있어요, 맛있어요, 즐거워요 등",
            )
        with col2:
            st.metric(
                label="🙁 부정 단어 등장 횟수",
                value=f"{neg_total}회",
                help="예: 피곤해요, 부족해서, 불편해요, 힘들어요 등",
            )

        # 긍정/부정 비교 막대그래프
        fig5, ax5 = plt.subplots(figsize=(5, 3))
        ax5.bar(
            ["긍정 단어", "부정 단어"],
            [pos_total, neg_total],
            color=["#70AD47", "#ED7D31"],
            width=0.5,
        )
        ax5.set_ylabel("등장 횟수 (회)")
        ax5.set_title(f"[{selected_dept}] 긍정 / 부정 단어 언급 비교")

        # 막대 위 숫자 표시
        for i, val in enumerate([pos_total, neg_total]):
            ax5.text(i, val + 0.5, f"{val}회", ha="center", fontsize=10)

        st.pyplot(fig5)

    else:
        st.info("분석할 단어 데이터가 충분하지 않습니다.")

else:
    st.warning("👈 위에서 `campus_life.csv` 파일을 업로드하면 분석이 시작됩니다!")