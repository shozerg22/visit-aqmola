#!/usr/bin/env node
/* Build script for Visit Aqmola web assets.
 * - Bundles and minifies src/web/app.js via esbuild
 * - Minifies styles.css
 * - Copies and rewrites index.html to reference minified assets
 */
const fs = require('fs');
const path = require('path');
const esbuild = require('esbuild');

const SRC_DIR = path.join(__dirname, '..', 'src', 'web');
const DIST_DIR = path.join(__dirname, '..', 'dist');

if (!fs.existsSync(DIST_DIR)) fs.mkdirSync(DIST_DIR, { recursive: true });

(async () => {
  try {
    // Build JS
    await esbuild.build({
      entryPoints: [path.join(SRC_DIR, 'app.js')],
      bundle: true,
      minify: true,
      sourcemap: false,
      target: ['es2018'],
      outfile: path.join(DIST_DIR, 'app.min.js')
    });

    // Minify CSS (very naive: remove comments + whitespace sequences)
    const cssSrc = fs.readFileSync(path.join(SRC_DIR, 'styles.css'), 'utf-8');
    const cssMin = cssSrc
      .replace(/\/\*[\s\S]*?\*\//g, '')
      .replace(/\s+/g, ' ') // collapse whitespace
      .replace(/ ?([;:{},>]) ?/g, '$1');
    fs.writeFileSync(path.join(DIST_DIR, 'styles.min.css'), cssMin, 'utf-8');

    // Process index.html
    const htmlSrc = fs.readFileSync(path.join(SRC_DIR, 'index.html'), 'utf-8');
    // Replace stylesheet/script references
    let htmlOut = htmlSrc.replace('styles.css', 'styles.min.css').replace('app.js', 'app.min.js');
    // Префикс /static для единичной подачи через /ui
    htmlOut = htmlOut
      .replace('href="styles.min.css"', 'href="/static/styles.min.css"')
      .replace('src="app.min.js"', 'src="/static/app.min.js"');
    // Inject build timestamp
    const stamp = new Date().toISOString();
    htmlOut = htmlOut.replace('</head>', `  <meta name="build" content="${stamp}" />\n</head>`);
    fs.writeFileSync(path.join(DIST_DIR, 'index.html'), htmlOut, 'utf-8');

    console.log('Web build complete. Files in dist/:');
    console.log(fs.readdirSync(DIST_DIR));
  } catch (e) {
    console.error('Build failed:', e);
    process.exit(1);
  }
})();
