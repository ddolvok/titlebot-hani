from bs4 import BeautifulSoup
import requests
import streamlit as st
import random

def spinner_with_text(text):
    @Spinner(text)
    def empty_function():
        pass
    empty_function()

if 'titles' not in st.session_state:
    st.session_state.titles = []
if 'analysis' not in st.session_state:
    st.session_state.analysis = ""
if 'presses' not in st.session_state:
    st.session_state.presses = []
if 'initiated' not in st.session_state:
    st.session_state.initiated = False

API_KEY = st.secrets["api_key"]
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537'}

def fetch_titles(base_url, num_pages):
    all_titles = []
    all_presses = []
    for i in range(1, num_pages + 1):
        url = f"{base_url}&page={i}"
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        titles = soup.select('.sh_text_headline.nclicks\(cls_pol\.clsart\)')
        presses = soup.select('.sh_text_press')
        for title, press in zip(titles, presses):
            all_titles.append(title.text)
            all_presses.append(press.text)
    return all_titles, all_presses

def fetch_from_openai(titles, prompt, tokens=200):
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {API_KEY}'}
    data = {'model': 'gpt-4', 'messages': [{"role": "user", "content": prompt}, {"role": "system", "content": '\n'.join(titles)}], 'max_tokens': tokens}
    response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data)
    return response.json()['choices'][0]['message']['content'].strip() if response.status_code == 200 else f"Error: {response.status_code}"

def filter_titles_by_keyword(titles, keyword):
    return [title for title in titles if keyword.lower() in title.lower()]

st.title("미디어랩 타이틀봇 프로젝트 (정치)")

if not st.session_state.initiated:
    keyword = st.text_input("키워드가 될 단어를 하나만 넣어주세요 :", key='keyword')
    if st.button("시작하기", key="start-button"):
        if not keyword:
            st.markdown("<span style='color:red'>키워드를 넣지 않으셔서 지금 이슈 기사를 모두 받아 옵니다.</span>", unsafe_allow_html=True)
        
        with st.spinner('AI가 일하고 있습니다. 10초만 기다려주세요!'):
            st.session_state.initiated = True
            st.session_state.titles, st.session_state.presses = fetch_titles("https://news.naver.com/main/main.naver?mode=LSD&mid=shm&sid1=100", 30)
            if keyword:
                st.session_state.titles = filter_titles_by_keyword(st.session_state.titles, keyword)
            st.session_state.analysis = fetch_from_openai(st.session_state.titles, "크롤링 된 기사 제목들이 어떤 내용을 다루고 있는지 200자 이내로 분석해 줘.")
else:
    keyword = st.text_input("키워드가 될 단어를 하나만 넣어주세요 :", value=st.session_state.get('keyword', ''), key='keyword')
    if st.button("다시 시작하기", key="restart-button"):
        with st.spinner('AI가 일하고 있습니다. 10초만 기다려주세요!'):
            st.session_state.initiated = True  # 작업을 다시 시작
            st.session_state.titles, st.session_state.presses = fetch_titles("https://news.naver.com/main/main.naver?mode=LSD&mid=shm&sid1=100", 30)
            if keyword:
                st.session_state.titles = filter_titles_by_keyword(st.session_state.titles, keyword)
            st.session_state.analysis = fetch_from_openai(st.session_state.titles, "크롤링 된 기사 제목들이 어떤 내용을 다루고 있는지 200자 이내로 분석해 줘.")


if st.session_state.initiated:
    st.subheader("AI의 기사 제목 분석 결과")
    st.write(st.session_state.analysis)

    # 새로운 부분: 키워드 입력 필드 3개 추가
    keyword1 = st.text_input("첫 번째 키워드를 입력해주세요 :", key='keyword1')
    keyword2 = st.text_input("두 번째 키워드를 입력해주세요 :", key='keyword2')
    keyword3 = st.text_input("세 번째 키워드를 입력해주세요 :", key='keyword3')
    
    # 새로운 부분: 키워드에 따른 기사 제목 필터링
    selected_titles = []
    if keyword1:
        selected_titles += filter_titles_by_keyword(st.session_state.titles, keyword1)
    if keyword2:
        selected_titles += filter_titles_by_keyword(st.session_state.titles, keyword2)
    if keyword3:
        selected_titles += filter_titles_by_keyword(st.session_state.titles, keyword3)
    
    if st.button("기사 제목 만들기", key="generate-similar-titles-button"):
        # 선택된 기사 제목을 사용해 GPT-4로부터 제목을 생성
        with st.spinner('GPT-4가 기사 제목을 만들고 있어'):
            if selected_titles:  # 선택된 기사 제목이 있다면
                prompt = "selected_titles의 기사 제목들을 그대로 5개를 뽑아 줘. 뽑은 기사 제목들을 거의 똑같이 보이게 미세하게 수정해 줘. 원래 제목에 없는 단어를 절대 추가하지 마. 원래 제목에서 " " 이렇게 큰 따옴표와 ' ' 이렇게 작은 따옴표에 들어있는 내용들은 똑같게 유지해. () [] 이런 괄호들에 들어있는 내용은 무조건 빼. 새롭게 뽑은 기사 제목만 보여주면 돼."
                similar_titles = fetch_from_openai(selected_titles, prompt, tokens=500)
                st.subheader("AI가 생성한 유사한 기사 제목")
                st.write(similar_titles)
            else:
                st.markdown("<span style='color:red'>적합한 기사 제목을 찾지 못했습니다.</span>", unsafe_allow_html=True)


    st.subheader("이슈가 되고 있는 정치부 기사들")
    for title, press in zip(st.session_state.titles, st.session_state.presses[:len(st.session_state.titles)]):
        st.markdown(f"{title} - <span style='color:blue'>{press}</span>", unsafe_allow_html=True)
