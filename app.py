import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import yt_dlp
import openai
import os
import re

st.set_page_config(page_title="쇼츠 원고 추출기", page_icon="🎬")
st.title("🎬 쇼츠 원고 추출기")

with st.expander("ℹ️ 이용 방법 및 주의사항"):
    st.write("1. OpenAI API Key를 입력하세요 (자막이 없는 영상 분석 시 사용됩니다).")
    st.write("2. 쇼츠 링크를 넣고 추출 버튼을 누르세요.")

st.subheader("🔑 서비스 설정")
user_api_key = st.text_input("OpenAI API Key (선택 사항)", type="password")
url = st.text_input("유튜브 쇼츠 링크", placeholder="https://youtube.com/shorts/...")

def get_video_id(url):
    pattern = r'(?:v=|\/shorts\/|\/embed\/|\/be\/)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

if st.button("🚀 원고 추출 시작"):
    if not url:
        st.warning("링크를 입력해 주세요.")
    else:
        video_id = get_video_id(url)
        with st.spinner("1단계: 유튜브 자막 데이터를 확인 중입니다..."):
            try:
                # [방법 1] 자막 API 시도 (가장 빠르고 안전함)
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                transcript = transcript_list.find_transcript(['ko', 'en'])
                data = transcript.fetch()
                formatter = TextFormatter()
                final_text = formatter.format_transcript(data)
                
                st.success("✅ 자막 데이터 추출 성공!")
                st.text_area("📄 추출된 대본", value=final_text, height=300)

            except Exception as e:
                st.info("자막 데이터가 없습니다. 2단계: 음성 분석(Whisper)을 시도합니다.")
                
                if not user_api_key:
                    st.error("음성 분석을 위해서는 OpenAI API Key가 필요합니다.")
                else:
                    try:
                        # [방법 2] 음성 추출 및 Whisper AI 실행
                        client = openai.OpenAI(api_key=user_api_key)
                        ydl_opts = {
                            'format': 'bestaudio/best',
                            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
                            'outtmpl': 'temp_audio',
                            'quiet': True,
                            'extractor_args': {'youtube': {'player_client': ['ios', 'web']}}
                        }
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            ydl.download([url])

                        audio_file = open("temp_audio.mp3", "rb")
                        transcript_ai = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
                        
                        st.success("✅ AI 음성 분석 성공!")
                        st.text_area("📄 추출된 대본", value=transcript_ai.text, height=300)
                        audio_file.close()
                        os.remove("temp_audio.mp3")
                    except Exception as e2:
                        st.error(f"모든 시도가 실패했습니다. 유튜브의 차단 정책 때문일 수 있습니다: {e2}")

st.markdown("---")
st.caption("본 서비스는 교육용이며, 대규모 트래픽 발생 시 유튜브 정책에 의해 제한될 수 있습니다.")
