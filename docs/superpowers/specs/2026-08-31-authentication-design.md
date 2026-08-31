# 사용자 인증 및 게임 소유권 설계

## 1. 개요

보험회사 운영 시뮬레이션에 일반 회원 시스템을 추가한다. 사용자는 이메일과 비밀번호로 가입·로그인하고, 자신의 여러 기기에서 게임 기록을 이어서 플레이할 수 있어야 한다. 로그인하지 않은 사용자는 게임 데이터와 게임 진행 API에 접근할 수 없어야 한다.

이 기능은 기존의 전역 게임 목록 구조를 사용자별 게임 소유권 구조로 변경한다. 인증은 FastAPI 서버 세션과 HttpOnly 쿠키를 사용하고, 운영 데이터베이스는 Render PostgreSQL로 전환한다.

## 2. 목표와 범위

### 목표

- 이메일/비밀번호 회원가입
- 로그인 상태 유지 및 로그아웃
- 사용자별 게임 생성·조회·진행·삭제
- 여러 기기에서 동일 계정으로 게임 이어하기
- Render 공개 배포 환경에서 안전한 쿠키 인증
- SQLite에서 PostgreSQL로의 명시적인 스키마 마이그레이션

### 1차 범위에 포함하지 않는 것

- 소셜 로그인
- 이메일 인증
- 비밀번호 재설정 및 변경
- 관리자 계정·관리자 화면
- 다중 사용자 게임 공유
- 완전한 CAPTCHA 기반 봇 방어

## 3. 선택한 접근 방식

### 서버 세션 + HttpOnly 쿠키

로그인 성공 시 서버가 충분한 길이의 암호학적 난수 세션 토큰을 생성한다. 브라우저에는 원본 토큰을 `HttpOnly`, `Secure`, `SameSite=None` 쿠키로 저장하고, 데이터베이스에는 토큰의 SHA-256 해시만 저장한다. 이후 요청에서 서버는 쿠키를 해시하여 유효한 세션과 사용자 계정을 조회한다.

이 방식은 게임 데이터가 서버 데이터베이스에 저장되는 현재 구조와 맞고, 로그아웃·세션 강제 만료·계정 비활성화가 쉽다. JWT를 클라이언트에 저장하는 방식은 토큰 폐기와 권한 변경 처리가 더 복잡하므로 사용하지 않는다.

## 4. 시스템 구성

### 백엔드

- `app/models.py`: `UserRow`, `SessionRow` 추가, `GameRow.user_id` 추가
- `app/schemas.py`: 인증 요청·응답 스키마 추가
- `app/auth.py`: 비밀번호 해시, 세션 토큰 생성·해시, 현재 사용자 의존성
- `app/api/auth.py`: 회원가입·로그인·로그아웃·현재 사용자 API
- `app/api/games.py`: 모든 게임 엔드포인트에 현재 사용자 및 소유권 검사 적용
- `app/db.py`: PostgreSQL URL 처리 및 테스트 가능한 엔진 초기화
- Alembic: 운영 및 개발 DB 스키마 마이그레이션

게임 엔진(`backend/app/engine/`)은 인증이나 데이터베이스를 import하지 않는다. 인증과 소유권 검사는 API 계층에서 수행하고, 게임 생성·진행의 DB 반영은 기존 repository 계층을 유지한다.

### 프론트엔드

- `src/views/LoginView.vue`: 로그인 화면
- `src/views/RegisterView.vue`: 회원가입 화면
- `src/stores/authStore.js`: 사용자 및 초기 인증 상태 관리
- `src/api/client.js`: `withCredentials`, 인증 API, 401 처리
- `src/main.js`: `/login`, `/register` 라우트와 인증 라우트 가드
- `src/App.vue` 또는 공통 헤더: 현재 사용자 이메일 및 로그아웃 UI

## 5. 데이터 모델

### users

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| id | integer | PK | 사용자 ID |
| email | varchar | unique, not null | 정규화한 소문자 이메일 |
| password_hash | varchar | not null | Argon2 해시 |
| is_active | boolean | not null, default true | 계정 사용 가능 여부 |
| created_at | timestamp | not null | 생성 시각 |
| updated_at | timestamp | not null | 수정 시각 |

### sessions

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| id | integer | PK | 세션 ID |
| user_id | integer | FK users.id, index | 세션 소유자 |
| token_hash | varchar | unique, not null | 쿠키 토큰의 SHA-256 해시 |
| expires_at | timestamp | index, not null | 만료 시각 |
| created_at | timestamp | not null | 발급 시각 |
| last_used_at | timestamp | not null | 마지막 사용 시각 |

세션 만료 기간은 발급 시점부터 30일이다. 만료 세션은 인증 조회 시 무효화하고, 별도의 정리 작업이 가능하도록 인덱스를 둔다.

### login_attempts

로그인 무차별 대입을 제한하기 위해 실패 시도도 PostgreSQL에 기록한다.

| 컬럼 | 타입 | 제약 | 설명 |
|---|---|---|---|
| id | integer | PK | 시도 ID |
| normalized_email | varchar | index, not null | 정규화한 로그인 이메일 |
| client_ip | varchar | index, not null | 요청 IP |
| attempted_at | timestamp | index, not null | 실패 시각 |

같은 이메일·IP 조합에 대해 최근 15분 동안 실패가 5회 이상이면 추가 로그인을 429로 거부한다. 성공 로그인 시 해당 조합의 오래된 실패 기록을 정리한다. 실패 기록은 24시간이 지난 뒤 정리할 수 있다.

### games 변경

`games.user_id`를 `users.id`에 연결하는 필수 외래 키로 추가한다. 기존 SQLite 게임 데이터에는 소유자를 안전하게 자동 추정할 수 없으므로, 인증 기능 배포 전 개발 DB는 재생성하고 운영 데이터가 있는 경우 별도 데이터 이전 절차를 수행한다. 임의의 사용자에게 기존 게임을 배정하지 않는다.

## 6. 인증 흐름

### 회원가입

1. 클라이언트가 이메일과 비밀번호를 전송한다.
2. 서버가 이메일을 trim 및 소문자 정규화한다.
3. 서버가 이메일 형식과 비밀번호 최소 조건을 검증한다.
4. Argon2로 비밀번호를 해시한다.
5. 중복 이메일이면 일반화된 충돌 오류를 반환한다.
6. 사용자 생성 후 세션을 발급하고 쿠키를 설정한다.

### 로그인

1. 이메일을 정규화하고 사용자 계정을 조회한다.
2. 계정이 없거나 비밀번호가 틀리거나 비활성 계정이면 동일한 인증 실패 응답을 반환한다.
3. 성공 시 기존 세션과 독립적인 새 세션을 발급한다. 여러 기기 로그인을 허용한다.
4. 쿠키에는 원본 세션 토큰을 설정하고 DB에는 해시만 저장한다.

### 인증된 요청

1. 브라우저가 쿠키를 포함해 요청한다.
2. `get_current_user`가 쿠키 토큰의 해시로 세션을 조회한다.
3. 세션 만료 여부와 사용자 `is_active`를 확인한다.
4. 유효하면 현재 사용자 객체를 API 핸들러에 전달한다.

### 로그아웃

현재 쿠키의 세션을 DB에서 삭제하고 쿠키를 만료시킨다. 이미 만료되거나 없는 세션에 대한 로그아웃도 성공으로 처리한다.

## 7. API 계약

```text
POST /auth/register
  request: { email: string, password: string }
  response: { id: integer, email: string }
  success: 201

POST /auth/login
  request: { email: string, password: string }
  response: { id: integer, email: string }
  success: 200

POST /auth/logout
  response: { logged_out: true }
  success: 200

GET /auth/me
  response: { id: integer, email: string }
  unauthenticated: 401
```

게임 API는 인증이 없으면 모두 `401`을 반환한다. 인증은 되었지만 다른 사용자의 게임 ID를 요청한 경우에는 게임 존재 여부를 노출하지 않도록 `404`를 반환한다. 목록 API는 현재 사용자 소유 게임만 반환한다.

## 8. 브라우저 및 Render 설정

백엔드와 정적 프론트엔드가 서로 다른 Render 호스트를 사용하므로 다음을 적용한다.

- Axios 인스턴스에 `withCredentials: true`
- FastAPI CORS `allow_credentials=True`
- `CORS_ALLOWED_ORIGINS`에 정확한 프론트엔드 origin만 허용
- 세션 쿠키 `HttpOnly=True`, `Secure=True`, `SameSite=None`, `Path=/`
- 세션 쿠키 이름은 `insurance_session`
- 허용 origin에 와일드카드(`*`) 사용 금지

Render 환경변수는 다음과 같다.

```text
DATABASE_URL=<Render PostgreSQL internal or external URL>
CORS_ALLOWED_ORIGINS=https://<frontend-host>
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_SAMESITE=none
```

PostgreSQL 연결 문자열의 `postgres://` 형식은 사용하는 드라이버가 요구하는 `postgresql://` 형식으로 정규화한다. 애플리케이션은 `DATABASE_URL`이 없을 때 로컬 개발용 SQLite를 사용할 수 있지만, Render 운영 환경에서는 PostgreSQL을 필수로 사용한다.

## 9. 오류 처리와 보안 기준

- 비밀번호 원문과 세션 원문을 로그에 남기지 않는다.
- 로그인 실패는 “이메일 또는 비밀번호가 올바르지 않습니다”로 통일한다.
- 회원가입 중복 이메일도 계정 존재 여부를 과도하게 노출하지 않는 메시지를 사용한다.
- 비밀번호는 Argon2id 설정으로 해시한다.
- 세션 토큰은 `secrets.token_urlsafe` 등 보안 난수로 생성한다.
- 쿠키 인증을 사용하므로 상태 변경 요청에는 CSRF 방어를 추가한다. 1차 구현에서는 허용 origin 검사와 double-submit CSRF 토큰을 함께 사용한다.
- 로그인 실패 횟수 제한은 `login_attempts` PostgreSQL 테이블을 사용한다. 동일 IP·이메일 조합의 최근 15분 실패 5회 초과를 429로 제한해 Render 다중 인스턴스에서도 동일하게 적용한다.
- 계정 비활성화 시 모든 세션을 사용할 수 없게 한다.

## 10. 프론트엔드 상태와 라우팅

`authStore`는 다음 상태를 관리한다.

```text
user: null | { id, email }
status: 'unknown' | 'authenticated' | 'anonymous'
```

앱 초기화 시 `/auth/me`를 한 번 호출한다. 인증이 필요한 게임·결과 라우트는 인증 확인 전까지 로딩 상태를 표시하고, 익명 사용자는 `/login`으로 이동시킨다. 로그인 성공 후에는 `/`로 이동한다. 로그아웃 후에는 사용자 상태를 비우고 `/login`으로 이동한다.

Axios의 전역 401 처리는 인증 요청 자체에는 재귀적으로 적용하지 않으며, 게임 API에서 401이 발생하면 auth store를 익명 상태로 바꾸고 로그인 화면으로 이동한다.

## 11. 테스트 전략

### 백엔드

- 비밀번호가 원문이 아닌 Argon2 해시로 저장되는지 검증
- 정상 회원가입 및 중복 이메일 검증
- 정상 로그인 시 세션 쿠키가 발급되는지 검증
- 잘못된 로그인 정보가 동일한 401 응답을 반환하는지 검증
- `/auth/me`의 인증·만료·비활성 계정 동작 검증
- 로그아웃 후 기존 세션이 무효화되는지 검증
- 사용자 A의 게임 목록에 사용자 B 게임이 포함되지 않는지 검증
- 사용자 B가 사용자 A 게임의 조회·진행·삭제를 할 수 없는지 검증
- 인증되지 않은 모든 게임 API가 401인지 검증
- 기존 게임 진행 회귀 테스트

### 프론트엔드

- 로그인·회원가입 폼 검증
- 앱 초기화 시 인증 상태 복원
- 인증 라우트 가드
- 401 응답 시 로그인 화면 이동
- 로그아웃 상태 초기화

### 배포 확인

- Render PostgreSQL 연결 및 Alembic upgrade
- 프론트엔드 origin에서 쿠키가 실제 요청에 포함되는지 확인
- HTTPS 환경에서 세션 쿠키 속성 확인
- 재배포 후 사용자와 게임 데이터 유지 확인

## 12. 배포 및 전환 순서

1. PostgreSQL과 `DATABASE_URL`을 Render에 생성한다.
2. Alembic 초기 스키마와 인증·소유권 마이그레이션을 적용한다.
3. 백엔드 인증 API 및 게임 소유권 검사를 배포한다.
4. 프론트엔드 인증 화면과 라우트 가드를 배포한다.
5. 운영 HTTPS 환경에서 회원가입, 로그인, 게임 생성, 다른 계정 접근 차단을 확인한다.
6. 기존 SQLite 데이터는 보존하되, 소유자 매핑이 불명확한 게임은 자동 이전하지 않는다.

## 13. 성공 기준

- 사용자가 가입 후 로그인할 수 있다.
- 페이지 새로고침과 다른 기기에서도 로그인 상태가 복원된다.
- 사용자는 자신의 게임만 보고 조작할 수 있다.
- 로그아웃 이후 게임 API 접근이 차단된다.
- Render PostgreSQL에 사용자·세션·게임 데이터가 재배포 후에도 유지된다.
- 기존 시뮬레이션 계산 및 턴 진행 테스트가 동일하게 통과한다.
