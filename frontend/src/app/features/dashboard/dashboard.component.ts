import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { BungieApiService } from '../../core/services/bungie-api.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss',
})
export class DashboardComponent implements OnInit {
  weapons: any[] = [];
  isLoading: boolean = true;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private bungieApi: BungieApiService,
  ) {}

  ngOnInit(): void {
    this.route.queryParams.subscribe((params) => {
      const token = params['token'];
      if (token) {
        localStorage.setItem('bungieAccessToken', token);
        this.router.navigate(['/dashboard'], { replaceUrl: true });
      }
      this.fetchPatterns();
    });
  }

  fetchPatterns(): void {
    this.bungieApi.getWeaponPatterns().subscribe({
      next: (data) => {
		this.weapons = data;
		this.isLoading = false;
      },
      error: (error) => {
        console.error('Error fetching weapon patterns:', error);
        this.isLoading = false;
      },
    });
  }
}
