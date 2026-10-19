#!/usr/bin/env node
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import { Dolos, File } from '@dodona/dolos-lib';

const options = { language: 'javascript', kgramLength: 70, kgramsInWindow: 17 };

async function fingerprints(code) {
  if (!code.trim()) return { total: 0, counts: {} };
  const report = await new Dolos(options).analyze([new File('0.js', code), new File('1.js', '')]);
  const entry = report.entries().find(entry => entry.file.path === '0.js');
  const counts = Object.fromEntries([...entry.shared].map(fp => [fp.hash, fp.occurrencesOf(entry.file).length]));
  assert.equal(Object.values(counts).reduce((sum, count) => sum + count, 0), entry.kgrams.length);
  return { total: entry.kgrams.length, counts };
}

function similarity(left, right) {
  const denominator = left.total + right.total;
  if (!denominator) return 0;
  let shared = 0;
  for (const [hash, count] of Object.entries(left.counts)) {
    if (Object.hasOwn(right.counts, hash)) shared += count + right.counts[hash];
  }
  return shared / denominator;
}

if (process.argv.includes('--selfcheck')) {
  const code = Array.from({ length: 20 }, (_, i) => `exports.f${i}=function(x){ return x*${i+1}+Math.max(x,0); };`).join('\n');
  for (const right of [code, code.replaceAll('x', 'renamed'), code.replaceAll('Math.max', 'Math.min'), 'exports.x=1;', '']) {
    const report = await new Dolos(options).analyze([new File('0.js', code), new File('1.js', right)]);
    const expected = report.allPairs()[0]?.similarity ?? 0;
    assert.equal(similarity(await fingerprints(code), await fingerprints(right)), expected);
  }
  console.log('cached fingerprint similarity equals Dolos Pair.similarity');
} else {
  const input = JSON.parse(await fs.readFile(process.argv[2], 'utf8'));
  process.stdout.write(JSON.stringify(await fingerprints(input.code)));
}
