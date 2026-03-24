import streamlit as st
import yt_dlp
import openai
import os

# 1. 웹 페이지 설정
st.set_page_config(page_title="쇼츠 원고 추출기", page_icon="🎬")
st.title("🎬 쇼츠 원고 추출기")

# 2. 면책 조항 안내
st.info("⚠️ **저작권 안내**: 본 도구는 개인적인 학습이나 분석 용도로만 사용해 주세요. 상업적 이용 시 저작권 문제가 발생할 수 있습니다.")

st.write("커피 한 잔 후원해주세요😊")

# 3. API 키 설정 (Streamlit Secrets 활용)
try:
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("OpenAI API 키가 설정되지 않았습니다. 관리자 설정을 확인하세요.")

# 4. URL 입력
url = st.text_input("유튜브 쇼츠 링크를 입력하세요", placeholder="https://youtube.com/shorts/...")

if st.button("원고 추출 시작"):
    if url:
        with st.spinner("AI가 영상을 분석 중입니다..."):
            try:
                # 403 Forbidden 에러 방지를 위한 설정 추가
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
                    'outtmpl': 'temp_audio',
                    'quiet': True,
                    # 유튜브 차단을 피하기 위해 실제 브라우저인 것처럼 속이는 정보 추가
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
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
                
                # 결과 다운로드
                st.download_button(
                    label="메모장으로 다운로드",
                    data=transcript.text,
                    file_name="script.txt",
                    mime="text/plain"
                )

                # 파일 삭제 및 닫기
                audio_file.close()
                os.remove("temp_audio.mp3")

            except Exception as e:
                # 상세 에러 메시지 출력
                st.error(f"오류가 발생했습니다: {e}")
    else:
        st.warning("링크를 입력해 주세요.")
