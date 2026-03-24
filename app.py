import streamlit as st
import yt_dlp
import openai
import os
import random

# 1. 웹 페이지 설정
st.set_page_config(page_title="쇼츠 원고 추출기", page_icon="🎬")
st.title("🎬 쇼츠 원고 추출기")

# 2. 저작권 안내 (면책 조항)
st.info("⚠️ **저작권 안내**: 본 도구는 개인적인 학습이나 분석 용도로만 사용해 주세요.")

st.write("커피 한 잔 후원해주세요😊")

# 3. OpenAI API 키 설정
try:
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("API 키 설정 오류: Streamlit Secrets를 확인하세요.")

# 4. URL 입력창
url = st.text_input("유튜브 쇼츠 링크를 입력하세요", placeholder="https://youtube.com/shorts/...")

if st.button("원고 추출 시작"):
    if url:
        with st.spinner("AI가 차단을 피해 음성을 분석 중입니다... 잠시만 기다려주세요."):
            try:
                # [필살기] 유튜브 차단을 피하기 위한 iOS/TV 클라이언트 우회 설정
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
                    'outtmpl': 'temp_audio',
                    'quiet': True,
                    'no_check_certificate': True,
                    # 유튜브 차단을 뚫는 최신 클라이언트 조합
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['ios', 'web', 'tv'],
                            'player_skip': ['webpage', 'configs'],
                        }
                    },
                    'headers': {
                        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                    }
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                # Whisper API로 받아쓰기 수행
                audio_file = open("temp_audio.mp3", "rb")
                transcript = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file
                )
                
                st.success("추출 완료!")
                st.text_area("📄 추출된 원고", value=transcript.text, height=300)
                
                st.download_button(
                    label="메모장으로 다운로드",
                    data=transcript.text,
                    file_name="script.txt",
                    mime="text/plain"
                )

                audio_file.close()
                os.remove("temp_audio.mp3")

            except Exception as e:
                if "403" in str(e):
                    st.error("유튜브 서버가 현재 웹 주소를 강력하게 차단하고 있습니다. 잠시 후 다시 시도하거나, 다른 영상 링크를 넣어보세요.")
                else:
                    st.error(f"오류가 발생했습니다: {e}")
    else:
        st.warning("링크를 입력해 주세요.")

# 하단 '내일을 바꾸는 한스푼' 문구는 완전히 삭제되었습니다.
