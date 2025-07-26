import streamlit as st

#import 파일이름 as 별명
#import 폴더.파일이름 as 별명 -> app.py와 같은 경로 X, 한 단계 아래 폴더 안에 있는 경우
import agents_and_tools as tools
from LangGraph import graph

#인터넷 페이지의 이름
st.set_page_config(page_title = '먹거리 할거리 추천 프로젝트',
               page_icon='🍽', #파비콘(favicon), 웹페이지의 앞에 붙는 아이콘
               layout='wide')

st.title("먹거리/할거리 추천 프로젝트")
st.markdown('날씨, 계절, 시간대, 사용자 입력에 따라 음식과 활동을 추천해 드립니다.')

#사이드 바 만들기
with st.sidebar:

   st.header('입력 정보')

   location = st.text_input("위치를 입력하세요.", value="천안시")
   user_input = st.text_input("지금의 기분이나 하고 싶은 활동을 입력하세요.")

   #제출
   submit = st.button('추천 시작하기')
   print('눌림')

if submit:
   #tools.print_something()

   state = {
      'user_input' : user_input,
      'location' : location
   }

   with st.spinner('추천 내용을 생성하는 중입니다....'):
      try :
         #여기부터 랭그래프가 생성, 실행됨
         events = list(graph.stream(state))

         #디버깅 출력
         st.write('>> LangGraph 실행 완료! <<')

         #최종 상태 추출
         final_state = events[-1].get('__end__') or events[-1].get('summarize_message', {})
         final_message = final_state.get('final_message', '추천 내용이 존재하지 않습니다.')

         st.session_state['last_result'] = final_state


         #결과를 스트림릿에 output
         st.subheader('최종 추천 결과')
         st.markdown(final_message)

         #디버깅(각 단계별 상태 출력)
         st.divider()
         st.subheader('디버깅 정보')

         for i, e in enumerate(events):
            st.markdown(f'Step {i+1} : {list(e.keys())[0]}')
            st.json(e)

      except Exception as e:
         st.error(f'오류 발생 : {str(e)}')