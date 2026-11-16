import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

import {
  CONTENT_SECURITY_POLICY,
  SECURITY_HEADERS,
  STRICT_TRANSPORT_SECURITY,
} from '../security-headers';

const read = (path: string) => readFileSync(resolve(__dirname, '..', path), 'utf8');

describe('production security headers', () => {
  it('nginx sends the same headers as security-headers.ts', () => {
    const snippet = read('docker/security-headers.conf');
    for (const [name, value] of Object.entries(SECURITY_HEADERS)) {
      expect(snippet).toContain(`add_header ${name} "${value}" always;`);
    }
  });

  it('every nginx location with its own headers includes the security headers', () => {
    const conf = read('docker/nginx.conf');
    const blocks = conf.split('location ').slice(1);
    for (const block of blocks.filter((body) => body.includes('add_header'))) {
      expect(block).toContain('include /etc/nginx/snippets/security-headers.conf;');
    }
  });

  it('the Render static site sends the same headers', () => {
    const blueprint = read('../render.yaml');
    for (const [name, value] of Object.entries(SECURITY_HEADERS)) {
      expect(blueprint).toContain(`name: ${name}\n        value: "${value}"`);
    }
  });

  it('the Render static site (HTTPS) also asks browsers to use HTTPS only', () => {
    const blueprint = read('../render.yaml');

    expect(blueprint).toContain(
      `name: Strict-Transport-Security\n        value: "${STRICT_TRANSPORT_SECURITY}"`,
    );
    expect(STRICT_TRANSPORT_SECURITY).toMatch(/^max-age=(\d+);/);
    expect(Number(/max-age=(\d+)/.exec(STRICT_TRANSPORT_SECURITY)![1])).toBeGreaterThanOrEqual(
      31536000,
    );
  });

  it('only allows scripts of the app itself', () => {
    expect(CONTENT_SECURITY_POLICY).toContain("script-src 'self';");
    expect(CONTENT_SECURITY_POLICY).not.toMatch(/script-src[^;]*unsafe/);
    expect(CONTENT_SECURITY_POLICY).toContain("frame-ancestors 'none'");
  });
});
