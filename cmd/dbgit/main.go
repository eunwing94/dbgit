// dbgit CLI 엔트리포인트.
//
// - 플래그 파싱 → 검증 → 설정 로드 → 서비스(저장소) → 훅 파이프라인 → 렌더 레지스트리
package main

import (
	"context"
	"errors"
	"flag"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/joho/godotenv"

	"github.com/eunwing94/dbgit/internal/cli"
	"github.com/eunwing94/dbgit/internal/config"
	dbgerrors "github.com/eunwing94/dbgit/internal/errors"
	"github.com/eunwing94/dbgit/internal/hooks"
	"github.com/eunwing94/dbgit/internal/render"
	"github.com/eunwing94/dbgit/internal/repository"
	"github.com/eunwing94/dbgit/internal/service"
)

func main() {
	os.Exit(run())
}

func userMsg(err error) string {
	var de *dbgerrors.Error
	if errors.As(err, &de) {
		return de.Error()
	}
	return err.Error()
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
		fmt.Fprintln(os.Stderr, dbgerrors.New(dbgerrors.InvalidArgument, "baseline 환경이 envs 목록에 포함되어야 합니다.").Error())
		return 1
	}

	kind, err := render.ParseKind(*outputFmt)
	if err != nil {
		fmt.Fprintln(os.Stderr, userMsg(err))
		return 1
	}

	cfgList, err := config.LoadEnvConfigs(envList)
	if err != nil {
		fmt.Fprintf(os.Stderr, "오류: %v\n", err)
		return 1
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
	defer cancel()

	svc := &service.CompareService{Repo: repository.SQLProcRepository{}}
	pipe := hooks.NewPipeline(hooks.LoggingHook{})
	pipe.Run(hooks.Event{
		Type: hooks.BeforeCompare,
		At:   time.Now(),
		Envs: cfgList,
		Proc: proc,
	})

	defs, err := svc.CompareAcrossEnvs(ctx, cfgList, proc)
	if err != nil {
		fmt.Fprintf(os.Stderr, "오류: %v\n", userMsg(err))
		return 1
	}

	pipe.Run(hooks.Event{
		Type:    hooks.AfterCompare,
		At:      time.Now(),
		Envs:    cfgList,
		Proc:    proc,
		Results: defs,
	})

	reg := render.NewRegistry()
	renderer, err := reg.Get(kind)
	if err != nil {
		fmt.Fprintln(os.Stderr, userMsg(err))
		return 1
	}
	out, err := renderer.Render(baseline, defs)
	if err != nil {
		fmt.Fprintf(os.Stderr, "오류: %v\n", err)
		return 1
	}
	fmt.Println(out)
	return 0
}
