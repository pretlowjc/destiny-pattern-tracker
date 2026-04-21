import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class BungieApiService {
  private apiUrl = 'https://d2patterntracker.com/api';

  constructor(private http: HttpClient) {}

  getWeaponPatterns(): Observable<any> {
    // Grab the secure token saved in local strorage
    const token = localStorage.getItem('bungie_access_token');

    // Attach it to the request headers
    const headers = new HttpHeaders({
      Authorization: `Bearer ${token}`,
    });

    // Make the call to FastAPI!
    return this.http.get(`${this.apiUrl}/patterns`, { headers });
  }

  getUserProfile(): Observable<any> {
    const token = localStorage.getItem('bungie_access_token');

    const headers = new HttpHeaders({
      Authorization: `Bearer ${token}`,
    });
    return this.http.get(`${this.apiUrl}/auth/profile`, { headers });
  }
}
