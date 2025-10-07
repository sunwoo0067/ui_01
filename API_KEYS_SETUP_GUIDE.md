# 마켓플레이스 API 키 설정 가이드

## 📋 개요
이 문서는 마켓플레이스 판매자 API 키를 설정하는 방법을 안내합니다.

## 🔑 API 키 발급 방법

### 1. 쿠팡 Wing API
**발급 URL**: https://wing.coupang.com/

**필요한 정보**:
- `COUPANG_ACCESS_KEY`: Wing API Access Key
- `COUPANG_SECRET_KEY`: Wing API Secret Key
- `COUPANG_VENDOR_ID`: 판매자 Vendor ID

**발급 절차**:
1. 쿠팡 Wing 판매자 센터 로그인
2. 설정 → API 설정 메뉴 이동
3. 액세스 키 생성
4. Access Key, Secret Key, Vendor ID 복사

---

### 2. 네이버 스마트스토어 API
**발급 URL**: https://commerce.naver.com/

**필요한 정보**:
- `NAVER_CLIENT_ID`: 애플리케이션 Client ID
- `NAVER_CLIENT_SECRET`: 애플리케이션 Client Secret
- `NAVER_ACCESS_TOKEN`: OAuth 2.0 Access Token (선택사항)

**발급 절차**:
1. 네이버 커머스 API 관리 페이지 이동
2. 애플리케이션 등록
3. Client ID, Client Secret 발급
4. (필요시) OAuth 2.0 인증 후 Access Token 발급

---

### 3. 11번가 OpenAPI
**발급 URL**: https://openapi.11st.co.kr/

**필요한 정보**:
- `ELEVENST_API_KEY`: 11번가 OpenAPI Key

**발급 절차**:
1. 11번가 OpenAPI 사이트 회원가입
2. 판매자 인증
3. API 키 발급 신청
4. 승인 후 API 키 수령

---

### 4. 지마켓 API (미발급)
**필요한 정보**:
- `GMARKET_API_KEY`: 지마켓 API Key

**상태**: API 키 미발급
**참고**: 판매자 센터 문의 필요

---

### 5. 옥션 API (미발급)
**필요한 정보**:
- `AUCTION_API_KEY`: 옥션 API Key

**상태**: API 키 미발급
**참고**: 판매자 센터 문의 필요

---

## ⚙️ 환경 변수 설정

### 방법 1: `.env` 파일 생성
프로젝트 루트에 `.env` 파일을 생성하고 다음 형식으로 입력:

```bash
# 쿠팡 Wing API
COUPANG_ACCESS_KEY=your_access_key_here
COUPANG_SECRET_KEY=your_secret_key_here
COUPANG_VENDOR_ID=your_vendor_id_here
COUPANG_ACCOUNT_NAME=쿠팡 메인 계정

# 네이버 스마트스토어 API
NAVER_CLIENT_ID=your_client_id_here
NAVER_CLIENT_SECRET=your_client_secret_here
NAVER_ACCESS_TOKEN=your_access_token_here
NAVER_ACCOUNT_NAME=네이버 메인 계정

# 11번가 OpenAPI
ELEVENST_API_KEY=your_api_key_here
ELEVENST_ACCOUNT_NAME=11번가 메인 계정

# 지마켓 API (선택)
GMARKET_API_KEY=
GMARKET_ACCOUNT_NAME=지마켓 메인 계정

# 옥션 API (선택)
AUCTION_API_KEY=
AUCTION_ACCOUNT_NAME=옥션 메인 계정
```

### 방법 2: 시스템 환경 변수 설정
Windows PowerShell:
```powershell
$env:COUPANG_ACCESS_KEY="your_access_key_here"
$env:COUPANG_SECRET_KEY="your_secret_key_here"
$env:COUPANG_VENDOR_ID="your_vendor_id_here"
```

---

## 🚀 계정 등록 실행

### 자동 등록 (권장)
```bash
python setup_marketplace_accounts_auto.py
```
- 환경 변수에서 API 키를 자동으로 읽어 데이터베이스에 저장
- 이미 등록된 계정은 건너뜀

### 수동 등록 (대화형)
```bash
python setup_marketplace_accounts.py
```
- 대화형 프롬프트로 API 키 입력
- 각 마켓플레이스별로 개별 설정

---

## 🧪 테스트 실행

### 1. API 키 확인
```bash
python check_api_keys.py
```

### 2. 통합 테스트
```bash
python test_marketplace_seller_integration.py
```
- 인증 테스트
- 상품 등록 테스트
- 재고 동기화 테스트
- 주문 동기화 테스트
- 요약 통계 테스트

---

## 📊 현재 상태 확인

### 등록된 마켓플레이스 확인
```bash
python check_accounts.py
```

---

## ⚠️ 주의사항

1. **API 키 보안**
   - `.env` 파일은 절대 Git에 커밋하지 마세요
   - `.gitignore`에 `.env`가 포함되어 있는지 확인하세요

2. **API 사용 제한**
   - 각 마켓플레이스는 API 호출 제한이 있습니다
   - 테스트 시 제한을 초과하지 않도록 주의하세요

3. **개발 환경 전용**
   - 이 도구는 로컬 개발 환경에서만 사용하세요
   - 실제 운영 환경에서는 보안 강화가 필요합니다

---

## 📞 문의

- 쿠팡 Wing API: https://wing-support.coupang.com/
- 네이버 커머스 API: https://commerce-api.naver.com/
- 11번가 OpenAPI: https://openapi.11st.co.kr/support/

