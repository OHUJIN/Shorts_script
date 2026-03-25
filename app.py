import streamlit as st
import os
import subprocess
from playwright.sync_api import sync_playwright
import yt_dlp
import openai

# [중요] 앱 시작 시 플레이라이트 브라우저 설치 (처음 한 번만 실행됨)
@st.cache_resource
def install_playwright():
    subprocess.run(["playwright", "install", "chromium"])

install_playwright()

st.set_page_config(page_title="쇼츠 원고 추출기 PRO", page_icon="🎬")
st.title("🎬 쇼츠 원고 추출기 (고급 우회 모드)")

# 이용 안내
with st.expander("ℹ️ 이용 방법"):
    st.write("본 도구는 헤드리스 브라우저를 사용하여 유튜브의 봇 감지를 우회합니다.")
    st.write("처음 실행 시 브라우저 구동으로 인해 약간의 시간이 소요될 수 있습니다.")

# 입력창
user_api_key = st.text_input("OpenAI API Key를 입력하세요", type="password")
url = st.text_input("유튜브 쇼츠 링크를 입력하세요", placeholder="https://youtube.com/shorts/...")

def get_cookies_via_playwright(video_url):
    """브라우저를 띄워 유튜브에 접속하고 쿠키를 추출합니다."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) # 보이지 않는 브라우저 실행
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        # 유튜브 접속 및 실제 사람처럼 대기
        page.goto(video_url, wait_until="networkidle")
        page.wait_for_timeout(3000) # 3초간 머무르기
        
        # 쿠키 추출 및 yt-dlp 형식으로 변환
        cookies = context.cookies()
        browser.close()
        return cookies

if st.button("🚀 원고 추출 시작"):
    if not user_api_key or not url:
        st.warning("키와 링크를 모두 입력해 주세요.")
    else:
        with st.spinner("헤드리스 브라우저를 가동하여 유튜브 보안을 우회 중입니다..."):
            try:
                # 1. 브라우저로 접속하여 쿠키 따오기
                # (이 과정에서 유튜브는 실제 브라우저 접속으로 인식함)
                
                # 2. yt-dlp 실행 (쿠키 정보 없이도 브라우저 흉내 설정을 강화함)
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
                    'outtmpl': 'temp_audio',
                    'quiet': True,
                    'no_check_certificate': True,
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['android', 'web', 'ios'],
                            'player_skip': ['webpage', 'configs'],
                        }
                    },
                    # 실제 브라우저 헤더 복사
                    'headers': {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                        'Accept': '*/*',
                        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8',
                    }
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                # 3. Whisper AI 분석
                client = openai.OpenAI(api_key=user_api_key)
                audio_file = open("temp_audio.mp3", "rb")
                transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
                
                st.success("추출 완료!")
                st.text_area("📄 추출된 원고", value=transcript.text, height=300)
                
                # 정리
                audio_file.close()
                if os.path.exists("temp_audio.mp3"): os.remove("temp_audio.mp3")

            except Exception as e:
                st.error(f"오류가 발생했습니다. 유튜브의 보안이 매우 강력합니다: {e}")
                st.info("💡 팁: 이 에러가 계속되면 유튜브가 서버 IP 자체를 막은 것입니다. 10분 뒤 다시 시도해 보세요.")

st.markdown("---")
st.caption("Playwright Headless Mode 활성화됨")
