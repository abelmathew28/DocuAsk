import {
  AfterViewInit,
  Component,
  ElementRef,
  HostListener,
  Input,
  OnChanges,
  OnDestroy,
  SimpleChanges,
  ViewChild,
} from '@angular/core';

type NodeKind = 'document' | 'page' | 'passage';

interface NetworkNode {
  id: number;
  x: number;
  y: number;
  vx: number;
  vy: number;
  r: number;
  kind: NodeKind;
}

@Component({
  selector: 'app-knowledge-network-canvas',
  standalone: true,
  template: `
    <canvas
      #canvas
      class="pointer-events-none absolute inset-0 h-full w-full"
      aria-hidden="true"
    ></canvas>
  `,
  host: {
    class: 'pointer-events-none absolute inset-0 -z-10 overflow-hidden',
  },
})
export class KnowledgeNetworkCanvasComponent implements AfterViewInit, OnChanges, OnDestroy {
  @ViewChild('canvas', { static: true }) canvasRef!: ElementRef<HTMLCanvasElement>;
  @Input() highlightIds: number[] = [];
  /** 0–1 opacity scale for dashboard vs marketing. */
  @Input() intensity = 1;

  private nodes: NetworkNode[] = [];
  private raf = 0;
  private reducedMotion = false;
  private pointerX = 0.5;
  private pointerY = 0.4;
  private width = 0;
  private height = 0;
  private dpr = 1;
  private running = false;

  ngAfterViewInit(): void {
    this.reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    this.resize();
    this.seed();
    this.running = true;
    if (this.reducedMotion) {
      this.draw(0);
      return;
    }
    this.loop(0);
  }

  ngOnChanges(changes: SimpleChanges): void {
    if ((changes['highlightIds'] || changes['intensity']) && this.reducedMotion && this.width) {
      this.draw(0);
    }
  }

  ngOnDestroy(): void {
    this.running = false;
    if (this.raf) cancelAnimationFrame(this.raf);
  }

  @HostListener('window:resize')
  onResize(): void {
    this.resize();
    this.seed();
    if (this.reducedMotion) this.draw(0);
  }

  @HostListener('window:pointermove', ['$event'])
  onPointer(event: PointerEvent): void {
    if (this.reducedMotion || !this.width || !this.height) return;
    this.pointerX = event.clientX / this.width;
    this.pointerY = event.clientY / this.height;
  }

  private resize(): void {
    const canvas = this.canvasRef.nativeElement;
    const parent = canvas.parentElement;
    this.width = parent?.clientWidth || window.innerWidth;
    this.height = Math.max(parent?.clientHeight || window.innerHeight, window.innerHeight);
    this.dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.floor(this.width * this.dpr);
    canvas.height = Math.floor(this.height * this.dpr);
    canvas.style.width = `${this.width}px`;
    canvas.style.height = `${this.height}px`;
    const ctx = canvas.getContext('2d');
    if (ctx) ctx.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);
  }

  private targetCount(): number {
    if (this.width < 640) return 24;
    if (this.width < 1024) return 40;
    return 55;
  }

  private seed(): void {
    const count = this.targetCount();
    const kinds: NodeKind[] = ['document', 'page', 'passage'];
    this.nodes = Array.from({ length: count }, (_, id) => {
      const kind = kinds[id % 3];
      return {
        id,
        x: Math.random() * this.width,
        y: Math.random() * this.height,
        vx: (Math.random() - 0.5) * 0.18,
        vy: (Math.random() - 0.5) * 0.18,
        r: kind === 'document' ? 2.6 : kind === 'page' ? 2 : 1.5,
        kind,
      };
    });
  }

  private loop(time: number): void {
    if (!this.running) return;
    this.draw(time);
    this.raf = requestAnimationFrame((t) => this.loop(t));
  }

  private draw(time: number): void {
    const canvas = this.canvasRef.nativeElement;
    const ctx = canvas.getContext('2d');
    if (!ctx || !this.width) return;

    ctx.clearRect(0, 0, this.width, this.height);

    const parallaxX = this.reducedMotion ? 0 : (this.pointerX - 0.5) * 18;
    const parallaxY = this.reducedMotion ? 0 : (this.pointerY - 0.5) * 12;
    const highlight = new Set(this.highlightIds);
    const linkDist = this.width < 640 ? 90 : 118;
    const scale = Math.max(0.2, Math.min(1, this.intensity));

    if (!this.reducedMotion) {
      for (const node of this.nodes) {
        node.x += node.vx * scale;
        node.y += node.vy * scale;
        if (node.x < 0 || node.x > this.width) node.vx *= -1;
        if (node.y < 0 || node.y > this.height) node.vy *= -1;
        node.x = Math.max(0, Math.min(this.width, node.x));
        node.y = Math.max(0, Math.min(this.height, node.y));
      }
    }

    for (let i = 0; i < this.nodes.length; i++) {
      for (let j = i + 1; j < this.nodes.length; j++) {
        const a = this.nodes[i];
        const b = this.nodes[j];
        const dx = a.x - b.x;
        const dy = a.y - b.y;
        const dist = Math.hypot(dx, dy);
        if (dist > linkDist) continue;
        const both = highlight.has(a.id) && highlight.has(b.id);
        const either = highlight.has(a.id) || highlight.has(b.id);
        const alpha = (both ? 0.55 : either ? 0.32 : 0.14 * (1 - dist / linkDist)) * scale;
        ctx.strokeStyle = both || either ? `rgba(91, 75, 138, ${alpha})` : `rgba(92, 87, 79, ${alpha})`;
        ctx.lineWidth = both ? 1.25 : 0.85;
        ctx.beginPath();
        ctx.moveTo(a.x + parallaxX * 0.15, a.y + parallaxY * 0.15);
        ctx.lineTo(b.x + parallaxX * 0.15, b.y + parallaxY * 0.15);
        ctx.stroke();
      }
    }

    const pulse = this.reducedMotion ? 1 : 0.85 + Math.sin(time / 900) * 0.15;
    for (const node of this.nodes) {
      const active = highlight.has(node.id);
      const x = node.x + parallaxX * (node.kind === 'document' ? 0.25 : 0.12);
      const y = node.y + parallaxY * (node.kind === 'document' ? 0.25 : 0.12);
      ctx.beginPath();
      ctx.arc(x, y, node.r * (active ? pulse * 1.35 : 1), 0, Math.PI * 2);
      ctx.fillStyle = active
        ? `rgba(91, 75, 138, ${0.9 * scale})`
        : `rgba(92, 87, 79, ${0.48 * scale})`;
      ctx.fill();
      if (active) {
        ctx.beginPath();
        ctx.arc(x, y, node.r * 3.2, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(91, 75, 138, ${0.16 * scale})`;
        ctx.fill();
      }
    }
  }
}
