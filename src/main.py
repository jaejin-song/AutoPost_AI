#!/usr/bin/env python3
"""
AutoPost AI - SNS 자동화 시스템 메인 실행 파일

주요 기능:
1. 트렌드/뉴스 데이터 수집
2. AI 기반 콘텐츠 생성
3. 다중 SNS 플랫폼 자동 업로드
"""

import asyncio
import argparse
from pathlib import Path
from typing import Optional, List

from src.core.workflow import WorkflowManager
from src.utils.logger import get_logger
from src.utils.config import ConfigManager


logger = get_logger(__name__)


async def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description="AutoPost AI - SNS 자동화 시스템")
    parser.add_argument("--workflow", choices=["daily", "weekly"], 
                       help="실행할 워크플로우 타입")
    parser.add_argument("--account-set", type=str, 
                       help="특정 계정 세트만 실행 (marketing, relationship, health, finance)")
    parser.add_argument("--dry-run", action="store_true", 
                       help="테스트 모드 (실제 발행 없음)")
    parser.add_argument("--config", type=str, default="config",
                       help="설정 파일 디렉토리 경로")
    
    args = parser.parse_args()
    
    try:
        # 설정 로드
        config_manager = ConfigManager(config_dir=args.config)
        
        # 워크플로우 매니저 초기화
        workflow_manager = WorkflowManager(
            config_manager=config_manager,
            dry_run=args.dry_run
        )
        
        # 워크플로우 실행
        if args.workflow == "daily":
            await workflow_manager.run_daily_workflow(account_set=args.account_set)
        elif args.workflow == "weekly":
            await workflow_manager.run_weekly_workflow(account_set=args.account_set)
        else:
            logger.error("워크플로우 타입을 지정해주세요: --workflow daily 또는 --workflow weekly")
            return
            
        logger.info("워크플로우 실행 완료")
        
    except Exception as e:
        logger.error(f"실행 중 오류 발생: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())