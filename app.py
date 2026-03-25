import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
import openai
import os
import re

st.set_page_config(page_title="쇼츠 원고 추출기 PRO", page_icon="🎬")
st.title("🎬 쇼츠 원고 추출기 (스마트 우회 모드)")

# 1. API 키 입력 (Whisper용)
user_api_key = st.text_input("OpenAI API Key (자막 없는 영상 분석용)", type="password")
url = st.text_input("유튜브 쇼츠 링크를 입력하세요")

def get_video_id(url):
    pattern = r'(?:v=|\/shorts\/|\/embed\/|\/be\/)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

if st.button("🚀 원고 추출 시작"):
    if not url:
        st.warning("링크를 입력해 주세요.")
    else:
        video_id = get_video_id(url)
        with st.spinner("1단계: 유튜브 자막 데이터를 즉시 추출 중..."):
            try:
                # [방법 1] 자막 API 시도 (가장 안전하고 빠름)
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko', 'en'])
                final_text = " ".join([t['text'] for t in transcript])
                
                st.success("✅ 자막 데이터 추출 성공! (API 모드)")
                st.text_area("📄 추출 대본", value=final_text, height=300)
                
            except Exception:
                st.info("자막 데이터가 없습니다. 2단계: AI 음성 분석을 시작합니다.")
                
                # [방법 2] 자막 없을 때만 Whisper 가동
                if not user_api_key:
                    st.error("이 영상은 자막이 없어 분석을 위해 OpenAI 키가 필요합니다.")
                else:
                    with st.spinner("유튜브 보안을 우회하여 음성을 분석 중..."):
                        try:
                            ydl_opts = {
                                'format': 'ba/b',
                                'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
                                'outtmpl': 'temp_audio',
                                'quiet': True,
                                'nocheckcertificate': True,
                                'headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}
                            }
                            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                                ydl.download([url])

                            client = openai.OpenAI(api_key=user_api_key)
                            audio_file = open("temp_audio.mp3", "rb")
                            transcript_ai = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
                            
                            st.success("✅ AI 분석 성공! (Whisper 모드)")
                            st.text_area("📄 추출 대본", value=transcript_ai.text, height=300)
                            audio_file.close()
                            os.remove("temp_audio.mp3")
                        except Exception as e:
                            st.error(f"유튜브의 보안 벽이 너무 높습니다. 다른 영상을 시도해 주세요: {e}")

st.markdown("---")
st.caption("Smart Bypass Logic Active (Transcript API + Whisper)")
