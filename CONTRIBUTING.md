# 기여 안내 (Java)

## 개발 환경

- JDK 17 이상
- Apache Maven

## 빌드

```bash
mvn -q package
```

## 코드 스타일

- DB 접속·비교·출력 로직은 `src/main/java/com/dbgit/` 패키지에 둡니다.
- 사용자에게 노출되는 메시지는 가능하면 한국어로 통일합니다.

## 커밋 전 체크리스트

1. `mvn -q compile` 성공
2. `.env`·비밀번호가 커밋에 포함되지 않았는지 확인
