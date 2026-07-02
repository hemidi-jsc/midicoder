/**
 * Contract Graph — Entity-Centric Constellation Layout
 *
 * Each entity is a hub; its operations orbit around it in a cluster.
 * DEFAULT  — Entity cards grid (summary), no interaction
 * FULLSCREEN — Full cluster graph, zoom/pan/tooltip
 */

import {
  Component,
  ElementRef,
  Input,
  OnDestroy,
  AfterViewInit,
  NgZone,
  OnChanges,
  SimpleChanges,
  ChangeDetectorRef,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import p5 from 'p5';

const CAT_COLOR: Record<string, [number, number, number]> = {
  entities: [52, 152, 219],
  commands: [46, 204, 113],
  queries: [26, 188, 156],
  events: [243, 156, 18],
  workflows: [155, 89, 182],
  value_objects: [142, 68, 173],
  guards: [231, 76, 60],
  roles: [241, 196, 15],
  ui_components: [230, 126, 34],
};

const STATUS_BORDER: Record<string, [number, number, number, number]> = {
  matched: [46, 204, 113, 200],
  orphan_analysis: [231, 76, 60, 255],
  orphan_contract: [241, 196, 15, 255],
  mismatch: [230, 126, 34, 255],
};

const EDGE_COLORS: Record<string, [number, number, number]> = {
  writes_to: [46, 204, 113],
  fetches: [52, 152, 219],
  reads_from: [26, 188, 156],
  emits: [243, 156, 18],
  source_entity: [243, 156, 18],
  uses_command: [155, 89, 182],
  guards: [231, 76, 60],
  entity_ref: [230, 126, 34],
};

/** Semantic edge label for display on the flow diagram. */
const EDGE_LABEL: Record<string, string> = {
  writes_to: '→',
  fetches: 'fetches',
  reads_from: 'reads',
  emits: 'emits',
  source_entity: 'from',
  uses_command: 'calls',
  guards: 'guards',
  entity_ref: 'renders',
};

interface Node {
  uid: string;
  label: string;
  category: string;
  status: string;
  x: number;
  y: number;
  w: number;
  h: number;
  entityGroup: string | null;
  payload?: Array<{ icon: string; label: string }>;
}
interface Edge {
  from: string;
  to: string;
  type: string;
}

/** Sequence diagram lifeline (a participant with a vertical dashed line) */
interface SeqLifeline {
  uid: string;
  label: string;
  category: string;
  x: number; // center X of the lifeline
  status: string;
  w: number; // box width
  fields?: Array<{ name: string; type: string; is_pk?: boolean; is_fk?: boolean }>;
  // UI component extras
  componentType?: string;
  properties?: Record<string, any>;
}

/** Sequence diagram message (arrow between two lifelines at a given Y) */
interface SeqMessage {
  fromUid: string;
  toUid: string;
  type: string; // edge type: writes_to, emits, guards, etc
  label: string; // display label on the arrow
  y: number; // vertical position of the arrow
  // Action enrichment (when action is on the arrow, not a participant)
  actionName?: string; // name of the command/query/event
  actionType?: string; // 'command' | 'query' | 'ui_component'
  guards?: string[]; // guard names
  events?: string[]; // emitted event names
  payload?: string[]; // payload detail lines (input, transaction, etc.)
  // For command hub: target entities this command writes to
  targetUids?: string[]; // multiple targets → drawn as hub with connectors
  // Drift status of the command itself (from traceMatrix)
  status?: string;
}

/** ERD entity with fields and FK references. */
interface ERDEntity {
  uid: string;
  label: string;
  status: string;
  x: number;
  y: number;
  w: number;
  h: number;
  fields: Array<{ name: string; type: string; is_pk?: boolean; is_fk?: boolean }>;
  foreignKeys: Array<{ field: string; target_entity: string; cardinality: string }>;
  hovered: boolean;
}

/** ERD FK edge between entities. */
interface ERDEdge {
  from: ERDEntity | null;
  to: ERDEntity | null;
  type: string;
  cardinality: string;
}

/** Position in the entity-detail flow layout. */
interface FlowPos {
  x: number;
  y: number;
  w: number;
  h: number;
}
interface Cluster {
  name: string;
  entityNode: Node | null;
  commands: Node[];
  queries: Node[];
  events: Node[];
  other: Node[];
  x: number;
  y: number;
  w: number;
  h: number;
  healthScore: number;
  hasDrift: boolean;
}

@Component({
  selector: 'app-contract-graph',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div
      #wrapRef
      class="cg-wrap"
      [class.cg-fullscreen]="isFullscreen"
      [class.cg-detail]="selectedEntity && !isFullscreen"
      (mouseleave)="tooltipNode = null"
    >
      <div class="cg-canvas" #canvasContainer></div>

      <div class="cg-toolbar">
        <div class="cg-stats" *ngIf="!selectedEntity">
          <i class="fa-solid fa-diagram-project"></i>
          <span>{{ clusters.length }} entities · {{ totalCount }} nodes</span>
        </div>
        <div class="cg-stats cg-entity-title" *ngIf="selectedEntity && !selectedUIComponent">
          <i class="fa-solid fa-cube"></i>
          <span>{{ selectedEntity }}</span>
        </div>
        <div class="cg-stats cg-entity-title" *ngIf="selectedUIComponent">
          <i class="fa-solid fa-palette"></i>
          <span>{{ selectedUIComponent.data.label }} — Wireframe</span>
        </div>
        <div class="cg-actions">
          <button
            *ngIf="selectedUIComponent"
            class="cg-btn cg-btn-back"
            (click)="backToFlow($event)"
            title="Back to flow diagram"
          >
            <i class="fa-solid fa-arrow-left"></i>
            <span class="cg-btn-label">Flow</span>
          </button>
          <button
            *ngIf="selectedEntity && !selectedUIComponent"
            class="cg-btn cg-btn-back"
            (click)="backToOverview($event)"
            title="Back to entities"
          >
            <i class="fa-solid fa-arrow-left"></i>
            <span class="cg-btn-label">Back</span>
          </button>
          <button
            *ngIf="!selectedEntity"
            class="cg-btn"
            (click)="autoArrange($event)"
            title="Auto arrange entities"
          >
            <i class="fa-solid fa-table-columns"></i>
            <span class="cg-btn-label">Arrange</span>
          </button>
          <button
            *ngIf="isFullscreen && !selectedEntity"
            class="cg-btn"
            (click)="resetView()"
            title="Reset view"
          >
            <i class="fa-solid fa-crosshairs"></i>
          </button>
          <button class="cg-btn cg-btn-primary" (click)="toggleFullscreen($event)">
            <i
              class="fa-solid"
              [class]="isFullscreen ? 'fa-down-left-and-up-right' : 'fa-up-right-and-down-left'"
            ></i>
            <span class="cg-btn-label">{{ isFullscreen ? 'Exit' : 'Expand' }}</span>
          </button>
        </div>
      </div>

      <div class="cg-legend" *ngIf="isFullscreen">
        <div class="cg-leg-title">Drift Status</div>
        @for (item of legendItems; track item.label) {
          <div class="cg-leg-row">
            <span class="cg-dot" [style.background]="item.color"></span> {{ item.label }}
          </div>
        }
      </div>

      <div class="cg-mode-hint" *ngIf="!selectedEntity">
        <i class="fa-solid fa-eye"></i> Entity overview — click an entity to see its flow diagram
        <span *ngIf="isFullscreen" style="margin-left:12px; color:#58a6ff;"
          >· Scroll zoom · Space+drag pan</span
        >
      </div>
      <div class="cg-mode-hint" *ngIf="selectedEntity">
        <i class="fa-solid fa-project-diagram" style="color:#58a6ff"></i>
        Flow diagram — {{ selectedEntity }}
        <span *ngIf="!selectedUIComponent" style="margin-left:12px; color:#f0883e;">
          · Click a UI component to preview wireframe
        </span>
      </div>
      <div class="cg-mode-hint" *ngIf="selectedUIComponent">
        <i class="fa-solid fa-palette" style="color:#f0883e"></i>
        Wireframe preview — {{ selectedUIComponent.data.label }}
      </div>

      <div
        class="cg-tooltip"
        *ngIf="tooltipNode"
        [style.left.px]="tooltipX"
        [style.top.px]="tooltipY"
      >
        <div class="cg-tooltip-cluster" *ngIf="tooltipNode.entityGroup">
          Cluster: {{ tooltipNode.entityGroup }}
        </div>
        <div class="cg-tooltip-cat">{{ getCategoryLabel(tooltipNode.category) }}</div>
        <div class="cg-tooltip-name">{{ tooltipNode.label }}</div>
        <div class="cg-tooltip-status" [class]="tooltipNode.status">
          {{ tooltipNode.status }}
        </div>
      </div>
    </div>
  `,
  styles: [
    `
      .cg-wrap {
        position: relative;
        width: 100%;
        height: 420px;
        background: #0d1117;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #21262d;
      }
      .cg-wrap.cg-fullscreen {
        position: fixed !important;
        top: 0;
        left: 0;
        width: 100vw !important;
        height: 100vh !important;
        z-index: 9999;
        border-radius: 0;
        border: none;
        background: #010409;
      }
      .cg-wrap.cg-detail {
        height: 100% !important;
      }
      .cg-canvas {
        width: 100%;
        height: 100%;
      }
      .cg-canvas canvas {
        display: block;
      }

      .cg-toolbar {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 14px;
        background: linear-gradient(to bottom, rgba(1, 4, 9, 0.95), rgba(1, 4, 9, 0));
        z-index: 20;
        pointer-events: none;
      }
      .cg-toolbar > * {
        pointer-events: auto;
      }
      .cg-stats {
        font-size: 11px;
        color: #8b949e;
        display: flex;
        gap: 6px;
        align-items: center;
      }
      .cg-stats i {
        color: #58a6ff;
      }
      .cg-actions {
        display: flex;
        gap: 6px;
      }
      .cg-btn {
        background: rgba(22, 27, 34, 0.9);
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 5px 10px;
        color: #c9d1d9;
        cursor: pointer;
        font-size: 12px;
        display: flex;
        align-items: center;
        gap: 5px;
        transition: all 0.2s;
      }
      .cg-btn:hover {
        background: #30363d;
        color: #e6edf3;
        border-color: #58a6ff;
      }
      .cg-btn-primary {
        background: rgba(56, 139, 253, 0.15);
        border-color: rgba(56, 139, 253, 0.4);
        color: #58a6ff;
      }
      .cg-btn-primary:hover {
        background: rgba(56, 139, 253, 0.3);
        color: #79b8ff;
      }
      .cg-btn-back {
        background: rgba(255, 255, 255, 0.05);
        border-color: rgba(255, 255, 255, 0.15);
        color: #c9d1d9;
      }
      .cg-btn-back:hover {
        background: rgba(255, 255, 255, 0.12);
        color: #e6edf3;
        border-color: #58a6ff;
      }
      .cg-entity-title {
        font-weight: 600;
        color: #e6edf3;
      }
      .cg-entity-title i {
        color: #3498db;
      }
      .cg-btn-label {
        font-size: 11px;
      }

      .cg-legend {
        position: absolute;
        bottom: 14px;
        left: 14px;
        background: rgba(1, 4, 9, 0.92);
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 8px 12px;
        display: flex;
        flex-direction: column;
        gap: 3px;
        font-size: 10px;
        color: #c9d1d9;
        z-index: 10;
      }
      .cg-leg-title {
        font-weight: 600;
        font-size: 11px;
        margin-bottom: 3px;
        color: #e6edf3;
      }
      .cg-leg-row {
        display: flex;
        align-items: center;
        gap: 6px;
      }
      .cg-dot {
        width: 9px;
        height: 9px;
        border-radius: 50%;
        flex-shrink: 0;
      }

      .cg-mode-hint {
        position: absolute;
        bottom: 14px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 11px;
        color: #484f58;
        display: flex;
        align-items: center;
        gap: 6px;
        background: rgba(1, 4, 9, 0.85);
        padding: 5px 14px;
        border-radius: 20px;
        z-index: 10;
        white-space: nowrap;
      }

      .cg-tooltip {
        position: absolute;
        background: rgba(22, 27, 34, 0.96);
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 11px;
        color: #e6edf3;
        z-index: 100;
        pointer-events: none;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
        min-width: 150px;
      }
      .cg-tooltip-cluster {
        font-size: 9px;
        color: #58a6ff;
        margin-bottom: 3px;
      }
      .cg-tooltip-cat {
        font-size: 9px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #58a6ff;
        margin-bottom: 3px;
      }
      .cg-tooltip-name {
        font-weight: 600;
        font-size: 12px;
        margin-bottom: 4px;
      }
      .cg-tooltip-status {
        font-size: 10px;
        padding: 2px 8px;
        border-radius: 8px;
        display: inline-block;
      }
      .cg-tooltip-status.matched {
        background: rgba(46, 204, 113, 0.15);
        color: #2ecc71;
      }
      .cg-tooltip-status.orphan_analysis {
        background: rgba(231, 76, 60, 0.15);
        color: #e74c3c;
      }
      .cg-tooltip-status.orphan_contract {
        background: rgba(241, 196, 15, 0.15);
        color: #f1c40f;
      }
      .cg-tooltip-status.mismatch {
        background: rgba(230, 126, 34, 0.15);
        color: #e67e22;
      }
    `,
  ],
})
export class ContractGraphComponent implements AfterViewInit, OnDestroy, OnChanges {
  @Input() traceMatrix: Record<
    string,
    Array<{
      analysis_name: string | null;
      contract_id: string | null;
      status: string;
      contract_node?: any;
    }>
  > = {};

  @Input() graph:
    | {
        nodes: Array<{
          uid: string;
          label: string;
          category: string;
          status: string;
          fields?: Array<{ name: string; type: string; is_pk?: boolean; is_fk?: boolean }>;
          foreign_keys?: Array<{ field: string; target_entity: string; cardinality: string }>;
        }>;
        edges: Array<{ from: string; to: string; type: string; cardinality?: string }>;
      }
    | null
    | undefined = null;

  private p5Inst: p5 | null = null;
  clusters: Cluster[] = [];
  floatingClusters: Cluster[] = [];
  intraEdges: Edge[] = [];
  crossEdges: Edge[] = [];
  private uidMap = new Map<string, Node>();

  private panX = 0;
  private panY = 0;
  private zoom = 1;
  private targetZoom = 1;
  private targetPanX = 0;
  private targetPanY = 0;
  private rebuildTimer: any = null;
  private pendingRebuild = false;

  isFullscreen = false;
  selectedEntity: string | null = null;
  selectedUIComponent: { uid: string; data: { label: string; properties: Record<string, any>; componentType: string; fields: Array<{ name: string; type: string }> } } | null = null;
  totalCount = 0;
  tooltipNode: Node | null = null;
  tooltipX = 0;
  tooltipY = 0;

  private flowNodes: Node[] = [];
  private flowEdges: Edge[] = [];
  private flowColumnHeights: { top: number; bottom: number } | null = null;

  // Sequence diagram state (Level 2)
  private seqLifelines: SeqLifeline[] = [];
  private seqMessages: SeqMessage[] = [];
  private flowLifelineTop = 0;
  private flowLifelineBottom = 0;
  private uiComponentBounds: Array<{ uid: string; x: number; y: number; w: number; h: number }> = [];

  private erdEntities: ERDEntity[] = [];
  private erdEdges: ERDEdge[] = [];

  legendItems = [
    { label: 'matched', color: '#2ecc71' },
    { label: 'orphan_analysis (in brief, missing contract)', color: '#ef4444' },
    { label: 'orphan_contract (in contract, missing brief)', color: '#eab308' },
    { label: 'mismatch', color: '#e67e22' },
  ];

  constructor(
    private el: ElementRef,
    private ngZone: NgZone,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['traceMatrix'] || changes['graph']) {
      this.selectedEntity = null;
      this.isFullscreen = false;
      // If p5 not ready, just mark pending — sk.setup will handle it
      if (!this.p5Inst) {
        this.pendingRebuild = true;
        return;
      }
      // Rebuild synchronously — no debounce needed
      this.ngZone.runOutsideAngular(() => this.rebuild());
    }
  }

  // ── Fullscreen ──────────────────────────────────────────

  toggleFullscreen($event: Event): void {
    $event?.stopPropagation();
    this.isFullscreen ? this.exitFullscreen() : this.enterFullscreen();
  }

  enterFullscreen(): void {
    this.isFullscreen = true;
    this.panX = 0;
    this.panY = 0;
    this.zoom = 0.7;
    this.targetPanX = 0;
    this.targetPanY = 0;
    this.targetZoom = 0.7;
    this.ngZone.run(() => this.cdr.detectChanges());
    requestAnimationFrame(() => this.resizeAndRebuild());
  }

  exitFullscreen(): void {
    this.isFullscreen = false;
    this.panX = 0;
    this.panY = 0;
    this.ngZone.run(() => this.cdr.detectChanges());
    requestAnimationFrame(() => this.resizeAndRebuild());
  }

  // ── Entity Detail Navigation ────────────────────────────

  selectEntity(entityName: string): void {
    this.selectedEntity = entityName;
    this.panX = 0;
    this.panY = 0;
    this.zoom = 1;
    this.targetPanX = 0;
    this.targetPanY = 0;
    this.targetZoom = 1;
    this.computeEntityDetailLayout(entityName);
    // Auto-fit will happen after layout computes bounds
    this.ngZone.run(() => this.cdr.detectChanges());
    // Fit to screen after a frame
    requestAnimationFrame(() => this.autoFitSequenceDiagram());
  }

  private autoFitSequenceDiagram(): void {
    if (!this.selectedEntity || !this.p5Inst) return;
    const W = this.p5Inst.width;
    const H = this.p5Inst.height;
    const padding = 40;

    // Compute bounds of all flow nodes + lifelines
    let minX = Infinity,
      minY = Infinity,
      maxX = -Infinity,
      maxY = -Infinity;
    for (const n of this.flowNodes) {
      if (n.x - n.w / 2 < minX) minX = n.x - n.w / 2;
      if (n.x + n.w / 2 > maxX) maxX = n.x + n.w / 2;
      if (n.y - n.h / 2 < minY) minY = n.y - n.h / 2;
      if (n.y + n.h / 2 > maxY) maxY = n.y + n.h / 2;
    }
    // Also account for lifelines (extend to bottom)
    if (this.flowLifelineBottom && this.flowLifelineBottom > maxY) maxY = this.flowLifelineBottom;
    if (this.flowLifelineTop !== undefined && this.flowLifelineTop < minY)
      minY = this.flowLifelineTop;

    const contentW = maxX - minX + padding * 2;
    const contentH = maxY - minY + padding * 2;
    if (contentH <= 0 || contentW <= 0) return;

    // Fit to height first (primary constraint), then check width
    const zoomFitH = H / contentH;
    const zoomFitW = W / contentW;
    const zoom = Math.min(zoomFitH, zoomFitW, 1.5); // cap at 1.5x
    const finalZoom = Math.max(0.3, Math.min(zoom, 1.5));

    this.targetZoom = finalZoom;
    this.targetPanX = (W - contentW * finalZoom) / 2 - (minX - padding) * finalZoom;
    this.targetPanY = (H - contentH * finalZoom) / 2 - (minY - padding) * finalZoom;
    // Apply immediately
    this.zoom = this.targetZoom;
    this.panX = this.targetPanX;
    this.panY = this.targetPanY;
  }

  backToOverview($event?: Event): void {
    $event?.stopPropagation();
    this.selectedEntity = null;
    this.selectedUIComponent = null;
    this.panX = 0;
    this.panY = 0;
    this.zoom = 1;
    this.targetPanX = 0;
    this.targetPanY = 0;
    this.targetZoom = 1;
    this.ngZone.run(() => this.cdr.detectChanges());
  }

  backToFlow($event?: Event): void {
    $event?.stopPropagation();
    this.selectedUIComponent = null;
    this.ngZone.run(() => this.cdr.detectChanges());
  }

  private resizeAndRebuild(): void {
    if (!this.p5Inst) return;
    const box = this.el.nativeElement.querySelector('.cg-canvas');
    if (!box) return;
    const r = box.getBoundingClientRect();
    const w = r.width || 960;
    const h = r.height || (this.isFullscreen ? 700 : 420);
    this.p5Inst.resizeCanvas(w, h);
    this.rebuild();
  }

  resetView(): void {
    if (this.erdEntities.length === 0) {
      this.panX = 0;
      this.panY = 0;
      this.zoom = 1;
      this.targetPanX = 0;
      this.targetPanY = 0;
      this.targetZoom = 1;
      return;
    }

    // Compute bounding box of all ERD entities
    let minX = Infinity,
      minY = Infinity,
      maxX = -Infinity,
      maxY = -Infinity;
    for (const e of this.erdEntities) {
      if (e.x < minX) minX = e.x;
      if (e.y < minY) minY = e.y;
      if (e.x + e.w > maxX) maxX = e.x + e.w;
      if (e.y + e.h > maxY) maxY = e.y + e.h;
    }

    const W = this.p5Inst?.width || 960;
    const H = this.p5Inst?.height || 420;
    const contentW = maxX - minX;
    const contentH = maxY - minY;
    const padding = 60;

    // Fit to screen height (primary constraint)
    const zoomFitH = (H - padding * 2) / contentH;
    const zoomFitW = (W - padding * 2) / contentW;
    const zoom = Math.min(zoomFitH, zoomFitW, 2); // cap at 2x

    // Center content
    this.targetZoom = zoom;
    this.targetPanX = (W - contentW * zoom) / 2 - minX * zoom;
    this.targetPanY = (H - contentH * zoom) / 2 - minY * zoom;

    // Apply immediately for instant effect
    this.panX = this.targetPanX;
    this.panY = this.targetPanY;
    this.zoom = this.targetZoom;
  }

  // ── p5 sketch ───────────────────────────────────────────

  ngAfterViewInit(): void {
    this.ngZone.runOutsideAngular(() => {
      this.p5Inst = new p5((sk: p5) => {
        let isPanning = false;
        let panStartX = 0,
          panStartY = 0;

        sk.setup = () => {
          const box = this.el.nativeElement.querySelector('.cg-canvas');
          const r = box.getBoundingClientRect();
          const cv = sk.createCanvas(r.width || 960, r.height || 420);
          cv.parent(box);
          sk.textFont('sans-serif');
          // Don't call rebuild() here — let ngOnChanges handle it
          // This avoids clobbering data when inputs arrive before p5 is ready
          if (this.pendingRebuild) {
            this.pendingRebuild = false;
            this.ngZone.runOutsideAngular(() => this.rebuild());
          }
        };

        sk.draw = () => {
          sk.clear();
          sk.background(13, 17, 23);

          // Smooth zoom/pan (only effective in fullscreen mode)
          this.zoom += (this.targetZoom - this.zoom) * 0.12;
          this.panX += (this.targetPanX - this.panX) * 0.12;
          this.panY += (this.targetPanY - this.panY) * 0.12;

          sk.push();
          sk.translate(this.panX, this.panY);
          sk.scale(this.zoom);

          // ── Level 1: ERD / Level 2: flow / Level 3: wireframe ──
          if (this.selectedUIComponent) {
            this.drawWireframe(sk);
          } else if (this.selectedEntity) {
            this.drawEntityDetail(sk);
          } else {
            this.drawERD(sk);
          }
          sk.pop();

          // Hover tooltip — Level 1 only (Level 2 focuses on command drift, no hover)
          const wx = (sk.mouseX - this.panX) / this.zoom;
          const wy = (sk.mouseY - this.panY) / this.zoom;
          let hovered: Node | null = null;

          if (!this.selectedEntity) {
            // ERD overview: hover on entity boxes
            let hoveredEnt: ERDEntity | null = null;
            for (const e of this.erdEntities) {
              if (wx >= e.x && wx <= e.x + e.w && wy >= e.y && wy <= e.y + e.h) {
                hoveredEnt = e;
                break;
              }
            }
            if (hoveredEnt) {
              hovered = {
                uid: hoveredEnt.uid,
                label: hoveredEnt.label,
                category: 'entities',
                status: hoveredEnt.status,
                x: hoveredEnt.x,
                y: hoveredEnt.y,
                w: hoveredEnt.w,
                h: hoveredEnt.h,
                entityGroup: null,
              };
              for (const ent of this.erdEntities) ent.hovered = false;
              hoveredEnt.hovered = true;
            } else {
              for (const ent of this.erdEntities) ent.hovered = false;
            }
          }

          if (hovered && hovered.uid !== this.tooltipNode?.uid) {
            this.ngZone.run(() => {
              this.tooltipNode = hovered;
              this.tooltipX = Math.min(sk.mouseX + 16, sk.width - 180);
              this.tooltipY = Math.max(sk.mouseY - 60, 10);
              this.cdr.detectChanges();
            });
          } else if (!hovered && this.tooltipNode) {
            this.ngZone.run(() => {
              this.tooltipNode = null;
              this.cdr.detectChanges();
            });
          }
        };

        // ERD drag state
        let dragEntity: ERDEntity | null = null;
        let dragOffsetX = 0,
          dragOffsetY = 0;

        sk.mousePressed = () => {
          if (!this.selectedEntity) {
            const wx = (sk.mouseX - this.panX) / this.zoom;
            const wy = (sk.mouseY - this.panY) / this.zoom;
            for (const e of this.erdEntities) {
              if (wx >= e.x && wx <= e.x + e.w && wy >= e.y && wy <= e.y + e.h) {
                dragEntity = e;
                dragOffsetX = wx - e.x;
                dragOffsetY = wy - e.y;
                sk.cursor(sk.MOVE);
                return;
              }
            }
            // Click background → pan (both modes)
            isPanning = true;
            panStartX = sk.mouseX - this.targetPanX;
            panStartY = sk.mouseY - this.targetPanY;
            sk.cursor(sk.MOVE);
            return;
          }

          // ── Entity detail: click UI component → Level 3 wireframe ──
          if (this.selectedEntity && !this.selectedUIComponent) {
            const wx = (sk.mouseX - this.panX) / this.zoom;
            const wy = (sk.mouseY - this.panY) / this.zoom;
            for (const b of this.uiComponentBounds) {
              if (wx >= b.x && wx <= b.x + b.w && wy >= b.y && wy <= b.y + b.h) {
                // Find the uiComponentData for this UID
                // Use the lifelines to find the data
                const ll = this.seqLifelines.find((l) => l.uid === b.uid);
                if (ll && ll.category === 'ui_components') {
                  // Trigger from outside Angular
                  this.ngZone.run(() => {
                    this.selectedUIComponent = {
                      uid: b.uid,
                      data: {
                        label: ll.label,
                        properties: ll.properties || {},
                        componentType: ll.componentType || '',
                        fields: ll.fields || [],
                      },
                    };
                    this.cdr.detectChanges();
                  });
                  return;
                }
              }
            }
          }

          // ── Entity detail: allow panning ──
          isPanning = true;
          panStartX = sk.mouseX - this.targetPanX;
          panStartY = sk.mouseY - this.targetPanY;
          sk.cursor(sk.MOVE);
        };

        sk.mouseDragged = () => {
          if (dragEntity) {
            const wx = (sk.mouseX - this.panX) / this.zoom;
            const wy = (sk.mouseY - this.panY) / this.zoom;
            dragEntity.x = wx - dragOffsetX;
            dragEntity.y = wy - dragOffsetY;
          }
          if (isPanning) {
            this.targetPanX = sk.mouseX - panStartX;
            this.targetPanY = sk.mouseY - panStartY;
          }
        };

        sk.mouseReleased = () => {
          if (dragEntity) {
            dragEntity = null;
            sk.cursor(sk.ARROW);
          }
          if (isPanning) {
            isPanning = false;
            sk.cursor(sk.ARROW);
          }
        };

        sk.mouseWheel = (e?: WheelEvent) => {
          // Zoom only when cursor is inside canvas bounds
          const mx = sk.mouseX;
          const my = sk.mouseY;
          if (mx < 0 || my < 0 || mx > sk.width || my > sk.height) return;

          // Prevent page scroll when zooming in canvas
          if (e) {
            (e as any).preventDefault();
            (e as any).stopPropagation();
          }

          // Zoom in both modes
          const delta = (e as any)?.delta > 0 ? 0.95 : 1.05;
          const nz = Math.max(0.15, Math.min(4, this.targetZoom * delta));
          const cx = sk.mouseX - this.panX;
          const cy = sk.mouseY - this.panY;
          this.targetPanX += cx * (1 - nz / this.targetZoom);
          this.targetPanY += cy * (1 - nz / this.targetZoom);
          this.targetZoom = nz;
        };

        sk.doubleClicked = () => {
          // Double-click ERD entity box → select entity for Level 2
          if (!this.selectedEntity) {
            const wx = (sk.mouseX - this.panX) / this.zoom;
            const wy = (sk.mouseY - this.panY) / this.zoom;
            for (const e of this.erdEntities) {
              if (wx >= e.x && wx <= e.x + e.w && wy >= e.y && wy <= e.y + e.h) {
                this.ngZone.run(() => this.selectEntity(e.label));
                return;
              }
            }
          }
        };

        sk.keyPressed = () => {
          if (sk.keyCode === 27 && this.isFullscreen) this.ngZone.run(() => this.exitFullscreen());
          if (sk.keyCode === 27 && this.selectedEntity && !this.isFullscreen)
            this.ngZone.run(() => this.backToOverview());
        };

        sk.windowResized = () => {
          const box = this.el.nativeElement.querySelector('.cg-canvas');
          if (box) {
            const r = box.getBoundingClientRect();
            sk.resizeCanvas(r.width || 960, r.height || 420);
            this.rebuild();
          }
        };
      });
    });
  }

  ngOnDestroy(): void {
    clearTimeout(this.rebuildTimer);
    this.p5Inst?.remove();
    this.p5Inst = null;
  }

  // ── rebuild ─────────────────────────────────────────────

  rebuild(): void {
    // ── 1. Build ERD from this.graph ──
    this.buildERD();

    // ── 2. Build clusters from traceMatrix (Level 2) ──
    const norm = (s: string) =>
      s
        .replace(/-/g, '_')
        .replace(/([a-z])([A-Z])/g, '$1_$2')
        .toLowerCase();
    const catRows = Object.entries(this.traceMatrix);

    // 1. Collect entity names — ONLY from MATCHED rows to avoid orphans as entity groups
    const entityNames = new Set<string>();
    const entityNormMap = new Map<string, string>(); // norm → canonical entity name
    const entityCanonicalNorm = new Set<string>(); // set of normalized canonical entity names

    for (const row of this.traceMatrix['entities'] || []) {
      // Prefer contract_id (canonical snake_case), fall back to analysis_name
      const name = row.contract_id || row.analysis_name || '';
      if (!name) continue;
      entityNames.add(name);
      const n = norm(name);
      entityCanonicalNorm.add(n);
      if (!entityNormMap.has(n)) entityNormMap.set(n, name);
    }

    // Build bidirectional mapping: analysis_name ↔ contract_id (only matched rows)
    const contractEntityToAnalysis = new Map<string, string>(); // contract name → analysis name
    const analysisEntityToContract = new Map<string, string>(); // analysis name → contract name
    for (const row of this.traceMatrix['entities'] || []) {
      if (row.status !== 'matched') continue;
      const aName = row.analysis_name || '';
      const cName = row.contract_id || '';
      if (aName && cName) {
        contractEntityToAnalysis.set(cName, aName);
        contractEntityToAnalysis.set(norm(cName), aName);
        analysisEntityToContract.set(aName, cName);
        analysisEntityToContract.set(norm(aName), cName);
      }
    }

    // Fuzzy: contract entity → analysis entity (word overlap, only for unmatched contract names)
    for (const row of this.traceMatrix['entities'] || []) {
      const aName = row.analysis_name || '';
      const cName = row.contract_id || '';
      if (aName && cName && !contractEntityToAnalysis.has(cName)) {
        const cWords = new Set(
          norm(cName)
            .split('_')
            .filter((w) => w.length > 2),
        );
        const aWords = new Set(
          norm(aName)
            .split('_')
            .filter((w) => w.length > 2),
        );
        let overlap = 0;
        for (const w of cWords) if (aWords.has(w)) overlap++;
        if (overlap >= 1) contractEntityToAnalysis.set(cName, aName);
      }
    }

    const findEntity = (ref: string): string | null => {
      if (!ref) return null;
      if (entityNames.has(ref)) return ref;
      const nRef = norm(ref);
      if (entityNormMap.has(nRef)) return entityNormMap.get(nRef)!;
      if (contractEntityToAnalysis.has(ref)) return contractEntityToAnalysis.get(ref)!;
      return null;
    };

    // Also build a fuzzy entity matcher: given any ref string, try to find entity by substring
    const fuzzyFindEntity = (ref: string): string | null => {
      if (!ref) return null;
      const direct = findEntity(ref);
      if (direct) return direct;

      const nRef = norm(ref);
      // Try to find an entity whose normalized name is contained in the ref or vice versa
      for (const entName of entityNames) {
        const entNorm = norm(entName);
        if (nRef.includes(entNorm) || entNorm.includes(nRef)) return entName;
      }
      return null;
    };

    const guessEntityFromName = (name: string): string | null => {
      const n = norm(name);

      // Strategy 1: PascalCase — strip verb prefix, check if remainder matches entity
      const pascalPrefix = name.match(
        /^(Create|Update|Delete|List|Get|SoftDelete|Search|Export|Complete|Execute|Validate)(.+)$/,
      );
      if (pascalPrefix) {
        const remainder = pascalPrefix[2];
        const rNorm = norm(remainder);
        if (entityCanonicalNorm.has(rNorm)) return entityNormMap.get(rNorm)!;
        if (entityNames.has(remainder)) return remainder;
      }

      // Strategy 2: snake_case — prefix match with entity + "_"
      // Only consider entity names >= 5 chars to avoid false positives (e.g. "stock" matching "stock_in")
      // Prefer the LONGEST matching entity prefix (most specific match wins)
      // CRITICAL: skip if remainder matches another entity (e.g. "stock_in_item" should match "stock_in_item", not "stock")
      let bestMatch: string | null = null;
      let bestLen = 0;
      for (const entNorm of entityCanonicalNorm) {
        if (entNorm.length < 5 || n === entNorm) continue;
        if (n.startsWith(entNorm + '_')) {
          const remainder = n.slice(entNorm.length + 1);
          if (remainder.length < 2) continue;
          // Skip if remainder itself matches another entity (more specific match wins)
          if (entityCanonicalNorm.has(remainder)) continue;
          if (remainder.startsWith(entNorm + '_')) continue; // skip sub-sub prefixes like "stock_in_item" matching "stock"
          if (entNorm.length > bestLen) {
            bestMatch = entityNormMap.get(entNorm)!;
            bestLen = entNorm.length;
          }
        }
      }
      if (bestMatch) return bestMatch;

      // Strategy 3: strip verb prefix, then check prefix match
      const stripped = n.replace(
        /^(create_|update_|delete_|list_|get_|soft_delete_|search_|export_|complete_|execute_|validate_|must_have_|must_be_|form_|menu_)/,
        '',
      );
      if (stripped !== n) {
        let sBestMatch: string | null = null;
        let sBestLen = 0;
        for (const entNorm of entityCanonicalNorm) {
          if (entNorm.length < 5 || stripped === entNorm) continue;
          if (stripped.startsWith(entNorm + '_')) {
            const remainder = stripped.slice(entNorm.length + 1);
            if (remainder.length >= 2 && entNorm.length > sBestLen) {
              sBestMatch = entityNormMap.get(entNorm)!;
              sBestLen = entNorm.length;
            }
          }
          // Also exact match after stripping
          if (stripped === entNorm && entNorm.length > sBestLen) {
            sBestMatch = entityNormMap.get(entNorm)!;
            sBestLen = entNorm.length;
          }
        }
        if (sBestMatch) return sBestMatch;
      }

      // Strategy 4: English plural — strip trailing 's'
      if (n.endsWith('s') && entityCanonicalNorm.has(n.slice(0, -1))) {
        return entityNormMap.get(n.slice(0, -1))!;
      }

      return null;
    };

    // 2. Build command → entity map
    const cmdToEntity = new Map<string, string>();
    for (const row of this.traceMatrix['commands'] || []) {
      const name = row.analysis_name || row.contract_id || '';
      const cn = row.contract_node;
      if (!name) continue;

      // Try to resolve entity from contract_node fields
      let e: string | null = null;
      if (cn) {
        for (const ref of cn.writes_to || []) {
          e = fuzzyFindEntity(String(ref));
          if (e) break;
        }
        if (!e)
          for (const f of cn.fetches || []) {
            if (typeof f === 'object') {
              e = fuzzyFindEntity((f as any).entity || (f as any).entity_id || '');
              if (e) break;
            }
          }
      }
      if (!e) e = guessEntityFromName(name);
      if (e) {
        cmdToEntity.set(name, e);
        cmdToEntity.set(norm(name), e);
      }
    }

    // 2b. Build guard → entity map from command.guards[] (reverse lookup)
    const guardToCmd = new Map<string, string>();
    for (const row of this.traceMatrix['commands'] || []) {
      const cmdName = row.analysis_name || row.contract_id || '';
      const cn = row.contract_node;
      if (!cmdName || !cn) continue;
      for (const g of cn.guards || []) {
        const guardId = typeof g === 'string' ? g : (g as any).id || (g as any).guard || '';
        if (guardId) {
          guardToCmd.set(guardId, cmdName);
          guardToCmd.set(norm(guardId), norm(cmdName));
        }
      }
    }

    // Also build a map: guard name → entity by parsing condition.check for entity name
    const guardNameToEntity = new Map<string, string>();
    for (const row of this.traceMatrix['guards'] || []) {
      const guardName = row.analysis_name || row.contract_id || '';
      const cn = row.contract_node;
      if (!guardName) continue;
      let ent: string | null = null;
      // Try parsing condition.check: e.g., "product.exists" → "product"
      if (cn && cn.condition && typeof cn.condition.check === 'string') {
        const parts = cn.condition.check.split('.');
        if (parts.length >= 2) ent = fuzzyFindEntity(parts[0]);
      }
      // Try condition.value for entity references
      if (!ent && cn && cn.condition && cn.condition.value) {
        // Some guards reference entities in error messages
      }
      if (ent) guardNameToEntity.set(guardName, ent);
      if (ent) guardNameToEntity.set(norm(guardName), ent);
    }

    // 3. Create nodes with entityGroup resolution
    const allNodes: Node[] = [];
    const uidMap = new Map<string, Node>();

    for (const [cat, rows] of catRows) {
      for (const row of rows) {
        const name = row.analysis_name || row.contract_id || '';
        if (!name) continue;
        const cn = row.contract_node;
        let entityGroup: string | null = null;

        if (cat === 'entities') {
          entityGroup = name;
        } else if (cat === 'commands') {
          entityGroup =
            cmdToEntity.get(name) ||
            cmdToEntity.get(norm(name)) ||
            guessEntityFromName(name) ||
            null;
        } else if (cat === 'queries') {
          if (cn) {
            for (const ref of cn.reads_from || []) {
              entityGroup = fuzzyFindEntity(String(ref));
              if (entityGroup) break;
            }
            if (!entityGroup)
              for (const f of cn.fetches || []) {
                if (typeof f === 'object') {
                  entityGroup = fuzzyFindEntity((f as any).entity || (f as any).entity_id || '');
                  if (entityGroup) break;
                }
              }
          }
          if (!entityGroup) entityGroup = guessEntityFromName(name);
        } else if (cat === 'events') {
          if (cn) entityGroup = fuzzyFindEntity(cn.source_entity || '');
          if (!entityGroup) entityGroup = guessEntityFromName(name);
        } else if (cat === 'ui_components') {
          if (cn) entityGroup = fuzzyFindEntity(cn.entity_id || '');
          if (!entityGroup) entityGroup = guessEntityFromName(name);
        } else if (cat === 'guards') {
          // Strategy 1: direct target
          const guardTarget = cn?.target || '';
          if (guardTarget) {
            const targetCmdEntity =
              cmdToEntity.get(guardTarget) || cmdToEntity.get(norm(guardTarget));
            if (targetCmdEntity) entityGroup = targetCmdEntity;
          }
          // Strategy 2: reverse lookup from command.guards[]
          if (!entityGroup) {
            const linkedCmd = guardToCmd.get(name) || guardToCmd.get(norm(name));
            if (linkedCmd)
              entityGroup = cmdToEntity.get(linkedCmd) || cmdToEntity.get(norm(linkedCmd)) || null;
          }
          // Strategy 3: parse condition.check for entity name
          if (!entityGroup)
            entityGroup = guardNameToEntity.get(name) || guardNameToEntity.get(norm(name)) || null;
          // Strategy 4: name-based heuristic
          if (!entityGroup) entityGroup = guessEntityFromName(name);
        } else if (cat === 'workflows') {
          if (cn) {
            for (const trans of cn.transitions || []) {
              if (typeof trans === 'object') {
                const cmd = (trans as any).on || (trans as any).command;
                if (cmd) {
                  entityGroup = cmdToEntity.get(cmd) || cmdToEntity.get(norm(cmd)) || null;
                  if (entityGroup) break;
                }
              }
            }
          }
          if (!entityGroup) entityGroup = guessEntityFromName(name);
        } else if (cat === 'value_objects') {
          // Value objects often relate to entities by name similarity
          entityGroup = guessEntityFromName(name);
        } else if (cat === 'roles') {
          // Roles are global, don't assign to a specific entity cluster
          entityGroup = null;
        }

        allNodes.push({
          uid: `${cat}:${name}`,
          label: name,
          category: cat,
          status: row.status || 'matched',
          x: 0,
          y: 0,
          w: 90,
          h: 22,
          entityGroup,
        });
        uidMap.set(`${cat}:${name}`, allNodes[allNodes.length - 1]);
      }
    }

    // 4. Build edges
    const allEdges: Edge[] = [];
    for (const [cat, rows] of catRows) {
      for (const row of rows) {
        const name = row.analysis_name || row.contract_id || '';
        const cn = row.contract_node;
        if (!name || !cn) continue;
        const addEdge = (from: string, to: string, type: string) => {
          if (uidMap.has(from) && uidMap.has(to)) allEdges.push({ from, to, type });
        };

        if (cat === 'commands') {
          for (const ref of cn.writes_to || []) {
            const t = findEntity(String(ref));
            if (t) addEdge(`${cat}:${name}`, `entities:${t}`, 'writes_to');
          }
          for (const f of cn.fetches || []) {
            if (typeof f === 'object') {
              const t = findEntity((f as any).entity || (f as any).entity_id || '');
              if (t) addEdge(`${cat}:${name}`, `entities:${t}`, 'fetches');
            }
          }
          for (const evt of cn.emits || []) addEdge(`${cat}:${name}`, `events:${evt}`, 'emits');
        }
        if (cat === 'queries') {
          for (const ref of cn.reads_from || []) {
            const t = findEntity(String(ref));
            if (t) addEdge(`${cat}:${name}`, `entities:${t}`, 'reads_from');
          }
          for (const f of cn.fetches || []) {
            if (typeof f === 'object') {
              const t = findEntity((f as any).entity || (f as any).entity_id || '');
              if (t) addEdge(`${cat}:${name}`, `entities:${t}`, 'fetches');
            }
          }
        }
        if (cat === 'events') {
          const t = findEntity(cn.source_entity || '');
          if (t) addEdge(`${cat}:${name}`, `entities:${t}`, 'source_entity');
        }
        if (cat === 'workflows') {
          for (const trans of cn.transitions || []) {
            if (typeof trans === 'object') {
              const cmd = (trans as any).on || (trans as any).command;
              if (cmd) addEdge(`${cat}:${name}`, `commands:${cmd}`, 'uses_command');
            }
          }
        }
        if (cat === 'ui_components') {
          const t = findEntity(cn.entity_id || '');
          if (t) addEdge(`${cat}:${name}`, `entities:${t}`, 'entity_ref');
        }
        if (cat === 'guards') {
          const t = cn.target || '';
          if (t) addEdge(`${cat}:${name}`, `commands:${t}`, 'guards');
        }
      }
    }

    // Deduplicate
    const seen = new Set<string>();
    for (const e of allEdges) seen.add(`${e.from}|${e.to}|${e.type}`);

    // 5. Separate intra vs cross cluster edges
    this.intraEdges = [];
    this.crossEdges = [];
    for (const e of allEdges) {
      const a = uidMap.get(e.from),
        b = uidMap.get(e.to);
      if (!a || !b) continue;
      if (a.entityGroup && b.entityGroup && a.entityGroup === b.entityGroup)
        this.intraEdges.push(e);
      else this.crossEdges.push(e);
    }

    // 6. Group into clusters
    const clusterMap = new Map<string, Cluster>();
    const floatingMap = new Map<string, Node[]>();

    for (const n of allNodes) {
      if (n.category === 'entities') {
        if (!clusterMap.has(n.entityGroup!)) {
          clusterMap.set(n.entityGroup!, {
            name: n.entityGroup!,
            entityNode: n,
            commands: [],
            queries: [],
            events: [],
            other: [],
            x: 0,
            y: 0,
            w: 0,
            h: 0,
            healthScore: 100,
            hasDrift: false,
          });
        }
      } else if (n.entityGroup && clusterMap.has(n.entityGroup)) {
        const c = clusterMap.get(n.entityGroup)!;
        if (n.category === 'commands') c.commands.push(n);
        else if (n.category === 'queries') c.queries.push(n);
        else if (n.category === 'events') c.events.push(n);
        else c.other.push(n);
      } else {
        if (!floatingMap.has(n.category)) floatingMap.set(n.category, []);
        floatingMap.get(n.category)!.push(n);
      }
    }

    // 7. Health score per cluster
    let allClList: Cluster[] = [];
    for (const c of clusterMap.values()) {
      const allN = [c.entityNode, ...c.commands, ...c.queries, ...c.events, ...c.other] as Node[];
      let score = 100;
      for (const n of allN) {
        if (n.status === 'orphan_analysis') score -= 10;
        else if (n.status === 'orphan_contract') score -= 2;
        else if (n.status === 'mismatch') score -= 5;
      }
      c.healthScore = Math.max(0, score);
      c.hasDrift = allN.some((n) => n.status !== 'matched');
      allClList.push(c);
    }

    // 7b. Merge small clusters — only merge known sub-entities into parents
    const mergeSmallClusters = (clusters: Cluster[]): Cluster[] => {
      const clusterSize = (c: Cluster) =>
        (c.entityNode ? 1 : 0) +
        c.commands.length +
        c.queries.length +
        c.events.length +
        c.other.length;

      // Domain merge rules: only explicit sub-entity → parent relationships
      // E.g. StockSlipItem is a child of StockSlip. Independent entities (Product, Warehouse, etc.) stay separate.
      const domainMergeRules: Record<string, string[]> = {
        StockSlip: ['stockslipitem'],
      };

      const shouldMergeInto = (childName: string): string | null => {
        const childNorm = norm(childName);
        for (const [parent, children] of Object.entries(domainMergeRules)) {
          if (!clusters.some((c) => norm(c.name) === norm(parent))) continue;
          for (const child of children) {
            if (childNorm === norm(child)) return parent;
          }
        }
        return null;
      };

      const sorted = [...clusters].sort((a, b) => clusterSize(b) - clusterSize(a));
      const merged = new Map<string, Cluster>();
      const removed = new Set<string>();
      for (const c of sorted) merged.set(c.name, c);

      // Phase 1: Domain-specific merges (explicit sub-entities only)
      for (const c of sorted) {
        if (removed.has(c.name)) continue;
        const targetName = shouldMergeInto(c.name);
        if (targetName) {
          let target: Cluster | null = null;
          for (const m of merged.values()) {
            if (norm(m.name) === norm(targetName) && !removed.has(m.name)) {
              target = m;
              break;
            }
          }
          if (target) {
            if (c.entityNode) target.other.push(c.entityNode);
            target.commands.push(...c.commands);
            target.queries.push(...c.queries);
            target.events.push(...c.events);
            target.other.push(...c.other);
            const mNodes = [
              target.entityNode,
              ...target.commands,
              ...target.queries,
              ...target.events,
              ...target.other,
            ] as Node[];
            let newScore = 100;
            for (const n of mNodes) {
              if (n.status === 'orphan_analysis') newScore -= 10;
              else if (n.status === 'orphan_contract') newScore -= 2;
              else if (n.status === 'mismatch') newScore -= 5;
            }
            target.healthScore = Math.max(0, newScore);
            target.hasDrift = mNodes.some((n) => n.status !== 'matched');
            removed.add(c.name);
          }
        }
      }

      // Phase 2: Deduplicate exact same-entity clusters (norm name collision only)
      // This handles the edge case where the same entity appears under both analysis_name and contract_id
      for (const c of sorted) {
        if (removed.has(c.name) || clusterSize(c) > 1) continue;
        const cNorm = norm(c.name);
        for (const targetName of merged.keys()) {
          if (targetName === c.name || removed.has(targetName)) continue;
          if (norm(targetName) === cNorm) {
            const target = merged.get(targetName)!;
            if (c.entityNode) target.other.push(c.entityNode);
            target.commands.push(...c.commands);
            target.queries.push(...c.queries);
            target.events.push(...c.events);
            target.other.push(...c.other);
            removed.add(c.name);
            break;
          }
        }
      }

      return [...merged.values()].filter((c) => !removed.has(c.name));
    };

    allClList = mergeSmallClusters(allClList);

    // Floating clusters
    this.floatingClusters = [];
    const floatingLabels: Record<string, string> = {
      workflows: 'Workflows',
      value_objects: 'Value Objects',
      roles: 'Roles',
      guards: 'Guards',
    };
    for (const [cat, nodes] of floatingMap) {
      if (nodes.length === 0) continue;
      this.floatingClusters.push({
        name: floatingLabels[cat] || cat,
        entityNode: null,
        commands: [],
        queries: [],
        events: [],
        other: nodes,
        x: 0,
        y: 0,
        w: 0,
        h: 0,
        healthScore: 100,
        hasDrift: nodes.some((n) => n.status !== 'matched'),
      });
    }

    allClList.sort((a, b) => a.healthScore - b.healthScore);
    this.clusters = allClList;
    this.uidMap = uidMap;

    // 7c. Compute worst drift status for ERD entities based on ALL nodes grouped by entityGroup
    const statusSeverity: Record<string, number> = {
      orphan_analysis: 4,
      mismatch: 3,
      orphan_contract: 2,
      matched: 1,
      default: 1,
    };

    // Collect worst status per entityGroup from allNodes
    const groupWorst = new Map<string, string>();
    for (const node of allNodes) {
      if (!node.entityGroup) continue;
      const current = groupWorst.get(node.entityGroup);
      const sev = statusSeverity[node.status] || 1;
      const curSev = current ? statusSeverity[current] || 1 : 1;
      if (sev > curSev) groupWorst.set(node.entityGroup, node.status);
    }

    // Apply worst status to ERD entities
    for (const ent of this.erdEntities) {
      // Match by normalized entityGroup name
      const entNorm = norm(ent.label);
      for (const [groupName, status] of groupWorst) {
        if (norm(groupName) === entNorm) {
          ent.status = status;
          break;
        }
      }
    }

    // 8. Layout
    this.computeLayout();
    this.computeERDLayout();
    this.totalCount = allNodes.length;
    this.ngZone.run(() => this.cdr.detectChanges());
  }

  // ── ERD data build from this.graph ──────────────────────

  private buildERD(): void {
    const graphNodes = this.graph?.nodes || [];
    const graphEdges = this.graph?.edges || [];
    const entityNodes = graphNodes.filter((n) => n.category === 'entities');

    const uidToEntity = new Map<string, ERDEntity>();
    const labelToEntity = new Map<string, ERDEntity>();
    const labelNorm = (s: string) =>
      s
        .replace(/-/g, '_')
        .replace(/([a-z])([A-Z])/g, '$1_$2')
        .toLowerCase();

    this.erdEntities = entityNodes.map((n) => {
      const fields = (n.fields || []).map((f) => ({
        name: f.name,
        type: f.type,
        is_pk: !!f.is_pk,
        is_fk: !!f.is_fk,
      }));
      const foreignKeys = (n.foreign_keys || []).map((fk) => ({
        field: fk.field,
        target_entity: fk.target_entity,
        cardinality: fk.cardinality || 'N:1',
      }));

      const ent: ERDEntity = {
        uid: n.uid,
        label: n.label,
        status: n.status || 'matched',
        x: 0,
        y: 0,
        w: 0,
        h: 0,
        fields,
        foreignKeys,
        hovered: false,
      };
      uidToEntity.set(n.uid, ent);
      labelToEntity.set(n.label, ent);
      labelToEntity.set(labelNorm(n.label), ent);
      return ent;
    });

    // Build edges from graphEdges (backend FK edges)
    const edgeSet = new Set<string>(); // deduplicate by "from_label→to_label"
    const allEdges: ERDEdge[] = [];

    for (const ge of graphEdges) {
      if (ge.type !== 'foreign_key') continue;
      const from = uidToEntity.get(ge.from) || null;
      const to = uidToEntity.get(ge.to) || null;
      if (from && to) {
        const key = `${from.label}→${to.label}`;
        if (!edgeSet.has(key)) {
          edgeSet.add(key);
          allEdges.push({ from, to, type: ge.type, cardinality: ge.cardinality || 'N:1' });
        }
      }
    }

    // Also build edges from each entity's foreign_keys[] (may not be in graphEdges)
    for (const ent of this.erdEntities) {
      for (const fk of ent.foreignKeys) {
        let target: ERDEntity | null = null;
        // Try exact label match
        target =
          labelToEntity.get(fk.target_entity) ||
          labelToEntity.get(labelNorm(fk.target_entity)) ||
          null;
        if (target) {
          const key = `${ent.label}→${target.label}`;
          if (!edgeSet.has(key)) {
            edgeSet.add(key);
            allEdges.push({
              from: ent,
              to: target,
              type: 'foreign_key',
              cardinality: fk.cardinality || 'N:1',
            });
          }
        }
      }
    }

    this.erdEdges = allEdges;
  }

  // ── Auto Arrange — hierarchical layout minimizing line-entity crossings ──

  autoArrange(event: Event): void {
    event?.stopPropagation();
    if (this.erdEntities.length === 0) return;

    // Build adjacency + in-degree from FK edges
    const labelIdx = new Map<string, number>();
    this.erdEntities.forEach((e, i) => labelIdx.set(e.label, i));

    const adj: number[][] = Array.from({ length: this.erdEntities.length }, () => []);
    const inDegree = new Array(this.erdEntities.length).fill(0);

    for (const edge of this.erdEdges) {
      if (!edge.from || !edge.to) continue;
      const fi = labelIdx.get(edge.from.label);
      const ti = labelIdx.get(edge.to.label);
      if (fi === undefined || ti === undefined || fi === ti) continue;
      adj[fi].push(ti);
      inDegree[ti]++;
    }

    // Longest-path layering: entities with no incoming FK are layer 0 (leftmost)
    const layer = new Array(this.erdEntities.length).fill(0);
    const queue: number[] = [];
    const dist = new Array(this.erdEntities.length).fill(0);

    for (let i = 0; i < inDegree.length; i++) {
      if (inDegree[i] === 0) {
        queue.push(i);
        dist[i] = 0;
      }
    }

    const tempIn = [...inDegree];
    while (queue.length > 0) {
      const u = queue.shift()!;
      layer[u] = dist[u];
      for (const v of adj[u]) {
        dist[v] = Math.max(dist[v], dist[u] + 1);
        tempIn[v]--;
        if (tempIn[v] === 0) queue.push(v);
      }
    }

    // Handle cycles — assign to layer 0
    for (let i = 0; i < inDegree.length; i++) {
      if (tempIn[i] > 0) layer[i] = 0;
    }

    // Group by layer
    const layers = new Map<number, number[]>();
    for (let i = 0; i < this.erdEntities.length; i++) {
      if (!layers.has(layer[i])) layers.set(layer[i], []);
      layers.get(layer[i])!.push(i);
    }

    // Barycenter crossing minimization
    const sortedLayers = Array.from(layers.keys()).sort((a, b) => a - b);

    for (const l of sortedLayers) {
      const group = layers.get(l)!;
      if (l === sortedLayers[0]) continue;
      const prevLayer = layers.get(sortedLayers[sortedLayers.indexOf(l) - 1])!;
      const prevOrder = new Map<number, number>();
      prevLayer.forEach((idx, pos) => prevOrder.set(idx, pos));

      group.sort((a, b) => {
        const aNeighbors = adj[a].filter((n) => prevOrder.has(n));
        const bNeighbors = adj[b].filter((n) => prevOrder.has(n));
        const aBar =
          aNeighbors.length > 0
            ? aNeighbors.reduce((s, n) => s + prevOrder.get(n)!, 0) / aNeighbors.length
            : 999;
        const bBar =
          bNeighbors.length > 0
            ? bNeighbors.reduce((s, n) => s + prevOrder.get(n)!, 0) / bNeighbors.length
            : 999;
        return aBar - bBar;
      });
    }

    // Assign coordinates: layers as columns (left to right)
    const boxW = 200;
    const gapX = 80;
    const gapY = 28;
    const marginX = 40;
    const marginY = 20;

    for (let ci = 0; ci < sortedLayers.length; ci++) {
      const group = layers.get(sortedLayers[ci])!;
      const colX = marginX + ci * (boxW + gapX);
      for (let ri = 0; ri < group.length; ri++) {
        const idx = group[ri];
        const e = this.erdEntities[idx];
        e.x = colX;
        e.y = marginY + ri * (e.h + gapY);
      }
    }

    // Force canvas redraw without calling rebuild() (which would reset grid layout)
    this.ngZone.run(() => {
      this.cdr.detectChanges();
      if (this.p5Inst) this.p5Inst.redraw();
    });
  }

  // ── ERD layout (grid) ───────────────────────────────────

  private computeERDLayout(): void {
    if (this.erdEntities.length === 0) return;
    const W = this.p5Inst?.width || 960;
    const boxW = 200;
    const gap = 24;
    const cols = Math.min(4, Math.max(2, Math.floor((W - 40) / (boxW + gap))));

    for (const e of this.erdEntities) {
      e.w = boxW;
      e.h = 36 + e.fields.length * 18;
    }

    // Find max height per column to layout rows
    const colHeights: number[] = [];
    const colAssign = Array.from({ length: cols }, () => [] as ERDEntity[]);
    for (let i = 0; i < this.erdEntities.length; i++) {
      colAssign[i % cols].push(this.erdEntities[i]);
    }
    for (let c = 0; c < cols; c++) {
      colHeights[c] =
        colAssign[c].reduce((s, e) => s + e.h, 0) +
        (colAssign[c].length - 1 > 0 ? (colAssign[c].length - 1) * gap : 0);
    }

    // Assign positions: round-robin with row tracking
    const rowY: number[] = Array(cols).fill(20);
    for (let i = 0; i < this.erdEntities.length; i++) {
      const c = i % cols;
      const r = Math.floor(i / cols);
      this.erdEntities[i].x = 20 + c * (boxW + gap);
      let y = 20;
      for (let prev = 0; prev < r; prev++) {
        const prevIdx = prev * cols + c;
        if (prevIdx < this.erdEntities.length) {
          y += this.erdEntities[prevIdx].h + gap;
        }
      }
      this.erdEntities[i].y = y;
    }
  }

  // ── ERD Drawing ─────────────────────────────────────────

  private drawERD(sk: p5): void {
    // Draw FK edges first (behind entity boxes)
    this.drawERDEdges(sk);

    // Draw entity boxes on top (cover edges)
    for (const e of this.erdEntities) this.drawERDBox(sk, e);
  }

  private drawERDBox(sk: p5, e: ERDEntity): void {
    const headerH = 36;
    const borderColor =
      e.status === 'orphan_analysis'
        ? [239, 68, 68]
        : e.status === 'orphan_contract'
          ? [234, 179, 8]
          : [34, 197, 94];
    const borderWidth = e.status === 'matched' ? 1 : 3;

    // Status border
    sk.stroke(borderColor[0], borderColor[1], borderColor[2]);
    sk.strokeWeight(borderWidth);
    sk.noFill();
    sk.rect(e.x - borderWidth / 2, e.y - borderWidth / 2, e.w + borderWidth, e.h + borderWidth, 6);

    // Box background
    sk.noStroke();
    sk.fill(18, 26, 37);
    sk.rect(e.x, e.y, e.w, e.h, 6);

    // Accent bar left
    sk.fill(52, 152, 219);
    sk.rect(e.x, e.y + 3, 5, headerH - 6, 2);

    // Hover highlight
    if (e.hovered) {
      sk.fill(52, 152, 219, 25);
      sk.rect(e.x + 2, e.y + 2, e.w - 4, e.h - 4, 6);
    }

    // Header text (entity label)
    sk.stroke(50, 56, 68);
    sk.strokeWeight(1);
    sk.noFill();
    sk.line(e.x + 10, e.y + headerH - 4, e.x + e.w - 4, e.y + headerH - 4);

    sk.noStroke();
    sk.fill(220, 228, 234);
    sk.textSize(13);
    sk.textStyle(sk.BOLD);
    sk.text(e.label, e.x + 12, e.y + 15);
    sk.textStyle(sk.NORMAL);

    // Field list
    sk.fill(139, 148, 160);
    sk.textSize(11);
    for (let i = 0; i < e.fields.length; i++) {
      const f = e.fields[i];
      const fy = e.y + headerH + 8 + i * 18;
      const icon = f.is_pk ? '\u{1F511}' : f.is_fk ? '\u{1F4CE}' : '  ';
      const iconColor = f.is_pk ? [234, 179, 8] : f.is_fk ? [9, 132, 227] : [139, 148, 160];
      sk.fill(iconColor[0], iconColor[1], iconColor[2]);
      sk.text(icon, e.x + 12, fy);
      sk.fill(139, 148, 160);
      sk.text(f.name, e.x + 32, fy);
      const typeX = e.x + e.w - 12;
      sk.fill(100, 110, 125);
      sk.textAlign(sk.RIGHT, sk.BASELINE);
      sk.text(f.type, typeX, fy);
      sk.textAlign(sk.LEFT, sk.BASELINE);
    }
  }

  private drawERDEdges(sk: p5): void {
    for (const edge of this.erdEdges) {
      if (!edge.from || !edge.to) continue;
      const a = edge.from;
      const b = edge.to;

      const aRight = a.x + a.w;
      const bRight = b.x + b.w;
      const aMidY = a.y + a.h / 2;
      const bMidY = b.y + b.h / 2;

      // Route points: array of {x, y}
      let pts: { x: number; y: number }[];

      // Case 1: a is fully left of b — route rightward
      if (aRight <= b.x) {
        const midX = (aRight + b.x) / 2;
        pts = [
          { x: aRight, y: aMidY }, // source right edge
          { x: midX, y: aMidY }, // turn point 1
          { x: midX, y: bMidY }, // turn point 2
          { x: b.x, y: bMidY }, // target left edge
        ];
      }
      // Case 2: b is fully left of a — route leftward
      else if (bRight <= a.x) {
        const midX = (bRight + a.x) / 2;
        pts = [
          { x: bRight, y: bMidY },
          { x: midX, y: bMidY },
          { x: midX, y: aMidY },
          { x: a.x, y: aMidY },
        ];
      }
      // Case 3: horizontally overlapping
      else {
        const aBottom = a.y + a.h;
        const bBottom = b.y + b.h;
        const aCenterX = a.x + a.w / 2;
        const bCenterX = b.x + b.w / 2;

        // a is above b — route downward
        if (aBottom <= b.y) {
          const midY = (aBottom + b.y) / 2;
          pts = [
            { x: aCenterX, y: aBottom },
            { x: aCenterX, y: midY },
            { x: bCenterX, y: midY },
            { x: bCenterX, y: b.y },
          ];
        }
        // b is above a — route downward from b
        else if (bBottom <= a.y) {
          const midY = (bBottom + a.y) / 2;
          pts = [
            { x: bCenterX, y: bBottom },
            { x: bCenterX, y: midY },
            { x: aCenterX, y: midY },
            { x: aCenterX, y: a.y },
          ];
        }
        // Fully overlapping — detour to the right
        else {
          const detourX = Math.max(aRight, bRight) + 30;
          pts = [
            { x: aRight, y: aMidY },
            { x: detourX, y: aMidY },
            { x: detourX, y: bMidY },
            { x: aRight, y: bMidY }, // connect to right side of b or a
          ];
          if (bRight > aRight) {
            pts[3] = { x: bRight, y: bMidY };
            pts[0] = { x: aRight, y: aMidY };
          } else {
            pts = [
              { x: bRight, y: bMidY },
              { x: detourX, y: bMidY },
              { x: detourX, y: aMidY },
              { x: aRight, y: aMidY },
            ];
          }
        }
      }

      // Determine color: yellow if connected to hovered entity, otherwise normal
      const isHighlighted = a.hovered || b.hovered;
      const lineColor = isHighlighted ? [254, 210, 40] : [200, 210, 220];
      const labelBg = isHighlighted ? [50, 45, 10] : [10, 14, 20];
      const labelColor = isHighlighted ? [254, 210, 40] : [200, 210, 220];
      const weight = isHighlighted ? 2 : 1;

      // Draw orthogonal path
      sk.noFill();
      sk.stroke(lineColor[0], lineColor[1], lineColor[2]);
      sk.strokeWeight(weight);
      for (let i = 0; i < pts.length - 1; i++) {
        sk.line(pts[i].x, pts[i].y, pts[i + 1].x, pts[i + 1].y);
      }

      // Arrowhead at last point (target)
      const tip = pts[pts.length - 1];
      const prev = pts[pts.length - 2];
      const arrowSize = isHighlighted ? 8 : 7;
      const angle = Math.atan2(tip.y - prev.y, tip.x - prev.x);
      sk.fill(lineColor[0], lineColor[1], lineColor[2]);
      sk.noStroke();
      sk.triangle(
        tip.x,
        tip.y,
        tip.x - arrowSize * Math.cos(angle - Math.PI / 6),
        tip.y - arrowSize * Math.sin(angle - Math.PI / 6),
        tip.x - arrowSize * Math.cos(angle + Math.PI / 6),
        tip.y - arrowSize * Math.sin(angle + Math.PI / 6),
      );

      // Cardinality label at center of vertical segment
      const midTop = pts[1];
      const midBot = pts[2];
      const lx = (midTop.x + midBot.x) / 2;
      const ly = (midTop.y + midBot.y) / 2;
      sk.noStroke();
      sk.fill(labelBg[0], labelBg[1], labelBg[2]);
      sk.rect(lx - 16, ly - 8, 32, 16, 4);
      sk.fill(labelColor[0], labelColor[1], labelColor[2]);
      sk.textSize(10);
      sk.textAlign(sk.CENTER, sk.CENTER);
      sk.text(edge.cardinality, lx, ly);
      sk.textAlign(sk.LEFT, sk.BASELINE);
    }
  }

  // ── Layout computation ──────────────────────────────────

  private computeLayout(): void {
    const W = this.p5Inst?.width || 960;
    const H = this.p5Inst?.height || 420;
    // Layout only entity clusters (floatingClusters are orphan non-entities)
    const allClusters = this.clusters;

    // Same layout in both modes: grid of entity cards
    const cardW = 140,
      cardH = 100,
      gap = 12;
    const cols = Math.max(2, Math.floor((W - 40) / (cardW + gap)));
    let i = 0;
    for (const c of allClusters) {
      c.x = 20 + (i % cols) * (cardW + gap);
      c.y = 20 + Math.floor(i / cols) * (cardH + gap);
      c.w = cardW;
      c.h = cardH;
      i++;
    }
  }

  // ── Draw methods ────────────────────────────────────────

  private drawEntityCards(sk: p5): void {
    for (const c of this.clusters) {
      const hw = c.w / 2;

      sk.noStroke();
      sk.fill(18, 24, 34, 220);
      sk.rect(c.x, c.y, c.w, c.h, 8);

      sk.noFill();
      sk.stroke(c.hasDrift ? 231 : 46, c.hasDrift ? 76 : 204, c.hasDrift ? 60 : 113, 80);
      sk.strokeWeight(1.5);
      sk.rect(c.x, c.y, c.w, c.h, 8);

      sk.noStroke();
      sk.fill(200, 210, 220);
      sk.textSize(12);
      sk.textAlign(sk.CENTER, sk.CENTER);
      sk.text(c.name, c.x + hw, c.y + 20);

      sk.stroke(40, 50, 70, 100);
      sk.strokeWeight(1);
      sk.line(c.x + 12, c.y + 30, c.x + c.w - 12, c.y + 30);

      sk.noStroke();
      const counts = [
        { label: 'commands', color: CAT_COLOR['commands'], count: c['commands'].length },
        { label: 'queries', color: CAT_COLOR['queries'], count: c['queries'].length },
        { label: 'events', color: CAT_COLOR['events'], count: c['events'].length },
        { label: 'other', color: [150, 150, 150], count: c.other.length },
      ];

      let iy = c.y + 44;
      sk.textSize(9);
      sk.textAlign(sk.LEFT, sk.CENTER);
      for (const item of counts) {
        if (item.count === 0) continue;
        sk.fill(item.color[0], item.color[1], item.color[2], 200);
        sk.ellipse(c.x + 20, iy, 6, 6);
        sk.fill(180, 190, 200);
        sk.text(`${item.count} ${item.label}`, c.x + 28, iy);
        iy += 16;
      }

      const hCol =
        c.healthScore >= 90 ? [46, 204, 113] : c.healthScore >= 70 ? [241, 196, 15] : [231, 76, 60];
      sk.fill(hCol[0], hCol[1], hCol[2], 160);
      sk.noStroke();
      sk.ellipse(c.x + c.w - 18, c.y + 18, 14, 14);
      sk.fill(255);
      sk.textSize(7);
      sk.textAlign(sk.CENTER, sk.CENTER);
      sk.text(`${c.healthScore}`, c.x + c.w - 18, c.y + 19);
    }
  }

  // ── Entity Detail Flow Layout ───────────────────────────

  // ── Infer component type from UI component name ────────────

  private inferComponentType(name: string): string {
    const n = name.toLowerCase();
    if (n.includes('table')) return 'data_table';
    if (n.includes('form')) return 'form_builder';
    if (n.includes('card')) return 'card';
    if (n.includes('dialog') || n.includes('modal')) return 'dialog';
    if (n.includes('list')) return 'list';
    if (n.includes('input')) return 'input';
    if (n.includes('select')) return 'select';
    if (n.includes('nav')) return 'navbar';
    if (n.includes('sidebar')) return 'sidebar';
    if (n.includes('chart')) return 'data_table';
    return 'data_table'; // default fallback for table-like UI components
  }

  // ── Entity Detail Layout ────────────────────────────────────

  private computeEntityDetailLayout(entityName: string): void {
    const W = this.p5Inst?.width || 960;
    const H = this.p5Inst?.height || 420;
    const cluster = this.clusters.find((c) => c.name === entityName);
    if (!cluster || !cluster.entityNode) return;

    const mainEntityUid = cluster.entityNode!.uid;
    const entityNameLower = entityName.toLowerCase();

    // Helper: resolve entity name (case-insensitive) to UID
    const resolveEntityUid = (refName: string): string | null => {
      const refLower = refName.toLowerCase();
      if (refLower === entityNameLower) return mainEntityUid;
      for (const [uid, node] of this.uidMap) {
        if (node.category === 'entities' && node.label.toLowerCase() === refLower) return uid;
      }
      return `entities:${refName}`;
    };

    // ── Phase 1: Scan traceMatrix, collect actions referencing our entity ──
    const messages: SeqMessage[] = [];
    const participantEntityUids = new Set<string>([mainEntityUid]);

    // Deduplicate commands by contract_id (canonical name) — pick the row with contract_node
    const seenCmdNames = new Set<string>();
    const cmdRows = (this.traceMatrix['commands'] || []).filter((row) => {
      const name = row.contract_id || row.analysis_name || '';
      if (!name) return false;
      if (seenCmdNames.has(name)) return false;
      seenCmdNames.add(name);
      return true;
    });
    for (const row of cmdRows) {
      const cn = row.contract_node;
      if (!cn) continue;

      // Find target entities (writes/effects) — deduplicate
      const targetUidSet = new Set<string>();
      for (const eff of cn.effects || []) {
        if (typeof eff === 'object' && (eff as any).entity) {
          if ((eff as any).entity.toLowerCase() === entityNameLower) {
            targetUidSet.add(mainEntityUid);
          } else {
            const r = resolveEntityUid((eff as any).entity);
            if (r) targetUidSet.add(r);
          }
        }
      }
      for (const ref of cn.writes_to || []) {
        const r = resolveEntityUid(String(ref));
        if (r) targetUidSet.add(r);
      }
      const targetUids = Array.from(targetUidSet);

      // Find source entities (fetches/reads)
      const sourceUids: string[] = [];
      for (const ref of cn.fetches || []) {
        if (typeof ref === 'object') {
          const r = resolveEntityUid((ref as any).entity || (ref as any).entity_id || '');
          if (r) sourceUids.push(r);
        }
      }

      // Skip if this command doesn't reference our entity ecosystem
      if (targetUids.length === 0) {
        const fetchesOurEntity = cn.fetches?.some((ref: any) => {
          if (typeof ref !== 'object') return false;
          return (ref.entity || ref.entity_id || '').toLowerCase() === entityNameLower;
        });
        if (!fetchesOurEntity) continue;
      } else {
        // Only include commands that touch the main entity or a participant we already track
        const touchesMain =
          targetUids.includes(mainEntityUid) || sourceUids.includes(mainEntityUid);
        const touchesParticipant =
          targetUids.some((u) => participantEntityUids.has(u)) ||
          sourceUids.some((u) => participantEntityUids.has(u));
        if (!touchesMain && !touchesParticipant) continue;
      }

      // Collect related entity UIDs for participants
      for (const u of [...targetUids, ...sourceUids]) participantEntityUids.add(u);

      // Collect guards
      const guardLabels: string[] = [];
      for (const g of cn.guards || []) {
        const gid = typeof g === 'string' ? g : (g as any).guard_id || '';
        if (gid) guardLabels.push(gid);
      }

      // Build payload lines
      const payloadLines: string[] = [];
      if (cn.input?.length)
        payloadLines.push(
          `input: ${cn.input
            .filter((i: any) => typeof i === 'object')
            .map((i: any) => `${i.name}(${i.type})`)
            .join(', ')}`,
        );
      if (cn.transaction) payloadLines.push('transaction: true');
      if (cn.category) payloadLines.push(`category: ${cn.category}`);

      // ── One message per command, with all target entities grouped ──
      // External trigger: no source entity → special "__external__" marker
      const fromUid = sourceUids.length > 0 ? sourceUids[0] : '__external__';
      // effectiveTargets: all entities this command writes to
      const effectiveTargets = targetUids.length > 0 ? targetUids : [mainEntityUid];
      // toUid is the first target for the primary arrow direction
      const toUid = effectiveTargets[0];

      messages.push({
        fromUid,
        toUid,
        type: 'writes_to',
        label: row.contract_id || '',
        actionName: row.contract_id || '',
        actionType: 'command',
        guards: guardLabels,
        events: cn.emits || [],
        payload: payloadLines,
        targetUids: effectiveTargets,
        status: row.status || 'matched',
        y: 0,
      });
    }

    // Scan queries — deduplicate by name
    const seenQueryNames = new Set<string>();
    const queryRows = (this.traceMatrix['queries'] || []).filter((row) => {
      const name = row.contract_id || row.analysis_name || '';
      if (!name) return false;
      if (seenQueryNames.has(name)) return false;
      seenQueryNames.add(name);
      return true;
    });
    for (const row of queryRows) {
      const cn = row.contract_node;
      if (!cn) continue;

      const targetUids: string[] = [];
      for (const ref of cn.reads_from || []) {
        const r = resolveEntityUid(String(ref));
        if (r) targetUids.push(r);
      }
      for (const ref of cn.fetches || []) {
        if (typeof ref === 'object') {
          const r = resolveEntityUid((ref as any).entity || (ref as any).entity_id || '');
          if (r) targetUids.push(r);
        }
      }

      if (targetUids.length === 0 || !targetUids.includes(mainEntityUid)) continue;
      for (const u of targetUids) participantEntityUids.add(u);

      const payloadLines: string[] = [];
      if (cn.input?.length)
        payloadLines.push(
          `input: ${cn.input
            .filter((i: any) => typeof i === 'object')
            .map((i: any) => `${i.name}(${i.type})`)
            .join(', ')}`,
        );

      // Query: external caller reads from entity
      messages.push({
        fromUid: '__external__',
        toUid: mainEntityUid,
        type: 'reads_from',
        label: row.contract_id || '',
        actionName: row.contract_id || '',
        actionType: 'query',
        guards: [],
        events: [],
        payload: payloadLines,
        status: row.status || 'matched',
        y: 0,
      });
    }

    // UI component data (properties to show in participant header)
    const uiComponentData = new Map<string, { label: string; properties: Record<string, any>; componentType: string; fields: Array<{ name: string; type: string }> }>();
    const seenUiNames = new Set<string>();
    const uiRows = (this.traceMatrix['ui_components'] || []).filter((row) => {
      const name = row.contract_id || row.analysis_name || '';
      if (!name) return false;
      if (seenUiNames.has(name)) return false;
      seenUiNames.add(name);
      return true;
    });
    for (const row of uiRows) {
      const cn = row.contract_node;
      if (!cn) continue;
      const entityId = cn.entity_id || '';
      if (entityId.toLowerCase() !== entityNameLower) continue;

      // Use contract_id or analysis_name as canonical name — never undefined
      const uiName = row.contract_id || row.analysis_name || '';
      const uiUid = `ui_components:${uiName}`;

      messages.push({
        fromUid: uiUid,
        toUid: mainEntityUid,
        type: 'entity_ref',
        label: uiName,
        actionName: uiName,
        actionType: 'ui_component',
        guards: [],
        events: [],
        payload: [],
        status: row.status || 'matched',
        y: 0,
      });
      participantEntityUids.add(uiUid);

      // Store UI component data for header rendering
      // Build fields from related entity (for data_table, form, etc.) + component properties
      const uiFields: Array<{ name: string; type: string; is_pk?: boolean; is_fk?: boolean }> = [];
      // First, pull fields from the related entity if available
      const norm = (s: string) => s.replace(/-/g, '_').replace(/([a-z])([A-Z])/g, '$1_$2').toLowerCase();
      const relatedErd = this.erdEntities.find((e) => norm(e.label) === norm(entityId));
      if (relatedErd && relatedErd.fields) {
        for (const f of relatedErd.fields.slice(0, 8)) {
          uiFields.push({ name: f.name, type: f.type, is_pk: f.is_pk, is_fk: f.is_fk });
        }
      }
      // If no entity fields, fall back to component_type, description, and properties
      if (uiFields.length === 0) {
        if (cn.component_type) uiFields.push({ name: 'type', type: cn.component_type });
        if (cn.description) uiFields.push({ name: 'desc', type: String(cn.description).slice(0, 25) + (String(cn.description).length > 25 ? '...' : '') });
      }
      const props = cn.properties || {};
      for (const [k, v] of Object.entries(props).slice(0, 4)) {
        uiFields.push({
          name: k,
          type: typeof v === 'object' ? 'Object' : String(v).slice(0, 20),
        });
      }
      uiComponentData.set(uiUid, {
        label: uiName,
        properties: props,
        componentType: cn.component_type || this.inferComponentType(uiName),
        fields: uiFields,
      });
    }

    // ── Phase 2: Build participant list (entities + UI only) ──
    // Main entity first, then related entities, then UI components
    const participantNodes: Array<{ uid: string; label: string; category: string }> = [];
    const used = new Set<string>([mainEntityUid]);
    participantNodes.push({
      uid: mainEntityUid,
      label: cluster.entityNode.label,
      category: 'entities',
    });

    for (const uid of participantEntityUids) {
      if (uid === mainEntityUid || used.has(uid)) continue;
      used.add(uid);
      const src = this.uidMap.get(uid);
      if (src) {
        participantNodes.push({ uid, label: src.label, category: src.category });
      } else {
        // Fallback for UI components not in uidMap
        const uiData = uiComponentData.get(uid);
        if (uiData) {
          participantNodes.push({ uid, label: uiData.label, category: 'ui_components' });
        }
      }
    }

    // ── Phase 3: Layout participants ──
    const seqHeaderH = 48;
    const sidePad = 40;
    const participantCount = participantNodes.length;
    const lifelineSpacing = Math.max(
      110,
      Math.min(180, (W - sidePad * 2) / Math.max(participantCount - 1, 1)),
    );
    const lifelineStartX =
      sidePad + (W - sidePad * 2 - (participantCount - 1) * lifelineSpacing) / 2;

    // Normalize helper
    const labelNorm = (s: string) =>
      s
        .replace(/-/g, '_')
        .replace(/([a-z])([A-Z])/g, '$1_$2')
        .toLowerCase();

    const uidToLifelineX = new Map<string, number>();

    // Compute dynamic header height based on fields
    const fieldLineH = 16;
    const headerBoxH = (fields: Array<{ name: string }> | undefined) =>
      36 + (fields?.length || 0) * fieldLineH;

    // Find max header height across all participants
    const maxHeaderH = Math.max(
      ...participantNodes.map((n) => {
        const erd = this.erdEntities.find((e) => labelNorm(e.label) === labelNorm(n.label));
        return headerBoxH(erd?.fields);
      }),
    );

    this.seqLifelines = participantNodes.map((n, i) => {
      const x = lifelineStartX + i * lifelineSpacing;
      uidToLifelineX.set(n.uid, x);

      // Lookup fields from ERD
      const erd = this.erdEntities.find((e) => labelNorm(e.label) === labelNorm(n.label));
      let fields = erd?.fields || [];

      // For UI components, use pre-built fields from uiComponentData
      if (n.category === 'ui_components' && fields.length === 0) {
        const uiData = uiComponentData.get(n.uid);
        if (uiData && uiData.fields) {
          fields = uiData.fields;
        }
      }

      // Lookup status from traceMatrix
      const entStatus =
        this.traceMatrix['entities']?.find(
          (r) =>
            labelNorm(r.analysis_name || '') === labelNorm(n.label) ||
            labelNorm(r.contract_id || '') === labelNorm(n.label),
        )?.status || 'matched';

      return {
        uid: n.uid,
        label: n.label,
        category: n.category,
        x,
        status: entStatus,
        w: 140,
        fields,
        componentType: n.category === 'ui_components' ? uiComponentData.get(n.uid)?.componentType : undefined,
        properties: n.category === 'ui_components' ? uiComponentData.get(n.uid)?.properties : undefined,
      };
    });

    // ── Phase 4: Sort and position messages with dynamic height ──
    // Order: commands first, then queries, then UI refs
    const msgOrder: Record<string, number> = { command: 0, query: 1, entity_ref: 2 };
    messages.sort((a, b) => {
      const oa = msgOrder[a.actionType || ''] ?? 9;
      const ob = msgOrder[b.actionType || ''] ?? 9;
      if (oa !== ob) return oa - ob;
      return (a.actionName || '').localeCompare(b.actionName || '');
    });

    // Compute dynamic height per message based on badge count
    const msgBaseH = 36; // arrow line + label card
    const badgeLineH = 14; // height per badge line
    const computeMsgHeight = (m: SeqMessage): number => {
      let h = msgBaseH;
      h += (m.guards?.length ?? 0) * badgeLineH;
      h += (m.events?.length ?? 0) * badgeLineH;
      h += (m.payload?.length ?? 0) * badgeLineH;
      return Math.max(msgBaseH, h);
    };

    // Cumulative Y positioning — each message gets its own vertical space
    const msgStartY = maxHeaderH + 80;
    let currentY = msgStartY;
    this.seqMessages = messages.map((m) => {
      const h = computeMsgHeight(m);
      const positioned = { ...m, y: currentY };
      currentY += h;
      return positioned;
    });

    // ── Phase 5: Store for drawing ──
    // Use maxHeaderH as the actual header height (not fixed seqHeaderH)
    this.flowLifelineTop = maxHeaderH;
    if (this.seqMessages.length > 0) {
      const lastMsg = this.seqMessages[this.seqMessages.length - 1];
      // Dynamic height for last message too
      const lastH =
        msgBaseH +
        (lastMsg.guards?.length ?? 0) * badgeLineH +
        (lastMsg.events?.length ?? 0) * badgeLineH +
        (lastMsg.payload?.length ?? 0) * badgeLineH;
      this.flowLifelineBottom = lastMsg.y + lastH + 20;
    } else {
      this.flowLifelineBottom = Math.max(H - 40, maxHeaderH + 200);
    }
    this.flowLifelineBottom = Math.max(this.flowLifelineBottom, maxHeaderH + 200);

    // Flow nodes for hover tooltip (position at header center)
    this.flowNodes = participantNodes.map((n) => ({
      uid: n.uid,
      label: n.label,
      category: n.category,
      status: 'matched',
      x: uidToLifelineX.get(n.uid) ?? 0,
      y: maxHeaderH / 2,
      w: 140,
      h: headerBoxH(this.seqLifelines.find((l) => l.uid === n.uid)?.fields),
      entityGroup: null,
    }));

    // Store UI component bounds for click detection (match actual drawn positions)
    const maxHH = Math.max(...this.seqLifelines.map((ll) => headerBoxH(ll.fields)));
    this.uiComponentBounds = this.seqLifelines
      .filter((ll) => ll.category === 'ui_components')
      .map((ll) => {
        const boxH = headerBoxH(ll.fields);
        return {
          uid: ll.uid,
          x: ll.x - ll.w / 2,
          y: maxHH - boxH,
          w: ll.w,
          h: boxH,
        };
      });

    this.flowColumnHeights = { top: this.flowLifelineTop, bottom: this.flowLifelineBottom };
  }

  // ── Entity Detail Drawing — Sequence Diagram ────────────

  private drawEntityDetail(sk: p5): void {
    const arrowSize = 9;
    const mainEntityUid = this.clusters.find((c) => c.name === this.selectedEntity)?.entityNode
      ?.uid;

    const uidToX = new Map<string, number>();
    for (const ll of this.seqLifelines) uidToX.set(ll.uid, ll.x);

    // ── 1. Draw participant headers (ERD-style boxes with fields) ──
    const fieldLineH = 16;
    const headerBoxH = (fields: Array<{ name: string }> | undefined) =>
      36 + (fields?.length || 0) * fieldLineH;
    const maxHeaderH = Math.max(...this.seqLifelines.map((ll) => headerBoxH(ll.fields)));

    for (const ll of this.seqLifelines) {
      const cc = CAT_COLOR[ll.category] || [150, 150, 150];
      const boxH = headerBoxH(ll.fields);
      const px = ll.x - ll.w / 2;
      // Align boxes to the bottom of the header area (straight on the separator line)
      const py = maxHeaderH - boxH;

      // Grey border for all participants — drift shown on Level 1
      sk.fill(0, 0, 0, 0);
      sk.stroke(80, 88, 100);
      sk.strokeWeight(1);
      sk.rect(px, py, ll.w, boxH, 6);

      // Box background
      sk.noStroke();
      sk.fill(18, 22, 30);
      sk.rect(px, py, ll.w, boxH, 6);

      // Accent bar left (subtle grey)
      sk.fill(cc[0], cc[1], cc[2], 120);
      sk.rect(px, py + 3, 5, 30, 2);

      // Header divider line
      sk.stroke(50, 56, 68);
      sk.strokeWeight(1);
      sk.line(px + 10, py + 32, px + ll.w - 4, py + 32);

      // Header text (entity label)
      sk.noStroke();
      sk.fill(220, 228, 234);
      sk.textSize(13);
      sk.textStyle(sk.BOLD);
      sk.text(ll.label, px + 12, py + 15);
      sk.textStyle(sk.NORMAL);

      // Field list
      const fields = ll.fields || [];
      for (let i = 0; i < fields.length; i++) {
        const f = fields[i];
        const fy = py + 36 + 8 + i * fieldLineH;

        // PK/FK icon
        const icon = f.is_pk ? '\u{1F511}' : f.is_fk ? '\u{1F4CE}' : '  ';
        const iconColor = f.is_pk ? [234, 179, 8] : f.is_fk ? [9, 132, 227] : [139, 148, 160];
        sk.fill(iconColor[0], iconColor[1], iconColor[2]);
        sk.textSize(10);
        sk.text(icon, px + 10, fy);

        // Field name (truncate if too long)
        sk.fill(139, 148, 160);
        sk.textSize(11);
        const nameMaxW = (px + ll.w - 8) - 70; // leave room for type column
        const nameText = sk.textWidth(f.name) > nameMaxW ? f.name.slice(0, 10) + '...' : f.name;
        sk.text(nameText, px + 30, fy);

        // Type (right aligned, truncate if too long)
        sk.fill(100, 110, 125);
        sk.textAlign(sk.RIGHT, sk.BASELINE);
        const typeMaxW = 60;
        let typeText = f.type;
        if (sk.textWidth(typeText) > typeMaxW) {
          const maxChars = Math.floor(typeMaxW / sk.textWidth('a'));
          typeText = typeText.slice(0, Math.min(maxChars, typeText.length)) + '...';
        }
        sk.text(typeText, px + ll.w - 8, fy);
        sk.textAlign(sk.LEFT, sk.BASELINE);
      }
    }

    // Separator
    sk.noFill();
    sk.stroke(30, 40, 55);
    sk.strokeWeight(1);
    const sepY = maxHeaderH;
    sk.line(20, sepY, sk.width - 20, sepY);

    // ── 2. Draw dashed lifelines ──
    const ctx2d = sk.drawingContext as CanvasRenderingContext2D;
    ctx2d.setLineDash([4, 4]);
    for (const ll of this.seqLifelines) {
      const isMain = ll.uid === mainEntityUid;
      const cc = CAT_COLOR[ll.category] || [150, 150, 150];
      sk.stroke(isMain ? cc[0] : 60, isMain ? cc[1] : 70, isMain ? cc[2] : 90, isMain ? 160 : 100);
      sk.strokeWeight(isMain ? 1.5 : 1);
      sk.line(ll.x, sepY + 2, ll.x, this.flowLifelineBottom);
    }
    ctx2d.setLineDash([]);

    // ── 3. Draw enriched message cards ──
    const externalX = 20; // left edge position for external triggers

    for (const msg of this.seqMessages) {
      const y = msg.y;
      const guards = msg.guards || [];
      const events = msg.events || [];
      const payload = msg.payload || [];

      // Determine message color based on drift status (not action type)
      // This way the arrow color shows whether this command/query is matched or has drift
      const driftColor: [number, number, number] =
        msg.status === 'orphan_analysis'
          ? [239, 68, 68] // red — in brief but missing from contract
          : msg.status === 'orphan_contract'
            ? [234, 179, 8] // yellow — in contract but missing from brief
            : msg.status === 'mismatch'
              ? [230, 126, 34] // orange — exists in both but different
              : [46, 204, 113]; // green — matched
      let msgColor: [number, number, number] = driftColor;

      const cardLabel = msg.actionName || msg.label;

      // ── Command Hub: multiple targets ──
      const targets = msg.targetUids || [msg.toUid];
      const isHub = msg.actionType === 'command' && targets.length > 1;

      if (isHub) {
        // Compute card bounds spanning all targets
        const targetXs = targets
          .map((t) => uidToX.get(t))
          .filter((x): x is number => x !== undefined);
        if (targetXs.length === 0) continue;

        const hubMinX = Math.min(...targetXs);
        const hubMaxX = Math.max(...targetXs);
        const hubCenterX = (hubMinX + hubMaxX) / 2;
        const hubCardW = Math.max(sk.textWidth(cardLabel) + 32, hubMaxX - hubMinX + 20);
        const hubCardH = 18; // label row height

        // External trigger icon
        const isExternal = msg.fromUid === '__external__';
        if (isExternal) {
          sk.noStroke();
          sk.fill(msgColor[0], msgColor[1], msgColor[2], 200);
          sk.ellipse(externalX, y, 10, 10);
          sk.fill(255);
          sk.textSize(7);
          sk.textAlign(sk.CENTER, sk.CENTER);
          sk.text('→', externalX, y);
        }

        // Activation bars on each target lifeline
        for (const tx of targetXs) {
          sk.noStroke();
          sk.fill(msgColor[0], msgColor[1], msgColor[2], 40);
          sk.rect(tx - 7, y - 12, 14, 24, 3);
        }

        // Connector lines: thin angled lines from card top to each lifeline
        sk.noFill();
        sk.stroke(msgColor[0], msgColor[1], msgColor[2], 120);
        sk.strokeWeight(1);
        for (const tx of targetXs) {
          // Clamp to card edge if target is inside card
          const anchorX = Math.max(
            hubCenterX - hubCardW / 2,
            Math.min(hubCenterX + hubCardW / 2, tx),
          );
          sk.line(tx, y, anchorX, y - 6);
        }

        // Horizontal bar connecting all lifelines at hub Y
        sk.stroke(msgColor[0], msgColor[1], msgColor[2], 160);
        sk.strokeWeight(1.5);
        sk.line(hubCenterX - hubCardW / 2, y - 6, hubCenterX + hubCardW / 2, y - 6);

        // Hub card background
        sk.noStroke();
        sk.fill(16, 20, 30, 240);
        sk.rect(hubCenterX - hubCardW / 2, y - 28, hubCardW, hubCardH, 4);

        // Card accent bar left
        sk.fill(msgColor[0], msgColor[1], msgColor[2]);
        sk.rect(hubCenterX - hubCardW / 2, y - 25, 3, hubCardH - 6, 1);

        // Action name + target count badge
        sk.fill(msgColor[0], msgColor[1], msgColor[2], 255);
        sk.textSize(10);
        sk.textAlign(sk.LEFT, sk.CENTER);
        sk.text(cardLabel, hubCenterX - hubCardW / 2 + 8, y - 19);

        // Target count badge on right side — count only targets with visible lifelines
        const countBadge = `→ ${targetXs.length} entities`;
        const badgeW = sk.textWidth(countBadge) + 8;
        sk.fill(msgColor[0], msgColor[1], msgColor[2], 60);
        sk.rect(hubCenterX + hubCardW / 2 - badgeW - 2, y - 25, badgeW, 14, 3);
        sk.fill(msgColor[0], msgColor[1], msgColor[2], 220);
        sk.textSize(8);
        sk.textAlign(sk.CENTER, sk.CENTER);
        sk.text(countBadge, hubCenterX + hubCardW / 2 - badgeW / 2 - 2, y - 19);

        // ── Badges below card ──
        let badgeY = y + 10;
        const guardColor: [number, number, number] = [231, 76, 60];
        const eventColor: [number, number, number] = [241, 196, 15];
        const payloadColor: [number, number, number] = [139, 148, 160];

        if (guards.length > 0) {
          const guardText = `\u26A0 ${guards.join(', ')}`;
          const gW = sk.textWidth(guardText) + 10;
          sk.noStroke();
          sk.fill(guardColor[0], guardColor[1], guardColor[2], 30);
          sk.rect(hubCenterX - gW / 2, badgeY - 7, gW, 12, 3);
          sk.fill(guardColor[0], guardColor[1], guardColor[2], 200);
          sk.textSize(8);
          sk.textAlign(sk.CENTER, sk.CENTER);
          sk.text(guardText, hubCenterX, badgeY - 1);
          badgeY += 14;
        }

        if (events.length > 0) {
          const evtText = `\u25B8 ${events.join(', ')}`;
          const eW = sk.textWidth(evtText) + 10;
          sk.noStroke();
          sk.fill(eventColor[0], eventColor[1], eventColor[2], 30);
          sk.rect(hubCenterX - eW / 2, badgeY - 7, eW, 12, 3);
          sk.fill(eventColor[0], eventColor[1], eventColor[2], 200);
          sk.textSize(8);
          sk.textAlign(sk.CENTER, sk.CENTER);
          sk.text(evtText, hubCenterX, badgeY - 1);
          badgeY += 14;
        }

        for (const pl of payload.slice(0, 2)) {
          const pW = sk.textWidth(pl) + 10;
          sk.noStroke();
          sk.fill(payloadColor[0], payloadColor[1], payloadColor[2], 20);
          sk.rect(hubCenterX - pW / 2, badgeY - 7, pW, 12, 3);
          sk.fill(payloadColor[0], payloadColor[1], payloadColor[2], 160);
          sk.textSize(8);
          sk.textAlign(sk.CENTER, sk.CENTER);
          sk.text(pl, hubCenterX, badgeY - 1);
          badgeY += 14;
        }

        // Target entity labels below badge area
        let labelY = badgeY + 4;
        const labelPerTarget = 14;
        sk.textSize(8);
        sk.textAlign(sk.CENTER, sk.CENTER);
        for (const tx of targetXs.sort((a, b) => a - b)) {
          const uid = targets.find((t) => uidToX.get(t) === tx);
          const label = uid ? uid.split(':')[1] || uid : '';
          sk.fill(msgColor[0], msgColor[1], msgColor[2], 140);
          const lw = sk.textWidth(label) + 10;
          sk.noStroke();
          sk.fill(msgColor[0], msgColor[1], msgColor[2], 30);
          sk.rect(tx - lw / 2, labelY - 6, lw, 12, 3);
          sk.fill(msgColor[0], msgColor[1], msgColor[2], 200);
          sk.text(label, tx, labelY);
        }
      } else {
        // ── Single target: normal arrow ──
        let fromX: number | undefined = uidToX.get(msg.fromUid);
        const toX = uidToX.get(msg.toUid);
        if (toX === undefined) continue;

        const isExternal = msg.fromUid === '__external__';
        if (fromX === undefined) fromX = externalX;

        const isSelf = !isExternal && Math.abs(fromX - toX) < 5;

        // Activation bar on target lifeline
        sk.noStroke();
        sk.fill(msgColor[0], msgColor[1], msgColor[2], 40);
        sk.rect(toX - 7, y - 12, 14, 24, 3);

        // Arrow line
        sk.noFill();
        sk.stroke(msgColor[0], msgColor[1], msgColor[2], 180);
        sk.strokeWeight(1.5);

        if (isSelf) {
          sk.arc(fromX + 22, y, 44, 44, sk.HALF_PI, sk.TWO_PI - sk.HALF_PI);
          sk.noStroke();
          sk.fill(msgColor[0], msgColor[1], msgColor[2], 255);
          sk.triangle(fromX + 19, y + 22, fromX + 28, y + 18, fromX + 28, y + 26);
        } else {
          const dir = toX > fromX ? 1 : -1;
          sk.line(fromX, y, toX - dir * arrowSize, y);
          sk.noStroke();
          sk.fill(msgColor[0], msgColor[1], msgColor[2], 255);
          sk.triangle(
            toX,
            y,
            toX - dir * arrowSize * 1.3,
            y - arrowSize * 0.6,
            toX - dir * arrowSize * 1.3,
            y + arrowSize * 0.6,
          );
        }

        // External trigger icon
        if (isExternal) {
          sk.noStroke();
          sk.fill(msgColor[0], msgColor[1], msgColor[2], 200);
          sk.ellipse(externalX, y, 10, 10);
          sk.fill(255);
          sk.textSize(7);
          sk.textAlign(sk.CENTER, sk.CENTER);
          sk.text('→', externalX, y);
        }

        // Message card above arrow
        const midX = isSelf ? fromX + 35 : (fromX + toX) / 2;
        sk.noStroke();
        sk.fill(16, 20, 30, 240);
        sk.rect(
          midX - (sk.textWidth(cardLabel) + 16) / 2,
          y - 28,
          sk.textWidth(cardLabel) + 16,
          20,
          4,
        );

        sk.fill(msgColor[0], msgColor[1], msgColor[2], 255);
        sk.textSize(10);
        sk.textAlign(sk.CENTER, sk.CENTER);
        sk.text(cardLabel, midX, y - 18);

        // Badges below arrow
        let badgeY = y + 10;
        const guardColor: [number, number, number] = [231, 76, 60];
        const eventColor: [number, number, number] = [241, 196, 15];
        const payloadColor: [number, number, number] = [139, 148, 160];

        if (guards.length > 0) {
          const guardText = `\u26A0 ${guards.join(', ')}`;
          const gW = sk.textWidth(guardText) + 10;
          sk.noStroke();
          sk.fill(guardColor[0], guardColor[1], guardColor[2], 30);
          sk.rect(midX - gW / 2, badgeY - 7, gW, 12, 3);
          sk.fill(guardColor[0], guardColor[1], guardColor[2], 200);
          sk.textSize(8);
          sk.textAlign(sk.CENTER, sk.CENTER);
          sk.text(guardText, midX, badgeY - 1);
          badgeY += 14;
        }

        if (events.length > 0) {
          const evtText = `\u25B8 ${events.join(', ')}`;
          const eW = sk.textWidth(evtText) + 10;
          sk.noStroke();
          sk.fill(eventColor[0], eventColor[1], eventColor[2], 30);
          sk.rect(midX - eW / 2, badgeY - 7, eW, 12, 3);
          sk.fill(eventColor[0], eventColor[1], eventColor[2], 200);
          sk.textSize(8);
          sk.textAlign(sk.CENTER, sk.CENTER);
          sk.text(evtText, midX, badgeY - 1);
          badgeY += 14;
        }

        for (const pl of payload.slice(0, 2)) {
          const pW = sk.textWidth(pl) + 10;
          sk.noStroke();
          sk.fill(payloadColor[0], payloadColor[1], payloadColor[2], 20);
          sk.rect(midX - pW / 2, badgeY - 7, pW, 12, 3);
          sk.fill(payloadColor[0], payloadColor[1], payloadColor[2], 160);
          sk.textSize(8);
          sk.textAlign(sk.CENTER, sk.CENTER);
          sk.text(pl, midX, badgeY - 1);
          badgeY += 14;
        }
      }
    }

    sk.textAlign(sk.LEFT, sk.BASELINE);
  }

  private getSeqCategoryIcon(cat: string): string {
    const icons: Record<string, string> = {
      entities: '\u25C6',
      commands: '\u26A1',
      queries: '\u25C8',
      events: '\u25B8',
      workflows: '\u27F3',
      value_objects: '\u25C7',
      guards: '\u26A0',
      roles: '\u2640',
      ui_components: '\u25A0',
    };
    return icons[cat] || '\u25CF';
  }

  // ── Helpers ─────────────────────────────────────────────

  getCategoryLabel(cat: string): string {
    const labels: Record<string, string> = {
      entities: 'Entity',
      commands: 'Command',
      queries: 'Query',
      events: 'Event',
      workflows: 'Workflow',
      value_objects: 'Value Object',
      guards: 'Guard',
      roles: 'Role',
      ui_components: 'UI Component',
    };
    return labels[cat] || cat;
  }

  // ── Level 3: Wireframe Drawing ───────────────────────────

  private drawWireframe(sk: p5): void {
    const W = sk.width;
    const H = sk.height;
    const comp = this.selectedUIComponent?.data;
    if (!comp) return;

    const compType = comp.componentType || 'unknown';

    // Title area
    sk.noStroke();
    sk.fill(100, 116, 139);
    sk.textSize(11);
    sk.textAlign(sk.LEFT, sk.TOP);
    sk.text(`${comp.label}  ·  ${compType}`, 30, 20);

    // Wireframe viewport frame (centered, Figma-like)
    const vw = Math.min(W - 100, 800);
    const vh = Math.min(H - 120, 500);
    const vx = (W - vw) / 2;
    const vy = 50;

    // Frame shadow
    sk.fill(0, 0, 0, 40);
    sk.noStroke();
    sk.rect(vx + 4, vy + 4, vw, vh, 8);

    // Frame background
    sk.fill(30, 35, 45);
    sk.stroke(48, 58, 72);
    sk.strokeWeight(1);
    sk.rect(vx, vy, vw, vh, 8);

    // Canvas inside frame
    const cx = vx + 20;
    const cy = vy + 20;
    const cw = vw - 40;
    const ch = vh - 40;

    // Draw based on component type
    this.drawWireframeForType(sk, compType, cx, cy, cw, ch, comp.fields || []);

    // Hint
    sk.noStroke();
    sk.fill(60, 70, 85);
    sk.textSize(10);
    sk.textAlign(sk.CENTER, sk.BOTTOM);
    sk.text('Wireframe preview — generated from component spec', W / 2, H - 15);
    sk.textAlign(sk.LEFT, sk.TOP);
  }

  private drawWireframeForType(
    sk: p5,
    compType: string,
    x: number,
    y: number,
    w: number,
    h: number,
    fields: Array<{ name: string; type: string; is_pk?: boolean; is_fk?: boolean }>,
  ): void {
    const isTable = compType.includes('table');
    const isForm = compType.includes('form') || compType.includes('input') || compType.includes('field');
    const isCard = compType.includes('card');
    const isDialog = compType.includes('dialog') || compType.includes('modal');

    if (isTable) {
      // ── Table wireframe ──
      const colCount = Math.min(fields.length, 5) || 4;
      const headerH = 28;
      const rowH = 32;
      const rowCount = Math.min(8, Math.floor((h - headerH) / rowH));
      const colW = w / colCount;

      // Header
      sk.noStroke();
      sk.fill(40, 48, 60);
      sk.rect(x, y, w, headerH, 4, 4, 0, 0);
      sk.fill(139, 148, 160);
      sk.textSize(10);
      for (let c = 0; c < colCount; c++) {
        const label = fields[c]?.name || `col_${c + 1}`;
        sk.textAlign(sk.LEFT, sk.CENTER);
        sk.text(label, x + c * colW + 8, y + headerH / 2);
      }

      // Rows
      for (let r = 0; r < rowCount; r++) {
        const ry = y + headerH + r * rowH;
        sk.noStroke();
        sk.fill(r % 2 === 0 ? 25 : 20, 30, 38);
        sk.rect(x, ry, w, rowH);
        sk.fill(80, 90, 105);
        sk.textSize(9);
        for (let c = 0; c < colCount; c++) {
          sk.textAlign(sk.LEFT, sk.CENTER);
          sk.text(c === 0 ? 'ID' : '---', x + c * colW + 8, ry + rowH / 2);
        }
        sk.stroke(30, 36, 45);
        sk.line(x, ry + rowH, x + w, ry + rowH);
      }
    } else if (isForm) {
      // ── Form wireframe ──
      const fieldH = 36;
      const gap = 12;
      const maxFields = Math.min(fields.length, Math.floor((h - 20) / (fieldH + gap)));
      if (maxFields <= 0) {
        sk.noStroke();
        sk.fill(80, 90, 105);
        sk.textSize(12);
        sk.textAlign(sk.CENTER, sk.CENTER);
        sk.text('No fields defined', x + w / 2, y + h / 2);
        return;
      }

      for (let i = 0; i < maxFields; i++) {
        const fy = y + i * (fieldH + gap);
        const f = fields[i];
        const label = f?.name || `field_${i + 1}`;
        const ftype = f?.type || 'String';

        // Label
        sk.noStroke();
        sk.fill(139, 148, 160);
        sk.textSize(10);
        sk.textAlign(sk.LEFT, sk.BOTTOM);
        sk.text(label, x + 10, fy + 14);

        // Input box
        sk.fill(25, 30, 40);
        sk.stroke(48, 58, 72);
        sk.strokeWeight(1);
        sk.rect(x + 10, fy + 16, w - 20, 22, 4);

        // Placeholder hint
        sk.noStroke();
        sk.fill(50, 60, 75);
        sk.textSize(9);
        sk.textAlign(sk.LEFT, sk.CENTER);
        sk.text(`${ftype}...`, x + 16, fy + 27);
      }
    } else if (isCard) {
      // ── Card wireframe ──
      const cardW = Math.min(w - 20, 300);
      const cardH = Math.min(h - 20, 250);

      sk.noStroke();
      sk.fill(25, 30, 40);
      sk.rect(x + 10, y + 10, cardW, cardH, 8);

      // Card image placeholder
      sk.fill(35, 42, 55);
      sk.rect(x + 20, y + 20, cardW - 40, cardH * 0.4, 4);
      sk.fill(50, 60, 75);
      sk.textSize(10);
      sk.textAlign(sk.CENTER, sk.CENTER);
      sk.text('Image', x + 10 + (cardW - 40) / 2, y + 20 + cardH * 0.2);

      // Card content
      sk.fill(139, 148, 160);
      sk.textSize(12);
      sk.textAlign(sk.LEFT, sk.BOTTOM);
      sk.text('Card Title', x + 20, y + 20 + cardH * 0.4 + 20);

      sk.fill(80, 90, 105);
      sk.textSize(10);
      sk.text('Card description text goes here...', x + 20, y + 20 + cardH * 0.4 + 38);

      // Fields as labels
      for (let i = 0; i < Math.min(fields.length, 3); i++) {
        const fy = y + 20 + cardH * 0.4 + 54 + i * 20;
        sk.fill(60, 70, 85);
        const label = fields[i]?.name || `field_${i + 1}`;
        const val = fields[i]?.type || 'value';
        sk.text(`${label}: ${val}`, x + 20, fy);
      }
    } else if (isDialog) {
      // ── Dialog/Modal wireframe ──
      const dw = Math.min(w - 40, 400);
      const dh = Math.min(h - 40, 300);
      const dx = x + (w - dw) / 2;
      const dy = y + (h - dh) / 2;

      // Backdrop
      sk.noStroke();
      sk.fill(0, 0, 0, 80);
      sk.rect(x, y, w, h);

      // Dialog box
      sk.fill(25, 30, 40);
      sk.stroke(48, 58, 72);
      sk.strokeWeight(1);
      sk.rect(dx, dy, dw, dh, 8);

      // Title bar
      sk.fill(40, 48, 60);
      sk.noStroke();
      sk.rect(dx, dy, dw, 32, 8, 8, 0, 0);
      sk.fill(139, 148, 160);
      sk.textSize(12);
      sk.textAlign(sk.CENTER, sk.CENTER);
      sk.text(compType.toUpperCase(), dx + dw / 2, dy + 16);

      // Content
      sk.fill(80, 90, 105);
      sk.textSize(10);
      sk.textAlign(sk.LEFT, sk.TOP);
      sk.text('Dialog content area...', dx + 16, dy + 48);

      // Fields
      for (let i = 0; i < Math.min(fields.length, 4); i++) {
        const fy = dy + 70 + i * 28;
        sk.fill(60, 70, 85);
        const label = fields[i]?.name || `field_${i + 1}`;
        sk.text(label, dx + 16, fy);
        sk.fill(25, 30, 40);
        sk.stroke(48, 58, 72);
        sk.rect(dx + 120, fy - 2, dw - 140, 20, 3);
      }

      // Buttons
      sk.noStroke();
      sk.fill(37, 99, 235);
      sk.rect(dx + dw - 110, dy + dh - 40, 50, 26, 4);
      sk.fill(255);
      sk.textSize(9);
      sk.textAlign(sk.CENTER, sk.CENTER);
      sk.text('OK', dx + dw - 85, dy + dh - 27);

      sk.fill(48, 58, 72);
      sk.rect(dx + dw - 165, dy + dh - 40, 50, 26, 4);
      sk.fill(200);
      sk.text('Cancel', dx + dw - 140, dy + dh - 27);
    } else {
      // ── Default generic wireframe ──
      sk.noStroke();
      sk.fill(25, 30, 40);
      sk.stroke(48, 58, 72);
      sk.strokeWeight(1);
      sk.rect(x + 10, y + 10, w - 20, h - 20, 8);

      sk.noStroke();
      sk.fill(100, 116, 139);
      sk.textSize(14);
      sk.textAlign(sk.CENTER, sk.CENTER);
      sk.text(`${compType.toUpperCase()}`, x + w / 2, y + h / 2 - 20);
      sk.fill(60, 70, 85);
      sk.textSize(10);
      sk.text(`Component type: ${compType}`, x + w / 2, y + h / 2 + 10);

      // Fields list
      for (let i = 0; i < Math.min(fields.length, 6); i++) {
        const fy = y + h / 2 + 30 + i * 22;
        sk.fill(50, 60, 75);
        const label = fields[i]?.name || `field_${i + 1}`;
        const ftype = fields[i]?.type || 'unknown';
        sk.textAlign(sk.LEFT, sk.CENTER);
        sk.text(`  ${label}  :  ${ftype}`, x + 30, fy);
      }
    }
  }
}
