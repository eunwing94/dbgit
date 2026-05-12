// Package service: 비교 유스케이스 오케스트레이션.
package service

import (
	"context"

	"github.com/eunwing94/dbgit/internal/config"
	"github.com/eunwing94/dbgit/internal/domain"
	"github.com/eunwing94/dbgit/internal/repository"
)

// CompareService 저장소를 사용한 환경 간 비교.
type CompareService struct {
	Repo repository.ProcDefinitionRepository
}

// CompareAcrossEnvs 모든 환경에서 동일 식별자로 조회.
func (s *CompareService) CompareAcrossEnvs(ctx context.Context, cfgs []config.EnvConfig, procIdentifier string) (map[string]domain.ProcDefinition, error) {
	out := make(map[string]domain.ProcDefinition, len(cfgs))
	for _, c := range cfgs {
		p, err := s.Repo.FetchProcDefinition(ctx, c, procIdentifier)
		if err != nil {
			return nil, err
		}
		out[c.Name] = p
	}
	return out, nil
}
