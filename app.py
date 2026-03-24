import streamlit as st
import yt_dlp
import openai
import os

# 1. 웹 페이지 설정
st.set_page_config(page_title="쇼츠 원고 추출기", page_icon="🎬")
st.title("🎬 쇼츠 원고 추출기")

# 2. 면책 조항 안내 (사용자 요청 반영)
st.info("⚠️ **저작권 안내**: 다른 사람의 영상을 텍스트로 변환하여 서비스할 때는 개인적인 학습이나 분석 용도로 안내하는 면책 조항을 넣는 것이 좋습니다. 본 도구는 교육 및 연구 목적으로만 사용해 주세요.")

st.write("커피 한 잔 후원해주세요🥹")

# 3. API 키 설정 (Streamlit Secrets 활용)
try:
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("OpenAI API 키가 설정되지 않았습니다. 관리자 설정을 확인하세요.")

# 4. URL 입력
url = st.text_input("유튜브 쇼츠 링크를 입력하세요", placeholder="https://youtube.com/shorts/...")

if st.button("원고 추출 시작"):
    if url:
        with st.spinner("OpenAI의 Whisper API를 연동하면, 아주 저렴한 비용으로 수백 명에게 안정적인 서비스를 제공할 수 있습니다. 현재 분석 중입니다..."):
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

                # Whisper API 호출 (서버 부하 감소 및 속도 향상)
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
                st.error(f"오류가 발생했습니다: {e}")
    else:
        st.warning("링크를 입력해 주세요.")

# 하단 푸터 (브랜드 강조)
st.markdown("---")
st.caption("© youtube shorts scripts downloader")
