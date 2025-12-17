import streamlit as st
import pandas as pd
import random
import os
from gtts import gTTS
import io

# --- 설정 ---
# 1. 페이지 기본 설정
st.set_page_config(page_title="토익 영단어장", page_icon="📚")

# 2. 데이터 로드 함수 (캐싱 사용으로 속도 향상)
@st.cache_data
def load_data():
    try:
        # csv 파일 경로 (현재 파일 위치 기준)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(script_dir, 'toeic_words.csv')
        
        # 인코딩 처리
        try:
            df = pd.read_csv(csv_path, encoding='utf-8-sig')
        except:
            df = pd.read_csv(csv_path, encoding='cp949')
        
        # Day를 문자열로 변환 (필터링 용이하게)
        df['Day'] = df['Day'].astype(str)
        return df
    except Exception as e:
        return None

df = load_data()

# --- 사이드바: 설정 ---
st.sidebar.title("⚙️ 설정")
if df is not None:
    # Day 목록 가져오기 (숫자 정렬)
    days = sorted(df['Day'].unique().tolist(), key=lambda x: int(x) if x.isdigit() else 999)
    selected_day = st.sidebar.selectbox("공부할 DAY를 선택하세요", days)
    
    # 학습 모드 초기화 버튼
    if st.sidebar.button("학습 시작 / 재시작"):
        # 선택한 Day의 단어들만 뽑아서 섞기
        day_words = df[df['Day'] == selected_day][['Word', 'Meaning']].to_dict('records')
        random.shuffle(day_words)
        
        # 세션 상태(Session State) 초기화
        st.session_state['quiz_data'] = day_words
        st.session_state['current_index'] = 0
        st.session_state['wrong_answers'] = []
        st.session_state['show_meaning'] = False
        st.session_state['study_finished'] = False
else:
    st.error("CSV 파일을 찾을 수 없습니다. 같은 폴더에 'toeic_words.csv'를 넣어주세요.")
    st.stop()

# --- 메인 화면 로직 ---
st.title(f"📖 Day {selected_day} 단어 학습")

# 1. 초기 상태일 때 (데이터가 아직 안 로드되었거나 시작 전)
if 'quiz_data' not in st.session_state:
    st.info("👈 왼쪽 사이드바에서 DAY를 선택하고 [학습 시작] 버튼을 눌러주세요!")

# 2. 학습 완료 상태
elif st.session_state['study_finished']:
    st.success("🎉 학습이 끝났습니다!")
    st.metric("틀린 개수", f"{len(st.session_state['wrong_answers'])}개")
    
    if st.session_state['wrong_answers']:
        st.write("### ❌ 오답 노트")
        wrong_df = pd.DataFrame(st.session_state['wrong_answers'])
        st.table(wrong_df)
        
        # CSV 다운로드 버튼
        csv = wrong_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="오답노트 다운로드 (CSV)",
            data=csv,
            file_name='my_wrong_note.csv',
            mime='text/csv',
        )
    else:
        st.balloons()
        st.write("완벽합니다! 틀린 단어가 없어요. 💯")

# 3. 퀴즈 진행 상태
else:
    # 현재 단어 가져오기
    index = st.session_state['current_index']
    total = len(st.session_state['quiz_data'])
    word_data = st.session_state['quiz_data'][index]
    
    # 진행률 표시
    st.progress(index / total)
    st.caption(f"진행 상황: {index + 1} / {total}")

    # 단어 카드 디자인
    st.markdown(f"""
    <div style="text-align: center; padding: 50px; background-color: #f0f2f6; border-radius: 10px; margin-bottom: 20px;">
        <h1 style="color: #333;">{word_data['Word']}</h1>
    </div>
    """, unsafe_allow_html=True)

    # 발음 듣기 (gTTS -> 메모리 -> 오디오 플레이어)
    # 매번 생성하면 느리므로 필요할 때만 생성하거나 그냥 둠 (웹에서는 자동재생이 브라우저 정책상 막힐 수 있어 플레이어 표시)
    tts = gTTS(text=word_data['Word'], lang='en')
    mp3_fp = io.BytesIO()
    tts.write_to_fp(mp3_fp)
    st.audio(mp3_fp, format='audio/mp3')

    # 뜻 확인하기 버튼
    if not st.session_state['show_meaning']:
        if st.button("뜻 확인하기 👀", use_container_width=True):
            st.session_state['show_meaning'] = True
            st.rerun() # 화면 새로고침

    # 뜻 확인 후 O/X 선택
    else:
        st.markdown(f"### 💡 뜻: **{word_data['Meaning']}**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ 맞음 (Next)", use_container_width=True):
                st.session_state['current_index'] += 1
                st.session_state['show_meaning'] = False
                # 마지막 문제인지 확인
                if st.session_state['current_index'] >= total:
                    st.session_state['study_finished'] = True
                st.rerun()

        with col2:
            if st.button("❌ 틀림 (Add to Note)", use_container_width=True):
                # 오답 목록에 추가
                st.session_state['wrong_answers'].append(word_data)
                st.session_state['current_index'] += 1
                st.session_state['show_meaning'] = False
                # 마지막 문제인지 확인
                if st.session_state['current_index'] >= total:
                    st.session_state['study_finished'] = True
                st.rerun()