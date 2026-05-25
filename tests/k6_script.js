import http from 'k6/http';
import { check, sleep } from 'k6';

// Test configuration
export const options = {
  stages: [
    { duration: '30s', target: 30 }, // Ramp up to 30 concurrent users over 30 seconds
    { duration: '2m', target: 30 },  // Stay at 30 users for 2 minutes
    { duration: '30s', target: 0 },  // Ramp down to 0 users
  ],
  thresholds: {
    // Requirements: average response time < 10s (10000ms)
    // 95% of requests should complete within 10s
    http_req_duration: ['avg<10000', 'p(95)<10000'],
    // Ensure no server crashes (success rate > 99%)
    http_req_failed: ['rate<0.01'], 
  },
};

const BASE_URL = 'http://localhost:8000/api';

export default function () {
  // Scenario 1: Search query
  const searchRes = http.get(`${BASE_URL}/search?query=List+the+problems+of+MiniPC+model+sales`);
  check(searchRes, {
    'search status is 200': (r) => r.status === 200,
  });
  
  sleep(1);

  // Scenario 2: View Dashboard
  const dashRes = http.get(`${BASE_URL}/meetings`);
  check(dashRes, {
    'dashboard status is 200': (r) => r.status === 200,
  });

  sleep(1);
}

// To run this script:
// k6 run k6_script.js
