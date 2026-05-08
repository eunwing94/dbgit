# 아키텍처 (C#)

C# 구현(`feature/csharp01`)은 `Microsoft.Data.SqlClient`로 SQL Server를 조회하고,
정의 텍스트를 정규화/해시하여 SAME/DIFF를 판단합니다.

## 구성

- `Program.cs`: CLI 옵션 파싱 및 실행
- `Config.cs`: `.env`/환경변수 기반 접속 정보 로딩
- `Db.cs`: SQL 조회 및 재시도
- `Compare.cs`: 조회/정규화/해시 및 비교
- `OutputFormat.cs`: text/json/markdown 출력

## 확장 포인트(스켈레톤)

- `Hooks/*`: before/after compare 훅
- `Render/*`: 렌더러 레지스트리(출력 플러그인)

