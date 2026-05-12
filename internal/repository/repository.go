// Package repository: 프로시저/함수 정의 조회 추상화.
package repository

import (
	"context"

	"github.com/eunwing94/dbgit/internal/config"
	"github.com/eunwing94/dbgit/internal/domain"
)

// ProcDefinitionRepository 환경별 1건 조회.
type ProcDefinitionRepository interface {
	FetchProcDefinition(ctx context.Context, c config.EnvConfig, procIdentifier string) (domain.ProcDefinition, error)
}
