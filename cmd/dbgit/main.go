// dbgit CLI 엔트리포인트.
//
// - 플래그 파싱 및 기본 검증
// - .env 로딩 및 환경별 설정 생성
// - 비교 유스케이스 호출 및 출력 포맷 선택
package main

import (
	"context"
	"flag"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/joho/godotenv"

	"github.com/eunwing94/dbgit/internal/compare"
	"github.com/eunwing94/dbgit/internal/cli"
	"github.com/eunwing94/dbgit/internal/config"
	"github.com/eunwing94/dbgit/internal/output"
)

func main() {
	os.Exit(run())
}

func run() int {
	fs := flag.NewFlagSet("dbgit", flag.ContinueOnError)
	fs.Usage = func() {
		fmt.Fprint(os.Stderr, `사용법: dbgit [옵션] <proc>

proc    프로시저/함수 object_id 또는 이름 (schema.name 권장)

`)
		fs.PrintDefaults()
		fmt.Fprintln(os.Stderr, "\n출력 형식: text | json | markdown")
	}

	envsFlag := fs.String("envs", strings.Join(config.DefaultEnvs, ","), "비교할 환경 (콤마 구분)")
	baselineFlag := fs.String("baseline", "PRD", "기준 환경")
	dotenvPath := fs.String("dotenv", ".env", "환경 변수 파일")
	outputFmt := fs.String("output", "text", "출력 형식 (text|json|markdown)")

	if err := fs.Parse(os.Args[1:]); err != nil {
		return 2
	}
	args := fs.Args()
	if len(args) < 1 {
		fs.Usage()
		return 2
	}
	proc := strings.TrimSpace(args[0])
	if *dotenvPath != "" {
		_ = godotenv.Load(*dotenvPath)
	}

	envList := cli.ParseEnvs(*envsFlag)
	baseline := strings.ToUpper(strings.TrimSpace(*baselineFlag))
	if !cli.Contains(envList, baseline) {
		fmt.Fprintln(os.Stderr, "baseline 환경이 envs 목록에 포함되어야 합니다.")
		return 1
	}

	fmtNorm := strings.ToLower(strings.TrimSpace(*outputFmt))
	if fmtNorm != "text" && fmtNorm != "json" && fmtNorm != "markdown" {
		fmt.Fprintln(os.Stderr, "output은 text, json, markdown 중 하나여야 합니다.")
		return 1
	}

	cfgList, err := config.LoadEnvConfigs(envList)
	if err != nil {
		fmt.Fprintf(os.Stderr, "오류: %v\n", err)
		return 1
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
	defer cancel()

	defs, err := compare.CompareAcrossEnvs(ctx, cfgList, proc)
	if err != nil {
		fmt.Fprintf(os.Stderr, "오류: %v\n", err)
		return 1
	}

	switch fmtNorm {
	case "json":
		s, err := output.FormatJSON(baseline, defs)
		if err != nil {
			fmt.Fprintf(os.Stderr, "오류: %v\n", err)
			return 1
		}
		fmt.Println(s)
	case "markdown":
		fmt.Println(output.FormatMarkdown(baseline, defs))
	default:
		fmt.Println(output.FormatText(baseline, defs))
	}
	return 0
}
