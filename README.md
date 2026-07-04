# AI 가계부 에이전트

자연어 지출 입력을 분석하고, 정산 금액과 카테고리를 계산해 저장하는 FastAPI 웹 앱입니다.

## MVP 기능

- 자연어 지출 입력 분석 미리보기
- 사용자 확인 후 지출 저장
- 지출 목록 보기
- 카테고리별 월간 요약
- 받을 돈 목록 보기
- 특정 사람에게 받을 돈 조회

## Skill 구조

- `ExpenseParserSkill`: 날짜, 금액, 인원 수, 결제자, 참여자, 메모 추출
- `SettlementCalculatorSkill`: 총 결제금액, 내 부담액, 받을 돈, 줄 돈 계산
- `CategoryClassifierSkill`: 소비 문장 기반 카테고리 자동 분류

각 skill은 `app/skills` 아래 독립 클래스로 구현되어 있으며, `SkillRegistry`에 등록해 확장할 수 있습니다.

## 환경 변수

`.env.example`을 참고해 `.env`를 만듭니다.

```env
APP_ENV=local
DATABASE_URL=postgresql+psycopg://postgres:password@db.example.supabase.co:5432/postgres
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
```

`OPENAI_API_KEY`가 없으면 개발용 규칙 기반 skill 파서로 동작합니다. `DATABASE_URL`에는 Supabase PostgreSQL 연결 문자열을 넣어야 저장/조회와 마이그레이션이 동작합니다.

## 로컬 실행

```bash
python -m pip install -r requirements.txt
python scripts/check_db.py
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

브라우저에서 `http://127.0.0.1:8000`을 엽니다.

## Render 배포

Render Web Service에서 이 저장소를 연결하고 다음 환경 변수를 설정합니다.

- `DATABASE_URL`: Supabase PostgreSQL 연결 문자열
- `OPENAI_API_KEY`: 선택
- `OPENAI_MODEL`: `gpt-4.1-mini`
- `APP_ENV`: `production`

`render.yaml`의 시작 명령은 배포 시 마이그레이션을 적용한 뒤 앱을 실행합니다.

## 테스트

```bash
python -m pytest
```
