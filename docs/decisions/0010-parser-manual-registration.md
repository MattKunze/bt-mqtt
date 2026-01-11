# 0010. Manual Parser Registration

**Date:** 2026-01-11

**Status:** Accepted

## Context

The subscriber uses a pluggable parser architecture (see ADR-0006) where device-specific parsers implement the `DeviceParser` interface. Parsers need to be registered with the central `ParserRegistry` before use. We need to decide how parsers are discovered and registered:

- Manual registration in code
- Automatic discovery via filesystem scanning
- Dynamic loading via configuration
- Convention-based registration

Considerations:
- Type safety and compile-time checking
- Tree-shaking and dead code elimination for unused parsers
- Clarity about which parsers are active
- Debugging and testing ease
- Build/bundle complexity

## Decision

Parsers will be **manually registered** via explicit imports and registration calls in `parsers/index.ts`.

Implementation:
```typescript
// parsers/index.ts
import { goveeParser } from './govee';
import { switchbotParser } from './switchbot';
import { ibeaconParser } from './ibeacon';

export function registerParsers(registry: ParserRegistry): void {
  registry.register(goveeParser);
  registry.register(switchbotParser);
  registry.register(ibeaconParser);
  // Add new parsers here
}
```

Application initialization:
```typescript
// main.ts
import { ParserRegistry } from './parser-registry';
import { registerParsers } from './parsers';

const registry = new ParserRegistry();
registerParsers(registry);
```

Adding new parser:
1. Create `parsers/new-device.ts` implementing `DeviceParser`
2. Add import and registration call to `parsers/index.ts`
3. TypeScript compiler ensures interface compliance

## Consequences

### Positive

- **Explicit and clear**: Easy to see exactly which parsers are active
- **Type safety**: TypeScript checks parser implementations at compile time
- **Tree-shaking**: Bundlers can eliminate unused parsers from builds
- **IDE support**: Autocomplete, go-to-definition, and refactoring work perfectly
- **Simple debugging**: Clear call stack, no dynamic loading magic
- **No runtime failures**: Parser loading issues caught at compile/build time, not at runtime
- **Testable**: Easy to register specific parsers for integration tests
- **Build simplicity**: No filesystem scanning or dynamic imports
- **Single source of truth**: `parsers/index.ts` is authoritative list of parsers
- **Fast startup**: No filesystem scanning or module discovery overhead

### Negative

- **Manual step**: Developer must remember to register new parsers
- **Easy to forget**: New parser file without registration means parser is ignored
- **Not plug-and-play**: Can't drop a parser file into a directory and have it work

### Neutral

- **Registration order matters**: Parser priority determined by registration order (document this)
- **Centralized list**: All parsers listed in one file (could grow long, but manageable)

## Alternatives Considered

### Automatic filesystem discovery

Scan `parsers/` directory and load all files:
```typescript
// DON'T DO THIS
const parserFiles = fs.readdirSync('./parsers');
parserFiles.forEach(file => {
  const parser = require(`./${file}`).default;
  registry.register(parser);
});
```

- **Pros**: Truly plug-and-play, no registration needed
- **Cons**: 
  - Runtime failures if parser file has issues
  - No tree-shaking (all parser code included in bundle)
  - TypeScript can't validate before runtime
  - Harder to debug (dynamic loading)
  - Filesystem dependency (breaks in bundled/containerized environments)
  - Unclear which parsers are active without inspecting filesystem
  - Test setup complexity (mock filesystem or have all parsers)

### Convention-based auto-registration

Use naming convention: any file matching `parsers/*-parser.ts` is auto-registered via import.meta.glob or similar:
```typescript
// DON'T DO THIS
const parsers = import.meta.glob('./parsers/*-parser.ts');
```

- **Pros**: Somewhat automatic, leverages build tools
- **Cons**:
  - Build-tool specific (Vite, webpack, etc.)
  - Still unclear which parsers are active
  - Harder to control order
  - Less explicit than manual
  - Complicates testing

### Configuration-based registration

List parsers in JSON/YAML config file:
```yaml
parsers:
  - govee
  - switchbot
  - ibeacon
```

- **Pros**: Can change parsers without code changes
- **Cons**:
  - Still need to map names to implementations (manual step)
  - Doesn't solve tree-shaking
  - Config can get out of sync with code
  - No compile-time validation
  - Harder to trace which parser implementation is loaded

### Decorator-based auto-registration

Use TypeScript decorators to auto-register:
```typescript
@RegisterParser
export class GoveeParser implements DeviceParser { }
```

- **Pros**: Self-registering, clear marker
- **Cons**:
  - Decorators are experimental/legacy in TypeScript
  - Requires decorator metadata and reflection
  - Still need to import files somewhere
  - Adds complexity and build configuration
  - Harder to understand execution flow

### Module federation / plugin system

Load parsers as separate bundles at runtime:
- **Pros**: True plugins, can be developed/deployed independently
- **Cons**: Massive complexity, overkill for this use case, versioning challenges, type safety issues

## Implementation Notes

### Adding a New Parser

Developer workflow:
1. Create `parsers/my-device.ts`:
```typescript
import { DeviceParser } from '../types';

export const myDeviceParser: DeviceParser = {
  name: 'MyDevice',
  canParse: (ad) => ad.manufacturerId === 0x1234,
  parse: (ad) => { /* ... */ }
};
```

2. Register in `parsers/index.ts`:
```typescript
import { myDeviceParser } from './my-device';

export function registerParsers(registry: ParserRegistry): void {
  // ... existing registrations
  registry.register(myDeviceParser);
}
```

3. TypeScript compiler validates implementation
4. Write unit tests in `parsers/my-device.test.ts`

### Testing

Test individual parser:
```typescript
import { goveeParser } from './govee';

test('parses Govee advertisement', () => {
  const ad = { manufacturerId: 0x0001, /* ... */ };
  const result = goveeParser.parse(ad);
  expect(result.temperature).toBe(23.5);
});
```

Test with specific parsers only:
```typescript
const testRegistry = new ParserRegistry();
testRegistry.register(goveeParser);
// Test subscriber with only Govee parser
```

### Documentation

Document in `parsers/README.md`:
- How to add a new parser
- Required interface methods
- Registration process
- Testing guidelines
- Parser ordering implications

Consider adding ESLint rule or test to warn if parser file exists but isn't registered.

## Future Considerations

If parser count grows very large (50+), could:
- Group parsers into categories with sub-registries
- Generate registration code via script
- Add tooling to validate all parsers are registered

But keep manual approach until complexity justifies automation.
