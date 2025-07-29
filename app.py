import streamlit as st

# 내부 파일 import
import agents_and_tools as tools
from LangGraph import graph

# 페이지 설정
st.set_page_config(
    page_title='먹거리 할거리 추천 프로젝트',
    page_icon='🍽',
    layout='wide'
)

# 타이틀 영역
st.title("🍽 먹거리/할거리 추천 프로젝트")
st.markdown("날씨, 계절, 시간대, 사용자 입력에 따라 음식과 활동을 추천해 드립니다.")

# 사이드바 입력
with st.sidebar:
    st.header("입력 정보")
    location = st.text_input("📍 위치를 입력하세요.", value="천안시")
    user_input = st.text_input("💬 지금의 기분이나 하고 싶은 활동을 입력하세요.")
    submit = st.button("추천 시작하기")

# 메인 실행
if submit:
    state = {
        'user_input': user_input,
        'location': location
    }

    with st.spinner("추천 내용을 생성하는 중입니다..."):
        try:
            # LangGraph 실행
            events = list(graph.stream(state))
            final_state = events[-1].get('__end__') or events[-1].get('summarize_messages', {})

            final_message = final_state.get('final_message', '추천 내용을 생성하지 못했습니다.')
            st.session_state['last_result'] = final_state

            # ✅ 최종 추천 결과 출력
            st.markdown("## ✅ 최종 추천 결과")
            st.markdown(final_message)

            # ✅ 디버깅 정보는 선택적으로 보기
            with st.expander("🔍 디버깅 정보 보기", expanded=False):
                for i, e in enumerate(events):
                    st.markdown(f"**Step {i+1} : `{list(e.keys())[0]}`**")
                    st.json(e)

        except Exception as e:
            st.error(f"❌ 오류 발생: {str(e)}")
