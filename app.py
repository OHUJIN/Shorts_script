import streamlit as st
import yt_dlp
import openai
import os

# 1. 웹 페이지 설정
st.set_page_config(page_title="쇼츠 원고 추출기", page_icon="🎬")
st.title("🎬 쇼츠 원고 추출기")

# 2. 저작권 안내 (면책 조항)
st.info("⚠️ **저작권 안내**: 본 도구는 개인적인 학습이나 분석 용도로만 사용해 주세요. 상업적 이용 시 저작권 문제가 발생할 수 있습니다.")

st.write("커피 한 잔 후원해주세요😊")

# 3. OpenAI API 키 설정
try:
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("API 키가 설정되지 않았습니다. Streamlit 설정에서 OPENAI_API_KEY를 확인하세요.")

# 4. URL 입력창
url = st.text_input("유튜브 쇼츠 링크를 입력하세요", placeholder="https://youtube.com/shorts/...")

if st.button("원고 추출 시작"):
    if url:
        with st.spinner("AI가 영상을 분석 중입니다..."):
            try:
                # [핵심] 유튜브 차단을 피하기 위한 고급 설정 추가
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
                    'outtmpl': 'temp_audio',
                    'quiet': True,
                    'no_check_certificate': True,
                    'nocheckcertificate': True,
                    'headers': {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'en-us,en;q=0.5',
                        'Sec-Fetch-Mode': 'navigate',
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
                # 403 에러가 계속될 경우 안내 메시지 출력
                if "403" in str(e):
                    st.error("유튜브 서버에서 일시적으로 접속을 차단했습니다. 잠시 후 다시 시도하거나 다른 영상을 입력해 주세요.")
                else:
                    st.error(f"오류가 발생했습니다: {e}")
    else:
        st.warning("링크를 입력해 주세요.")

# 요청하신 대로 하단 '내일을 바꾸는 한스푼' 문구는 삭제되었습니다.
