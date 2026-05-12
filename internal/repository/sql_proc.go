package repository

import (
	"context"
	"database/sql"
	"fmt"
	"regexp"
	"strconv"
	"strings"

	"github.com/eunwing94/dbgit/internal/config"
	"github.com/eunwing94/dbgit/internal/db"
	"github.com/eunwing94/dbgit/internal/domain"
	"github.com/eunwing94/dbgit/internal/errors"
)

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

// SQLProcRepository sys.sql_modules 기반 구현.
type SQLProcRepository struct{}

// FetchProcDefinition 한 환경에서 1건 조회.
func (SQLProcRepository) FetchProcDefinition(ctx context.Context, c config.EnvConfig, procIdentifier string) (domain.ProcDefinition, error) {
	sdb, err := db.OpenWithRetry(ctx, c)
	if err != nil {
		return domain.ProcDefinition{}, errors.Wrap(errors.Database, "DB 연결", err)
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
			return domain.ProcDefinition{}, errors.New(errors.NotFound,
				fmt.Sprintf("%s에서 프로시저를 찾지 못했습니다: %s", c.Name, procIdentifier))
		}
		return domain.ProcDefinition{}, errors.Wrap(errors.Database, "조회", err)
	}
	definition := ""
	if def.Valid {
		definition = def.String
	}
	norm := normalizeDefinition(definition)
	return domain.ProcDefinition{
		ObjectID:             objectID,
		SchemaName:           schemaName,
		Name:                 name,
		Definition:           definition,
		NormalizedDefinition: norm,
	}, nil
}
