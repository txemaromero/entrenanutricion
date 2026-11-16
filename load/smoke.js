// Load smoke test (k6) of the main client screens through nginx → gunicorn → PostgreSQL.
//   docker run --rm --network host -v "$PWD/load:/load" -e BASE_URL=http://localhost:8080 \
//     grafana/k6:2.2.0 run /load/smoke.js
// Needs the demo data (seed_demo). It logs in once (login is rate limited) and shares the token.
// Outside development the demo accounts have their own password: pass it with -e DEMO_PASSWORD.
import http from 'k6/http';
import { check, group, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';
const API = `${BASE_URL}/api/v1`;
const PASSWORD = __ENV.DEMO_PASSWORD || 'entrenanutricion#2025';

export const options = {
  scenarios: {
    clients: { executor: 'constant-vus', vus: 20, duration: '30s' },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<800'],
    checks: ['rate>0.99'],
  },
};

export function setup() {
  const response = http.post(
    `${API}/auth/login`,
    JSON.stringify({ email: 'cliente@entrenanutricion.dev', password: PASSWORD }),
    { headers: { 'Content-Type': 'application/json' } },
  );
  check(response, { 'login 200': (r) => r.status === 200 });
  return { access: response.json('access') };
}

export default function (data) {
  const params = { headers: { Authorization: `Bearer ${data.access}` } };
  const get = (name, path) => {
    const response = http.get(`${API}${path}`, { ...params, tags: { name } });
    check(response, { [`${name} 200`]: (r) => r.status === 200 });
  };

  group('client screens', () => {
    get('me', '/me');
    get('training plan', '/me/training-plan');
    get('dashboard', '/me/progress/dashboard');
    get('nutrition plan', '/me/nutrition-plan');
    get('weights', '/me/weight-records');
    get('badges', '/me/badges');
    get('foods', '/foods?limit=20');
  });
  sleep(1);
}
