//! 출력 렌더러 레지스트리 스켈레톤.
//!
//! 포맷 렌더링을 플러그인 형태로 확장할 때 사용합니다.
use anyhow::{anyhow, Result};

use crate::compare::ProcDefinition;

pub trait Renderer: Send + Sync {
    fn id(&self) -> &'static str;
    fn render(&self, baseline: &str, defs: &std::collections::BTreeMap<String, ProcDefinition>) -> Result<String>;
}

pub struct RendererRegistry {
    renderers: std::collections::BTreeMap<&'static str, Box<dyn Renderer>>,
}

impl RendererRegistry {
    pub fn new() -> Self {
        Self { renderers: std::collections::BTreeMap::new() }
    }

    pub fn register(mut self, r: impl Renderer + 'static) -> Self {
        self.renderers.insert(r.id(), Box::new(r));
        self
    }

    pub fn get(&self, id: &str) -> Result<&dyn Renderer> {
        self.renderers
            .get(id)
            .map(|b| b.as_ref())
            .ok_or_else(|| anyhow!("등록되지 않은 렌더러: {id}"))
    }
}

