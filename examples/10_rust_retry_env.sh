export DBGIT_DB_MAX_RETRIES=5
export DBGIT_DB_RETRY_DELAY_SEC=0.5
cargo run -- dbo.usp_Sample --baseline PRD --envs PRD,STG

