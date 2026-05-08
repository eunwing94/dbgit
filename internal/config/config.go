package config

import (
	"fmt"
	"os"
	"strconv"
	"strings"
)

// DefaultEnvs 기본 비교 환경.
var DefaultEnvs = []string{"PRD", "STG", "DEV", "QA"}

// EnvConfig 한 환경의 SQL Server 접속.
type EnvConfig struct {
	Name     string
	Host     string
	Port     int
	User     string
	Password string
	Database string
}

func require(val, key, envName string) (string, error) {
	if strings.TrimSpace(val) == "" {
		return "", fmt.Errorf("%s 설정 누락: %s", envName, key)
	}
	return val, nil
}

// LoadEnvConfig 환경변수에서 EnvConfig 로드.
func LoadEnvConfig(envName string) (EnvConfig, error) {
	prefix := strings.ToUpper(envName)
	host, err := require(os.Getenv(prefix+"_HOST"), prefix+"_HOST", envName)
	if err != nil {
		return EnvConfig{}, err
	}
	portRaw, err := require(os.Getenv(prefix+"_PORT"), prefix+"_PORT", envName)
	if err != nil {
		return EnvConfig{}, err
	}
	user, err := require(os.Getenv(prefix+"_USER"), prefix+"_USER", envName)
	if err != nil {
		return EnvConfig{}, err
	}
	password, err := require(os.Getenv(prefix+"_PASSWORD"), prefix+"_PASSWORD", envName)
	if err != nil {
		return EnvConfig{}, err
	}
	database, err := require(os.Getenv(prefix+"_DATABASE"), prefix+"_DATABASE", envName)
	if err != nil {
		return EnvConfig{}, err
	}
	port, err := strconv.Atoi(portRaw)
	if err != nil {
		return EnvConfig{}, fmt.Errorf("%s PORT 형식 오류: %s", envName, portRaw)
	}
	return EnvConfig{
		Name:     prefix,
		Host:     host,
		Port:     port,
		User:     user,
		Password: password,
		Database: database,
	}, nil
}

// LoadEnvConfigs 여러 환경 로드.
func LoadEnvConfigs(names []string) ([]EnvConfig, error) {
	out := make([]EnvConfig, 0, len(names))
	for _, n := range names {
		c, err := LoadEnvConfig(n)
		if err != nil {
			return nil, err
		}
		out = append(out, c)
	}
	return out, nil
}
