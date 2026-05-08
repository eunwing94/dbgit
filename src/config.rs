//! 설정 로딩.
//!
//! `.env`/환경변수에서 `{ENV}_HOST` 등의 키를 읽어 `EnvConfig`를 구성합니다.
use std::env;

#[derive(Debug, Clone)]
pub struct EnvConfig {
    pub name: String,
    pub host: String,
    pub port: u16,
    pub user: String,
    pub password: String,
    pub database: String,
}

fn require(val: Option<String>, key: &str, env_name: &str) -> anyhow::Result<String> {
    val.filter(|s| !s.trim().is_empty())
        .ok_or_else(|| anyhow::anyhow!("{env_name} 설정 누락: {key}"))
}

pub fn load_env_config(env_name: &str) -> anyhow::Result<EnvConfig> {
    let prefix = env_name.to_uppercase();
    let host = require(env::var(format!("{prefix}_HOST")), &format!("{prefix}_HOST"), env_name)?;
    let port_raw =
        require(env::var(format!("{prefix}_PORT")), &format!("{prefix}_PORT"), env_name)?;
    let port: u16 = port_raw
        .parse()
        .map_err(|_| anyhow::anyhow!("{env_name} PORT 형식 오류: {port_raw}"))?;
    let user = require(env::var(format!("{prefix}_USER")), &format!("{prefix}_USER"), env_name)?;
    let password =
        require(env::var(format!("{prefix}_PASSWORD")), &format!("{prefix}_PASSWORD"), env_name)?;
    let database =
        require(env::var(format!("{prefix}_DATABASE")), &format!("{prefix}_DATABASE"), env_name)?;

    Ok(EnvConfig {
        name: prefix,
        host,
        port,
        user,
        password,
        database,
    })
}

pub fn load_env_configs(names: &[String]) -> anyhow::Result<Vec<EnvConfig>> {
    names.iter().map(|n| load_env_config(n)).collect()
}
