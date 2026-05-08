go build -o dbgit ./cmd/dbgit
./dbgit dbo.usp_Sample --baseline PRD --envs PRD,STG,DEV,QA --output text

