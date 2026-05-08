mod compare;
mod config;
mod output;

use std::collections::BTreeMap;

use anyhow::{bail, Context, Result};
use clap::Parser;

#[derive(Parser, Debug)]
#[command(name = "dbgit")]
struct Args {
    /// 프로시저/함수 object_id 또는 이름
    proc: String,

    #[arg(long, default_value = "PRD,STG,DEV,QA")]
    envs: String,

    #[arg(long, default_value = "PRD")]
    baseline: String,

    #[arg(long, default_value = ".env")]
    dotenv: String,

    /// text | json | markdown
    #[arg(long, default_value = "text")]
    output: String,
}

#[tokio::main]
async fn main() {
    if let Err(e) = run().await {
        eprintln!("오류: {e:#}");
        std::process::exit(1);
    }
}

async fn run() -> Result<()> {
    let args = Args::parse();
    if !args.dotenv.trim().is_empty() {
        let _ = dotenvy::from_filename(&args.dotenv);
    }

    let env_list: Vec<String> = args
        .envs
        .split(',')
        .map(|s| s.trim().to_uppercase())
        .filter(|s| !s.is_empty())
        .collect();
    let baseline = args.baseline.trim().to_uppercase();
    if !env_list.contains(&baseline) {
        bail!("baseline 환경이 envs 목록에 포함되어야 합니다.");
    }

    let fmt = args.output.to_lowercase();
    if !matches!(fmt.as_str(), "text" | "json" | "markdown") {
        bail!("--output 은 text, json, markdown 중 하나여야 합니다.");
    }

    let cfgs = config::load_env_configs(&env_list).context("환경 변수 로드")?;
    let defs: BTreeMap<String, compare::ProcDefinition> =
        compare::compare_across(&cfgs, &args.proc).await?;

    match fmt.as_str() {
        "json" => println!("{}", output::format_json(&baseline, &defs)?),
        "markdown" => println!("{}", output::format_md(&baseline, &defs)),
        _ => print!("{}", output::format_text(&baseline, &defs)),
    }
    Ok(())
}
