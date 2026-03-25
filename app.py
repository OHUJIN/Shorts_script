import streamlit as st
import os
import subprocess
import yt_dlp
import openai

# [중요] 플레이라이트 및 브라우저 의존성 자동 설치 함수
@st.cache_resource
def install_playwright_environment():
    try:
        # 브라우저 엔진 설치
        subprocess.run(["playwright", "install", "chromium"], check=True)
        # 리눅스 시스템에 부족한 라이브러리 자동 채우기
        subprocess.run(["playwright", "install-deps", "chromium"], check=True)
        return True
    except Exception as e:
        st.error(f"브라우저 환경 설정 중 오류 발생: {e}")
        return False

# 앱 시작 시 환경 설정 실행
is_ready = install_playwright_environment()

# 1. 웹 페이지 설정
st.set_page_config(page_title="쇼츠 원고 추출기 PRO", page_icon="🎬")
st.title("🎬 쇼츠 원고 추출기 (고급 우회 모드)")

# 2. 이용 안내
with st.expander("ℹ️ 이용 방법 및 보안 안내 (클릭)"):
    st.write("""
    1. 본인의 **OpenAI API Key**를 입력하세요. (비용은 본인 계정에서 차감됩니다.)
    2. **유튜브 쇼츠 링크**를 입력하세요.
    3. 첫 실행 시 브라우저 구동으로 인해 **약 1~2분 정도** 시간이 소요될 수 있습니다.
    * 본 도구는 입력하신 API 키를 서버에 절대 저장하지 않습니다.
    """)

# 3. 사용자 입력 섹션
st.subheader("🔑 서비스 설정")
user_api_key = st.text_input("1. OpenAI API Key를 입력하세요", type="password", help="sk-... 형태의 키를 입력하세요.")
url = st.text_input("2. 유튜브 쇼츠 링크를 입력하세요", placeholder="https://youtube.com/shorts/...")

# 4. 핵심 로직 실행
if st.button("🚀 원고 추출 시작"):
    if not user_api_key or not url:
        st.warning("API 키와 쇼츠 링크를 모두 입력해 주세요.")
    elif not is_ready:
        st.error("서버 환경이 아직 준비되지 않았습니다. 잠시 후 다시 시도해 주세요.")
    else:
        with st.spinner("가상 브라우저를 가동하여 유튜브 보안을 우회 중입니다..."):
            try:
                # [A] 유튜브 음성 추출 설정 (가장 강력한 우회 설정 조합)
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
                    # 안드로이드/iOS 클라이언트로 위장하여 403 에러 방지
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['android', 'ios', 'web'],
                            'player_skip': ['webpage', 'configs'],
                        }
                    },
                    'headers': {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                        'Accept': '*/*',
                        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8',
                    }
                }

                # 음성 파일 다운로드
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                # [B] Whisper AI 분석 (사용자 키 사용)
                client = openai.OpenAI(api_key=user_api_key)
                audio_file = open("temp_audio.mp3", "rb")
                
                with st.spinner("AI가 음성을 텍스트로 변환하고 있습니다..."):
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1", 
                        file=audio_file
                    )
                
                # [C] 결과 출력
                st.success("✅ 원고 추출 성공!")
                st.text_area("📄 추출된 대본", value=transcript.text, height=300)
                
                # 결과 다운로드 버튼
                st.download_button(
                    label="📥 메모장으로 다운로드",
                    data=transcript.text,
                    file_name="shorts_script.txt",
                    mime="text/plain"
                )

                # 임시 파일 정리
                audio_file.close()
                if os.path.exists("temp_audio.mp3"):
                    os.remove("temp_audio.mp3")

            except Exception as e:
                error_msg = str(e)
                if "403" in error_msg or "Sign in" in error_msg:
                    st.error("유튜브가 현재 서버의 접속을 강력하게 차단 중입니다. 10분 뒤 다시 시도하거나 다른 영상으로 테스트해 주세요.")
                elif "Incorrect API key" in error_msg:
                    st.error("입력하신 OpenAI API 키가 올바르지 않습니다.")
                else:
                    st.error(f"오류가 발생했습니다: {error_msg}")

# 5. 하단 안내
st.markdown("---")
st.caption("Advanced Bypass Mode Active (Playwright + YT-DLP)")
