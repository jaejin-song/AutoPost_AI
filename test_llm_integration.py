#!/usr/bin/env python3
# LLM Provider 통합 테스트

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.ai.llm_providers import get_llm_provider, LLMProviderFactory
from modules.ai.pydantic_models import TopicSelection, BlogContentResponse
from config import load_accounts
from modules.utils import logger

def test_llm_providers():
    """LLM Provider 통합 테스트"""
    print("=== LLM Provider 통합 테스트 시작 ===\n")
    
    # 계정 정보 로드
    accounts = load_accounts()
    print("사용 가능한 계정 세트:")
    for set_name, account_info in accounts.items():
        llm_config = account_info.get('llm', {})
        provider_type = llm_config.get('provider', 'default')
        model = llm_config.get('model', 'default')
        print(f"  - {set_name}: {provider_type} ({model})")
    print()
    
    # 각 계정 세트별 LLM Provider 테스트
    for set_name in accounts.keys():
        print(f"=== {set_name} 계정 테스트 ===")
        
        try:
            # LLM Provider 생성
            llm_provider = get_llm_provider(set_name, accounts)
            
            print(f"Provider 타입: {type(llm_provider).__name__}")
            print(f"사용 가능: {llm_provider.is_available()}")
            
            if llm_provider.is_available():
                # 간단한 테스트 메시지 생성
                test_messages = [
                    {
                        "role": "user",
                        "content": "안녕하세요! 간단한 테스트 메시지입니다. '테스트 완료'라고만 응답해주세요."
                    }
                ]
                
                print("테스트 메시지 전송 중...")
                response = llm_provider.generate(
                    messages=test_messages,
                    system_prompt="당신은 도움이 되는 AI 어시스턴트입니다.",
                    max_tokens=100,
                    temperature=0
                )
                
                if response:
                    print(f"✅ 응답 성공: {response[:100]}{'...' if len(response) > 100 else ''}")
                else:
                    print("❌ 응답 실패")
            else:
                print("⚠️ Provider 사용 불가 (서비스 중단 또는 설정 오류)")
                
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
        
        print("-" * 50)
    
    print("\n=== 테스트 완료 ===")

def test_provider_factory():
    """Provider Factory 테스트"""
    print("\n=== Provider Factory 테스트 ===")
    
    # Claude Provider 테스트
    claude_config = {
        "provider": "claude",
        "model": "claude-sonnet-4-20250514"
    }
    claude_provider = LLMProviderFactory.create_provider(claude_config)
    print(f"Claude Provider: {claude_provider is not None}")
    if claude_provider:
        print(f"  - 사용 가능: {claude_provider.is_available()}")
    
    # Ollama Provider 테스트
    ollama_config = {
        "provider": "ollama",
        "model": "llama3.2",
        "base_url": "http://localhost:11434"
    }
    ollama_provider = LLMProviderFactory.create_provider(ollama_config)
    print(f"Ollama Provider: {ollama_provider is not None}")
    if ollama_provider:
        print(f"  - 사용 가능: {ollama_provider.is_available()}")
    
    # 기본 Provider 테스트
    default_provider = LLMProviderFactory.get_default_provider()
    print(f"Default Provider: {default_provider is not None}")
    if default_provider:
        print(f"  - 사용 가능: {default_provider.is_available()}")

def test_structured_output():
    """구조화된 출력 테스트 (Pydantic format)"""
    print("\n=== 구조화된 출력 테스트 ===")
    
    # 계정 정보 로드
    accounts = load_accounts()
    
    for set_name, account_info in accounts.items():
        llm_config = account_info.get('llm', {})
        provider_type = llm_config.get('provider', 'claude').lower()
        
        print(f"\n--- {set_name} ({provider_type}) ---")
        
        try:
            llm_provider = get_llm_provider(set_name, accounts)
            
            if llm_provider.is_available():
                # 주제 선정 구조화 테스트
                print("1. 주제 선정 구조화 출력 테스트")
                topic_messages = [
                    {
                        "role": "user",
                        "content": "다음 주제들 중 3개를 선택해주세요:\n1. AI 기술 동향\n2. 건강한 식단\n3. 부동산 투자\n4. 여행 팁\n5. 온라인 마케팅\n\n정확히 3개의 번호만 선택하세요."
                    }
                ]
                
                response = llm_provider.generate(
                    messages=topic_messages,
                    system_prompt="주제를 선정하는 전문가입니다.",
                    max_tokens=200,
                    temperature=0,
                    format=TopicSelection
                )
                
                if response:
                    print(f"✅ 주제 선정 응답: {response[:200]}...")
                    
                    # Pydantic 파싱 테스트
                    try:
                        topic_selection = TopicSelection.model_validate_json(response)
                        print(f"📋 선정된 주제 번호: {topic_selection.selected_numbers}")
                        print(f"💭 선정 이유: {topic_selection.reasoning}")
                    except Exception as e:
                        print(f"⚠️ Pydantic 파싱 실패: {e}")
                else:
                    print("❌ 주제 선정 응답 실패")
                
                print()
                
                # 블로그 콘텐츠 구조화 테스트
                print("2. 블로그 콘텐츠 구조화 출력 테스트")
                blog_messages = [
                    {
                        "role": "user", 
                        "content": "AI 기술 동향에 대한 짧은 블로그 글을 작성해주세요. 제목, 내용, 카테고리, 태그를 포함해서 JSON 형식으로 작성해주세요."
                    }
                ]
                
                response = llm_provider.generate(
                    messages=blog_messages,
                    system_prompt="블로그 작성 전문가입니다.",
                    max_tokens=800,
                    temperature=0,
                    format=BlogContentResponse
                )
                
                if response:
                    print(f"✅ 블로그 응답 길이: {len(response)} 문자")
                    
                    # Pydantic 파싱 테스트
                    try:
                        blog_content = BlogContentResponse.model_validate_json(response)
                        print(f"📰 제목: {blog_content.title}")
                        print(f"📝 내용 길이: {len(blog_content.content)} 문자")
                        print(f"🏷️ 카테고리: {blog_content.category}")
                        print(f"🏷️ 태그: {blog_content.tags}")
                    except Exception as e:
                        print(f"⚠️ Pydantic 파싱 실패: {e}")
                        # 원본 응답 일부 출력
                        print(f"원본 응답: {response[:300]}...")
                else:
                    print("❌ 블로그 콘텐츠 응답 실패")
                    
            else:
                print("⚠️ Provider 사용 불가")
                
        except Exception as e:
            print(f"❌ 테스트 중 오류 발생: {e}")
        
        print("-" * 50)

if __name__ == "__main__":
    test_provider_factory()
    test_llm_providers()
    test_structured_output()