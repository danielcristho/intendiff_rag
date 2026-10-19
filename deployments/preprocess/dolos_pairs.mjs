#!/usr/bin/env node
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import { Dolos, File } from '@dodona/dolos-lib';

async function compare(items) {
  const nonempty = items.filter(item => item.code.trim());
  if (nonempty.length < 2) return [];
  const files = nonempty.map((item, index) => new File(`${index}.js`, item.code));
  const report = await new Dolos({
    language: 'javascript', kgramLength: 70, kgramsInWindow: 17,
  }).analyze(files);
  return report.allPairs().map(pair => ({
    left: nonempty[Number.parseInt(pair.leftFile.path)].id,
    right: nonempty[Number.parseInt(pair.rightFile.path)].id,
    similarity: pair.similarity,
  }));
}

if (process.argv.includes('--selfcheck')) {
  const code = Array.from({ length: 30 }, (_, i) =>
    `function f${i}(x) { return x * ${i + 1} + Math.max(0, x); }`).join('\n');
  const pairs = await compare([{ id: 'a', code }, { id: 'b', code: code.replaceAll('(x)', '(renamed)').replaceAll('x *', 'renamed *').replaceAll(', x)', ', renamed)') }]);
  assert.equal(pairs.length, 1);
  assert.equal(pairs[0].similarity, 1);
  assert.deepEqual(await compare([{ id: 'a', code: '' }]), []);
  console.log('ok');
} else {
  const text = await fs.readFile(process.argv[2], 'utf8');
  const items = text.trim().split('\n').filter(Boolean).map(line => JSON.parse(line));
  console.log(JSON.stringify(await compare(items)));
}
