import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
import openai
import os
import re

st.set_page_config(page_title="쇼츠 원고 추출기 PRO", page_icon="🎬")
st.title("🎬 쇼츠 원고 추출기 (스마트 우회 모드)")

# 1. API 키 및 URL 입력
user_api_key = st.text_input("OpenAI API Key (음성 분석용)", type="password")
url = st.text_input("유튜브 쇼츠 링크를 입력하세요", placeholder="https://www.youtube.com/shorts/...")

def get_video_id(url):
    pattern = r'(?:v=|\/shorts\/|\/embed\/|\/be\/)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

if st.button("🚀 원고 추출 시작"):
    if not url:
        st.warning("링크를 입력해 주세요.")
    else:
        video_id = get_video_id(url)
        with st.spinner("1단계: 자막 데이터를 검색 중입니다..."):
            try:
                # [수정] 모든 언어 자막을 다 뒤져서 가져오는 로직으로 강화
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                # 한국어 최우선, 없으면 영어, 그래도 없으면 자동생성 자막 가져오기
                transcript = transcript_list.find_transcript(['ko', 'en'])
                data = transcript.fetch()
                final_text = " ".join([t['text'] for t in data])
                
                st.success("✅ 자막 데이터 추출 성공!")
                st.text_area("📄 추출 대본", value=final_text, height=300)
                
            except Exception:
                st.info("자막 데이터가 없습니다. 2단계: AI 음성 분석을 시작합니다.")
                
                if not user_api_key:
                    st.error("이 영상은 자막이 없어 분석을 위해 OpenAI 키가 필요합니다.")
                else:
                    with st.spinner("유튜브 보안을 피해 음성을 다운로드 중입니다..."):
                        try:
                            # [핵심] 현재 403 에러를 뚫는 가장 확실한 'web_creator' 설정 적용
                            ydl_opts = {
                                'format': 'ba/b',
                                'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
                                'outtmpl': 'temp_audio',
                                'quiet': True,
                                'no_check_certificate': True,
                                'extractor_args': {
                                    'youtube': {
                                        # 최신 우회 클라이언트 조합
                                        'player_client': ['web_creator', 'ios', 'android'],
                                    }
                                },
                                'headers': {
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                                    'Accept': '*/*',
                                    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8',
                                }
                            }
                            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                                ydl.download([url])

                            # Whisper AI 분석
                            client = openai.OpenAI(api_key=user_api_key)
                            audio_file = open("temp_audio.mp3", "rb")
                            transcript_ai = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
                            
                            st.success("✅ AI 분석 성공!")
                            st.text_area("📄 추출 대본", value=transcript_ai.text, height=300)
                            
                            audio_file.close()
                            if os.path.exists("temp_audio.mp3"): os.remove("temp_audio.mp3")
                            
                        except Exception as e:
                            st.error(f"유튜브 서버가 이 주소를 완전히 차단했습니다: {e}")
                            st.info("💡 해결 방법: 우측 하단 [Manage app] -> [Reboot]를 눌러 '새 IP'를 할당받으세요.")

st.markdown("---")
st.caption("Advanced Smart Bypass Engine (V3.0)")
