export PRD_HOST=localhost
export PRD_PORT=1433
export PRD_USER=sa
export PRD_PASSWORD=Your_password123
export PRD_DATABASE=master
npm run -s build
node dist/cli.js dbo.usp_Sample --baseline PRD --envs PRD

