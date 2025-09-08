# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from openai import OpenAI
import os
import datetime
import locale

# 로케일 설정
try:
    locale.setlocale(locale.LC_ALL, 'ko_KR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'Korean_Korea.949')
    except:
        pass

# ---- 페이지 설정 ----
st.set_page_config(page_title="꿈 해몽 심리 분석 🌙", layout="wide")
st.title("🌙 꿈 해몽 심리 분석 챗봇")
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("<p style='opacity:0.7;'>꿈을 통해 당신의 심리 상태를 분석하고 개선 방안을 제시합니다.</p>", unsafe_allow_html=True)
st.markdown("<br><br>", unsafe_allow_html=True)

# ---- 사이드바: OpenAI API 키 는  현재 아래 시크릿파일대체----
## st.sidebar.title("설정")
## if "api_key" not in st.session_state:
##    st.session_state.api_key = ""
## st.session_state.api_key = st.sidebar.text_input("🔑 OpenAI API Key", type="password", value=st.session_state.api_key)
## if not st.session_state.api_key:
##    st.sidebar.warning("API 키를 입력해야 사용 가능합니다.")
##    st.stop()

##client = OpenAI(api_key=st.session_state.api_key)

# Streamlit Secrets에서 API 키를 불러옵니다.
api_key = st.secrets.get("OPENAI_API_KEY")

if not api_key:
    st.error("❌ OpenAI API 키가 설정되지 않았습니다.")
    st.stop()

client = OpenAI(api_key=api_key)

# ---- 세션 상태 초기화 ----
if "analysis_step" not in st.session_state:
    st.session_state.analysis_step = 0
if "dream_content" not in st.session_state:
    st.session_state.dream_content = ""
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "psychological_type" not in st.session_state:
    st.session_state.psychological_type = ""
if "initial_analysis" not in st.session_state:
    st.session_state.initial_analysis = ""

# 5단계 심리학적 질문 정의
psychological_questions = [
    {
        "id": "stress",
        "question": "최근 일상생활에서 스트레스를 많이 받고 계신가요?",
        "category": "스트레스 수준"
    },
    {
        "id": "decision",
        "question": "현재 중요한 결정을 내려야 하는 상황에 있으신가요?",
        "category": "의사결정 상황"
    },
    {
        "id": "relationship",
        "question": "주변 사람들과의 관계에서 어려움을 겪고 있나요?",
        "category": "대인관계"
    },
    {
        "id": "self_reflection",
        "question": "자신에 대해 깊이 생각해볼 시간이 필요하다고 느끼시나요?",
        "category": "자아 성찰"
    },
    {
        "id": "future_anxiety",
        "question": "앞으로의 일에 대해 불안하거나 걱정이 많으신가요?",
        "category": "미래 불안"
    }
]

# 심리학적 유형 분류 함수
def classify_psychological_type(answers):
    scores = {
        "스트레스 과부하형": 0,
        "관계 갈등형": 0,
        "결정 고민형": 0,
        "성장 욕구형": 0,
        "불안 우울형": 0
    }
    
    if answers.get("stress") == "예":
        scores["스트레스 과부하형"] += 2
        scores["불안 우울형"] += 1
    
    if answers.get("decision") == "예":
        scores["결정 고민형"] += 2
        scores["불안 우울형"] += 1
    
    if answers.get("relationship") == "예":
        scores["관계 갈등형"] += 2
        scores["스트레스 과부하형"] += 1
    
    if answers.get("self_reflection") == "예":
        scores["성장 욕구형"] += 2
        scores["결정 고민형"] += 1
    
    if answers.get("future_anxiety") == "예":
        scores["불안 우울형"] += 2
        scores["스트레스 과부하형"] += 1
    
    return max(scores, key=scores.get)

# 유형별 대안 제시 함수
def get_psychological_alternatives(psych_type):
    alternatives = {
        "스트레스 과부하형": {
            "분석": "현재 과도한 스트레스로 인해 심리적 부담을 느끼고 있습니다. 꿈은 이러한 압박감을 해소하려는 무의식의 시도입니다.",
            "대안": [
                "규칙적인 운동이나 명상을 통한 스트레스 해소",
                "업무/학업 시간 관리 및 우선순위 설정",
                "충분한 휴식과 수면 시간 확보",
                "신뢰할 수 있는 사람과의 대화를 통한 감정 표출"
            ]
        },
        "관계 갈등형": {
            "분석": "대인관계에서의 갈등이나 소통 문제가 심리적 스트레스의 주요 원인입니다. 꿈을 통해 관계 개선의 필요성을 나타냅니다.",
            "대안": [
                "솔직하고 열린 대화를 통한 갈등 해결",
                "상대방의 입장을 이해하려는 노력",
                "필요시 중재자를 통한 문제 해결",
                "새로운 인간관계 형성을 위한 활동 참여"
            ]
        },
        "결정 고민형": {
            "분석": "중요한 선택 앞에서 혼란과 불안을 느끼고 있습니다. 꿈은 올바른 결정을 내리고자 하는 내면의 욕구를 반영합니다.",
            "대안": [
                "장단점을 명확히 정리하여 객관적 판단",
                "신뢰할 수 있는 조언자와의 상담",
                "충분한 정보 수집과 시간적 여유 확보",
                "작은 결정부터 시작하여 자신감 회복"
            ]
        },
        "성장 욕구형": {
            "분석": "자아실현과 개인적 성장에 대한 강한 욕구를 가지고 있습니다. 꿈은 더 나은 자신이 되고자 하는 의지를 나타냅니다.",
            "대안": [
                "새로운 기술이나 지식 습득을 위한 학습",
                "창의적 활동이나 취미 개발",
                "목표 설정과 단계적 실행 계획 수립",
                "멘토나 롤모델과의 교류 확대"
            ]
        },
        "불안 우울형": {
            "분석": "미래에 대한 불안과 우울감이 심리 상태에 영향을 미치고 있습니다. 꿈은 이러한 감정을 처리하려는 시도입니다.",
            "대안": [
                "긍정적 사고 훈련과 마음챙김 명상",
                "규칙적인 생활 패턴과 건강한 습관 형성",
                "사회적 지지체계 구축 및 활용",
                "필요시 전문 상담사나 심리치료사 상담"
            ]
        }
    }
    return alternatives.get(psych_type, alternatives["불안 우울형"])

# 안전한 API 호출 함수
def safe_api_call(system_msg, user_msg):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"API 호출 중 오류가 발생했습니다: {str(e)}"

# ---- 초기화 버튼 ----
if st.sidebar.button("🧹 새로운 분석 시작"):
    st.session_state.analysis_step = 0
    st.session_state.dream_content = ""
    st.session_state.answers = {}
    st.session_state.psychological_type = ""
    st.session_state.initial_analysis = ""
    st.rerun()

# ---- 메인 분석 프로세스 ----
if st.session_state.analysis_step == 0:
    # 1단계: 꿈 내용 입력
    st.markdown("### 💭 1단계: 꿈 내용 입력")
    dream_input = st.text_area(
        "해몽받고 싶은 꿈을 자세히 적어주세요:",
        placeholder="예: 지난 밤에 높은 건물에서 떨어지는 꿈을 꾸었습니다. 처음에는 무서웠지만 나중에는 날아다니는 기분이었습니다...",
        height=150
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("꿈 분석 시작하기", type="primary") and dream_input.strip():
        st.session_state.dream_content = dream_input.strip()
        
        with st.spinner("꿈을 분석하고 있습니다..."):
            system_msg = "You are a dream interpretation expert and psychology doctor. Please analyze the user's dream from a psychological perspective and respond in Korean."
            user_msg = f"Please analyze this dream: {dream_input}"
            
            analysis_result = safe_api_call(system_msg, user_msg)
            st.session_state.initial_analysis = analysis_result
            st.session_state.analysis_step = 1
            st.rerun()

elif st.session_state.analysis_step >= 1 and st.session_state.analysis_step <= 5:
    # 2단계: 5단계 심리학적 질문
    st.markdown("### 🧠 2단계: 심리 상태 진단")
    st.write("**입력하신 꿈:**")
    st.info(st.session_state.dream_content)
    
    st.write("**초기 분석 결과:**")
    st.success(st.session_state.initial_analysis)
    
    st.markdown("---")
    st.write("더 정확한 분석을 위해 몇 가지 질문에 답해주세요:")
    
    current_question_idx = st.session_state.analysis_step - 1
    question_data = psychological_questions[current_question_idx]
    
    st.markdown(f"### 질문 {current_question_idx + 1}/5: {question_data['category']}")
    st.markdown(f"**{question_data['question']}**")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("예", key=f"yes_{current_question_idx}", type="primary"):
            st.session_state.answers[question_data['id']] = "예"
            st.session_state.analysis_step += 1
            st.rerun()
    
    with col2:
        if st.button("아니오", key=f"no_{current_question_idx}"):
            st.session_state.answers[question_data['id']] = "아니오"
            st.session_state.analysis_step += 1
            st.rerun()
    
    # 진행률 표시
    progress = (current_question_idx + 1) / 5
    st.progress(progress)
    st.write(f"진행률: {current_question_idx + 1}/5")

elif st.session_state.analysis_step == 6:
    # 3단계: 최종 분석 및 대안 제시
    st.markdown("### 📊 3단계: 종합 분석 결과")
    
    # 심리학적 유형 분류
    psych_type = classify_psychological_type(st.session_state.answers)
    st.session_state.psychological_type = psych_type
    
    # 결과 표시
    st.write("**입력하신 꿈:**")
    st.info(st.session_state.dream_content)
    
    st.write("**질문 답변 요약:**")
    for i, question in enumerate(psychological_questions):
        answer = st.session_state.answers.get(question['id'], '답변 없음')
        st.write(f"• {question['category']}: {answer}")
    
    st.markdown("---")
    
    # 심리학적 유형 및 분석
    st.markdown(f"### 🎯 당신의 심리학적 유형: **{psych_type}**")
    
    alternatives = get_psychological_alternatives(psych_type)
    
    st.markdown("#### 📋 심리학적 분석")
    st.write(alternatives["분석"])
    
    st.markdown("#### 💡 개선 방안")
    for i, alt in enumerate(alternatives["대안"], 1):
        st.write(f"{i}. {alt}")
    
    # 최종 AI 분석
    st.markdown("#### 🤖 AI 전문가 종합 의견")
    with st.spinner("종합 분석을 생성하고 있습니다..."):
        system_msg = "You are a dream interpretation expert and psychology doctor. Please provide comprehensive and practical advice in Korean."
        user_msg = f"""
        Dream content: {st.session_state.dream_content}
        Psychological type: {psych_type}
        Question answers: {st.session_state.answers}
        
        Based on the above information, please provide comprehensive psychological analysis and specific action plans in Korean.
        """
        
        final_analysis = safe_api_call(system_msg, user_msg)
        st.write(final_analysis)
    
    # 새로운 분석 시작 버튼
    if st.button("🔄 새로운 꿈 분석하기", type="primary"):
        st.session_state.analysis_step = 0
        st.session_state.dream_content = ""
        st.session_state.answers = {}
        st.session_state.psychological_type = ""
        st.session_state.initial_analysis = ""
        st.rerun()

# ---- 사이드바 정보 ----
st.sidebar.markdown("---")
st.sidebar.markdown("### 📚 심리학적 유형 설명")
st.sidebar.markdown("""
- **스트레스 과부하형**: 과도한 업무/학업 스트레스
- **관계 갈등형**: 대인관계 문제가 주원인
- **결정 고민형**: 중요한 선택 앞에서 혼란
- **성장 욕구형**: 자아실현 욕구가 강함
- **불안 우울형**: 미래에 대한 걱정이 많음
""")
