import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-empty-state',
  template: `
    <div class="py-16">
      <p class="font-display text-2xl">{{ title }}</p>
      <p class="mt-2 max-w-md text-sm leading-6 text-ink-600">{{ message }}</p>
      <div class="mt-4">
        <ng-content></ng-content>
      </div>
    </div>
  `,
})
export class EmptyStateComponent {
  @Input() title = 'Nothing here yet';
  @Input() message = '';
}
