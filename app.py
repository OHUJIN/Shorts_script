import streamlit as st
import os
import subprocess
import yt_dlp
import openai
from playwright.sync_api import sync_playwright

# 1. 브라우저 엔진 설치 (캐시 처리)
@st.cache_resource
def install_browser():
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
        return True
    except:
        return False

is_ready = install_browser()

st.set_page_config(page_title="쇼츠 원고 추출기 PRO", page_icon="🎬")
st.title("🎬 쇼츠 원고 추출기 (고급 우회 모드)")

# UI 설정
user_api_key = st.text_input("1. OpenAI API Key를 입력하세요", type="password")
url = st.text_input("2. 유튜브 쇼츠 링크를 입력하세요")

# [핵심] 가상 브라우저로 쿠키를 따오는 함수
def fetch_cookies_with_playwright(video_url):
    with sync_playwright() as p:
        # 브라우저 실행
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        page = context.new_page()
        
        # 유튜브 접속
        page.goto(video_url)
        page.wait_for_timeout(3000) # 사람처럼 3초 대기
        
        # 쿠키 추출 및 Netscape 형식 변환
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
        with st.spinner("가상 브라우저가 유튜브 신분증을 챙겨오는 중입니다..."):
            try:
                # 1단계: 쿠키 따오기
                cookie_file = fetch_cookies_with_playwright(url)
                
                # 2단계: 따온 쿠키를 들고 음성 추출
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
                    'outtmpl': 'temp_audio',
                    'cookiefile': cookie_file, # 추출한 신분증 사용
                    'quiet': True,
                    'extractor_args': {'youtube': {'player_client': ['ios', 'web']}}
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                # 3단계: Whisper 분석
                client = openai.OpenAI(api_key=user_api_key)
                audio_file = open("temp_audio.mp3", "rb")
                transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
                
                st.success("✅ 추출 완료!")
                st.text_area("📄 추출 대본", value=transcript.text, height=300)

                # 정리
                audio_file.close()
                if os.path.exists("temp_audio.mp3"): os.remove("temp_audio.mp3")
                if os.path.exists(cookie_file): os.remove(cookie_file)

            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
                st.info("💡 팁: 스트림릿의 주소가 완전히 차단되었을 수 있습니다. 5분 뒤 다시 시도해 보세요.")
