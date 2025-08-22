"""
로깅 유틸리티

전체 애플리케이션에서 사용할 공통 로거 설정
- 파일 및 콘솔 출력
- 로그 레벨 별 포맷팅
- 로그 로테이션
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime


def get_logger(name: str) -> logging.Logger:
    """로거 인스턴스 반환"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # 로그 레벨 설정
        logger.setLevel(logging.INFO)
        
        # 포맷터 설정
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 콘솔 핸들러
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 파일 핸들러 (로그 디렉토리)
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / 'autopost_ai.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def setup_logging(log_level: str = 'INFO', log_file: str = None):
    """전체 로깅 설정"""
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file or 'logs/autopost_ai.log', encoding='utf-8')
        ]
    )