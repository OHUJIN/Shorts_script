import streamlit as st
import yt_dlp
import whisper
import os

# 웹 페이지 설정
st.set_page_config(page_title="쇼츠 원고 추출기", page_icon="🎬")
st.title("🎬 쇼츠 원고 추출기")
st.write("다른 제작자들도 쓸 수 있는 쇼츠 대본 추출 도구입니다.")

# 링크 입력 받기
url = st.text_input("유튜브 쇼츠 링크를 입력하세요", placeholder="https://youtube.com/shorts/...")

if st.button("원고 추출"):
    if url:
        with st.spinner("AI가 분석 중입니다..."):
            try:
                # 음성 추출
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
                    'outtmpl': 'temp_audio',
                    'quiet': True
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                # Whisper AI 실행
                model = whisper.load_model("base")
                result = model.transcribe("temp_audio.mp3")
                
                st.success("추출 성공!")
                st.text_area("추출된 원고", value=result['text'], height=300)
                
                # 파일 삭제
                os.remove("temp_audio.mp3")
            except Exception as e:
                st.error(f"오류: {e}")