import streamlit as st
import pandas as pd
import random
import os
from gtts import gTTS
import io

# --- 설정 ---
st.set_page_config(page_title="토익 영단어장", page_icon="📚")

# CSS 스타일 (카드, 리스트, 탭 디자인)
st.markdown("""
    <style>
    /* 전체 폰트 및 배경 */
    .stApp {
        background-color: #ffffff;
    }
    /* 단어 공부 탭의 리스트 스타일 */
    .study-list-item {
        padding: 15px 20px;
        background-color: #f8f9fa;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .study-word {
        font-size: 20px;
        font-weight: bold;
        color: #333;
    }
    .study-meaning {
        font-size: 18px;
        color: #555;
    }
    /* 시험 보기 탭의 카드 스타일 */
    .quiz-card {
        padding: 40px;
        border-radius: 15px;
        background-color: #fff;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        text-align: center;
        margin: 20px 0;
        border: 2px solid #e0e0e0;
    }
    .quiz-word-text {
        color: #333; 
        font-size: 50px; 
        font-weight: bold;
        margin: 10px 0;
    }
    .meaning-box {
        text-align: center; 
        margin-bottom: 20px; 
        padding: 15px; 
        background-color: #e8f5e9; 
        border-radius: 10px;
        border: 1px solid #c8e6c9;
    }
    .meaning-text {
        color: #2e7d32; 
        font-size: 24px;
        font-weight: bold;
        margin: 0;
    }
    /* 버튼 높이 조정 */
    .stButton button {
        height: 50px;
        font-size: 18px;
    }
    </style>
""", unsafe_allow_html=True)

# 1. 데이터 로드 함수
@st.cache_data
def load_data():
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(script_dir, 'toeic_words.csv')
        try:
            df = pd.read_csv(csv_path, encoding='utf-8-sig')
        except:
            df = pd.read_csv(csv_path, encoding='cp949')
        df['Day'] = df['Day'].astype(str)
        return df
    except Exception as e:
        return None

df = load_data()

# --- 사이드바 (설정 영역) ---
st.sidebar.title("⚙️ 설정")

if df is not None:
    # 1. Day 선택
    days = sorted(df['Day'].unique().tolist(), key=lambda x: int(x) if x.isdigit() else 999)
    selected_day = st.sidebar.selectbox("공부할 DAY를 선택하세요", days)
    
    # 해당 Day 데이터 추출
    day_words_all = df[df['Day'] == selected_day][['Word', 'Meaning']].to_dict('records')
    
    st.sidebar.markdown("---")
    
    # 2. [위치 이동됨] 발음 자동 재생 토글
    auto_play = st.sidebar.toggle("🔊 발음 자동 재생 (시험용)", value=True)
    
    st.sidebar.caption(f"총 단어 수: {len(day_words_all)}개")
    
    # 3. 시험 초기화 버튼
    if st.sidebar.button("🔄 시험 시작"):
        random.shuffle(day_words_all)
        st.session_state['quiz_data'] = day_words_all
        st.session_state['current_index'] = 0
        st.session_state['wrong_answers'] = []
        st.session_state['show_meaning'] = False
        st.session_state['study_finished'] = False
        st.rerun()
else:
    st.error("CSV 파일을 찾을 수 없습니다.")
    st.stop()

# --- 메인 화면: 탭 분리 ---
st.title(f"📖 Day {selected_day} 마스터하기")

# 탭 생성
tab1, tab2 = st.tabs(["👀 단어 공부 (List)", "📝 실전 시험 (Test)"])

# ==========================================
# 탭 1: 단어 공부 모드 (리스트 보기)
# ==========================================
with tab1:
    st.header("단어 목록 훑어보기")
    st.caption("시험 보기 전에 단어와 뜻을 가볍게 읽어보세요.")
    
    for item in day_words_all:
        st.markdown(f"""
        <div class="study-list-item">
            <span class="study-word">{item['Word']}</span>
            <span class="study-meaning">{item['Meaning']}</span>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# 탭 2: 시험 보기 모드 (퀴즈 기능)
# ==========================================
with tab2:
    if 'quiz_data' not in st.session_state:
        st.info("👈 왼쪽 사이드바에서 [시험 초기화] 버튼을 눌러 시작하세요!")
    
    elif st.session_state['study_finished']:
        st.balloons()
        st.success("🎉 시험 종료! 결과가 나왔습니다.")
        
        score = len(st.session_state['quiz_data']) - len(st.session_state['wrong_answers'])
        total_q = len(st.session_state['quiz_data'])
        st.metric("내 점수", f"{score} / {total_q}점")

        if st.session_state['wrong_answers']:
            st.write("### ❌ 틀린 문제 (오답노트)")
            wrong_df = pd.DataFrame(st.session_state['wrong_answers'])
            st.table(wrong_df)
            
            csv = wrong_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("오답노트 다운로드 (CSV)", csv, 'wrong_notes.csv', 'text/csv')
        else:
            st.write("완벽합니다! 💯 하나도 틀리지 않았어요.")
            
    else:
        # 현재 문제 데이터
        index = st.session_state['current_index']
        total = len(st.session_state['quiz_data'])
        word_data = st.session_state['quiz_data'][index]

        # 진행바
        st.progress((index / total))
        st.caption(f"문제 {index + 1} / {total}")

        # 단어 카드
        st.markdown(f"""
        <div class="quiz-card">
            <div class="quiz-word-text">{word_data['Word']}</div>
        </div>
        """, unsafe_allow_html=True)

        # 발음 재생 (사이드바의 auto_play 변수 사용)
        tts = gTTS(text=word_data['Word'], lang='en')
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        st.audio(mp3_fp, format='audio/mp3', autoplay=auto_play, start_time=0)

        # 버튼 인터페이스
        if not st.session_state['show_meaning']:
            if st.button("🔍 정답 확인", use_container_width=True):
                st.session_state['show_meaning'] = True
                st.rerun()
        else:
            st.markdown(f"""
            <div class="meaning-box">
                <p class="meaning-text">{word_data['Meaning']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("⭕ 맞았음", use_container_width=True):
                    st.session_state['current_index'] += 1
                    st.session_state['show_meaning'] = False
                    if st.session_state['current_index'] >= total:
                        st.session_state['study_finished'] = True
                    st.rerun()
            
            with col2:
                if st.button("❌ 틀렸음", use_container_width=True):
                    st.session_state['wrong_answers'].append(word_data)
                    st.toast(f"🥲 오답노트 저장! ({len(st.session_state['wrong_answers'])}개째)")
                    st.session_state['current_index'] += 1
                    st.session_state['show_meaning'] = False
                    if st.session_state['current_index'] >= total:
                        st.session_state['study_finished'] = True
                    st.rerun()

