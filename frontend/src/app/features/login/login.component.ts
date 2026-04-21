import { Component } from '@angular/core';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss',
})
export class LoginComponent {
  loginWithBungie(): void {
    // This physically redirects the user's browser to the FastAPI backend
    // which then automatically bounces them to the offical Bungie login screen.
    window.location.href = 'https://d2patterntracker.com/api/auth/login';
  }
}
