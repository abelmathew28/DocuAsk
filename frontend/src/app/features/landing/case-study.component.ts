import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { SiteHeaderComponent } from '../../shared/components/site-header.component';
import { SiteFooterComponent } from '../../shared/components/site-footer.component';
import { KnowledgeNetworkCanvasComponent } from './knowledge-network-canvas.component';

@Component({
  selector: 'app-case-study',
  imports: [RouterLink, SiteHeaderComponent, SiteFooterComponent, KnowledgeNetworkCanvasComponent],
  templateUrl: './case-study.component.html',
})
export class CaseStudyComponent {}
