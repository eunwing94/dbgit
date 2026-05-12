// Package domain: 프로시저/함수 정의 도메인 모델.
package domain

import (
	"crypto/sha256"
	"encoding/hex"
)

// ProcDefinition 단일 환경 조회 결과.
type ProcDefinition struct {
	ObjectID             int
	SchemaName           string
	Name                 string
	Definition           string
	NormalizedDefinition string
}

// FullName schema.name
func (p ProcDefinition) FullName() string {
	return p.SchemaName + "." + p.Name
}

// Digest SHA-256 hex
func (p ProcDefinition) Digest() string {
	h := sha256.Sum256([]byte(p.NormalizedDefinition))
	return hex.EncodeToString(h[:])
}
