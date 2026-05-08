export DBGIT_DB_MAX_RETRIES=5
export DBGIT_DB_RETRY_DELAY_SEC=0.5
go run ./cmd/dbgit -- dbo.usp_Sample --baseline PRD --envs PRD,STG

