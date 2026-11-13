import { bootstrapApplication } from '@angular/platform-browser';
import { provideZoneChangeDetection } from '@angular/core';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { AppComponent } from './app/app.component';
import { authInterceptor } from './app/core/api/api.service';

bootstrapApplication(AppComponent, { providers: [provideZoneChangeDetection({ eventCoalescing: true }), provideHttpClient(withInterceptors([authInterceptor]))] })
  .catch(err => console.error(err));
