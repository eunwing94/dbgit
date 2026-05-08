package db

import (
	"context"
	"database/sql"
	"fmt"
	"os"
	"strconv"
	"time"

	_ "github.com/microsoft/go-mssqldb"

	"github.com/eunwing94/dbgit/internal/config"
)

const (
	retriesEnv = "DBGIT_DB_MAX_RETRIES"
	delayEnv   = "DBGIT_DB_RETRY_DELAY_SEC"
)

func retryParams() (int, time.Duration) {
	max := 3
	if v := os.Getenv(retriesEnv); v != "" {
		if n, err := strconv.Atoi(v); err == nil && n > 0 {
			max = n
		}
	}
	delaySec := 1.0
	if v := os.Getenv(delayEnv); v != "" {
		if f, err := strconv.ParseFloat(v, 64); err == nil && f >= 0 {
			delaySec = f
		}
	}
	return max, time.Duration(delaySec * float64(time.Second))
}

// BuildConnectionString ADO 스타일 연결 문자열.
func BuildConnectionString(c config.EnvConfig) string {
	return fmt.Sprintf(
		"server=%s,%d;user id=%s;password=%s;database=%s;encrypt=true;TrustServerCertificate=true;connection timeout=5",
		c.Host, c.Port, c.User, c.Password, c.Database,
	)
}

// OpenWithRetry 연결 시 재시도.
func OpenWithRetry(ctx context.Context, c config.EnvConfig) (*sql.DB, error) {
	maxAttempts, delay := retryParams()
	connStr := BuildConnectionString(c)
	var lastErr error
	for attempt := 1; attempt <= maxAttempts; attempt++ {
		db, err := sql.Open("sqlserver", connStr)
		if err != nil {
			lastErr = err
			fmt.Fprintf(os.Stderr, "DB Open 실패 env=%s 시도 %d/%d: %v\n", c.Name, attempt, maxAttempts, err)
		} else {
			pingCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
			err = db.PingContext(pingCtx)
			cancel()
			if err == nil {
				return db, nil
			}
			_ = db.Close()
			lastErr = err
			fmt.Fprintf(os.Stderr, "DB 연결 실패 env=%s 시도 %d/%d: %v\n", c.Name, attempt, maxAttempts, err)
		}
		if attempt < maxAttempts && delay > 0 {
			time.Sleep(delay)
		}
	}
	return nil, lastErr
}
