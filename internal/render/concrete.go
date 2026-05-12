package render

import (
	"encoding/json"
	"fmt"
	"sort"
	"strings"

	"github.com/eunwing94/dbgit/internal/domain"
)

func diffEnvNames(baseline string, defs map[string]domain.ProcDefinition) []string {
	baseDigest := defs[baseline].Digest()
	var names []string
	for k, v := range defs {
		if v.Digest() != baseDigest {
			names = append(names, k)
		}
	}
	sort.Strings(names)
	return names
}

func sortedKeys(defs map[string]domain.ProcDefinition) []string {
	keys := make([]string, 0, len(defs))
	for k := range defs {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	return keys
}

// TextRenderer 텍스트 출력.
type TextRenderer struct{}

func (TextRenderer) Kind() Kind { return KindText }

func (TextRenderer) Render(baseline string, defs map[string]domain.ProcDefinition) (string, error) {
	b := defs[baseline]
	var sb strings.Builder
	sb.WriteString(fmt.Sprintf("기준 환경: %s (%s)\n\n", baseline, b.FullName()))
	sb.WriteString("환경별 결과:\n")
	for _, env := range sortedKeys(defs) {
		p := defs[env]
		m := "DIFF"
		if p.Digest() == b.Digest() {
			m = "SAME"
		}
		sb.WriteString(fmt.Sprintf("- %s: %s (object_id=%d)\n", env, m, p.ObjectID))
	}
	sb.WriteString("\n")
	diff := diffEnvNames(baseline, defs)
	if len(diff) > 0 {
		sb.WriteString("차이나는 환경:\n")
		sb.WriteString(strings.Join(diff, ", "))
	} else {
		sb.WriteString("모든 환경이 동일합니다.")
	}
	return sb.String(), nil
}

type envEntry struct {
	ObjectID       int    `json:"object_id"`
	SchemaName     string `json:"schema_name"`
	Name           string `json:"name"`
	FullName       string `json:"full_name"`
	Digest         string `json:"digest"`
	SameAsBaseline bool   `json:"same_as_baseline"`
}

type defWithBody struct {
	ObjectID   int    `json:"object_id"`
	SchemaName string `json:"schema_name"`
	Name       string `json:"name"`
	FullName   string `json:"full_name"`
	Digest     string `json:"digest"`
	Definition string `json:"definition"`
}

// JSONRenderer JSON 출력.
type JSONRenderer struct{}

func (JSONRenderer) Kind() Kind { return KindJSON }

func (JSONRenderer) Render(baseline string, defs map[string]domain.ProcDefinition) (string, error) {
	baseDigest := defs[baseline].Digest()
	envs := make(map[string]envEntry, len(defs))
	defBodies := make(map[string]defWithBody, len(defs))
	for k, v := range defs {
		envs[k] = envEntry{
			ObjectID:       v.ObjectID,
			SchemaName:     v.SchemaName,
			Name:           v.Name,
			FullName:       v.FullName(),
			Digest:         v.Digest(),
			SameAsBaseline: v.Digest() == baseDigest,
		}
		defBodies[k] = defWithBody{
			ObjectID:   v.ObjectID,
			SchemaName: v.SchemaName,
			Name:       v.Name,
			FullName:   v.FullName(),
			Digest:     v.Digest(),
			Definition: v.Definition,
		}
	}
	diff := diffEnvNames(baseline, defs)
	payload := map[string]any{
		"baseline":                 baseline,
		"target_full_name":         defs[baseline].FullName(),
		"environments":             envs,
		"diff_environment_names":   diff,
		"all_same":                 len(diff) == 0,
		"definitions_with_body":  defBodies,
	}
	b, err := json.MarshalIndent(payload, "", "  ")
	if err != nil {
		return "", err
	}
	return string(b), nil
}

// MarkdownRenderer 마크다운 출력.
type MarkdownRenderer struct{}

func (MarkdownRenderer) Kind() Kind { return KindMarkdown }

func (MarkdownRenderer) Render(baseline string, defs map[string]domain.ProcDefinition) (string, error) {
	b := defs[baseline]
	var sb strings.Builder
	sb.WriteString("## 프로시저·함수 비교 결과\n\n")
	sb.WriteString(fmt.Sprintf("- **기준 환경:** `%s` — `%s`\n\n", baseline, b.FullName()))
	sb.WriteString("| 환경 | 상태 | object_id | full_name |\n")
	sb.WriteString("|:--|:--|--:|:--|\n")
	for _, env := range sortedKeys(defs) {
		p := defs[env]
		st := "DIFF"
		if p.Digest() == b.Digest() {
			st = "SAME"
		}
		sb.WriteString(fmt.Sprintf("| %s | %s | %d | `%s` |\n", env, st, p.ObjectID, p.FullName()))
	}
	sb.WriteString("\n")
	diff := diffEnvNames(baseline, defs)
	if len(diff) > 0 {
		sb.WriteString("**차이 환경:** " + strings.Join(diff, ", "))
	} else {
		sb.WriteString("**모든 환경이 동일합니다.**")
	}
	return sb.String(), nil
}
