import { Component, ElementRef, Input, OnChanges, AfterViewInit, SimpleChanges, ViewChild, signal } from '@angular/core';
import { NgIf } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { installPdfPolyfills } from '../../../pdfjs-polyfills';
import {
  getDocument,
  GlobalWorkerOptions,
  Util,
  type PDFDocumentProxy,
  type PDFPageProxy,
  type PageViewport,
  type RenderTask,
} from 'pdfjs-dist/legacy/build/pdf.mjs';
import { environment } from '../../../environments/environment';

installPdfPolyfills();
GlobalWorkerOptions.workerSrc = '/pdfjs/pdf.worker.min.mjs';

@Component({
  selector: 'app-pdf-viewer',
  imports: [NgIf],
  template: `
    <div class="flex h-[calc(100vh-8rem)] flex-col">
      <div class="flex items-center justify-between px-3 py-2 text-sm">
        <button type="button" class="rounded-md px-2 py-1 hover:bg-paper-100 disabled:opacity-40 dark:hover:bg-white/10" (click)="change(-1)" [disabled]="pageNum() <= 1">Prev</button>
        <span>Page {{ pageNum() }} / {{ pages() || '—' }}</span>
        <button type="button" class="rounded-md px-2 py-1 hover:bg-paper-100 disabled:opacity-40 dark:hover:bg-white/10" (click)="change(1)" [disabled]="pageNum() >= pages()">Next</button>
      </div>
      <div class="flex items-center justify-center gap-2 px-3 pb-2 text-sm">
        <button type="button" class="rounded-md px-2 py-1 hover:bg-paper-100 dark:hover:bg-white/10" (click)="zoom(-0.1)">−</button>
        <span>{{ Math.round(scale() * 100) }}%</span>
        <button type="button" class="rounded-md px-2 py-1 hover:bg-paper-100 dark:hover:bg-white/10" (click)="zoom(0.1)">+</button>
      </div>
      <div class="relative flex-1 overflow-auto bg-paper-100 p-3 dark:bg-ink-950">
        <p *ngIf="loading" class="p-4 text-sm text-ink-600">Opening the page…</p>
        <p *ngIf="error" class="p-4 text-sm text-red-600">{{ error }}</p>
        <div class="relative mx-auto w-fit" [class.hidden]="!!error || loading">
          <canvas #canvas class="max-w-full bg-white shadow"></canvas>
          <div #highlights class="pointer-events-none absolute inset-0"></div>
        </div>
      </div>
    </div>
  `,
})
export class PdfViewerComponent implements OnChanges, AfterViewInit {
  @Input() documentId = '';
  @Input() page = 1;
  @Input() excerpt = '';
  @ViewChild('canvas') canvas?: ElementRef<HTMLCanvasElement>;
  @ViewChild('highlights') highlights?: ElementRef<HTMLDivElement>;
  pageNum = signal(1);
  pages = signal(0);
  scale = signal(1.1);
  error = '';
  loading = false;
  Math = Math;
  private pdf: PDFDocumentProxy | null = null;
  private loadedId = '';
  private renderTask: RenderTask | null = null;
  private viewReady = false;

  constructor(private readonly http: HttpClient) {}

  ngAfterViewInit(): void {
    this.viewReady = true;
    void this.render();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (!this.documentId) return;
    if (changes['documentId'] && this.documentId !== this.loadedId) {
      void this.load();
      return;
    }
    if ((changes['page'] || changes['excerpt']) && this.pdf) {
      this.pageNum.set(Math.min(Math.max(this.page, 1), this.pdf.numPages));
      void this.render();
    }
  }

  async load(): Promise<void> {
    this.error = '';
    this.loading = true;
    try {
      const data = await firstValueFrom(
        this.http.get(`${environment.apiUrl}/documents/${this.documentId}/file`, { responseType: 'arraybuffer' })
      );
      const bytes = new Uint8Array(data);
      if (bytes.byteLength < 5 || String.fromCharCode(...bytes.slice(0, 5)) !== '%PDF-') {
        this.error = 'This source is not a PDF, so it cannot open in the page viewer. Download the original file instead.';
        return;
      }
      this.pdf = await this.openPdf(bytes);
      this.loadedId = this.documentId;
      this.pages.set(this.pdf.numPages);
      this.pageNum.set(Math.min(Math.max(this.page, 1), this.pdf.numPages));
      await this.render();
    } catch (err) {
      this.error = this.describeError(err);
    } finally {
      this.loading = false;
    }
  }

  change(delta: number): void {
    const next = this.pageNum() + delta;
    if (next < 1 || next > this.pages()) return;
    this.pageNum.set(next);
    void this.render();
  }

  zoom(delta: number): void {
    this.scale.set(Math.min(2.2, Math.max(0.6, this.scale() + delta)));
    void this.render();
  }

  private async openPdf(data: Uint8Array): Promise<PDFDocumentProxy> {
    const options = {
      wasmUrl: '/pdfjs/wasm/',
      cMapUrl: '/pdfjs/cmaps/',
      cMapPacked: true,
      standardFontDataUrl: '/pdfjs/standard_fonts/',
    };
    try {
      return await getDocument({ data: data.slice(), ...options }).promise;
    } catch {
      return await getDocument({ data: data.slice(), useWasm: false }).promise;
    }
  }

  private async render(): Promise<void> {
    if (!this.pdf || !this.viewReady) return;
    const page = await this.pdf.getPage(this.pageNum());
    const viewport = page.getViewport({ scale: this.scale() });
    const canvas = this.canvas?.nativeElement;
    if (!canvas) return;
    if (this.renderTask) {
      this.renderTask.cancel();
      try {
        await this.renderTask.promise;
      } catch {
        /* cancelled */
      }
    }
    canvas.width = viewport.width;
    canvas.height = viewport.height;
    this.renderTask = page.render({ canvas, viewport });
    await this.renderTask.promise;
    await this.paintHighlights(page, viewport);
  }

  private async paintHighlights(page: PDFPageProxy, viewport: PageViewport): Promise<void> {
    const layer = this.highlights?.nativeElement;
    if (!layer) return;
    layer.innerHTML = '';
    layer.style.width = `${viewport.width}px`;
    layer.style.height = `${viewport.height}px`;
    const needle = this.normalize(this.excerpt).slice(0, 80);
    if (!needle) return;
    const text = await page.getTextContent();
    for (const item of text.items) {
      if (!('str' in item) || !item.str) continue;
      const hay = this.normalize(item.str);
      if (!hay || (!needle.includes(hay) && !hay.includes(needle.slice(0, Math.min(24, needle.length))))) {
        continue;
      }
      const tx = Util.transform(viewport.transform, item.transform);
      const x = tx[4];
      const y = tx[5];
      const height = Math.hypot(tx[2], tx[3]) || 10;
      const width = ('width' in item && typeof item.width === 'number' ? item.width : item.str.length * 5) * (viewport.scale || 1);
      const mark = document.createElement('div');
      mark.style.position = 'absolute';
      mark.style.left = `${x}px`;
      mark.style.top = `${y - height}px`;
      mark.style.width = `${Math.max(width, 12)}px`;
      mark.style.height = `${height * 1.15}px`;
      mark.style.background = 'rgba(140, 59, 42, 0.22)';
      layer.appendChild(mark);
    }
  }

  private describeError(err: unknown): string {
    const message = err && typeof err === 'object' && 'message' in err ? String((err as { message: string }).message) : '';
    if (message.toLowerCase().includes('worker')) {
      return 'The PDF worker failed to start. Refresh the page and open the citation again.';
    }
    if (message.toLowerCase().includes('invalid pdf') || message.toLowerCase().includes('invalidpdf')) {
      return 'This file could not be parsed as a PDF.';
    }
    return message ? `Unable to open this page: ${message}` : 'Unable to load this file in the PDF viewer.';
  }

  private normalize(value: string): string {
    return (value || '').toLowerCase().replace(/\s+/g, ' ').trim();
  }
}
