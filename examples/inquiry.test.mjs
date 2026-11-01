import { test } from 'node:test';
import assert from 'node:assert/strict';
import { parseInquiry } from './inquiry.mjs';
function baseline() {
  const form = new FormData();
  for (const [key, value] of Object.entries({fullName: ' Test User ', email: 'test@example.com', message: 'Test inquiry'})) form.set(key, value);
  return form;
}
test('accepts the contact fields and trims surrounding whitespace', () => {
  assert.equal(parseInquiry(baseline()).fullName, 'Test User');
});
for (const [name, change] of [
  ['missing name', f => f.delete('fullName')],
  ['blank message', f => f.set('message', '   ')],
  ['duplicate email', f => f.append('email', 'other@example.com')],
  ['unexpected property', f => f.set('role', 'admin')],
  ['oversized message', f => f.set('message', 'x'.repeat(4001))],
  ['invalid email', f => f.set('email', 'invalid')],
  ['file in text field', f => f.set('message', new Blob(['hello']))],
]) test(`rejects ${name}`, () => {
  const form = baseline(); change(form);
  assert.throws(() => parseInquiry(form));
});
