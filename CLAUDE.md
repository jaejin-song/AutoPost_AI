# AutoPost AI - 프로젝트 컨텍스트

## 프로젝트 개요

AI로 SNS 주제선정부터 포스팅까지 자동화하는 개인용 파이썬 프로그램입니다.

## 워크플로우

1. **데이터 수집**
2. **스프레드 시트 저장**
3. **AI로 뉴스 선정**
4. **AI로 블로그용 글 작성**
5. **글에서 짧은 문구 뽑아서 X/쓰레드용 글 작성**
6. **각 글별로 SNS 업로드**

## 데이터 수집

### 1. 트렌드/키워드 수집

- Google Trends

### 2. 키워드 기반으로 뉴스 수집

- NewsAPI

### 3. 스프레드 시트에 저장

- 뉴스를 스프레드 시트에 저장

## 기술 스택

- **언어**: Python
- **LLM**: Ollama (로컬 LLM)
- **데이터베이스**: 스프레드 시트

## 보안

- 계정 정보는 accounts.yaml 파일로 관리
  - 아래 양식을 따름

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
        access_token: xxxx
        access_token_secret: xxxx
      - platform: threads
        username: marketing_threads_id
        password: marketing_threads_pw
```

- API 키, 스프레드 시트 관련 정보같은 민감한 정보는 .env 파일로 관리

## 데이터베이스 규칙

- 데이터 수집 후 키워드, 뉴스를 형식에 맞게 저장
- 뉴스를 선정해 블로그 글을 작성하면 스프레드 시트 해당 뉴스에 사용했다는 것을 표시

## SNS 운영 규칙

- 주제별로 티스토리, X, 쓰레드 계정을 하나씩 세트로 운영하고 4개의 세트를 운영하는 것으로 시작
  - 4개로 시작하지만 더 늘어날 수도 있고 더 줄어들 수도 있음
- 각 블로그는 스프레드 시트의 뉴스 중에서 자신의 컨셉에 맞는 주제만을 골라서 작성
  - 스프레드 시트에는 블로그별로 해당 주제를 사용했다는 것을 표기

## AI 글 작성 규칙

- 이미지는 사용하지 않고 텍스트로만 글 작성
- 블로그 1개당 하루에 최대 5개의 글만 작성
- **다양한 톤**으로 변주:
  - 블로그용: 정보성/SEO 맞춤 (키워드 밀도 최적화)
  - SNS용: 감정/이슈 환기형 톤 (짧고 공감 유도)
- **중복 방지**: 자동화하면 글이 비슷해지는 문제가 있음 → LLM 프롬프트에 "기존 글과 중복 표현 피하기" 조건 추가
- **콜 투 액션(CTA)** 삽입: "자세한 내용은 블로그에서 👉" 같은 문구는 유입 전환에 핵심
- **계정별 차별화**
  - X: 짧고 자극적, 트렌드 해시태그 적극 활용
  - Threads: 스토리텔링/커뮤니티 대화형 톤
  - 블로그: 깊이 있는 글 + SEO 최적화
    - **뉴스 + 해설 + 의견** 3단 구조 추천
      - 단순 요약보다 "내 생각"이 들어가야 SNS에서 공유·반응이 커짐
      - 로컬 LLM에도 "뉴스 요약 + 추가 해설 + 독자에게 질문 던지기" 프롬프트 적용

## 블로그 컨셉

- **마케팅/온라인 비즈니스**
- 관계/연애
- 건강/웰빙
- 개인 금융

## 프로젝트 구조

```bash
AutoPost_AI/
│── main.py                 # 전체 워크플로우 실행 진입점
│── config.py               # accounts.yaml + .env 로딩
│── requirements.txt        # 필요한 라이브러리 목록
│── .env                    # API 키 등 민감 정보
│── accounts.yaml           # SNS 계정 세트 정보
│
├── data/                   # 수집된 데이터 저장소
│   ├── news/               # 뉴스 원본 저장
│   └── posts/              # 생성된 글/문구 저장
│
├── modules/                # 핵심 기능 모듈
│   ├── collect/            # 데이터 수집 단계
│   │   ├── google_trends.py
│   │   └── news_api.py
│   │
│   ├── storage/            # 스프레드시트/DB 관련
│   │   └── spreadsheet.py
│   │
│   ├── ai/                 # LLM 관련 기능
│   │   ├── content_writer.py   # 블로그 글 작성
│   │   └── post_writer.py      # SNS용 짧은 글 작성
│   │
│   ├── publisher/          # SNS/블로그 업로드
│   │   ├── tistory.py
│   │   ├── x.py
│   │   ├── threads.py
│   │   └── runner.py   # 계정 세트별 게시 실행기
│   │
│   └── utils/              # 공통 유틸
│       ├── logger.py
│       └── helpers.py
│
└── tests/                  # 간단한 테스트 코드
    ├── test_ai.py
    ├── test_collect.py
    └── test_publish.py
```

## 역할 설명

- **main.py**
  → "오늘의 뉴스 → 블로그 글 생성 → SNS 글 생성 → 업로드" 워크플로우 실행

- **modules/collect**
  → 트렌드 키워드, 뉴스 기사 수집 담당

- **modules/storage**
  → 스프레드시트에 데이터 기록/조회

- **modules/ai**
  → LLM을 불러서 글 생성/키워드 생성/중복 방지 처리

- **modules/publisher**
  → 티스토리, X, 쓰레드 등에 업로드 담당

- **modules/utils**
  → 로깅, 공통 함수

- **data/**
  → 뉴스 원문, 생성된 포스팅 저장 (실패시 복구 가능)
