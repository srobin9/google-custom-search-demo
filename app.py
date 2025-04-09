import os
import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
# render_template 추가
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
# CORS는 이제 필요 없을 수 있지만, 혹시 다른 도메인에서 테스트할 경우를 대비해 남겨둘 수 있습니다.
CORS(app)

# --- 기존 Custom Search API 관련 설정 (동일) ---
CSE_ID = os.environ.get('CSE_ID', 'YOUR_DEFAULT_CSE_ID')

try:
    credentials, project = google.auth.default(scopes=['https://www.googleapis.com/auth/cse'])
    service = build("customsearch", "v1", credentials=credentials) if credentials else None
except google.auth.exceptions.DefaultCredentialsError:
    print("경고: 기본 자격 증명을 찾을 수 없습니다.")
    service = None
except Exception as e:
    print(f"API 서비스 빌드 중 오류 발생: {e}")
    service = None
# --- 여기까지 동일 ---

# 루트 경로 ('/') 요청 시 index.html 렌더링
@app.route('/')
def index():
    # templates 폴더의 index.html 파일을 렌더링하여 반환
    return render_template('index.html')

# 기존 검색 API 경로 ('/search')
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "검색어 'q' 파라미터가 필요합니다."}), 400

    if not service:
         return jsonify({"error": "Custom Search API 서비스가 초기화되지 않았습니다."}), 500

    if not CSE_ID or CSE_ID == 'YOUR_DEFAULT_CSE_ID':
         return jsonify({"error": "CSE ID가 설정되지 않았습니다. 환경 변수를 확인하세요."}), 500

    try:
        result = service.cse().list(
            q=query,
            cx=CSE_ID,
            num=10
        ).execute()

        items = []
        if 'items' in result:
            for item in result.get('items', []):
                items.append({
                    'title': item.get('title'),
                    'link': item.get('link'),
                    'snippet': item.get('snippet')
                })
        return jsonify(items)

    except HttpError as e:
        print(f"API 호출 중 오류 발생: {e}")
        return jsonify({"error": f"Custom Search API 호출 실패: {e.resp.status} {e._get_reason()}"}), 500
    except Exception as e:
        print(f"처리 중 예상치 못한 오류 발생: {e}")
        return jsonify({"error": "서버 내부 오류 발생"}), 500

# --- __main__ 부분 (Gunicorn 사용을 위해 변경 없음) ---
if __name__ == '__main__':
    # Cloud Run 배포 시에는 Dockerfile의 CMD에서 gunicorn을 실행
    pass