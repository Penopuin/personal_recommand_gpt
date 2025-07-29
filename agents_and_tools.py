# 상단에 필요한 라이브러리
from langchain_openai import ChatOpenAI
import json
import requests
from datetime import datetime


# LLM 세팅
llm = ChatOpenAI(
    model='gpt-4o-mini',
    api_key='내 OPENAI KEY',
    temperature=0.3,
    model_kwargs={'response_format': {'type': 'json_object'}}
)


# 1. 사용자 의도 분류 함수
def classify_intent(state: dict) -> dict:
    user_input = state.get('user_input', '')

    prompt = f"""
    당신은 사용자의 자연어 입력을 food / activity / unknown 중 하나로 분류하는 AI입니다.
    입력: "{user_input}"
    - 음식 관련 표현 → "food"
    - 활동 관련 표현 → "activity"
    - 애매한 표현 → "unknown"
    출력은 JSON으로: ["food"] 또는 {{ "intent": ["food"] }}
    """

    response = llm.invoke([{'role': 'user', 'content': prompt.strip()}])
    intents = response.content.strip()

    try:
        parsed = json.loads(intents)

        if isinstance(parsed, list) and parsed and parsed[0] in ['food', 'activity']:
            return {**state, 'intent': parsed[0]}

        if isinstance(parsed, dict):
            in_value = parsed.get('intent', [])
            if isinstance(in_value, list) and in_value and in_value[0] in ['food', 'activity']:
                return {**state, 'intent': in_value[0]}
            for key in ['food', 'activity']:
                if key in parsed:
                    return {**state, 'intent': key}

    except Exception as e:
        print(f'에러 발생 : {e}')

    return {**state, 'intent': 'unknown'}


# 2. 시간대 판단
def get_time_slot(state: dict) -> dict:
    hour = datetime.now().hour
    if 5 <= hour < 11:
        return {**state, 'time_slot': '아침'}
    elif 11 <= hour < 15:
        return {**state, 'time_slot': '점심'}
    elif 15 <= hour < 18:
        return {**state, 'time_slot': '오후'}
    else:
        return {**state, 'time_slot': '저녁'}


# 3. 계절 판단
def get_season(state: dict) -> dict:
    month = datetime.now().month
    if 3 <= month <= 5:
        return {**state, 'season': '봄'}
    elif 6 <= month <= 8:
        return {**state, 'season': '여름'}
    elif 9 <= month <= 11:
        return {**state, 'season': '가을'}
    else:
        return {**state, 'season': '겨울'}


# 4. 날씨 API 호출
def get_weather(state: dict) -> dict:
    WEATHER_API_KEY = 'YOUR_OPENWEATHER_API_KEY'
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {'q': 'Cheonan', 'appid': WEATHER_API_KEY, 'lang': 'kr', 'units': 'metric'}
    response = requests.get(url, params=params)
    response.raise_for_status()
    weather_data = response.json()
    weather = weather_data['weather'][0]['main']
    return {**state, 'weather': weather}


# 5. 음식 추천
def recommend_food(state: dict) -> dict:
    prompt = f"""
    조건에 맞는 음식 2개 추천해주세요. 결과는 JSON 배열 형식 ["냉면", "김밥"]
    계절: {state.get('season')}, 날씨: {state.get('weather')}, 시간대: {state.get('time_slot')}, 입력: {state.get('user_input')}
    """
    response = llm.invoke([{'role': 'user', 'content': prompt.strip()}])
    try:
        items = json.loads(response.content)
        if isinstance(items, dict):
            items = [i for sub in items.values() for i in (sub if isinstance(sub, list) else [sub])]
        elif not isinstance(items, list):
            items = [str(items)]
    except:
        items = ["추천 음식 없음"]
    return {**state, 'recommend_items': items}


# 6. 활동 추천
def recommend_activity(state: dict) -> dict:
    prompt = f"""
    조건에 맞는 활동 2개 추천해주세요. 결과는 JSON 배열 ["북카페 가기", "실내 보드게임"]
    계절: {state.get('season')}, 날씨: {state.get('weather')}, 시간대: {state.get('time_slot')}, 입력: {state.get('user_input')}
    """
    response = llm.invoke([{'role': 'user', 'content': prompt.strip()}])
    try:
        items = json.loads(response.content)
        if isinstance(items, dict):
            items = [i for sub in items.values() for i in (sub if isinstance(sub, list) else [sub])]
        elif not isinstance(items, list):
            items = [str(items)]
    except:
        items = ["추천 활동 없음"]
    return {**state, 'recommend_items': items}


# 7. 검색 키워드 생성
def generate_search_keyword(state: dict) -> dict:
    item = state.get('recommend_items', ['추천'])[0]
    intent = state.get('intent', 'unknown')

    prompt = f"""
    추천 항목 "{item}"의 검색용 키워드를 장소 기준으로 변환 (예: "라면" → "분식", "보드게임" → "보드게임 카페")
    결과는 JSON 배열로 출력
    """
    response = llm.invoke([{'role': 'user', 'content': prompt.strip()}])
    try:
        keywords = json.loads(response.content)
        if isinstance(keywords, dict):
            keywords = [i for sub in keywords.values() for i in (sub if isinstance(sub, list) else [sub])]
        elif not isinstance(keywords, list):
            keywords = [str(keywords)]
    except:
        keywords = [item]
    return {**state, 'search_keyword': keywords[0]}


# 8. 카카오맵 장소 검색
def search_place(state: dict) -> dict:
    location = state.get('location', '천안')
    keyword = state.get('search_keyword', '추천')
    query = f'{location} {keyword}'
    print(f'> 검색어: {query}')

    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": "KakaoAK YOUR_KAKAO_API_KEY"}
    params = {'query': query, 'size': 3}

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    doc = response.json().get('documents', [])
    if doc:
        top_one = doc[0]
        place = {
            'name': top_one['place_name'],
            'address': top_one['road_address_name'],
            'url': top_one['place_url']
        }
    else:
        place = {'name': '추천 장소 없음', 'address': '', 'url': ''}
    return {**state, 'recommend_place': place}


# 9. 최종 메시지 생성
def summarize_messages(state: dict) -> dict:
    item = state.get('recommend_items', ['추천'])[0]
    place = state.get('recommend_place', {})
    prompt = f"""
    사용자가 원하는 {state.get('intent')}에 맞춰 {item}을 추천했습니다.
    추천 장소: {place.get('name')} ({place.get('address')})
    링크: {place.get('url')}
    이 내용을 기반으로 따뜻한 추천 메시지를 작성하세요.
    """

    response = llm.invoke([
        {'role': 'system', 'content': '너는 따뜻한 말투의 추천 AI야.'},
        {'role': 'user', 'content': prompt.strip()}
    ])
    return {**state, 'final_message': response.content.strip()}
