# Python 런타임 베이스 이미지 사용
FROM python:3.9-slim

# 환경 변수 설정 (non-buffered stdout/stderr)
ENV PYTHONUNBUFFERED=True

# Cloud Run이 사용할 포트 설정 (기본 8080)
ENV PORT=8080

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 복사 및 설치
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 애플리케이션 실행 (Gunicorn 사용)
# Gunicorn은 여러 워커를 사용하여 요청을 처리하므로 프로덕션 환경에 더 적합
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--threads", "8", "app:app"]
# app:app 은 app.py 파일의 app 객체를 의미
# --bind 0.0.0.0:$PORT 형식 대신 직접 포트 지정 (Cloud Run이 ENV PORT를 gunicorn에 전달하지 않음)