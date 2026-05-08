//! 비교 전/후 이벤트 훅.
//!
//! 기본 `LoggingHook`을 포함합니다.
use std::time::SystemTime;

use crate::compare::ProcDefinition;
use crate::config::EnvConfig;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum HookEventType {
    BeforeCompare,
    AfterCompare,
}

#[derive(Debug)]
pub struct HookEvent<'a> {
    pub kind: HookEventType,
    pub at: SystemTime,
    pub envs: &'a [EnvConfig],
    pub proc_identifier: &'a str,
    pub results: Option<&'a std::collections::BTreeMap<String, ProcDefinition>>,
}

pub trait Hook: Send + Sync {
    fn on_event(&self, e: &HookEvent);
}

pub struct LoggingHook;

impl Hook for LoggingHook {
    fn on_event(&self, e: &HookEvent) {
        match e.kind {
            HookEventType::BeforeCompare => {
                eprintln!(
                    "[dbgit] before_compare envs={} proc={}",
                    e.envs.len(),
                    e.proc_identifier
                );
            }
            HookEventType::AfterCompare => {
                eprintln!(
                    "[dbgit] after_compare envs={} proc={} results={}",
                    e.envs.len(),
                    e.proc_identifier,
                    e.results.map(|m| m.len()).unwrap_or(0)
                );
            }
        }
    }
}

