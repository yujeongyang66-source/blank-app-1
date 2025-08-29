#######################
# Import libraries
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px

#######################
# Page configuration
st.set_page_config(
    page_title="US Population Dashboard",
    page_icon="🏂",
    layout="wide",
    initial_sidebar_state="expanded")
alt.themes.enable("default")

#######################
# CSS styling
st.markdown("""
<style>

[data-testid="block-container"] {
    padding-left: 2rem;
    padding-right: 2rem;
    padding-top: 1rem;
    padding-bottom: 0rem;
    margin-bottom: -7rem;
}

[data-testid="stVerticalBlock"] {
    padding-left: 0rem;
    padding-right: 0rem;
}

/* ▶ metric 카드: 흰색 배경 */
[data-testid="stMetric"] {
    background-color: #ffffff;
    text-align: center;
    padding: 15px 0;
    border: 1px solid #eee;
    border-radius: 12px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

/* 중앙 정렬 유지 */
[data-testid="stMetricLabel"] {
  display: flex;
  justify-content: center;
  align-items: center;
}

/* delta 아이콘 위치 보정 */
[data-testid="stMetricDeltaIcon-Up"],
[data-testid="stMetricDeltaIcon-Down"] {
    position: relative;
    left: 38%;
    -webkit-transform: translateX(-50%);
    -ms-transform: translateX(-50%);
    transform: translateX(-50%);
}

/* (선택) metric 글자색 강화 */
[data-testid="stMetricValue"] { color: #111; }
[data-testid="stMetricLabel"] { color: #222; }

</style>
""", unsafe_allow_html=True)

#######################
# Load data
df_reshaped = pd.read_csv('titanic.csv')  # 분석 데이터 넣기

#######################
# Sidebar
with st.sidebar:
    st.markdown("### 🚢 Titanic Survival Dashboard")
    st.caption("타이타닉 승객 데이터 필터")

    df = df_reshaped.copy()

    # 테마 선택
    theme = st.selectbox(
        "색상 테마 선택",
        options=["blues", "viridis", "plasma", "inferno", "magma", "turbo"],
        index=0,
        help="차트 팔레트를 바꿉니다. (컬럼2/3에서 사용)"
    )

    # 필터 위젯
    embarked_opts = sorted([x for x in df["Embarked"].dropna().unique()])
    embarked = st.multiselect(
        "탑승 항구(Embarked)",
        options=embarked_opts,
        default=embarked_opts,
        help="C(Cherbourg) / Q(Queenstown) / S(Southampton)"
    )

    sex_opts = ["male", "female"]
    sex = st.multiselect("성별(Sex)", options=sex_opts, default=sex_opts)

    pclass_opts = [1, 2, 3]
    pclass = st.multiselect("객실 등급(Pclass)", options=pclass_opts, default=pclass_opts)

    # 안전한 min/max
    age_min = int(df["Age"].dropna().min()) if df["Age"].notna().any() else 0
    age_max = int(df["Age"].dropna().max()) if df["Age"].notna().any() else 80
    age_range = st.slider("나이 범위(Age)", 0, max(80, age_max), (age_min, age_max), 1)

    fare_min = float(df["Fare"].dropna().min()) if df["Fare"].notna().any() else 0.0
    fare_max = float(df["Fare"].dropna().max()) if df["Fare"].notna().any() else 600.0
    fare_range = st.slider("운임 범위(Fare)", 0.0, max(600.0, fare_max), (fare_min, fare_max), 0.5)

    # 리셋
    if st.button("필터 초기화", use_container_width=True):
        st.experimental_rerun()

    # 필터 적용
    df_filtered = df.copy()
    if embarked:
        df_filtered = df_filtered[df_filtered["Embarked"].isin(embarked)]
    if sex:
        df_filtered = df_filtered[df_filtered["Sex"].isin(sex)]
    if pclass:
        df_filtered = df_filtered[df_filtered["Pclass"].isin(pclass)]

    df_filtered = df_filtered[
        (df_filtered["Age"].between(age_range[0], age_range[1]) | df_filtered["Age"].isna())
        &
        (df_filtered["Fare"].between(fare_range[0], fare_range[1]) | df_filtered["Fare"].isna())
    ]

    st.session_state["df_filtered"] = df_filtered
    st.session_state["theme"] = theme

    st.markdown("---")
    st.markdown("**현재 필터 결과 요약**")
    st.metric("행 개수", len(df_filtered))
    st.caption("이 결과가 컬럼1/2/3 시각화의 입력이 됩니다.")

#######################
# Dashboard Main Panel
col = st.columns((1.5, 4.5, 2), gap='medium')

# -------- 컬럼 1: 요약 지표 --------
with col[0]:
    st.markdown("### ⚓ Survival Insights")

    df_filtered = st.session_state["df_filtered"]

    total = len(df_filtered)
    survived = int(df_filtered["Survived"].sum())
    died = total - survived
    survival_rate = survived / total * 100 if total > 0 else 0

    st.metric("전체 승객 수", f"{total}")
    st.metric("생존자 수", f"{survived}", delta=f"{survival_rate:.1f}%")
    st.metric("사망자 수", f"{died}")

    st.markdown("---")
    st.markdown("#### 👥 성별별 생존률")

    sex_stats = (
        df_filtered.groupby("Sex")["Survived"]
        .mean()
        .mul(100)
        .round(1)
        .to_dict()
    )
    col_sex = st.columns(2)
    with col_sex[0]:
        st.metric("남성 생존률", f"{sex_stats.get('male', 0.0):.1f} %")
    with col_sex[1]:
        st.metric("여성 생존률", f"{sex_stats.get('female', 0.0):.1f} %")

# -------- 컬럼 2: 분포/패턴 --------
with col[1]:
    st.markdown("### 📊 Distribution & Patterns")

    df_filtered = st.session_state["df_filtered"].copy()
    theme = st.session_state["theme"]

    if len(df_filtered) > 0:
        # 연령대 컬럼
        bins = [0, 10, 20, 30, 40, 50, 60, 70, 80]
        labels = ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70+"]
        df_filtered["AgeGroup"] = pd.cut(
            df_filtered["Age"], bins=bins, labels=labels, right=False
        )

        # 히트맵 (AgeGroup × Pclass 생존률)
        heatmap_data = (
            df_filtered.groupby(["AgeGroup", "Pclass"])["Survived"]
            .mean()
            .reset_index()
        )
        heatmap_data["Survived"] = heatmap_data["Survived"] * 100

        st.markdown("#### 🔥 연령대 × 객실등급별 생존률 히트맵")
        heatmap_chart = px.density_heatmap(
            heatmap_data, x="Pclass", y="AgeGroup", z="Survived",
            color_continuous_scale=theme, text_auto=".1f",
            labels={"Survived": "생존률(%)"},
        )
        st.plotly_chart(heatmap_chart, use_container_width=True)

        # 탑승 항구별 생존률
        embarked_data = (
            df_filtered.groupby("Embarked")["Survived"]
            .mean()
            .mul(100)
            .reset_index()
            .rename(columns={"Survived": "SurvivalRate"})
        )

        st.markdown("#### 🛳 탑승 항구별 생존률")
        embarked_chart = px.bar(
            embarked_data, x="Embarked", y="SurvivalRate",
            text="SurvivalRate", color="Embarked",
            color_discrete_sequence=px.colors.qualitative.Set2,
            labels={"SurvivalRate": "생존률(%)", "Embarked": "탑승 항구"},
        )
        embarked_chart.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        st.plotly_chart(embarked_chart, use_container_width=True)
    else:
        st.warning("⚠️ 선택된 조건에 맞는 데이터가 없습니다.")

# -------- 컬럼 3: 상세/Top --------
with col[2]:
    st.markdown("### 🏅 Detailed Analysis")

    df_filtered = st.session_state["df_filtered"].copy()

    if len(df_filtered) > 0:
        # 연령대 컬럼
        bins = [0, 10, 20, 30, 40, 50, 60, 70, 80]
        labels = ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70+"]
        df_filtered["AgeGroup"] = pd.cut(
            df_filtered["Age"], bins=bins, labels=labels, right=False
        )

        # 연령대별 생존자 TOP5
        top_age = (
            df_filtered[df_filtered["Survived"] == 1]
            .groupby("AgeGroup")["Survived"]
            .count()
            .reset_index()
            .rename(columns={"Survived": "Survivors"})
            .sort_values(by="Survivors", ascending=False)
            .head(5)
        )

        st.markdown("#### 👶 연령대별 생존자 TOP 5")
        top_age_chart = px.bar(
            top_age, x="Survivors", y="AgeGroup",
            orientation="h", text="Survivors",
            color="AgeGroup", color_discrete_sequence=px.colors.qualitative.Set3,
            labels={"Survivors": "생존자 수", "AgeGroup": "연령대"},
        )
        top_age_chart.update_traces(textposition="outside")
        st.plotly_chart(top_age_chart, use_container_width=True)

        # 운임(Fare) 상위 10명
        st.markdown("#### 💰 운임 상위 10명 승객")
        top_fare = (
            df_filtered[["Name", "Pclass", "Sex", "Age", "Fare", "Survived"]]
            .sort_values(by="Fare", ascending=False)
            .head(10)
        )
        st.dataframe(top_fare, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ 선택된 조건에 맞는 데이터가 없습니다.")

    # About
    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.write(
        """
        - **데이터셋**: Titanic Dataset (Kaggle 제공)
        - **주요 변수 설명**
            - `Survived`: 생존 여부 (0=사망, 1=생존)  
            - `Pclass`: 객실 등급 (1=1등급, 2=2등급, 3=3등급)  
            - `Sex`: 성별  
            - `Age`: 나이  
            - `Fare`: 운임 요금  
            - `Embarked`: 탑승 항구 (C=Cherbourg, Q=Queenstown, S=Southampton)  
        - **대시보드 목적**:  
          탑승객 특성(성별, 연령대, 객실 등급, 탑승 항구 등)에 따른 생존률 패턴을 시각적으로 탐색
        """
    )
