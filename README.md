# Google Custom Search API 데모 (Cloud Run + 서비스 계정 인증)

이 프로젝트는 Google Cloud Run에서 실행되는 Python Flask 백엔드를 사용하여 Google Custom Search JSON API를 호출하는 방법을 보여주는 웹 데모 애플리케이션입니다. 특히, API 키 대신 **서비스 계정(Service Account)** 을 사용하여 Google Cloud 환경 내에서 안전하게 API를 인증하는 방법을 중점적으로 다룹니다.

사용자는 웹 페이지의 검색창에 검색어를 입력하고, 백엔드는 이 요청을 받아 서비스 계정의 권한으로 Custom Search API를 호출한 후, 그 결과를 다시 웹 페이지에 표시합니다.

## 주요 특징

*   Flask 웹 프레임워크 기반 백엔드
*   Docker를 사용한 컨테이너화
*   Google Cloud Run을 이용한 서버리스 배포
*   **서비스 계정(Service Account)** 을 통한 안전한 API 인증 (API 키 불필요)
*   간단한 HTML/JavaScript 프론트엔드

## 목차

1.  [서비스 계정(SA) vs API 키](#서비스-계정sa-vs-api-키)
2.  [사전 준비 사항](#사전-준비-사항)
3.  [환경 변수 설정](#환경-변수-설정)
4.  [프로젝트 구조 및 파일 설명](#프로젝트-구조-및-파일-설명)
5.  [빌드 및 배포 방법](#빌드-및-배포-방법)
6.  [데모 테스트](#데모-테스트)

## 서비스 계정(SA) vs API 키

Google API 인증에는 여러 방법이 있지만, 이 프로젝트에서는 서비스 계정을 사용했습니다. Google Cloud 환경에서 실행되는 애플리케이션의 경우 서비스 계정 사용이 권장되는 방식입니다.

**서비스 계정(SA) 사용 시 이점:**

*   **보안 강화:**
    *   API 키와 같은 비밀 정보를 코드나 설정 파일에 직접 포함할 필요가 없습니다.
    *   Cloud Run과 같은 GCP 환경에서는 연결된 서비스 계정의 임시 자격 증명(Access Token)을 메타데이터 서버를 통해 안전하게 자동으로 가져옵니다. 이 토큰은 수명이 짧아 탈취 위험이 적습니다.
*   **세분화된 권한 관리:** Google Cloud IAM(Identity and Access Management)을 통해 서비스 계정에 필요한 최소한의 역할(Role)만 부여할 수 있습니다 (최소 권한 원칙). API 키는 일반적으로 특정 API에 대한 접근 자체만 제어합니다.
*   **자동화된 자격 증명 관리:** Google Cloud 클라이언트 라이브러리(`google-auth` 등)가 환경(예: Cloud Run, GCE)을 감지하고 자동으로 적절한 자격 증명을 찾아 사용하므로 개발이 편리합니다.

## 사전 준비 사항

이 데모를 실행하려면 다음 사항들이 준비되어 있어야 합니다.

1.  **Google Cloud Project:** 데모를 배포할 Google Cloud 프로젝트가 필요합니다.
2.  **API 활성화:** Google Cloud Console에서 다음 API를 활성화해야 합니다:
    *   Custom Search API
    *   Cloud Run API
    *   Artifact Registry API
    *   IAM Service Account Credentials API (서비스 계정이 다른 API와 상호작용하기 위해 내부적으로 필요할 수 있음)
3.  **서비스 계정(Service Account) 생성:**
    *   IAM 및 관리자 > 서비스 계정 메뉴에서 새 서비스 계정을 생성합니다. (예: `custom-search-runner`)
    *   **별도의 키(JSON) 파일 다운로드는 필요 없습니다.** Cloud Run에 직접 연결할 것입니다.
4.  **서비스 계정에 역할 부여:** 생성한 서비스 계정에 Custom Search API를 사용할 권한을 부여해야 합니다. IAM 페이지에서 서비스 계정을 선택하고 다음 역할 중 하나를 추가합니다:
    *   `서비스 사용량 소비자 (roles/serviceusage.serviceUsageConsumer)`: 가장 간단하며 여러 Google API 사용 권한을 포함합니다.
    *   (더 세분화된 제어를 원할 경우 Custom Role 생성 가능)
5.  **Custom Search Engine (CSE) 생성:**
    *   [Programmable Search Engine](https://programmablesearchengine.google.com/controlpanel/all) 페이지에서 새 검색 엔진을 만듭니다.
    *   검색할 사이트(예: 전체 웹 또는 특정 사이트)를 지정합니다.
    *   생성된 **검색 엔진 ID (CSE ID)** 를 복사해 둡니다. 이 ID는 이후 환경 변수로 사용됩니다.

##  환경 변수 설정

Cloud Shell 또는 로컬 터미널에서 빌드 및 배포를 진행하기 전에 다음 환경 변수를 설정해야 합니다. 실제 값으로 변경해 주세요.

```bash
export PROJECT_ID="YOUR_PROJECT_ID"                             # 본인의 Google Cloud 프로젝트 ID
export REGION="asia-northeast3"                                 # 배포할 리전 (예: 서울)
export SERVICE_NAME="custom-search-demo"                        # Cloud Run 서비스 이름
export IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/YOUR_REPO_NAME/${SERVICE_NAME}:v1" # Artifact Registry 이미지 경로
export SERVICE_ACCOUNT_EMAIL="YOUR_SERVICE_ACCOUNT_EMAIL"       # 생성한 서비스 계정 이메일 주소
export CUSTOM_SEARCH_ENGINE_ID="YOUR_CSE_ID"                    # Custom Search Engine 생성 후 얻은 ID
```

##  프로젝트 구조 및 파일 설명
```bash
.
├── app.py              # Flask 백엔드 애플리케이션 로직
├── Dockerfile          # 애플리케이션 컨테이너 이미지 빌드 정의
├── requirements.txt    # Python 의존성 라이브러리 목록
└── templates/
    └── index.html      # 사용자 인터페이스 (HTML, CSS, JavaScript)
```

app.py:

Flask 애플리케이션 인스턴스를 생성합니다.

루트 경로(/) 요청 시 templates/index.html 파일을 렌더링하여 반환합니다.

/search 경로로 GET 요청이 오면, q 파라미터(검색어)를 받아옵니다.

google-auth 라이브러리를 사용하여 환경(Cloud Run)에서 자동으로 서비스 계정 자격 증명을 가져옵니다.

google-api-python-client를 사용하여 Custom Search API 클라이언트를 빌드합니다.

환경 변수로 설정된 CSE_ID와 검색어를 사용하여 Custom Search API를 호출합니다.

결과를 JSON 형식으로 가공하여 반환합니다.

Dockerfile:

Python 3.9 슬림 이미지를 기반으로 합니다.

requirements.txt에 명시된 라이브러리들을 설치합니다.

애플리케이션 코드(현재 디렉토리의 모든 파일)를 이미지 안의 /app 디렉토리로 복사합니다.

gunicorn WSGI 서버를 사용하여 app.py의 Flask 앱을 실행합니다. (Cloud Run 환경에 적합)

requirements.txt:

애플리케이션 실행에 필요한 Python 라이브러리 목록입니다 (Flask, google-api-python-client, google-auth, gunicorn, Flask-Cors).

templates/index.html:

검색어 입력 필드, 검색 버튼, 결과 표시 영역을 포함하는 간단한 HTML 구조입니다.

기본적인 CSS 스타일링이 포함되어 있습니다.

JavaScript 코드가 포함되어 있습니다:

검색 버튼 클릭 또는 Enter 키 입력 시 performSearch 함수를 호출합니다.

현재 페이지의 상대 경로인 /search 엔드포인트로 검색어를 포함하여 GET 요청을 보냅니다.

백엔드로부터 받은 JSON 응답을 파싱하여 결과를 HTML 형식으로 동적으로 생성하고 페이지에 표시합니다.

로딩 상태 및 오류 메시지를 표시하는 기능도 포함합니다.

빌드 및 배포 방법

(Cloud Shell 또는 gcloud 및 docker가 설치된 로컬 환경에서 진행)

프로젝트 폴더로 이동: cd 명령어를 사용하여 이 README 파일이 있는 프로젝트의 루트 폴더로 이동합니다.

gcloud 설정: (필요시) 사용할 프로젝트와 리전을 설정합니다.

gcloud config set project ${PROJECT_ID}
gcloud config set run/region ${REGION}
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

Docker 이미지 빌드:

docker build -t ${IMAGE_NAME} .
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

Docker 인증 설정: (Container Registry 또는 Artifact Registry에 푸시하기 위해 필요)

# Artifact Registry 사용 시 (예: asia-northeast3 리전)
# gcloud auth configure-docker ${REGION}-docker.pkg.dev
# Container Registry 사용 시
gcloud auth configure-docker
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

Docker 이미지 푸시:

docker push ${IMAGE_NAME}
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

Cloud Run 서비스 배포:

gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --service-account ${SERVICE_ACCOUNT_EMAIL} \
  --set-env-vars "CSE_ID=${CUSTOM_SEARCH_ENGINE_ID}" \
  --allow-unauthenticated \
  --region ${REGION}
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

--image: 방금 푸시한 Docker 이미지 경로.

--platform managed: 서버리스 환경 지정.

--service-account: 중요! 사전 준비 단계에서 생성하고 권한을 부여한 서비스 계정 이메일. 이 계정의 권한으로 코드가 실행됩니다.

--set-env-vars: CSE_ID 값을 환경 변수로 컨테이너에 전달합니다. app.py에서 이 값을 읽습니다.

--allow-unauthenticated: 데모 목적으로 인증 없이 누구나 웹 페이지에 접근할 수 있도록 허용합니다. 실제 프로덕션 환경에서는 필요에 따라 인증 설정을 강화해야 합니다.

배포가 완료되면 서비스 URL이 출력됩니다.

데모 테스트

Cloud Run 배포 후 출력된 서비스 URL을 웹 브라우저 주소창에 입력하여 접속합니다.

"Google Custom Search Demo (Cloud Run)" 제목과 함께 검색창이 나타납니다.

검색창에 원하는 검색어(예: "007")를 입력하고 "검색" 버튼을 클릭하거나 Enter 키를 누릅니다.

"검색 중..." 메시지가 잠시 나타난 후, 검색 결과가 아래에 제목, 링크, 요약(snippet) 형태로 표시됩니다.

만약 오류가 발생하면, 오류 메시지가 화면에 표시됩니다. (Cloud Run 로그나 브라우저 개발자 도구 콘솔에서 더 자세한 내용을 확인할 수 있습니다.)

참고: Google Cloud 서비스 사용 시 비용이 발생할 수 있습니다. 특히 Custom Search API는 무료 할당량을 초과하면 요금이 부과됩니다. Cloud Run 또한 사용량에 따라 비용이 발생할 수 있습니다. 데모 사용 후 불필요한 리소스는 삭제하는 것이 좋습니다.

IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
IGNORE_WHEN_COPYING_END
