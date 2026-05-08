// 비교 유스케이스.
//
// 각 환경에서 프로시저/함수 정의를 조회한 뒤 정규화+해시로 SAME/DIFF를 판정합니다.
package compare

import (
	"context"
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"fmt"
	"regexp"
	"strconv"
	"strings"

	"github.com/eunwing94/dbgit/internal/config"
	"github.com/eunwing94/dbgit/internal/db"
)

// ProcDefinition 단일 환경 조회 결과.
type ProcDefinition struct {
	ObjectID               int
	SchemaName             string
	Name                   string
	Definition             string
	NormalizedDefinition   string
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

const procQuery = `
SELECT TOP 1
    o.object_id,
    s.name AS schema_name,
    o.name,
    m.definition
FROM sys.objects o
JOIN sys.sql_modules m ON o.object_id = m.object_id
JOIN sys.schemas s ON o.schema_id = s.schema_id
WHERE o.type IN ('P', 'PC', 'FN', 'IF', 'TF')
  AND (
        o.object_id = @oid
        OR o.name = @pname
        OR s.name + '.' + o.name = @qual
  )
ORDER BY
    CASE WHEN o.object_id = @oid2 THEN 0 ELSE 1 END,
    o.name;
`

var spaceRe = regexp.MustCompile(`\s+`)

func normalizeDefinition(def string) string {
	return spaceRe.ReplaceAllString(def, "")
}

func parseObjectID(s string) *int {
	n, err := strconv.Atoi(strings.TrimSpace(s))
	if err != nil {
		return nil
	}
	return &n
}

// FetchProcDefinition 한 환경에서 1건 조회.
func FetchProcDefinition(ctx context.Context, c config.EnvConfig, procIdentifier string) (ProcDefinition, error) {
	sdb, err := db.OpenWithRetry(ctx, c)
	if err != nil {
		return ProcDefinition{}, err
	}
	defer sdb.Close()

	oid := parseObjectID(procIdentifier)
	oidArg := any(nil)
	oid2 := any(nil)
	if oid != nil {
		oidArg = *oid
		oid2 = *oid
	}
	row := sdb.QueryRowContext(ctx, procQuery,
		sql.Named("oid", oidArg),
		sql.Named("pname", procIdentifier),
		sql.Named("qual", procIdentifier),
		sql.Named("oid2", oid2),
	)
	var objectID int
	var schemaName, name string
	var def sql.NullString
	if err := row.Scan(&objectID, &schemaName, &name, &def); err != nil {
		if err == sql.ErrNoRows {
			return ProcDefinition{}, fmt.Errorf("%s에서 프로시저를 찾지 못했습니다: %s", c.Name, procIdentifier)
		}
		return ProcDefinition{}, err
	}
	definition := ""
	if def.Valid {
		definition = def.String
	}
	norm := normalizeDefinition(definition)
	return ProcDefinition{
		ObjectID:             objectID,
		SchemaName:           schemaName,
		Name:                 name,
		Definition:           definition,
		NormalizedDefinition: norm,
	}, nil
}

// CompareAcrossEnvs 모든 환경에서 동일 식별자로 조회.
func CompareAcrossEnvs(ctx context.Context, cfgs []config.EnvConfig, procIdentifier string) (map[string]ProcDefinition, error) {
	out := make(map[string]ProcDefinition, len(cfgs))
	for _, c := range cfgs {
		p, err := FetchProcDefinition(ctx, c, procIdentifier)
		if err != nil {
			return nil, err
		}
		out[c.Name] = p
	}
	return out, nil
}
