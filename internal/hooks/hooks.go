// 비교 전/후 이벤트 훅 스켈레톤.
//
// 확장(로깅/메트릭/추적)을 위해 이벤트를 수집하는 인터페이스를 제공합니다.
package hooks

import (
	"time"

	"github.com/eunwing94/dbgit/internal/config"
	"github.com/eunwing94/dbgit/internal/compare"
)

type EventType string

const (
	BeforeCompare EventType = "before_compare"
	AfterCompare  EventType = "after_compare"
)

type Event struct {
	Type      EventType
	At        time.Time
	Envs      []config.EnvConfig
	Proc      string
	Results   map[string]compare.ProcDefinition
}

type Hook interface {
	OnEvent(e Event)
}

