import streamlit as st
import yt_dlp
import openai
import os

# 1. 웹 페이지 설정
st.set_page_config(page_title="쇼츠 원고 추출기", page_icon="🎬")
st.title("🎬 쇼츠 원고 추출기")

# 2. 이용 방법 및 저작권 안내
with st.expander("ℹ️ 이용 방법 및 주의사항 (클릭해서 확인)"):
    st.write("""
    1. 본인의 **OpenAI API Key**를 입력창에 넣어주세요. (비용은 본인 계정에서 차감됩니다.)
    2. 추출하고 싶은 **유튜브 쇼츠 링크**를 입력하세요.
    3. '원고 추출 시작' 버튼을 누르면 AI가 분석을 시작합니다.
    * **주의**: 추출된 데이터는 개인 학습 및 분석 용도로만 사용하시기 바랍니다.
    """)

# 3. 사용자 정보 입력 받기
st.subheader("🔑 서비스 설정을 입력하세요")
user_api_key = st.text_input("1. OpenAI API Key를 입력하세요", type="password", help="sk-...로 시작하는 키를 입력하세요.")
url = st.text_input("2. 유튜브 쇼츠 링크를 입력하세요", placeholder="https://youtube.com/shorts/...")

# 4. 추출 로직 실행
if st.button("🚀 원고 추출 시작"):
    if not user_api_key:
        st.warning("OpenAI API 키를 입력해야 서비스 이용이 가능합니다.")
    elif not url:
        st.warning("쇼츠 링크를 입력해 주세요.")
    else:
        with st.spinner("사용자님의 API 키를 사용하여 AI 분석 중입니다..."):
            try:
                # [A] OpenAI 클라이언트 설정
                client = openai.OpenAI(api_key=user_api_key)

                # [B] 유튜브 음성 추출 설정 (차단 우회 강화)
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
                    'outtmpl': 'temp_audio',
                    'quiet': True,
                    'no_check_certificate': True,
                    'extractor_args': {'youtube': {'player_client': ['ios', 'web']}},
                    'headers': {
                        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
                    }
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                # [C] Whisper API 호출 (사용자 키 사용)
                audio_file = open("temp_audio.mp3", "rb")
                transcript = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file
                )
                
                st.success("✅ 원고 추출 성공!")
                st.text_area("📄 추출된 대본", value=transcript.text, height=300)
                
                # 결과 파일 제공
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
                if "403" in str(e):
                    st.error("유튜브 서버에서 일시적으로 접속을 차단했습니다. 잠시 후 다시 시도해 주세요.")
                elif "Incorrect API key" in str(e):
                    st.error("입력하신 OpenAI API 키가 올바르지 않습니다. 다시 확인해 주세요.")
                else:
                    st.error(f"오류가 발생했습니다: {e}")

# 5. 하단 안내 (삭제 요청 반영)
st.markdown("---")
st.caption("본 도구는 사용자의 API 키를 서버에 저장하지 않으며, 일시적으로만 사용합니다.")
