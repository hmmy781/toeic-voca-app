import streamlit as st
import pandas as pd
import random
import os
from gtts import gTTS
import io
import base64  # [추가됨] 오디오 파일을 코드로 변환하기 위해 필요

# --- 설정 ---
st.set_page_config(page_title="토익 영단어장", page_icon="📚")

# CSS 스타일
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    
    /* 리스트 모드 스타일 (클릭 가능하게 커서 변경) */
    .study-list-item {
        padding: 20px;
        background-color: #f8f9fa;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        cursor: pointer; /* 손가락 모양 커서 */
        transition: transform 0.1s;
    }
    .study-list-item:active {
        transform: scale(0.98); /* 클릭 시 살짝 눌리는 효과 */
        background-color: #e3f2fd;
    }
    .study-word { font-size: 22px; font-weight: bold; color: #333; display: block; }
    .study-meaning { font-size: 18px; color: #666; display: block; margin-top: 5px;}
    
    /* 퀴즈 카드 스타일 */
    .quiz-card {
        padding: 50px;
        border-radius: 20px;
        background-color: #fff;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        text-align: center;
        margin: 20px 0;
        border: 2px solid #e0e0e0;
        cursor: pointer;
        transition: transform 0.1s;
    }
    .quiz-card:active {
        transform: scale(0.98);
        border-color: #1f77b4;
        background-color: #f0f8ff;
    }
    .quiz-word-text { color: #333; font-size: 50px; font-weight: bold; }
    .click-hint { font-size: 12px; color: #999; margin-top: 10px; }

    /* 뜻 박스 */
    .meaning-box {
        text-align: center; margin-bottom: 20px; padding: 15px;
        background-color: #e8f5e9; border-radius: 10px; border: 1px solid #c8e6c9;
    }
    .meaning-text { color: #2e7d32; font-size: 24px; font-weight: bold; margin: 0; }
    
    /* 버튼 크기 */
    .stButton button { height: 50px; font-size: 18px; }
    </style>
""", unsafe_allow_html=True)

# 1. 데이터 로드
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

# [핵심 함수] 텍스트를 오디오 HTML 코드로 변환 (막대기 없이)
def get_audio_html(text, unique_id):
    tts = gTTS(text=text, lang='en')
    mp3_fp = io.BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    # 오디오를 base64 문자열로 변환
    b64 = base64.b64encode(mp3_fp.read()).decode()
    # HTML 생성: 오디오 태그는 숨기고(display:none), 자바스크립트로 재생
    html = f"""
        <audio id="audio_{unique_id}" style="display:none;">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        <script>
            function play_{unique_id}() {{
                var audio = document.getElementById("audio_{unique_id}");
                audio.currentTime = 0;
                audio.play();
            }}
        </script>
    """
    return html

df = load_data()

# --- 사이드바 ---
st.sidebar.title("⚙️ 설정")
if df is not None:
    days = sorted(df['Day'].unique().tolist(), key=lambda x: int(x) if x.isdigit() else 999)
    selected_day = st.sidebar.selectbox("공부할 DAY를 선택하세요", days)
    day_words_all = df[df['Day'] == selected_day][['Word', 'Meaning']].to_dict('records')
    
    st.sidebar.markdown("---")
    st.sidebar.caption(f"총 단어 수: {len(day_words_all)}개")
    
    if st.sidebar.button("🔄 시험 초기화"):
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

# --- 메인 화면 ---
st.title(f"📖 Day {selected_day} 마스터하기")
tab1, tab2 = st.tabs(["👀 단어 공부 (List)", "📝 실전 시험 (Test)"])

# ==========================================
# 탭 1: 단어 공부 (클릭해서 소리 듣기)
# ==========================================
with tab1:
    st.header("단어 목록 훑어보기")
    st.info("💡 단어 박스를 **클릭**하면 발음이 나옵니다!")
    
    # 리스트 출력
    for i, item in enumerate(day_words_all):
        unique_id = f"list_{i}"
        audio_html = get_audio_html(item['Word'], unique_id)
        
        # HTML 카드 (onclick 이벤트 추가)
        st.markdown(f"""
        {audio_html}
        <div class="study-list-item" onclick="document.getElementById('audio_{unique_id}').play()">
            <span class="study-word">{item['Word']} 🔊</span>
            <span class="study-meaning">{item['Meaning']}</span>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# 탭 2: 실전 시험 (박스 클릭 재생)
# ==========================================
with tab2:
    if 'quiz_data' not in st.session_state:
        st.info("👈 왼쪽 사이드바에서 [시험 초기화] 버튼을 눌러 시작하세요!")
    
    elif st.session_state['study_finished']:
        st.balloons()
        st.success("🎉 시험 종료!")
        score = len(st.session_state['quiz_data']) - len(st.session_state['wrong_answers'])
        total_q = len(st.session_state['quiz_data'])
        st.metric("내 점수", f"{score} / {total_q}점")

        if st.session_state['wrong_answers']:
            st.write("### ❌ 틀린 문제")
            wrong_df = pd.DataFrame(st.session_state['wrong_answers'])
            st.table(wrong_df)
    else:
        index = st.session_state['current_index']
        total = len(st.session_state['quiz_data'])
        word_data = st.session_state['quiz_data'][index]

        # 진행바
        st.progress((index / total))
        st.caption(f"문제 {index + 1} / {total}")

        # --- [핵심] 오디오 생성 및 카드 렌더링 ---
        unique_id = f"quiz_{index}"
        audio_html = get_audio_html(word_data['Word'], unique_id)

        # 퀴즈 카드 (onclick 추가)
        st.markdown(f"""
        {audio_html}
        <div class="quiz-card" onclick="document.getElementById('audio_{unique_id}').play()">
            <div class="quiz-word-text">{word_data['Word']}</div>
            <div class="click-hint">👆 클릭해서 발음 듣기</div>
        </div>
        """, unsafe_allow_html=True)
        # --------------------------------------

        # 문제 넘어가면 자동으로 한 번 재생 (선택 사항 - 싫으면 이 줄 삭제)
        st.markdown(f"<script>document.getElementById('audio_{unique_id}').play();</script>", unsafe_allow_html=True)

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
                    st.toast(f"🥲 오답노트 저장!")
                    st.session_state['current_index'] += 1
                    st.session_state['show_meaning'] = False
                    if st.session_state['current_index'] >= total:
                        st.session_state['study_finished'] = True
                    st.rerun()
