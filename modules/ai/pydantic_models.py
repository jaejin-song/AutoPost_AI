# Pydantic 모델 정의 - LLM 구조화된 출력용
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# 주제 선정 응답 모델
class TopicSelection(BaseModel):
    """AI가 주제를 선정할 때 사용하는 응답 모델"""
    selected_numbers: List[int] = Field(
        description="선정된 주제 번호 목록", 
        min_items=1, 
        max_items=50
    )
    reasoning: Optional[str] = Field(
        description="선정 이유 설명",
        default=""
    )


# 블로그 콘텐츠 응답 모델
class BlogContentResponse(BaseModel):
    """AI가 블로그 글을 생성할 때 사용하는 응답 모델"""
    title: str = Field(description="블로그 글 제목", min_length=1, max_length=200)
    content: str = Field(description="블로그 글 내용", min_length=10)
    category: Optional[str] = Field(description="블로그 카테고리", default="")
    tags: List[str] = Field(description="블로그 태그 목록", default=[])
    summary: Optional[str] = Field(description="글 요약", default="")


# SNS 포스트 응답 모델
class SocialMediaPost(BaseModel):
    """SNS 포스트 생성용 응답 모델"""
    content: str = Field(description="SNS 포스트 내용", min_length=10, max_length=280)
    hashtags: List[str] = Field(description="해시태그 목록", default=[])
    call_to_action: Optional[str] = Field(description="행동 유도 문구", default="")


# 분석 결과 응답 모델
class AnalysisResult(BaseModel):
    """AI 분석 결과용 응답 모델"""
    summary: str = Field(description="분석 요약")
    key_points: List[str] = Field(description="주요 포인트 목록", default=[])
    recommendations: List[str] = Field(description="추천 사항 목록", default=[])
    confidence_score: Optional[float] = Field(
        description="신뢰도 점수 (0-1)", 
        ge=0.0, 
        le=1.0, 
        default=None
    )


# 뉴스 요약 응답 모델
class NewsSummary(BaseModel):
    """뉴스 요약용 응답 모델"""
    headline: str = Field(description="요약된 헤드라인", max_length=100)
    summary: str = Field(description="뉴스 요약 내용", max_length=500)
    key_points: List[str] = Field(description="주요 핵심 내용", default=[])
    sentiment: Optional[str] = Field(
        description="감정 분석 (positive/negative/neutral)", 
        default=None
    )
    category: Optional[str] = Field(description="뉴스 카테고리", default="")


# 키워드 추출 응답 모델
class KeywordExtraction(BaseModel):
    """키워드 추출용 응답 모델"""
    primary_keywords: List[str] = Field(description="주요 키워드", default=[])
    secondary_keywords: List[str] = Field(description="보조 키워드", default=[])
    topics: List[str] = Field(description="주제 태그", default=[])
    difficulty: Optional[str] = Field(
        description="키워드 난이도 (easy/medium/hard)", 
        default=None
    )


# 스케줄 관리 응답 모델
class ScheduleResponse(BaseModel):
    """일정 관리용 응답 모델"""
    scheduled_items: List[Dict[str, Any]] = Field(
        description="예정된 항목들", 
        default=[]
    )
    priority_levels: List[str] = Field(description="우선순위 레벨", default=[])
    suggested_times: List[str] = Field(description="제안 시간대", default=[])


# 일반적인 JSON 응답 모델
class GeneralResponse(BaseModel):
    """일반적인 구조화된 응답용 모델"""
    status: str = Field(description="상태 (success/error)", default="success")
    data: Dict[str, Any] = Field(description="응답 데이터", default={})
    message: Optional[str] = Field(description="응답 메시지", default="")
    errors: List[str] = Field(description="오류 목록", default=[])


# 질문 답변 응답 모델  
class QuestionAnswerResponse(BaseModel):
    """질문 답변용 응답 모델"""
    answer: str = Field(description="답변 내용", min_length=10)
    confidence: Optional[float] = Field(
        description="답변 신뢰도 (0-1)", 
        ge=0.0, 
        le=1.0, 
        default=None
    )
    sources: List[str] = Field(description="참조 소스 목록", default=[])
    follow_up_questions: List[str] = Field(description="후속 질문", default=[])


# 번역 응답 모델
class TranslationResponse(BaseModel):
    """번역용 응답 모델"""
    translated_text: str = Field(description="번역된 텍스트", min_length=1)
    source_language: Optional[str] = Field(description="원본 언어", default="")
    target_language: Optional[str] = Field(description="번역 언어", default="")
    confidence: Optional[float] = Field(
        description="번역 신뢰도 (0-1)", 
        ge=0.0, 
        le=1.0, 
        default=None
    )