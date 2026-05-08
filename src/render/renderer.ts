import type { ProcDefinition } from "../compare.js";

export type RendererId = "text" | "json" | "markdown";

export interface Renderer {
  id: RendererId;
  render(baseline: string, definitions: Record<string, ProcDefinition>): string;
}

export class RendererRegistry {
  private readonly map = new Map<RendererId, Renderer>();

  register(r: Renderer): this {
    this.map.set(r.id, r);
    return this;
  }

  get(id: RendererId): Renderer {
    const r = this.map.get(id);
    if (!r) throw new Error(`등록되지 않은 렌더러: ${id}`);
    return r;
  }
}

