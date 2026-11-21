import test from 'node:test';
import assert from 'node:assert/strict';
import { parseUpdateLog } from '../src/lib/update-log.mjs';

test('brief overrides the log heading and metadata is excluded from the rendered Markdown', () => {
  const markdown = '\n## 2026-11-22\n\n- 更新记录。\n';
  assert.deepEqual(parseUpdateLog(`---\nbrief: "20261122心兔巡演"\n---\n${markdown}`), {
    brief: '20261122心兔巡演', markdown,
  });
});

test('YAML quoting preserves colons, hash signs and escaped quotes in a brief', () => {
  for (const value of ['更新：心兔巡演', 'Update: "tour" #2']) {
    assert.equal(parseUpdateLog(`---\nbrief: ${JSON.stringify(value)}\n---\n## 日期`).brief, value);
  }
  assert.equal(parseUpdateLog("---\nbrief: 'It''s updated'\n---\n## 日期").brief, "It's updated");
});

test('Windows newlines and a UTF-8 BOM are accepted', () => {
  assert.deepEqual(parseUpdateLog('\uFEFF---\r\nbrief: 最新更新\r\n---\r\n## 日期\r\n'), {
    brief: '最新更新', markdown: '## 日期\r\n',
  });
});

test('missing, empty, non-text and malformed briefs fall back to the first entry title', () => {
  for (const metadata of ['', 'other: value\n', 'brief: "  "\n', 'brief:\n', 'brief: 123\n',
    'brief: [a, b]\n', 'brief: "unclosed\n']) {
    const result = parseUpdateLog(`---\n${metadata}---\n## 最新条目\n\n## 历史条目\n`);
    assert.equal(result.brief, '最新条目');
    assert.equal(result.markdown, '## 最新条目\n\n## 历史条目\n');
  }
});

test('existing logs without metadata retain their content and first-entry fallback', () => {
  const markdown = '## 最新条目\n\n正文\n\n---\n\n## 历史条目\n';
  assert.deepEqual(parseUpdateLog(markdown), { brief: '最新条目', markdown });
});

test('an empty log has no fabricated update brief', () => {
  assert.deepEqual(parseUpdateLog(''), { brief: undefined, markdown: '' });
});
