from langchain_openai import ChatOpenAI
import json
import requests
import traceback
from datetime import datetime

import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
KAKAO_API_KEY = os.getenv('KAKAO_API_KEY')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')

#시간 라이브러리
from datetime import datetime

def print_something():
   print(f'Hahaha@')

#일반적인 의도 파악 및 메시지를 작성
llm = ChatOpenAI(
   model = 'gpt-4o-mini', 
   api_key = OPENAI_API_KEY,
   temperature= 0.3,
   model_kwargs={'response_format' : {'type':'json_object'}})

llm2 = ChatOpenAI(
   model = 'gpt-4o-mini', 
   api_key = OPENAI_API_KEY,
   temperature= 0.3,)

#user_input을 바탕으로, 사용자의 의도를 파악함
#LLM을 사용하는 agent
def classify_intent(state : dict) -> dict :

   #사용자의 입력 문장을 state에서 가져옴
   user_input = state.get('user_input', '')

   prompt = f"""
      당신은 사용자의 자연어 입력을 food / activity / unknown 중 하나로 분류하는 AI입니다.

      입력: "{user_input}"

      분류 기준:
      - 음식 관련 표현 → "food" (예: 배고파, 뭐 먹지, 야식 추천해줘 등)
      - 활동 관련 표현 → "activity" (예: 심심해, 뭐 하지, 놀고 싶어 등)
      - 증상, 감정, 질문, 애매한 표현 → "unknown"

      조금 애매한 표현이라도 의미가 보이면 food 또는 activity로 분류하세요.

      출력은 반드시 다음 중 하나의 JSON 배열 또는 객체로 작성하세요:
      - 배열: ["food"]
      - 객체: {{ "intent": ["food"] }}
      """

   response = llm.invoke([
      {'role' : 'user', 'content' : prompt.strip()}
      ])

   #strip()을 통해 양쪽 공백 제거
   intents = response.content.strip()
   print(f'{user_input}에 대한 GPT의 의도 분류 : {intents}')

   try:
      #intents를 json.loads()로 파싱하여 가져옴
      parsed = json.loads(intents)

      #isinstance(A, B) -> A가 B타입이냐?
      #parsed != None
      #parsed[0]가 food나 activity중에 하나라면~
      if isinstance(parsed, list) and parsed and parsed[0] in ['food', 'activity']:
         return {**state, 'intent' : parsed[0]}

      if isinstance(parsed, dict):
         if 'intent' in parsed:
            in_value = parsed['intent']

            if isinstance(in_value, list) and in_value and in_value[0] in ['food', 'activity']:
               return {**state, 'intent':in_value[0]}

            for key in ['food', 'activity']:
               if key in parsed:
                  return {**state, 'intent':key}

   except Exception as e :
      print(f'에러 발생 : {e}')

   return {**state, 'intent':'unknown'}


#현재 시각을 기준으로 시간대를 분류
def get_time_slot(state : dict) -> dict :

   #시간 00~24까지
   hour = datetime.now().hour

   if 5 <= hour < 11:
      return {**state, 'time_slot':'아침'}

   elif 11 <= hour < 15:
      return {**state, 'time_slot':'점심'}

   elif 15 <= hour < 18:
      return {**state, 'time_slot':'오후'}

   else:
      return {**state, 'time_slot': '저녁'}


#현재 날짜를 기준으로 계절 분류 
def get_season(state : dict) -> dict:
   month = datetime.now().month

   if 3 <= month <= 5:
      season = '봄'
   elif 6 <= month <= 8:
      season = '여름'
   elif 9 <= month <= 11:
      season = '가을'
   else:
      season = '겨울'
   return {**state, 'season':season} 


#llm을 이용하여 음식 추천을 받음
def recommend_food(state : dict) -> dict:

   user_input = state.get('user_input', '') 
   season = state.get('season', '봄')
   weather = state.get('weather', 'Clear')
   time_slot = state.get('time_slot', '오후')

   prompt = f"""당신은 음식 추천 AI입니다.
      사용자 입력: "{user_input}"
      현재 조건:
      - 계절: {season}
      - 날씨: {weather}
      - 시간대: {time_slot}

      이 조건에 어울리는 음식 2가지를 추천해 주세요.

      사용자가 특정 음식을 언급한 경우(예: "피자")에는 그 음식을 포함하거나,
      관련된 음식 또는 어울리는 음식으로 추천해도 좋습니다.

      결과는 반드시 JSON 배열 형식으로 출력하세요.
      예: ["피자", "떡볶이"]
      """

   response = llm.invoke([{'role':'user', 'content':prompt.strip()}])
   items = json.loads(response.content)

   if isinstance(items, dict):
      items = [i for sub in items.values() for i in (sub if isinstance(sub, list) else [sub])] 

   elif not isinstance(items, list):
      items = [str(items)]

   return {**state, 'recommend_food': items}


#현재 날씨를 가져옴(api를 활용)
def get_weather(state : dict) -> dict:
   url = "https://api.openweathermap.org/data/2.5/weather"
   params = {
      'q' : 'Cheonan',
      'appid' : WEATHER_API_KEY,
      'lang' : 'kr',
      'units' : 'metric'}

   response = requests.get(url, params=params)
   response.raise_for_status()

   weather_data = response.json()
   weather = weather_data['weather'][0]['main'] 

   return {**state, 'weather': weather}


def recommend_activity(state:dict) -> dict:

   user_input = state.get('user_input', '')
   season = state.get('season', '봄')
   weather = state.get('weather', 'Clear')
   time_slot = state.get('time_slot', '오후')

   prompt = f"""당신은 활동 추천 AI입니다.

         사용자 입력: "{user_input}"
         현재 조건:
         - 계절: {season}
         - 날씨: {weather}
         - 시간대: {time_slot}

         이 조건과 입력에 어울리는 활동 2가지를 추천해 주세요.
         실내 활동이 포함되면 더 좋습니다.

         결과는 반드시 JSON 배열 형식으로 출력하세요.
         예: ["북카페 가기", "실내 보드게임"]
         """ 

   response = llm.invoke([{'role':'user', 'content': prompt.strip()}])
   items = json.loads(response.content)

   if isinstance(items, dict):
      items = [i for sub in items.values() for i in (sub if isinstance(sub, list) else [sub])]

   elif not isinstance(items, list):
      items = [str(items)]

   return {**state, 'recommend_activity': items}


#langgraph 플로우 안에 포함되어 있음
#추천된 항목을 바탕으로 장소 검색용 키워드를 생성
def generate_search_keyword(state:dict) -> dict: 

   items = state.get('recommend_items', ['추천'])

   if isinstance(items, dict):
      items = [i for sub in items.values() for i in (sub if isinstance(sub, list) else [sub])]
   elif not isinstance(items, list):
      items = [str(items)]

   item = items[0]
   user_input = state.get('user_input', '')
   intent = state.get('intent', 'unknown')

   prompt = f"""사용자의 입력: "{user_input}"
            추천 항목: "{item}"
            의도: "{intent}"

            이 항목을 장소에서 검색하려고 합니다.
            음식이라면 음식 종류(예: 김치찌개 → 한식),
            활동이라면 장소 유형(예: 책 읽기 → 북카페)으로 변환하세요.

            결과는 반드시 JSON 배열로 출력하세요.
            예: ["한식"]
            """ 

   response = llm.invoke([{'role':'user', 'content':prompt.strip()}])
   keywords = json.loads(response.content)

   if isinstance(keywords, dict):
      keywords = [i for sub in keywords.values() for i in (sub if isinstance(sub, list) else [sub])]
   elif not isinstance(keywords, list):
      keywords = [str(keywords)]

   return {**state, 'search_keyword': keywords[0] if keywords else item}


#location과 search_keyword를 바탕으로,
#카카오맵을 활용해서 장소 정보를 가져오는 함
def search_place(state : dict) -> dict:

   location = state.get('location', '천안') 
   keyword = state.get('search_keyword', '추천')

   query = f'{location} {keyword}'
   print(f'> GPT 최종 서치 키워드 : {query}')

   url = "https://dapi.kakao.com/v2/local/search/keyword.json"
   headers = {
      "Authorization" : f'KakaoAK {KAKAO_API_KEY}'
   }

   params = {
      'query' : query,
      'size'  : 3
   }

   response = requests.get(url, headers=headers, params=params)
   response.raise_for_status()
   doc = response.json()['documents']

   if doc:
      top_one = doc[0]
      place = {
         'name' : top_one['place_name'],
         'address' : top_one['road_address_name'],
         'url' : top_one['place_url']
      }
   else:
      place = {
         'name':'추천 장소 없음',
         'address' : '',
         'url' : ''
      }

   return {**state, 'recommend_place': place}


#위의 모든 정보를 토대로 사용자에게 return할 문장을 생성하는 함수이다.
def summarize_messages(state: dict) -> dict:

   items = state.get('recommend_items', ['추천 항목 없음'])

   if isinstance(items, dict):
      items = list(items.values())
   elif not isinstance(items, list):
      items = [str(items)]

   item = items[0]
   season = state.get('season', '')
   weather = state.get('weather', '')
   time_slot = state.get('time_slot','')
   intent = state.get('intent', 'food')
   place = state.get('recommend_place', {})

   place_name = place.get('name', '추천 장소 없음')
   place_address = place.get('address', '')
   place_url = place.get('url', '')

   category = '음식' if intent == 'food' else '활동'

   prompt = f'''
      현재 사용자는 {category}라는 의도로 질문하였습니다.
      계절은 {season}이고, 날씨는 {weather}, 시간대는 {time_slot}입니다.

      추천할 아이템은 {category} : {item} 이고,
      추천 장소는 {place_name}({place_address}),
      추천 장소의 지도 링크는 {place_url} 입니다.

      위의 정보를 바탕으로 사용자의 의도를 감성적이고 따뜻한 시선으로 해석하여
      추천할 아이템 및 장소에 대해 잘 소개해 주세요.

      추천메시지는 한 문단 정도 길이로, 위의 추천 아이템, 장소, 주소, url이 모두 들어가야 합니다.
   '''

   response = llm2.invoke([
      {'role':'system', 'content': '너는 음식과 활동에 대해 추천할만한 재미있는 장소를 잘 알고있는 여행 보조 AI야.'},
      {'role':'user', 'content':prompt}
   ])

   return {**state, 'final_message': response.content.strip()}

def intent_unknown(state : dict) -> dict:
   return {**state, 'final_message':'저는 음식이나 활동 관련 추천만 해드릴 수 있어요.'}

   # if __name__ == '__main__':
      # get_weather()