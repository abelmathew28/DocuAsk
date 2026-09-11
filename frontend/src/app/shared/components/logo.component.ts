import { Component, Input } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-logo',
  imports: [RouterLink],
  template: `
    <a [routerLink]="link" class="inline-flex items-center gap-2 text-ink-950 no-underline dark:text-paper-50">
      <span class="font-display text-[1.35rem] leading-none tracking-tight">DocuAsk</span>
    </a>
  `,
})
export class LogoComponent {
  @Input() link = '/';
  @Input() showSubtitle = false;
  @Input() invert = false;
}
