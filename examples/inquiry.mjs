// Proposed application-field parser, after Next.js transport decoding.
// Limits are example policy choices, not the site's observed server rules.
export function parseInquiry(form) {
  const limits = { fullName: 120, email: 254, company: 160, industry: 160, message: 4000 };
  const values = Object.create(null);
  for (const [key, value] of form.entries()) {
    if (!Object.hasOwn(limits, key)) throw new Error('Unknown field');
    if (Object.hasOwn(values, key)) throw new Error('Duplicate field');
    if (typeof value !== 'string') throw new Error('Expected text');
    if (value.length > limits[key]) throw new Error('Field too long');
    values[key] = value.trim();
  }
  for (const key of ['fullName', 'email', 'message']) {
    if (!values[key]) throw new Error(`${key} is required`);
  }
  // Basic syntax check only. Email ownership needs a separate confirmation flow.
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(values.email)) throw new Error('Invalid email');
  return { ...values };
}
