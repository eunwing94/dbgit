//! CLI 입력 파싱/검증 유틸.
use anyhow::{bail, Result};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum OutputFormat {
    Text,
    Json,
    Markdown,
}

impl OutputFormat {
    pub fn parse(s: &str) -> Result<Self> {
        match s.trim().to_lowercase().as_str() {
            "text" => Ok(Self::Text),
            "json" => Ok(Self::Json),
            "markdown" => Ok(Self::Markdown),
            _ => bail!("--output 은 text, json, markdown 중 하나여야 합니다."),
        }
    }
}

pub fn parse_envs(raw: &str) -> Vec<String> {
    raw.split(',')
        .map(|s| s.trim().to_uppercase())
        .filter(|s| !s.is_empty())
        .collect()
}

pub fn validate_baseline(envs: &[String], baseline: &str) -> Result<()> {
    if !envs.contains(&baseline.to_string()) {
        bail!("baseline 환경이 envs 목록에 포함되어야 합니다.");
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_envs_trims_and_uppercases() {
        let got = parse_envs(" prd, stg,DEV ,, qa ");
        assert_eq!(got, vec!["PRD", "STG", "DEV", "QA"]);
    }

    #[test]
    fn parse_output_format() {
        assert_eq!(OutputFormat::parse("text").unwrap(), OutputFormat::Text);
        assert_eq!(OutputFormat::parse(" JSON ").unwrap(), OutputFormat::Json);
        assert_eq!(OutputFormat::parse("markdown").unwrap(), OutputFormat::Markdown);
    }
}

