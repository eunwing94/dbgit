npm run -s build
node dist/cli.js dbo.usp_Sample --dotenv ./secrets/dev.env --envs PRD,DEV --baseline PRD

