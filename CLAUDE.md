# AutoPost AI - 프로젝트 컨텍스트

## 프로젝트 개요

AI로 SNS 주제선정부터 포스팅까지 자동화하는 개인용 파이썬 프로그램입니다.

## 워크플로우

1. **데이터 수집**: Google Trends, NewsAPI를 통한 트렌드/뉴스 수집
2. **스프레드시트 저장**: 수집된 데이터를 구글 스프레드시트에 저장
3. **AI로 뉴스 선정**: Ollama(로컬 LLM)로 주제에 맞는 뉴스 선별
4. **AI로 블로그용 글 작성**: 선정된 뉴스 기반으로 블로그 포스트 생성
5. **SNS용 글 작성**: 블로그 글에서 짧은 문구 추출하여 X/쓰레드용 글 생성
6. **SNS 업로드**: 각 플랫폼별로 자동 업로드

## 기술 스택

- **언어**: Python
- **LLM**: Ollama (로컬 LLM)
- **데이터베이스**: Google Spreadsheet
- **자동화**: Playwright (웹 자동화)
- **API**: NewsAPI, Twitter API, Threads API

## 데이터 수집 규칙

### 트렌드/키워드 수집
- Google Trends API 활용
- 한국 지역 기준으로 트렌딩 키워드 수집

### 뉴스 수집
- NewsAPI를 통한 키워드 기반 뉴스 수집
- 한국어 뉴스 우선 수집
- 최신순 정렬로 관련성 높은 뉴스 선별

### 스프레드시트 저장
- 수집된 뉴스는 구글 스프레드시트에 체계적으로 저장
- 뉴스 사용 여부를 계정별로 추적 관리

## 계정 관리

accounts.yaml 파일로 계정 정보를 관리합니다:

```yaml
account_sets:
  marketing:
    topic: "마케팅"
    description: "마케팅 관련 콘텐츠 계정 세트"
    accounts:
      - platform: tistory
        username: marketing_blog_id
        password: marketing_blog_pw
        blog_url: https://marketing-blog.tistory.com
      - platform: x
        username: marketing_x_id
        password: marketing_x_pw
        api_key: xxxx
        api_secret: xxxx
        access_token: xxxx
        access_token_secret: xxxx
      - platform: threads
        username: marketing_threads_id
        password: marketing_threads_pw
```

## SNS 운영 규칙

### 계정 구조
- 주제별로 티스토리, X, 쓰레드 계정을 하나씩 세트로 운영
- 현재 4개 세트로 시작 (확장 가능)
- 각 블로그는 자신의 컨셉에 맞는 주제만 선별하여 작성

### 블로그 컨셉 (4개 세트)
1. **마케팅/온라인 비즈니스**
2. **관계/연애**
3. **건강/웰빙**
4. **개인 금융**

## AI 글 작성 규칙

### 기본 원칙
- 이미지는 사용하지 않고 텍스트로만 글 작성
- 블로그 1개당 하루에 최대 5개의 글만 작성
- 중복 방지를 위한 다양한 표현 활용

### 톤 앤 매너
- **블로그용**: 정보성/SEO 맞춤 (키워드 밀도 최적화)
- **SNS용**: 감정/이슈 환기형 톤 (짧고 공감 유도)

### 플랫폼별 차별화
- **X**: 짧고 자극적, 트렌드 해시태그 적극 활용
- **Threads**: 스토리텔링/커뮤니티 대화형 톤  
- **블로그**: 깊이 있는 글 + SEO 최적화
  - **뉴스 + 해설 + 의견** 3단 구조
  - 단순 요약보다 "내 생각"이 포함된 독창적인 콘텐츠

### 콜 투 액션 (CTA)
- SNS 글에 블로그 유입을 위한 CTA 문구 삽입
- 예: "자세한 내용은 블로그에서 👉"

### 중복 방지
- LLM 프롬프트에 "기존 글과 중복 표현 피하기" 조건 추가
- 계정별 글 작성 이력을 바탕으로 유사성 검증

## 데이터베이스 관리 규칙

- 뉴스 수집 후 키워드, 뉴스를 구조화된 형식으로 저장
- 뉴스 사용 시 해당 계정에서 사용했다는 플래그 표시
- 중복 사용 방지를 위한 추적 시스템 구축

## 개발 시 고려사항

### 보안
- API 키와 계정 정보는 .env 파일로 분리 관리
- .gitignore에 민감 정보 파일 추가

### 확장성
- 새로운 계정 세트 추가가 용이한 구조
- 새로운 플랫폼 지원 시 모듈식 확장 가능

### 안정성
- API 호출 실패 시 재시도 로직
- 로그 시스템을 통한 실행 과정 추적
- 예외 처리를 통한 안정적인 자동화 운영

## 실행 방법

```bash
# 일별 워크플로우 실행
python src/main.py --workflow daily

# 주별 워크플로우 실행  
python src/main.py --workflow weekly

# 특정 계정 세트만 실행
python src/main.py --account-set marketing

# 테스트 모드 (실제 발행 없음)
python src/main.py --dry-run
```