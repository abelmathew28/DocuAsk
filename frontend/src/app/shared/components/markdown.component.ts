import { Component, Input } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { SecurityContext } from '@angular/core';
import { marked } from 'marked';

@Component({
  selector: 'app-markdown',
  template: `<div class="prose-chat text-[15px] leading-7" [innerHTML]="html"></div>`,
})
export class MarkdownComponent {
  html: SafeHtml | string = '';

  constructor(private readonly sanitizer: DomSanitizer) {}

  @Input() set content(value: string) {
    const raw = marked.parse(value || '', { async: false }) as string;
    this.html = this.sanitizer.sanitize(SecurityContext.HTML, raw) ?? '';
  }
}
