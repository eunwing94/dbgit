package hooks

import (
	"fmt"
	"os"
)

// Pipeline 등록된 훅을 순서대로 실행하는 미들웨어.
type Pipeline struct {
	hooks []Hook
}

// NewPipeline 훅 목록으로 파이프라인 생성.
func NewPipeline(hooks ...Hook) *Pipeline {
	return &Pipeline{hooks: append([]Hook(nil), hooks...)}
}

// Run 모든 훅에 이벤트 전달.
func (p *Pipeline) Run(e Event) {
	for _, h := range p.hooks {
		h.OnEvent(e)
	}
}

// LoggingHook stderr 로깅 기본 구현.
type LoggingHook struct{}

func (LoggingHook) OnEvent(e Event) {
	if e.Type == BeforeCompare {
		fmt.Fprintf(os.Stderr, "[dbgit] before_compare envs=%d proc=%s\n", len(e.Envs), e.Proc)
		return
	}
	n := 0
	if e.Results != nil {
		n = len(e.Results)
	}
	fmt.Fprintf(os.Stderr, "[dbgit] after_compare envs=%d proc=%s results=%d\n", len(e.Envs), e.Proc, n)
}
