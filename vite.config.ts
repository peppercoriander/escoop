import { defineConfig } from 'vite';
import { cpSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

export default defineConfig({
  // Relative output works at both a GitHub user domain and a repository subpath.
  base: './',
  plugins: [{
    name: 'catalog-static-assets',
    closeBundle() {
      mkdirSync(resolve('dist/data/normalized'), { recursive: true });
      cpSync(resolve('data/normalized/site_data.json'), resolve('dist/data/normalized/site_data.json'));
      cpSync(resolve('images'), resolve('dist/images'), { recursive: true });
    },
  }],
});
