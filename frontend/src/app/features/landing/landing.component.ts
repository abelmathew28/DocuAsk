import { Component } from '@angular/core';
import { SiteHeaderComponent } from '../../shared/components/site-header.component';
import { SiteFooterComponent } from '../../shared/components/site-footer.component';
import { KnowledgeNetworkCanvasComponent } from './knowledge-network-canvas.component';
import { LandingHeroComponent } from './sections/landing-hero.component';
import { LandingDemoQaComponent } from './sections/landing-demo-qa.component';
import { LandingWorkflowComponent } from './sections/landing-workflow.component';
import { LandingFeaturesComponent } from './sections/landing-features.component';
import { LandingCitationPreviewComponent } from './sections/landing-citation-preview.component';
import { LandingSecurityTeaserComponent } from './sections/landing-security-teaser.component';
import { LandingArchitectureComponent } from './sections/landing-architecture.component';
import { LandingCtaComponent } from './sections/landing-cta.component';
import { SAMPLE_DEMOS, SampleDemo } from './sample-docs';

@Component({
  selector: 'app-landing',
  imports: [
    SiteHeaderComponent,
    SiteFooterComponent,
    KnowledgeNetworkCanvasComponent,
    LandingHeroComponent,
    LandingDemoQaComponent,
    LandingWorkflowComponent,
    LandingFeaturesComponent,
    LandingCitationPreviewComponent,
    LandingSecurityTeaserComponent,
    LandingArchitectureComponent,
    LandingCtaComponent,
  ],
  templateUrl: './landing.component.html',
})
export class LandingComponent {
  readonly demos = SAMPLE_DEMOS;
  activeDemo = 0;

  get demo(): SampleDemo {
    return this.demos[this.activeDemo];
  }

  get highlightIds(): number[] {
    return this.demo?.highlightIds ?? [];
  }

  onDemoChange(index: number): void {
    this.activeDemo = index;
  }

  scrollToCitation(): void {
    document.getElementById('citation')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}
