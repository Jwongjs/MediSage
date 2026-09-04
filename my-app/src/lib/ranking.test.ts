// my-app/src/lib/ranking.test.ts
import test from 'node:test';
import assert from 'node:assert/strict';
import { rank } from './ranking';

test('more strong support ranks higher', () => {
  const matrix = { A: { k1: 'strong', k2: 'strong' }, B: { k1: 'strong' } };
  const statuses = { k1: 'supported', k2: 'supported' } as const;
  const groups = rank(matrix as any, statuses as any);
  assert.deepEqual(groups[0], ['A']);
  assert.deepEqual(groups[1], ['B']);
});

test('strong contradiction dominates strong support', () => {
  const matrix = {
    A: { k1: 'strong', k2: 'strong', k3: 'strong' },
    B: { k1: 'strong' },
  };
  const statuses = { k1: 'supported', k2: 'supported', k3: 'contradicted' } as const;
  const groups = rank(matrix as any, statuses as any);
  assert.deepEqual(groups[0], ['B']);
  assert.deepEqual(groups[1], ['A']);
});

test('identical evidence produces one tie group', () => {
  const matrix = { A: { k1: 'strong' }, B: { k1: 'strong' } };
  const statuses = { k1: 'supported' } as const;
  assert.deepEqual(rank(matrix as any, statuses as any), [['A', 'B']]);
});

test('a diagnosis with no criteria is neutral, not last', () => {
  const matrix = { A: { k1: 'strong' }, Empty: {} };
  assert.deepEqual(
    rank(matrix as any, { k1: 'supported' } as any),
    [['A'], ['Empty']],
  );
  assert.deepEqual(
    rank(matrix as any, { k1: 'not_mentioned' } as any),
    [['Empty'], ['A']],
  );
});

test('an unjudged key is treated as not_mentioned', () => {
  const matrix = { A: { k1: 'strong' } };
  assert.deepEqual(rank(matrix as any, {} as any), [['A']]);
});
