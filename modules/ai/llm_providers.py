# LLM Provider 추상화 인터페이스
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import os
import json
import anthropic
import requests
from pydantic import BaseModel
from modules.utils import logger

DEFAULT_CLAUDE_MODEL="claude-sonnet-4-20250514"
DEFAULT_OLLAMA_MODEL="deepseek-r1:8b"

class LLMProvider(ABC):
    """LLM Provider 추상 베이스 클래스"""
    
    @abstractmethod
    def generate(self, messages: list, system_prompt: str = "", max_tokens: int = 4096, temperature: float = 0, format: Optional[BaseModel] = None) -> Optional[str]:
        """텍스트 생성
        
        Args:
            messages: 메시지 목록
            system_prompt: 시스템 프롬프트
            max_tokens: 최대 토큰 수
            temperature: 온도 (창의성)
            format: 구조화된 출력을 위한 Pydantic 모델 (Ollama만 지원)
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Provider 사용 가능 여부 확인"""
        pass


class ClaudeProvider(LLMProvider):
    """Claude API Provider"""
    
    def __init__(self, model: str = DEFAULT_CLAUDE_MODEL):
        self.model = model
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        self.client = None
        
        if self.api_key:
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
            except Exception as e:
                logger.log(f"Claude 클라이언트 초기화 실패: {e}")
    
    def generate(self, messages: list, system_prompt: str = "", max_tokens: int = 4096, temperature: float = 0, format: Optional[BaseModel] = None) -> Optional[str]:
        """Claude API로 텍스트 생성
        
        Note: Claude는 구조화된 출력 format을 지원하지 않으므로 format 파라미터는 무시됩니다.
        구조화된 출력이 필요한 경우 수동으로 JSON 파싱을 해야 합니다.
        """
        if not self.client:
            logger.log("Claude 클라이언트가 초기화되지 않았습니다")
            return None
        
        # format 파라미터 경고 (디버그용)
        if format is not None:
            logger.log("Claude는 구조화된 출력 format을 지원하지 않습니다. format 파라미터가 무시됩니다.")
            
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=messages
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.log(f"Claude API 호출 실패: {e}")
            return None
    
    def is_available(self) -> bool:
        """Claude API 사용 가능 여부 확인"""
        return self.client is not None and self.api_key is not None


class OllamaProvider(LLMProvider):
    """Ollama Provider"""
    
    def __init__(self, model: str = DEFAULT_OLLAMA_MODEL, base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/api/generate"
    
    def generate(self, messages: list, system_prompt: str = "", max_tokens: int = 4096, temperature: float = 0, format: Optional[BaseModel] = None) -> Optional[str]:
        """Ollama API로 텍스트 생성
        
        Args:
            format: Pydantic BaseModel - 제공시 JSON 스키마로 구조화된 출력 강제
        """
        try:
            # messages를 Ollama 형식으로 변환
            prompt = ""
            if system_prompt:
                prompt += f"System: {system_prompt}\n\n"
            
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                prompt += f"{role.capitalize()}: {content}\n"
            
            # Ollama API 데이터 구성
            data = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            # 구조화된 출력을 위한 format 파라미터 추가 (Ollama 0.5.0+)
            if format is not None:
                try:
                    # Pydantic 모델에서 JSON 스키마 추출
                    json_schema = format.model_json_schema()
                    data["format"] = json_schema
                    logger.log(f"구조화된 출력 형식 적용: {format.__name__}")
                except Exception as e:
                    logger.log(f"format 스키마 생성 실패, 일반 모드로 진행: {e}")
            
            response = requests.post(
                self.api_url,
                json=data,
                timeout=10 * 60  # 10분 타임아웃
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                logger.log(f"Ollama API 오류: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.log(f"Ollama API 연결 실패: {e}")
            return None
        except Exception as e:
            logger.log(f"Ollama API 호출 실패: {e}")
            return None
    
    def is_available(self) -> bool:
        """Ollama 서버 사용 가능 여부 확인"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False


class LLMProviderFactory:
    """LLM Provider 팩토리 클래스"""
    
    @staticmethod
    def create_provider(config: Dict[str, Any]) -> Optional[LLMProvider]:
        """설정에 따라 LLM Provider 생성"""
        provider_type = config.get("provider", "ollama").lower()
        model = config.get("model", "")
        
        if provider_type == "claude":
            default_model = "claude-sonnet-4-20250514"
            return ClaudeProvider(model=model or default_model)
        
        elif provider_type == "ollama":
            default_model = "gemma3n:e2b"
            base_url = config.get("base_url", "http://localhost:11434")
            return OllamaProvider(model=model or default_model, base_url=base_url)
        
        else:
            logger.log(f"지원하지 않는 LLM Provider: {provider_type}")
            return None
    
    @staticmethod
    def get_default_provider() -> LLMProvider:
        """기본 Provider 반환 (Claude)"""
        return ClaudeProvider()


# 편의 함수들
def get_llm_provider(set_name: str, accounts_data: Dict[str, Any] = None) -> LLMProvider:
    """계정 설정에 따라 LLM Provider 가져오기"""
    if accounts_data is None:
        from config import load_accounts
        accounts_data = load_accounts()
    
    account_info = accounts_data.get(set_name, {})
    llm_config = account_info.get("llm", {})
    
    if llm_config:
        provider = LLMProviderFactory.create_provider(llm_config)
        if provider and provider.is_available():
            return provider
        else:
            logger.log(f"설정된 LLM Provider를 사용할 수 없어 기본값(Claude)을 사용합니다: {set_name}")
    
    # 기본값으로 Claude 사용
    return LLMProviderFactory.get_default_provider()