import streamlit as st
import yt_dlp
import openai
import os

# 1. 웹 페이지 설정
st.set_page_config(page_title="쇼츠 원고 추출기", page_icon="🎬")
st.title("🎬 쇼츠 원고 추출기")

# 2. 저작권 안내
st.info("⚠️ **저작권 안내**: 본 도구는 개인적인 학습이나 분석 용도로만 사용해 주세요. 상업적 이용 시 저작권 문제가 발생할 수 있습니다.")

st.write("커피 한 잔 후원해주세요😊")

# 3. API 키 설정
try:
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("API 키 설정 오류: Streamlit Secrets를 확인하세요.")

# 4. URL 입력
url = st.text_input("유튜브 쇼츠 링크를 입력하세요", placeholder="https://youtube.com/shorts/...")

if st.button("원고 추출 시작"):
    if url:
        with st.spinner("유튜브 차단을 우회하여 분석 중입니다... 잠시만 기다려주세요."):
            try:
                # [필살기] 유튜브 차단을 피하기 위한 최신 설정
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
                    'outtmpl': 'temp_audio',
                    'quiet': True,
                    # 안드로이드 기기인 것처럼 속여 차단을 피함
                    'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
                    'nocheckcertificate': True,
                    'headers': {
                        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36',
                    }
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                # Whisper API 호출
                audio_file = open("temp_audio.mp3", "rb")
                transcript = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file
                )
                
                st.success("추출 완료!")
                st.text_area("📄 추출된 원고", value=transcript.text, height=300)
                
                # 파일 다운로드 버튼
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
                    st.error("유튜브가 현재 서버의 접속을 강력하게 차단 중입니다. 5~10분 후 다시 시도하거나, 다른 영상 링크를 넣어보세요.")
                else:
                    st.error(f"오류 발생: {e}")
    else:
        st.warning("링크를 입력해 주세요.")
