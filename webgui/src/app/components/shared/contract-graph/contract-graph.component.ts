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
}
interface Edge {
  from: string;
  to: string;
  type: string;
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
        <div class="cg-stats cg-entity-title" *ngIf="selectedEntity">
          <i class="fa-solid fa-cube"></i>
          <span>{{ selectedEntity }}</span>
        </div>
        <div class="cg-actions">
          <button
            *ngIf="selectedEntity"
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
        <div class="cg-leg-title">Edge Types</div>
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
  totalCount = 0;
  tooltipNode: Node | null = null;
  tooltipX = 0;
  tooltipY = 0;

  private flowNodes: Node[] = [];
  private flowEdges: Edge[] = [];

  private erdEntities: ERDEntity[] = [];
  private erdEdges: ERDEdge[] = [];

  legendItems = [
    { label: 'writes_to', color: '#2ecc71' },
    { label: 'fetches', color: '#3498db' },
    { label: 'reads_from', color: '#1abc9c' },
    { label: 'emits', color: '#f39c12' },
    { label: 'uses_command', color: '#9b59b6' },
    { label: 'guards', color: '#e74c3c' },
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
    this.ngZone.run(() => this.cdr.detectChanges());
  }

  backToOverview($event?: Event): void {
    $event?.stopPropagation();
    this.selectedEntity = null;
    this.panX = 0;
    this.panY = 0;
    this.zoom = 1;
    this.targetPanX = 0;
    this.targetPanY = 0;
    this.targetZoom = 1;
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

          // ── Level 1: ERD overview / Level 2: entity detail ──
          if (this.selectedEntity) {
            this.drawEntityDetail(sk);
          } else {
            this.drawERD(sk);
          }
          sk.pop();

          // Hover tooltip — both modes
          const wx = (sk.mouseX - this.panX) / this.zoom;
          const wy = (sk.mouseY - this.panY) / this.zoom;
          let hovered: Node | null = null;

          if (this.selectedEntity) {
            for (const n of this.flowNodes) {
              if (!n) continue;
              if (
                wx > n.x - n.w / 2 &&
                wx < n.x + n.w / 2 &&
                wy > n.y - n.h / 2 &&
                wy < n.y + n.h / 2
              ) {
                hovered = n;
                break;
              }
            }
          } else {
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

          // ── Entity detail: read-only (no interaction) ──
          return;
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

  private computeEntityDetailLayout(entityName: string): void {
    const W = this.p5Inst?.width || 960;
    const cluster = this.clusters.find((c) => c.name === entityName);
    if (!cluster || !cluster.entityNode) return;

    const nodeW = 155;
    const nodeH = 28;
    const vGap = 18;
    const hGap = 55;

    // Collect nodes per category
    const guards: Node[] = [];
    const commands: Node[] = [...cluster.commands];
    const queries: Node[] = [...cluster.queries];
    const events: Node[] = [...cluster.events];
    const workflows: Node[] = cluster.other.filter((n) => n.category === 'workflows');
    const uiComponents: Node[] = cluster.other.filter((n) => n.category === 'ui_components');

    // ── Phase 1: Discover related nodes from contract references ──
    const extraEntityUids = new Set<string>();
    const extraEventUids = new Set<string>();
    const extraCmdUids = new Set<string>();

    const discoverTargets = (n: Node) => {
      const rows = this.traceMatrix[n.category] || [];
      for (const row of rows) {
        if ((row.analysis_name || row.contract_id || '') !== n.label) continue;
        const cn = row.contract_node;
        if (!cn) continue;
        if (n.category === 'commands') {
          for (const ref of cn.writes_to || []) extraEntityUids.add(`entities:${String(ref)}`);
          for (const ref of cn.fetches || []) {
            if (typeof ref === 'object')
              extraEntityUids.add(
                `entities:${(ref as any).entity || (ref as any).entity_id || ''}`,
              );
          }
          for (const eff of cn.effects || []) {
            if (typeof eff === 'object' && (eff as any).entity)
              extraEntityUids.add(`entities:${(eff as any).entity}`);
          }
          for (const evt of cn.emits || []) extraEventUids.add(`events:${evt}`);
          for (const g of cn.guards || []) {
            const gid = typeof g === 'string' ? g : (g as any).guard_id || '';
            if (gid) extraCmdUids.add(`guards:${gid}`);
          }
        }
        if (n.category === 'queries') {
          for (const ref of cn.reads_from || []) extraEntityUids.add(`entities:${String(ref)}`);
          for (const ref of cn.fetches || []) {
            if (typeof ref === 'object')
              extraEntityUids.add(
                `entities:${(ref as any).entity || (ref as any).entity_id || ''}`,
              );
          }
        }
        if (n.category === 'workflows') {
          for (const trans of cn.transitions || []) {
            if (typeof trans === 'object') {
              const cmd = (trans as any).on || (trans as any).command;
              if (cmd) extraCmdUids.add(`commands:${cmd}`);
            }
          }
        }
        if (n.category === 'guards') {
          const t = cn.target || '';
          if (t) extraCmdUids.add(`commands:${t}`);
        }
        if (n.category === 'ui_components') {
          const t = cn.entity_id || '';
          if (t) extraEntityUids.add(`entities:${t}`);
        }
      }
    };

    for (const n of [
      ...guards,
      ...commands,
      ...queries,
      ...events,
      ...workflows,
      ...uiComponents,
    ]) {
      discoverTargets(n);
    }

    // Build base UID set and add extra nodes
    const baseUids = new Set<string>([
      cluster.entityNode.uid,
      ...cluster.commands.map((n) => n.uid),
      ...cluster.queries.map((n) => n.uid),
      ...cluster.events.map((n) => n.uid),
      ...workflows.map((n) => n.uid),
      ...uiComponents.map((n) => n.uid),
    ]);
    const extraNodes: Node[] = [];
    for (const uid of [...extraEntityUids, ...extraEventUids, ...extraCmdUids]) {
      if (!baseUids.has(uid)) {
        const src = this.uidMap.get(uid);
        if (src) {
          extraNodes.push({ ...src });
          baseUids.add(uid);
        }
      }
    }

    // Categorize extra nodes
    const extraGuards = extraNodes.filter((n) => n.category === 'guards');
    const extraCommands = extraNodes.filter((n) => n.category === 'commands');
    const extraEntities = extraNodes.filter(
      (n) => n.category === 'entities' && n.uid !== (cluster?.entityNode?.uid || ''),
    );
    const extraEvents = extraNodes.filter((n) => n.category === 'events');

    // ── Phase 2: 5-column CQRS layout ──
    // [Guards] → [Commands] → [Entity + Related] → [Events] → [Queries + Workflows + UI]
    const totalWidth = 5 * nodeW + 4 * hGap;
    const startX = Math.max(40, (W - totalWidth) / 2);
    const col = (i: number) => startX + i * (nodeW + hGap);
    const startY = 50;

    const posCol = (nodes: Node[], cx: number, cy: number) => {
      nodes.forEach((n, i) => {
        n.x = cx;
        n.y = cy + i * (nodeH + vGap);
        n.w = nodeW;
        n.h = nodeH;
      });
      return cy + nodes.length * (nodeH + vGap);
    };

    // Col 0: Guards
    posCol([...guards, ...extraGuards], col(0), startY);

    // Col 1: Commands
    posCol([...commands, ...extraCommands], col(1), startY);

    // Col 2: Main entity + related entities
    cluster.entityNode.x = col(2);
    cluster.entityNode.y = startY;
    cluster.entityNode.w = nodeW + 20;
    cluster.entityNode.h = nodeH + 6;
    posCol(extraEntities, col(2), startY + nodeH + vGap + 20);

    // Col 3: Events
    posCol([...events, ...extraEvents], col(3), startY);

    // Col 4: Queries, Workflows, UI components stacked vertically
    let ry = startY;
    ry = posCol(queries, col(4), ry);
    ry += 10;
    ry = posCol(workflows, col(4), ry);
    ry += 10;
    ry = posCol(uiComponents, col(4), ry);

    // ── Phase 3: Build edges ──
    this.flowNodes = [
      cluster.entityNode,
      ...guards,
      ...extraGuards,
      ...commands,
      ...extraCommands,
      ...extraEntities,
      ...events,
      ...extraEvents,
      ...queries,
      ...workflows,
      ...uiComponents,
    ];
    const uidSet = new Set(this.flowNodes.map((n) => n.uid));
    this.flowEdges = [];

    const conn = (from: string, to: string, type: string) => {
      if (uidSet.has(from) && uidSet.has(to)) this.flowEdges.push({ from, to, type });
    };

    for (const n of this.flowNodes) {
      if (n.category === 'entities') continue;
      const rows = this.traceMatrix[n.category] || [];
      for (const row of rows) {
        if ((row.analysis_name || row.contract_id || '') !== n.label) continue;
        const cn = row.contract_node;
        if (!cn) continue;
        if (n.category === 'guards') {
          const t = cn.target || '';
          if (t) conn(n.uid, `commands:${t}`, 'guards');
        }
        if (n.category === 'commands') {
          for (const ref of cn.writes_to || []) conn(n.uid, `entities:${String(ref)}`, 'writes_to');
          for (const ref of cn.fetches || []) {
            if (typeof ref === 'object')
              conn(
                n.uid,
                `entities:${(ref as any).entity || (ref as any).entity_id || ''}`,
                'fetches',
              );
          }
          for (const eff of cn.effects || []) {
            if (typeof eff === 'object' && (eff as any).entity)
              conn(n.uid, `entities:${(eff as any).entity}`, 'writes_to');
          }
          for (const evt of cn.emits || []) conn(n.uid, `events:${evt}`, 'emits');
        }
        if (n.category === 'queries') {
          for (const ref of cn.reads_from || [])
            conn(n.uid, `entities:${String(ref)}`, 'reads_from');
          for (const ref of cn.fetches || []) {
            if (typeof ref === 'object')
              conn(
                n.uid,
                `entities:${(ref as any).entity || (ref as any).entity_id || ''}`,
                'fetches',
              );
          }
        }
        if (n.category === 'workflows') {
          for (const trans of cn.transitions || []) {
            if (typeof trans === 'object') {
              const cmd = (trans as any).on || (trans as any).command;
              if (cmd) conn(n.uid, `commands:${cmd}`, 'uses_command');
            }
          }
        }
        if (n.category === 'ui_components') {
          const t = cn.entity_id || '';
          if (t) conn(n.uid, `entities:${t}`, 'entity_ref');
        }
      }
    }

    // Deduplicate
    const seen = new Set<string>();
    this.flowEdges = this.flowEdges.filter((e) => {
      const key = `${e.from}|${e.to}|${e.type}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }

  // ── Entity Detail Drawing ───────────────────────────────

  private drawEntityDetail(sk: p5): void {
    // Draw edges first (behind nodes)
    this.drawFlowEdges(sk);

    // Draw nodes
    for (const n of this.flowNodes) {
      this.drawFlowNode(sk, n);
    }

    // Draw edge labels
    this.drawEdgeLabels(sk);
  }

  private drawFlowEdges(sk: p5): void {
    const arrowSize = 7;
    // Build local uid->Node map from flowNodes (positions are from flow layout)
    const flowUidMap = new Map<string, Node>();
    for (const n of this.flowNodes) flowUidMap.set(n.uid, n);

    for (const e of this.flowEdges) {
      const a = flowUidMap.get(e.from);
      const b = flowUidMap.get(e.to);
      if (!a || !b) continue;
      const ec = EDGE_COLORS[e.type] || [100, 100, 120];

      // Determine if edge is vertical (same x) or needs angled path
      const dx = b.x - a.x;
      const dy = b.y - a.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;

      if (Math.abs(dx) < 10) {
        // Vertical edge (same column)
        const fromBottom = a.y + a.h / 2;
        const toTop = b.y - b.h / 2;

        sk.noFill();
        sk.stroke(ec[0], ec[1], ec[2], 120);
        sk.strokeWeight(1.5);
        sk.line(a.x, fromBottom, b.x, toTop);

        // Arrowhead
        const midY = (fromBottom + toTop) / 2;
        sk.noStroke();
        sk.fill(ec[0], ec[1], ec[2], 180);
        sk.triangle(
          b.x,
          toTop + arrowSize,
          b.x - arrowSize * 0.6,
          toTop - arrowSize * 0.4,
          b.x + arrowSize * 0.6,
          toTop - arrowSize * 0.4,
        );
      } else {
        // Angled edge with elbow
        const fromBottom = a.y + a.h / 2;
        const toTop = b.y - b.h / 2;
        const elbowY = fromBottom + (toTop - fromBottom) * 0.5;

        sk.noFill();
        sk.stroke(ec[0], ec[1], ec[2], 100);
        sk.strokeWeight(1.2);
        // Elbow path: down from source, horizontal, up to target
        sk.beginShape();
        sk.vertex(a.x, fromBottom);
        sk.vertex(a.x, elbowY);
        sk.vertex(b.x, elbowY);
        sk.vertex(b.x, toTop);
        sk.endShape();

        // Arrowhead at target
        const midX = b.x;
        const midY2 = toTop;
        sk.noStroke();
        sk.fill(ec[0], ec[1], ec[2], 150);
        sk.triangle(
          midX,
          midY2 + arrowSize,
          midX - arrowSize * 0.6,
          midY2 - arrowSize * 0.4,
          midX + arrowSize * 0.6,
          midY2 - arrowSize * 0.4,
        );
      }
    }
  }

  private drawEdgeLabels(sk: p5): void {
    for (const e of this.flowEdges) {
      const a = this.uidMap.get(e.from);
      const b = this.uidMap.get(e.to);
      if (!a || !b) continue;

      const label = EDGE_LABEL[e.type] || e.type;
      const mx = (a.x + b.x) / 2;
      const my = (a.y + b.y) / 2;

      sk.noStroke();
      sk.fill(139, 148, 158, 140);
      sk.textSize(8);
      sk.textAlign(sk.CENTER, sk.CENTER);
      sk.text(label, mx, my);
    }
  }

  private drawFlowNode(sk: p5, n: Node): void {
    const cc = CAT_COLOR[n.category] || [150, 150, 150];
    const sc = STATUS_BORDER[n.status] || STATUS_BORDER['matched'];
    const hw = n.w / 2,
      hh = n.h / 2;
    const isEntity = n.category === 'entities';

    // Shadow
    sk.noStroke();
    sk.fill(0, 0, 0, 30);
    sk.rect(n.x - hw + 2, n.y - hh + 2, n.w, n.h, 6);

    // Background
    sk.fill(isEntity ? 22 : 18, isEntity ? 30 : 24, isEntity ? 45 : 35);
    sk.stroke(sc[0], sc[1], sc[2], sc[3]);
    sk.strokeWeight(isEntity ? 2.5 : n.status === 'matched' ? 1 : 2);
    sk.rect(n.x - hw, n.y - hh, n.w, n.h, 6);

    // Category accent bar (left side, wider for entity)
    sk.noStroke();
    const barW = isEntity ? 5 : 3;
    sk.fill(cc[0], cc[1], cc[2], isEntity ? 255 : 220);
    sk.rect(n.x - hw, n.y - hh + 2, barW, n.h - 4, 2);

    // Category icon/text
    const catIcon = this.getCategoryIcon(n.category);
    sk.fill(cc[0], cc[1], cc[2], 200);
    sk.textSize(9);
    sk.textAlign(sk.LEFT, sk.CENTER);
    sk.text(catIcon, n.x - hw + 10, n.y);

    // Label
    const maxChars = Math.floor((n.w - 30) / 5.2);
    const label = n.label.length > maxChars ? n.label.substring(0, maxChars - 1) + '…' : n.label;
    sk.fill(220, 225, 235);
    sk.textSize(isEntity ? 11 : 9);
    sk.textAlign(sk.LEFT, sk.CENTER);
    sk.text(label, n.x - hw + 24, n.y);

    // Status indicator
    if (n.status !== 'matched') {
      const warnColor =
        n.status === 'orphan_analysis'
          ? [231, 76, 60]
          : n.status === 'orphan_contract'
            ? [241, 196, 15]
            : [230, 126, 34];
      sk.fill(warnColor[0], warnColor[1], warnColor[2], 200);
      sk.noStroke();
      sk.textSize(11);
      sk.textAlign(sk.RIGHT, sk.CENTER);
      sk.text('!', n.x + hw - 5, n.y);
    }
  }

  private getCategoryIcon(cat: string): string {
    const icons: Record<string, string> = {
      entities: '◆',
      commands: '⚡',
      queries: '◉',
      events: '◈',
      workflows: '⟳',
      value_objects: '◇',
      guards: '⛨',
      roles: '👤',
      ui_components: '▣',
    };
    return icons[cat] || '●';
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
}
