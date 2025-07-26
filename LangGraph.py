#랭그래프(그래프 : 노드, 엣지, 상태 -> 컴파일)
#StateGraph : 상태를 컨트롤
#END : 제일 마지막 노드
from langgraph.graph import StateGraph, END 
from typing_extensions import TypedDict
from agents_and_tools import *

#상태를 정의할 클래스
class State(TypedDict):
	user_input : str  #사용자의 현재 상황과 질문
	location : str    #사용자의 지역 정의
	time_slot : str   #질문 시간대 (아침, 점심, 저녁...)
	season : str      #현재 계절
	weather : str     #현재 날씨
	intent : str      #사용자에게 추천할 카테고리 의도(food, activity, unkown)

	recommend_items : list # 추천된 음식, 활동의 리스트
	search_keyword : str   # 장소 검색용 키워드
	recommend_place : dict # 장소 추천 결과(장소 이름, 주소, url)
	final_message : str    # 최종 결론 메시지

workflow = StateGraph(State)
#전체 workflow안에 포함될 각 노드를 정의
workflow.add_node('classify_intent', classify_intent)
workflow.add_node('get_time_slot', get_time_slot)
workflow.add_node('get_season', get_season)
workflow.add_node('get_weather', get_weather)
workflow.add_node('recommend_food', recommend_food)
workflow.add_node('recommend_activity', recommend_activity)
workflow.add_node('generate_search_keyword', generate_search_keyword)
workflow.add_node('search_place', search_place)
workflow.add_node('summarize_messages', summarize_messages)
workflow.add_node('intent_unkown', intent_unknown)

#노드를 엣지로 연결
workflow.set_entry_point('classify_intent')
workflow.add_edge('classify_intent', 'get_time_slot')
workflow.add_edge('get_time_slot', 'get_season')
workflow.add_edge('get_season', 'get_weather')

def routing_intent(state : State) -> str:
	#classify_intent 된 의도(intent)를 가져옴
	intent = state.get('intent', '') 
	if intent == 'food':
		return 'recommend_food'

	elif intent == 'activity':
		return 'recommend_activity'

	else:
		return 'intent_unkown'

workflow.add_conditional_edges('get_weather', routing_intent,
	#해석된 의도(intent)에 따라 다음 노드를 어디로 향할지 알려줌
	{'recommend_food':'recommend_food',
	'recommend_activity' : 'recommend_activity',
	'intent_unkown': 'intent_unkown'})

workflow.add_edge('recommend_food', 'generate_search_keyword')
workflow.add_edge('recommend_activity', 'generate_search_keyword')
#generate_search_keyword : 음식/활동별로 검색해 볼만한 키워드를 생성 
#search_place : 실제로 만든 키워드로 '카카오맵'에 장소 검색
workflow.add_edge('generate_search_keyword', 'search_place') 
workflow.add_edge('search_place', 'summarize_messages')

workflow.add_edge('summarize_messages', END)
workflow.add_edge('intent_unkown', END)

graph = workflow.compile()
