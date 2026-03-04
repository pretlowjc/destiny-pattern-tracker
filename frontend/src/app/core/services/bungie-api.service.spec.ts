import { TestBed } from '@angular/core/testing';

import { BungieApiService } from './bungie-api.service';

describe('BungieApiService', () => {
  let service: BungieApiService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(BungieApiService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
