#!/usr/bin/env node
// Mechanical AI-pattern scan using the vendored avoid-ai-writing detector (local only).
// Usage: node scripts/detect_ai_writing.js applications/<slug>/cover-letter.md
// This is the quick scan. The skill's full detect-mode read (references/patterns.md) is still the review step.
const fs = require('fs');
const path = require('path');
const det = require(path.join(__dirname, '..', '.claude', 'skills', 'avoid-ai-writing', 'detector', 'patterns.js'));
const file = process.argv[2];
if (!file) { console.error('usage: detect_ai_writing.js <file>'); process.exit(2); }
const r = det.analyzeText(fs.readFileSync(file, 'utf8'));
console.log(`${file}: ${r.label} (score ${r.score}, ${r.stats.wordCount} words, ${r.issues.length} issue(s))`);
for (const i of r.issues) console.log('-', JSON.stringify(i).slice(0, 240));
process.exit(r.issues.length ? 1 : 0);
