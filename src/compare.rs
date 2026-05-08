//! 비교 유스케이스.
//!
//! SQL Server에서 모듈 정의를 읽어 정규화 후 digest(SHA-256)로 비교합니다.
use std::env;
use std::sync::OnceLock;
use std::time::Duration;

use anyhow::{Context, Result};
use futures_util::TryStreamExt;
use regex::Regex;
use sha2::{Digest as _, Sha256};
use tokio::net::TcpStream;
use tokio::time::sleep;
use tiberius::{Client, Config, Row};

use crate::config::EnvConfig;

const PROC_QUERY: &str = r#"
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
        o.object_id = @p1
        OR o.name = @p2
        OR s.name + '.' + o.name = @p3
  )
ORDER BY
    CASE WHEN o.object_id = @p4 THEN 0 ELSE 1 END,
    o.name;
"#;

#[derive(Debug, Clone)]
pub struct ProcDefinition {
    pub object_id: i32,
    pub schema_name: String,
    pub name: String,
    pub definition: String,
    pub normalized_definition: String,
}

impl ProcDefinition {
    pub fn full_name(&self) -> String {
        format!("{}.{}", self.schema_name, self.name)
    }

    pub fn digest_hex(&self) -> String {
        let mut h = Sha256::new();
        h.update(self.normalized_definition.as_bytes());
        format!("{:x}", h.finalize())
    }
}

fn normalize(def: &str) -> String {
    static RE: OnceLock<Regex> = OnceLock::new();
    let re = RE.get_or_init(|| Regex::new(r"\s+").unwrap());
    re.replace_all(def, "").to_string()
}

fn parse_object_id(ident: &str) -> Option<i32> {
    ident.trim().parse().ok()
}

fn retry_params() -> (usize, Duration) {
    let max = env::var("DBGIT_DB_MAX_RETRIES")
        .ok()
        .and_then(|s| s.parse().ok())
        .filter(|&n: &usize| n > 0)
        .unwrap_or(3);
    let delay_sec: f64 = env::var("DBGIT_DB_RETRY_DELAY_SEC")
        .ok()
        .and_then(|s| s.parse().ok())
        .filter(|d: &f64| *d >= 0.0)
        .unwrap_or(1.0);
    (max, Duration::from_secs_f64(delay_sec))
}

fn to_ado(cfg: &EnvConfig) -> String {
    format!(
        "Server=tcp:{};Database={};User ID={};Password={};Encrypt=true;TrustServerCertificate=true;Connection Timeout=5;",
        format!("{},{}", cfg.host, cfg.port),
        cfg.database,
        cfg.user,
        cfg.password
    )
}

async fn connect(cfg: &EnvConfig) -> Result<Client<TcpStream>> {
    let (max_attempts, delay) = retry_params();
    let mut last_err = anyhow::anyhow!("연결 실패");
    for attempt in 1..=max_attempts {
        let ado = to_ado(cfg);
        let config =
            Config::from_ado_string(&ado).with_context(|| format!("ADO 파싱 실패 env={}", cfg.name))?;
        match TcpStream::connect(config.get_addr()).await {
            Ok(tcp) => match Client::connect(config, tcp).await {
                Ok(c) => return Ok(c),
                Err(e) => {
                    last_err = e.into();
                    eprintln!(
                        "DB 연결 실패 env={} 시도 {}/{}: {:?}",
                        cfg.name, attempt, max_attempts, last_err
                    );
                }
            },
            Err(e) => {
                last_err = e.into();
                eprintln!(
                    "TCP 연결 실패 env={} 시도 {}/{}: {:?}",
                    cfg.name, attempt, max_attempts, last_err
                );
            }
        }
        if attempt < max_attempts && delay > Duration::ZERO {
            sleep(delay).await;
        }
    }
    Err(last_err)
}

fn row_to_def(row: Row) -> Result<ProcDefinition> {
    let object_id: i32 = row.try_get(0).context("object_id")?;
    let schema_name: &str = row.try_get(1).context("schema_name")?;
    let name: &str = row.try_get(2).context("name")?;
    let definition: String = match row.try_get::<&str, _>(3) {
        Ok(s) => s.to_string(),
        Err(_) => row
            .try_get::<Option<&str>, _>(3)
            .ok()
            .flatten()
            .unwrap_or("")
            .to_string(),
    };
    let normalized_definition = normalize(&definition);
    Ok(ProcDefinition {
        object_id,
        schema_name: schema_name.to_string(),
        name: name.to_string(),
        definition,
        normalized_definition,
    })
}

pub async fn fetch_proc(cfg: &EnvConfig, proc_identifier: &str) -> Result<ProcDefinition> {
    let mut client = connect(cfg).await?;
    let oid = parse_object_id(proc_identifier);

    let params: [&dyn tiberius::ToSql; 4] = [&oid, &proc_identifier, &proc_identifier, &oid];
    let mut stream = client
        .query(PROC_QUERY, &params)
        .await
        .with_context(|| format!("쿼리 실행 env={}", cfg.name))?;

    let mut rows = stream.into_first_result().await?;
    let row = rows
        .try_next()
        .await?
        .ok_or_else(|| anyhow::anyhow!("{}에서 프로시저를 찾지 못했습니다: {proc_identifier}", cfg.name))?;
    row_to_def(row)
}

pub async fn compare_across(
    cfgs: &[EnvConfig],
    proc_identifier: &str,
) -> Result<std::collections::BTreeMap<String, ProcDefinition>> {
    let mut out = std::collections::BTreeMap::new();
    for c in cfgs {
        let p = fetch_proc(c, proc_identifier).await?;
        out.insert(c.name.clone(), p);
    }
    Ok(out)
}
