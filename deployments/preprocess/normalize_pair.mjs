#!/usr/bin/env node
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import UglifyJS from 'uglify-js';
import { webcrack } from 'webcrack';
import { Dolos, File } from '@dodona/dolos-lib';

export async function canonical(code) {
  const result = UglifyJS.minify(code, { compress: true, mangle: true });
  if (result.error) throw result.error;
  return (await webcrack(result.code, {
    deobfuscate: false, unpack: false, unminify: true,
    sandbox: () => { throw new Error('Sample execution is prohibited'); },
  })).code;
}

// Ignore boundary lines: parser columns vary with non-ASCII encodings.
export function exactInterior(left, right, fragments) {
  const lines = [left.split('\n'), right.split('\n')];
  const drop = [new Set(), new Set()];
  for (const fragment of fragments) {
    const selections = [fragment.leftSelection, fragment.rightSelection];
    const pieces = selections.map((s, i) => lines[i].slice(s.startRow + 1, s.endRow));
    // Full boundary lines must also agree so changed literals are never erased.
    const whole = selections.map((s, i) => lines[i].slice(s.startRow, s.endRow + 1).join('\n'));
    if (whole[0] !== whole[1] || !pieces[0].length) continue;
    selections.forEach((s, i) => {
      for (let row = s.startRow + 1; row < s.endRow; row++) drop[i].add(row);
    });
  }
  return {
    codes: lines.map((rows, i) => rows.filter((_, row) => !drop[i].has(row)).join('\n')),
    removed: drop.map(rows => rows.size),
  };
}

function matchingWindows(report, codes) {
  const entries = report.entries();
  const lines = codes.map(code => code.split('\n'));
  const fragments = [];
  for (const fingerprint of entries[0].shared) {
    if (!entries[1].shared.has(fingerprint)) continue;
    const groups = entries.map((entry, side) => {
      const windows = new Map();
      for (const occurrence of fingerprint.occurrencesOf(entry.file)) {
        const selection = occurrence.side.location;
        const key = lines[side].slice(selection.startRow, selection.endRow + 1).join('\n');
        const matches = windows.get(key) ?? [];
        matches.push(selection);
        windows.set(key, matches);
      }
      return windows;
    });
    for (const [text, left] of groups[0]) {
      const right = groups[1].get(text);
      if (!right) continue;
      // Equal windows need a covering set of matches, not the Cartesian product.
      for (const selection of left) fragments.push({ leftSelection: selection, rightSelection: right[0] });
      for (const selection of right) fragments.push({ leftSelection: left[0], rightSelection: selection });
    }
  }
  return fragments;
}

export async function transform(job) {
  let codes = [job.before, job.after];
  try {
    if (job.path.endsWith('js')) {
      codes = await Promise.all(codes.map(code => code === null ? null : canonical(code)));
    }
    if (codes.every(code => code !== null && code.trim())) {
      const language = job.path.endsWith('.ts') ? 'typescript' : 'javascript';
      const files = codes.map((code, i) => new File(`${i}.${language === 'typescript' ? 'ts' : 'js'}`, code));
      const report = await new Dolos({ language, kgramLength: 70, kgramsInWindow: 17 }).analyze(files);
      const fragments = matchingWindows(report, codes);
      if (fragments.length) {
        const stripped = exactInterior(codes[0], codes[1], fragments);
        return { path: job.path, before: stripped.codes[0], after: stripped.codes[1],
          status: 'transformed', removed_lines: stripped.removed };
      }
    }
    return { path: job.path, before: codes[0], after: codes[1], status: 'transformed', removed_lines: [0, 0] };
  } catch (error) {
    return { ...job, status: 'raw_fallback', error: String(error.message).slice(0, 300), removed_lines: [0, 0] };
  }
}

async function selfcheck() {
  // Locals are deliberately absent: Uglify's frequency-based mangling can
  // rename them differently when an unrelated call is appended.
  const shared = Array.from({ length: 30 }, (_, i) => `exports.f${i} = function() { return Math.max(${i}, ${i + 1}); };`).join('\n');
  const result = await transform({ path: 'code.js', before: shared, after: shared + '\nrequire("https").request("https://example.invalid");' });
  assert.equal(result.status, 'transformed');
  assert.ok(result.removed_lines[0] > 0);
  assert.ok(result.after.includes('example.invalid'));
  const changed = await transform({ path: 'code.js', before: shared + '\nexports.target="old";', after: shared + '\nexports.target="new";' });
  assert.ok(changed.before.includes('old') && changed.after.includes('new'));
  const invalid = await transform({ path: 'view.ejs', before: '<% invalid %>', after: '<% changed %>' });
  assert.equal(invalid.status, 'raw_fallback');
  assert.equal(invalid.before, '<% invalid %>');
  const sentinel = '/tmp/intendiff-must-not-execute';
  const inert = await transform({ path: 'payload.js', before: null,
    after: `require('fs').writeFileSync('${sentinel}', 'executed');` });
  assert.equal(inert.status, 'transformed');
  await assert.rejects(fs.stat(sentinel), { code: 'ENOENT' });
  console.log('normalization preservation selfcheck passed');
}

if (process.argv.includes('--selfcheck')) {
  await selfcheck();
} else {
  const jobs = JSON.parse(await fs.readFile(process.argv[2], 'utf8'));
  const results = [];
  for (const job of jobs) results.push(await transform(job));
  process.stdout.write(JSON.stringify(results));
}
