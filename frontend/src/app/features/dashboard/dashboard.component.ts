import { Component, OnInit, signal, computed } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { BungieApiService } from '../../core/services/bungie-api.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss'
})


export class DashboardComponent implements OnInit {
  errorMessage = signal<string | null>(null);

  // --- DAY 13: STATE MANAGEMENT (Signals) ---
  weapons = signal<any[]>([]);
  isLoading = signal<boolean>(true);

  // --- DAY 14: SEARCH AND FILTER STATE ---
  searchQuery = signal<string>('');
  selectedCategory = signal<string>('All');

// This magically recalculates itself anytime the search query or category changes!
  filteredWeapons = computed(() => {
    const query = this.searchQuery().toLowerCase();
    const category = this.selectedCategory();
    
    let filtered = this.weapons().filter(w => {
      const matchesSearch = w.name.toLowerCase().includes(query);
      const matchesCategory = category === 'All' || w.type === category;
      return matchesSearch && matchesCategory;
    });

    // --- DAY 19: Sorting Logic ---
    filtered.sort((a, b) => {
      const aComplete = a.progress >= a.completionValue ? 1 : 0;
      const bComplete = b.progress >= b.completionValue ? 1 : 0;
      
      // 1. If one is complete and the other isn't, push the complete one down
      if (aComplete !== bComplete) {
        return aComplete - bComplete;
      }
      
      // 2. Otherwise, sort by percentage complete (highest percentage at the top)
      const aPercentage = a.progress / a.completionValue;
      const bPercentage = b.progress / b.completionValue;
      return bPercentage - aPercentage;
    });

    return filtered;
  });

  constructor(
    private route: ActivatedRoute, 
    private router: Router,
    private bungieApi: BungieApiService
  ) {}

  ngOnInit(): void {
    this.route.queryParams.subscribe(params => {
      const urlToken = params['token'];

      if (urlToken) {
        localStorage.setItem('bungie_access_token', urlToken);
        this.router.navigate(['/dashboard'], { replaceUrl: true });
        return; 
      }

      const savedToken = localStorage.getItem('bungie_access_token');
      if (savedToken && savedToken !== 'null') {
        this.bungieApi.getUserProfile().subscribe({
          next: (profile) => console.log("Identity Confirmed! My Destiny Profile:", profile),
          error: (err) => console.error("Identity check failed:", err)
        });

        this.fetchPatterns();
      } else {
        console.warn("No token found in storage. Please log in again.");
      }
    });
  }

  fetchPatterns(): void {
    this.errorMessage.set(null);

    this.bungieApi.getWeaponPatterns().subscribe({
      next: (data) => {
        this.weapons.set(data);
        this.isLoading.set(false);
      },
      error: (err) => {
        console.error("Failed to fetch weapons:", err);
        this.errorMessage.set("Lost connection to Bungie servers. Please try again later.");
        this.isLoading.set(false);
      }
    });
  }

  // --- HTML Event Listeners ---
  updateSearch(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.searchQuery.set(input.value);
  }

  updateCategory(event: Event): void {
    const select = event.target as HTMLSelectElement;
    this.selectedCategory.set(select.value);
  }
}