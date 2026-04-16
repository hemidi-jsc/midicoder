import { Component } from '@angular/core';

import { AppComponent } from './app.component';

@Component({
  selector: 'app-webgui',
  standalone: true,
  imports: [AppComponent],
  template: `
    <app-root />
  `
})
export class App {
  protected readonly title = 'Midicoder';
}
