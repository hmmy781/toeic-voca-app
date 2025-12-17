import streamlit as st
import pandas as pd
import random
import os
from gtts import gTTS
import io

# --- 설정 ---
st.set_page_config(page_title="토익 영단어장", page_icon="📚")

# CSS 스타일 적용 (카드 디자인, 버튼 꾸미기)
st.markdown("""
    <style>
    .word-card {
        padding: 30px;
        border-radius: 15px;
        background-color: #f9f9f9;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        text-align: center;
        margin: 20px 0;
        border: 2px solid #e0e0e0;
    }
    .word-text {
        color: #333; 
        font-size: 48px; 
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

# --- 사이드바 ---
st.sidebar.title("⚙️ 설정")
if df is not None:
    days = sorted(df['Day'].unique().tolist(), key=lambda x: int(x) if x.isdigit() else 999)
    selected_day = st.sidebar.selectbox("공부할 DAY를 선택하세요", days)
    
    if st.sidebar.button("🚀 학습 시작 / 재시작"):
        day_words = df[df['Day'] == selected_day][['Word', 'Meaning']].to_dict('records')
        random.shuffle(day_words)
        
        st.session_state['quiz_data'] = day_words
        st.session_state['current_index'] = 0
        st.session_state['wrong_answers'] = []
        st.session_state['show_meaning'] = False
        st.session_state['study_finished'] = False
        st.rerun()
else:
    st.error("CSV 파일을 찾을 수 없습니다.")
    st.stop()

# --- 메인 화면 ---
st.title(f"📖 Day {selected_day} 집중 학습")

if 'quiz_data' not in st.session_state:
    st.info("👈 왼쪽 사이드바에서 [학습 시작] 버튼을 눌러주세요!")

elif st.session_state['study_finished']:
    st.balloons()
    st.success("🎉 학습 완료! 수고하셨습니다.")
    st.metric("틀린 단어", f"{len(st.session_state['wrong_answers'])}개")
    
    if st.session_state['wrong_answers']:
        st.write("### ❌ 오답 노트")
        wrong_df = pd.DataFrame(st.session_state['wrong_answers'])
        st.table(wrong_df)
        
        csv = wrong_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("오답노트 다운로드 (CSV)", csv, 'my_wrong_note.csv', 'text/csv')
    else:
        st.write("완벽합니다! 💯")
    
    if st.button("다시 하기"):
        st.session_state['study_finished'] = False
        st.session_state['current_index'] = 0
        st.session_state['wrong_answers'] = []
        random.shuffle(st.session_state['quiz_data'])
        st.rerun()

else:
    # --- [중요] 변수 정의 (에러가 났던 부분 해결!) ---
    index = st.session_state['current_index']
    total = len(st.session_state['quiz_data'])
    word_data = st.session_state['quiz_data'][index]

    # 진행바 표시
    progress = (index / total)
    st.progress(progress)
    st.caption(f"진행 상황: {index + 1} / {total}")

    # 단어 카드 (CSS 적용됨)
    st.markdown(f"""
    <div class="word-card">
        <div class="word-text">{word_data['Word']}</div>
    </div>
    """, unsafe_allow_html=True)

    # 발음 듣기
    tts = gTTS(text=word_data['Word'], lang='en')
    mp3_fp = io.BytesIO()
    tts.write_to_fp(mp3_fp)
    st.audio(mp3_fp, format='audio/mp3')

    # 버튼 영역
    if not st.session_state['show_meaning']:
        if st.button("🔍 뜻 확인하기", use_container_width=True, type="primary"):
            st.session_state['show_meaning'] = True
            st.rerun()
    else:
        # 뜻 보여주기
        st.markdown(f"""
        <div class="meaning-box">
            <p class="meaning-text">{word_data['Meaning']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ 알아요 (O)", use_container_width=True):
                st.session_state['current_index'] += 1
                st.session_state['show_meaning'] = False
                if random.random() > 0.8: # 가끔 칭찬 효과
                    st.toast("잘하고 있어요! 👍")
                if st.session_state['current_index'] >= total:
                    st.session_state['study_finished'] = True
                st.rerun()

        with col2:
            if st.button("❌ 몰라요 (X)", use_container_width=True):
                st.session_state['wrong_answers'].append(word_data)
                st.toast(f"🥲 오답노트 추가! (현재 {len(st.session_state['wrong_answers'])}개)")
                st.session_state['current_index'] += 1
                st.session_state['show_meaning'] = False
                if st.session_state['current_index'] >= total:
                    st.session_state['study_finished'] = True
                st.rerun()
