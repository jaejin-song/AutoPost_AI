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

# Ollama 서버 시작
echo "🦙 Ollama 서버 시작 중..."
if command -v ollama &> /dev/null; then
    # Ollama가 이미 실행 중인지 확인
    if ! pgrep -f "ollama serve" > /dev/null; then
        echo "🔄 Ollama 서버를 백그라운드에서 시작합니다..."
        ollama serve &
        OLLAMA_PID=$!
        
        # Ollama 서버가 준비될 때까지 대기
        echo "⏳ Ollama 서버 준비 대기 중..."
        sleep 3
        
        # 서버 상태 확인
        max_attempts=10
        attempt=1
        while [ $attempt -le $max_attempts ]; do
            if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
                echo "✅ Ollama 서버가 준비되었습니다."
                break
            fi
            echo "⏳ Ollama 서버 대기 중... (시도 $attempt/$max_attempts)"
            sleep 2
            attempt=$((attempt + 1))
        done
        
        if [ $attempt -gt $max_attempts ]; then
            echo "⚠️ Ollama 서버 시작에 시간이 걸리고 있습니다. 계속 진행합니다."
        fi
    else
        echo "✅ Ollama 서버가 이미 실행 중입니다."
    fi
else
    echo "⚠️ Ollama가 설치되지 않았습니다. Claude만 사용됩니다."
fi

# main.py 실행
echo "▶️ AutoPost AI 실행..."
python main.py

# 정리 작업
if [ ! -z "$OLLAMA_PID" ]; then
    echo "🧹 Ollama 서버 종료 중..."
    kill $OLLAMA_PID 2>/dev/null || true
fi

echo "✅ AutoPost AI 완료"