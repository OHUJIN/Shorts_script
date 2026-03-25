import streamlit as st
import os
import subprocess
import yt_dlp
import openai
from playwright.sync_api import sync_playwright

@st.cache_resource
def install_browser():
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
        return True
    except: return False

is_ready = install_browser()

st.set_page_config(page_title="쇼츠 원고 추출기 PRO", page_icon="🎬")
st.title("🎬 쇼츠 원고 추출기 (고급 우회 모드)")

user_api_key = st.text_input("1. OpenAI API Key를 입력하세요", type="password")
url = st.text_input("2. 유튜브 쇼츠 링크를 입력하세요")

def fetch_cookies_with_playwright(video_url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        page = context.new_page()
        page.goto(video_url)
        page.wait_for_timeout(4000) # 대기 시간을 조금 더 늘림
        cookies = context.cookies()
        
        cookie_path = "temp_cookies.txt"
        with open(cookie_path, "w") as f:
            f.write("# Netscape HTTP Cookie File\n")
            for c in cookies:
                domain = c['domain']
                path = c['path']
                secure = "TRUE" if c['secure'] else "FALSE"
                expires = str(int(c.get('expires', 0)))
                name = c['name']
                value = c['value']
                f.write(f"{domain}\tTRUE\t{path}\t{secure}\t{expires}\t{name}\t{value}\n")
        browser.close()
        return cookie_path

if st.button("🚀 원고 추출 시작"):
    if not user_api_key or not url:
        st.warning("정보를 모두 입력해 주세요.")
    else:
        with st.spinner("가상 브라우저가 보안을 우회하여 데이터를 가져오는 중입니다..."):
            try:
                cookie_file = fetch_cookies_with_playwright(url)
                
                # [수정] 포맷 선택을 더 유연하게(ba/b) 변경하고 불필요한 클라이언트 제한 삭제
                ydl_opts = {
                    'format': 'ba/b', # 가장 좋은 오디오, 안되면 일반 파일이라도!
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'outtmpl': 'temp_audio', # 확장자는 yt-dlp가 알아서 처리
                    'cookiefile': cookie_file,
                    'quiet': True,
                    'no_warnings': True,
                    'nocheckcertificate': True,
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                # 파일 이름 확인 (yt-dlp가 mp3로 변환한 결과물 찾기)
                audio_path = "temp_audio.mp3"
                if not os.path.exists(audio_path):
                    # 간혹 변환 과정에서 다른 이름이 될 경우 대비
                    audio_path = "temp_audio"

                client = openai.OpenAI(api_key=user_api_key)
                with open(audio_path, "rb") as audio_file:
                    transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
                
                st.success("✅ 추출 완료!")
                st.text_area("📄 추출 대본", value=transcript.text, height=300)

                if os.path.exists("temp_audio.mp3"): os.remove("temp_audio.mp3")
                if os.path.exists(cookie_file): os.remove(cookie_file)

            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
                st.info("💡 팁: 유튜브가 이 서버 주소를 강력하게 막고 있을 수 있습니다. 다른 영상을 시도해보거나 잠시 후 다시 해보세요.")
