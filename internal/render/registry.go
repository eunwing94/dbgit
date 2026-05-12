// Package render: 출력 렌더러 레지스트리(플러그인).
package render

import (
	"fmt"
	"strings"

	"github.com/eunwing94/dbgit/internal/domain"
	"github.com/eunwing94/dbgit/internal/errors"
)

// Kind 출력 종류.
type Kind string

const (
	KindText     Kind = "text"
	KindJSON     Kind = "json"
	KindMarkdown Kind = "markdown"
)

// Renderer 단일 포맷 렌더러.
type Renderer interface {
	Kind() Kind
	Render(baseline string, defs map[string]domain.ProcDefinition) (string, error)
}

// Registry 등록 테이블.
type Registry struct {
	m map[Kind]Renderer
}

// NewRegistry 기본 렌더러 등록.
func NewRegistry() *Registry {
	r := &Registry{m: make(map[Kind]Renderer)}
	r.Register(TextRenderer{})
	r.Register(JSONRenderer{})
	r.Register(MarkdownRenderer{})
	return r
}

// Register 렌더러 추가(덮어쓰기).
func (r *Registry) Register(renderer Renderer) {
	r.m[renderer.Kind()] = renderer
}

// Get 포맷 조회.
func (r *Registry) Get(k Kind) (Renderer, error) {
	v, ok := r.m[k]
	if !ok {
		return nil, errors.New(errors.Output, fmt.Sprintf("등록되지 않은 렌더러: %s", k))
	}
	return v, nil
}

// ParseKind 문자열 → Kind.
func ParseKind(s string) (Kind, error) {
	switch strings.ToLower(strings.TrimSpace(s)) {
	case "json":
		return KindJSON, nil
	case "markdown":
		return KindMarkdown, nil
	case "text":
		return KindText, nil
	default:
		return "", errors.New(errors.Output, "output은 text, json, markdown 중 하나여야 합니다.")
	}
}
