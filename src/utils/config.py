"""
설정 관리 유틸리티

환경변수, 계정 정보, 서비스 계정 파일 관리
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from .logger import get_logger


logger = get_logger(__name__)


class ConfigManager:
    """설정 관리 클래스"""
    
    def __init__(self, config_dir: str = 'config'):
        self.config_dir = Path(config_dir)
        self._load_environment()
    
    def _load_environment(self):
        """환경변수 로드"""
        env_file = self.config_dir / '.env'
        if env_file.exists():
            load_dotenv(env_file)
            logger.info(f"환경변수 로드: {env_file}")
        else:
            logger.warning(f"환경변수 파일을 찾을 수 없습니다: {env_file}")
    
    def get_env_var(self, key: str, default: Optional[str] = None) -> str:
        """환경변수 값 얻기"""
        value = os.getenv(key, default)
        if value is None:
            raise ValueError(f"필수 환경변수가 설정되지 않았습니다: {key}")
        return value
    
    def get_service_account_file(self) -> Path:
        """구글 서비스 계정 파일 경로"""
        service_account_file = self.config_dir / 'service_account.json'
        if not service_account_file.exists():
            raise FileNotFoundError(f"서비스 계정 파일을 찾을 수 없습니다: {service_account_file}")
        return service_account_file
    
    def validate_required_env_vars(self) -> bool:
        """필수 환경변수 검증"""
        required_vars = [
            'GOOGLE_SHEETS_ID',
            'NEWS_API_KEY',
            'OLLAMA_BASE_URL',
            'OLLAMA_MODEL'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"누락된 필수 환경변수: {', '.join(missing_vars)}")
            return False
        
        logger.info("모든 필수 환경변수 확인 완료")
        return True