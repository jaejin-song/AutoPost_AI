"""
계정 관리 모듈

4개 주제별 계정 세트 관리:
- marketing: 마케팅/온라인 비즈니스
- relationship: 관계/연애  
- health: 건강/웰빙
- finance: 개인 금융
"""

from typing import Dict, List, Optional
import yaml
from pathlib import Path

from ..utils.logger import get_logger
from ..utils.config import ConfigManager


logger = get_logger(__name__)


class AccountManager:
    """계정 관리 클래스"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.accounts_data = self._load_accounts_config()
    
    def _load_accounts_config(self) -> Dict:
        """계정 설정 파일 로드"""
        try:
            accounts_file = Path(self.config_manager.config_dir) / "accounts.yaml"
            
            if not accounts_file.exists():
                raise FileNotFoundError(f"계정 설정 파일을 찾을 수 없습니다: {accounts_file}")
            
            with open(accounts_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            logger.info(f"계정 설정 로드 완료: {len(data.get('account_sets', {}))}개 세트")
            return data
            
        except Exception as e:
            logger.error(f"계정 설정 로드 실패: {e}")
            raise
    
    def get_account_set(self, account_set_name: str) -> Dict:
        """특정 계정 세트 정보 반환"""
        account_sets = self.accounts_data.get('account_sets', {})
        
        if account_set_name not in account_sets:
            available_sets = list(account_sets.keys())
            raise ValueError(f"존재하지 않는 계정 세트: {account_set_name}. "
                           f"사용 가능한 세트: {available_sets}")
        
        return account_sets[account_set_name]
    
    def get_all_account_sets(self) -> Dict:
        """모든 계정 세트 정보 반환"""
        return self.accounts_data.get('account_sets', {})
    
    def get_accounts_by_platform(self, platform: str) -> List[Dict]:
        """특정 플랫폼의 모든 계정 반환"""
        accounts = []
        
        for account_set_name, account_set in self.get_all_account_sets().items():
            for account in account_set.get('accounts', []):
                if account.get('platform') == platform:
                    account_with_set = account.copy()
                    account_with_set['account_set'] = account_set_name
                    account_with_set['topic'] = account_set.get('topic')
                    accounts.append(account_with_set)
        
        return accounts
    
    def get_account(self, account_set_name: str, platform: str) -> Optional[Dict]:
        """특정 계정 세트의 특정 플랫폼 계정 반환"""
        account_set = self.get_account_set(account_set_name)
        
        for account in account_set.get('accounts', []):
            if account.get('platform') == platform:
                return account
        
        return None
    
    def validate_account_sets(self) -> bool:
        """계정 세트 유효성 검증"""
        required_platforms = {'tistory', 'x', 'threads'}
        valid = True
        
        for account_set_name, account_set in self.get_all_account_sets().items():
            # 필수 필드 확인
            if not account_set.get('topic'):
                logger.error(f"계정 세트 '{account_set_name}'에 topic이 없습니다")
                valid = False
            
            # 플랫폼 완성도 확인
            platforms = {acc.get('platform') for acc in account_set.get('accounts', [])}
            missing_platforms = required_platforms - platforms
            
            if missing_platforms:
                logger.warning(f"계정 세트 '{account_set_name}'에 누락된 플랫폼: {missing_platforms}")
            
            # 계정 정보 유효성 확인
            for account in account_set.get('accounts', []):
                if not self._validate_account(account):
                    logger.error(f"유효하지 않은 계정: {account}")
                    valid = False
        
        return valid
    
    def _validate_account(self, account: Dict) -> bool:
        """개별 계정 유효성 검증"""
        required_fields = {'platform', 'username'}
        
        # 필수 필드 확인
        if not all(field in account for field in required_fields):
            return False
        
        # 플랫폼별 추가 필드 확인
        platform = account.get('platform')
        
        if platform == 'tistory':
            return 'blog_url' in account
        elif platform == 'x':
            # API 키 정보가 있어야 함 (선택적으로 password도 허용)
            return any(key in account for key in ['api_key', 'password'])
        elif platform == 'threads':
            return 'password' in account
        
        return True