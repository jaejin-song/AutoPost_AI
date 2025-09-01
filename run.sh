#!/bin/bash

# AutoPost AI 실행 스크립트
# 가상환경 활성화 후 main.py 실행

echo "🚀 AutoPost AI 시작 중..."

# 스크립트가 있는 디렉토리로 이동
cd "$(dirname "$0")"

# 가상환경 활성화
if [ -d ".venv" ]; then
    echo "📦 가상환경 활성화 중..."
    source .venv/bin/activate
else
    echo "❌ 가상환경(.venv)을 찾을 수 없습니다."
    echo "다음 명령으로 가상환경을 생성하세요:"
    echo "python3 -m venv .venv"
    echo "source .venv/bin/activate"
    echo "pip install -r requirements.txt"
    exit 1
fi

# 의존성 확인
if [ -f "requirements.txt" ]; then
    echo "📋 의존성 확인 중..."
    pip install -r requirements.txt --quiet
fi

# main.py 실행
echo "▶️ AutoPost AI 실행..."
python main.py

echo "✅ AutoPost AI 완료"