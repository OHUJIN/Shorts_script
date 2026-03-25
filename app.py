import streamlit as st
import os
import subprocess
import yt_dlp
import openai

# [수정] 시스템 의존성 설치를 빼고 브라우저만 가볍게 설치합니다.
@st.cache_resource
def install_playwright_browser():
    try:
        # 이미 설치되어 있는지 확인 후 브라우저만 설치
        subprocess.run(["playwright", "install", "chromium"], check=True)
        return True
    except Exception as e:
        st.error(f"브라우저 엔진 설치 중 오류 발생: {e}")
        return False

# 앱 시작 시 실행
is_ready = install_playwright_browser()

st.set_page_config(page_title="쇼츠 원고 추출기 PRO", page_icon="🎬")
st.title("🎬 쇼츠 원고 추출기 (고급 우회 모드)")

with st.expander("ℹ️ 이용 방법 및 보안 안내"):
    st.write("1. OpenAI API Key를 입력하세요.")
    st.write("2. 유튜브 쇼츠 링크를 입력하세요.")
    st.write("첫 실행 시 엔진 로딩으로 10~20초 정도 소요될 수 있습니다.")

st.subheader("🔑 서비스 설정")
user_api_key = st.text_input("1. OpenAI API Key를 입력하세요", type="password")
url = st.text_input("2. 유튜브 쇼츠 링크를 입력하세요", placeholder="https://youtube.com/shorts/...")

if st.button("🚀 원고 추출 시작"):
    if not user_api_key or not url:
        st.warning("키와 링크를 모두 입력해 주세요.")
    elif not is_ready:
        st.error("서버 환경 설정 중입니다. 10초 뒤에 다시 시도해 주세요.")
    else:
        with st.spinner("유튜브 보안을 우회하여 음성을 분석 중입니다..."):
            try:
                # 우회 성능이 가장 좋은 설정 조합
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'outtmpl': 'temp_audio',
                    'quiet': True,
                    'no_check_certificate': True,
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['android', 'ios', 'web'],
                            'player_skip': ['webpage', 'configs'],
                        }
                    },
                    'headers': {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                    }
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                client = openai.OpenAI(api_key=user_api_key)
                audio_file = open("temp_audio.mp3", "rb")
                transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
                
                st.success("✅ 원고 추출 성공!")
                st.text_area("📄 추출된 대본", value=transcript.text, height=300)
                
                st.download_button(label="📥 메모장으로 다운로드", data=transcript.text, file_name="script.txt", mime="text/plain")

                audio_file.close()
                if os.path.exists("temp_audio.mp3"): os.remove("temp_audio.mp3")

            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")

st.markdown("---")
st.caption("Cloud Optimized Mode Active")
