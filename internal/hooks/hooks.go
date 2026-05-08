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

