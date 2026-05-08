mod compare;
mod cli;
mod config;
mod hooks;
mod output;
mod render;

use std::collections::BTreeMap;

use anyhow::{bail, Context, Result};
use clap::Parser;
use hooks::{Hook, HookEvent, HookEventType, LoggingHook};
use std::time::SystemTime;

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

    let env_list: Vec<String> = cli::parse_envs(&args.envs);
    let baseline = args.baseline.trim().to_uppercase();
    cli::validate_baseline(&env_list, &baseline)?;

    let fmt = cli::OutputFormat::parse(&args.output)?;

    let cfgs = config::load_env_configs(&env_list).context("환경 변수 로드")?;
    let hooks: Vec<Box<dyn Hook>> = vec![Box::new(LoggingHook)];
    let before = HookEvent {
        kind: HookEventType::BeforeCompare,
        at: SystemTime::now(),
        envs: &cfgs,
        proc_identifier: &args.proc,
        results: None,
    };
    for h in &hooks {
        h.on_event(&before);
    }
    let defs: BTreeMap<String, compare::ProcDefinition> =
        compare::compare_across(&cfgs, &args.proc).await?;
    let after = HookEvent {
        kind: HookEventType::AfterCompare,
        at: SystemTime::now(),
        envs: &cfgs,
        proc_identifier: &args.proc,
        results: Some(&defs),
    };
    for h in &hooks {
        h.on_event(&after);
    }

    match fmt {
        cli::OutputFormat::Json => println!("{}", output::format_json(&baseline, &defs)?),
        cli::OutputFormat::Markdown => println!("{}", output::format_md(&baseline, &defs)),
        cli::OutputFormat::Text => print!("{}", output::format_text(&baseline, &defs)),
    }
    Ok(())
}
