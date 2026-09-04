// Node ESM loader for running lib/*.test.ts directly via `node --test`.
//
// Needed because two requirements conflict and neither side can move:
// TypeScript 4.9.5 (moduleResolution: "node") rejects a relative import
// with an explicit ".ts" extension, but Node's own ESM resolver refuses to
// guess an extension for an extensionless relative specifier. Source keeps
// the extensionless form tsc wants; this hook retries with ".ts" appended
// so plain `node --test` can still resolve it at runtime.
//
// Registers itself as the hooks module — pass this file to `--import`.
import { register } from 'node:module';
register(import.meta.url);

export async function resolve(specifier, context, next) {
  if (specifier.startsWith('.') && !/\.[a-zA-Z0-9]+$/.test(specifier)) {
    try {
      return await next(specifier + '.ts', context);
    } catch {
      // fall through to the normal resolution error below
    }
  }
  return next(specifier, context);
}
