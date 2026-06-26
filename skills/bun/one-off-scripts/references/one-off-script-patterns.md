# One-Off Script Patterns

Use these patterns as starting points, then adapt them to the project's existing
scripts. Prefer local conventions over these snippets when they conflict.

## Canonical Shape

```ts
const start = performance.now()

import { PrismaClient } from '@prisma/client'

let prisma: PrismaClient

// bun --env-file=./.env ./scripts/example-task.ts
// bun --env-file=./.env.production ./scripts/example-task.ts
async function main() {
  if (!process.env.DATABASE_URL) {
    throw new Error('Missing envs (DATABASE_URL).')
  }

  prisma = new PrismaClient({
    datasources: {
      db: {
        url: process.env.DATABASE_URL as string
      }
    }
  })

  console.log('Fetching records...')
  const records = await prisma.users.findMany({
    select: { id: true, email: true }
  })

  console.log(`Found ${records.length} records.`)
}

await main()
  .catch(err => {
    console.error(err)
    process.exitCode = 1
  })
  .finally(async () => {
    await prisma?.$disconnect()

    const end = performance.now()
    const duration = (end - start) / 1_000
    console.log(`Program executed for ${duration.toFixed(2)} seconds.`)
  })

export {}
```

## CSV Output

Use a tiny local escaper when the project does not already have a CSV helper.
Always quote string fields; it prevents commas, quotes, and newlines from
breaking the file.

```ts
function csvField(value: string | number | null | undefined): string {
  const str = value == null ? '' : String(value)
  return `"${str.replace(/"/g, '""')}"`
}

const header = ['email', 'userId', 'status'].map(csvField).join(',')
const rows = results.map(result =>
  [csvField(result.email), csvField(result.userId), csvField(result.status)].join(',')
)

const csv = [header, ...rows].join('\n') + '\n'
const filename = `example-report-${Date.now()}.csv`
await Bun.write(filename, csv)
console.log(`Created CSV ${filename} with ${rows.length} rows.`)
```

## Batched API Reads

When calling external APIs, batch and delay by default. Prefer a project-level
retry helper if one exists.

```ts
const BATCH_SIZE = 10
const BATCH_DELAY_MS = 250

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

const results: ResultRow[] = []
for (let i = 0; i < inputs.length; i += BATCH_SIZE) {
  const batch = inputs.slice(i, i + BATCH_SIZE)
  const batchResults = await Promise.all(
    batch.map(async input => {
      try {
        return await fetchOne(input)
      } catch (err) {
        return { input, error: (err as Error).message.slice(0, 200) }
      }
    })
  )

  results.push(...batchResults)

  const processed = Math.min(i + BATCH_SIZE, inputs.length)
  console.log(`  ${processed}/${inputs.length} processed`)

  if (i + BATCH_SIZE < inputs.length) {
    await sleep(BATCH_DELAY_MS)
  }
}
```

## Large Job Performance Patterns

Use these only when the job is large enough to need them. For a tiny script, the
simple loop is clearer and safer.

### Bounded Concurrency

Avoid `Promise.all(inputs.map(...))` for hundreds or thousands of records. It can
overrun API limits, database pools, or memory. If the project already uses a
concurrency helper, match it. Otherwise use explicit batches.

```ts
import { PromisePool } from '@supercharge/promise-pool'
import { cpus } from 'os'

const CONCURRENCY = Math.min(50, Number(process.env.CONCURRENCY) || cpus().length * 4)

const { results, errors } = await PromisePool.withConcurrency(CONCURRENCY)
  .for(inputs)
  .withTaskTimeout(30_000)
  .process(async input => {
    return processOne(input)
  })

console.log(`Processed ${results.length} records, ${errors.length} failed.`)
```

If the dependency is not already installed, do not add it just for a one-off
without asking. Use a batch loop instead.

### In-Memory Indexes

When joining two sets already loaded in memory, build a `Map` once instead of
nesting `.find()` inside a loop.

```ts
const profileByUserId = new Map(profiles.map(profile => [profile.userId, profile]))

const rows = users.map(user => {
  const profile = profileByUserId.get(user.id)
  return {
    userId: user.id,
    email: user.email,
    externalId: profile?.externalId ?? null
  }
})
```

This changes repeated linear scans into constant-time lookups. It also makes
missing relationships explicit.

### Paginated API Loops

For APIs that return a cursor or page token, loop until the token is empty. Log
page progress and keep per-page writes small.

```ts
async function fetchPage(pageToken?: string | null) {
  const params = new URLSearchParams()
  params.append('page_size', PAGE_SIZE.toString())
  if (pageToken) params.append('page_token', pageToken)

  const response = await fetch(`${BASE_URL}/resources?${params}`, {
    headers: { authorization: `Bearer ${process.env.API_TOKEN}` }
  })

  if (!response.ok) {
    throw new Error(`API ${response.status}: ${await response.text()}`)
  }

  return response.json() as Promise<{ data: RawRecord[]; next_page_token?: string | null }>
}

let pageToken: string | null = null
let page = 0
let total = 0

do {
  const { data, next_page_token } = await fetchPage(pageToken)
  page += 1
  total += data.length

  console.log(`Fetched page ${page}: ${data.length} records`)
  await storeRecords(data)

  pageToken = next_page_token || null
} while (pageToken)

console.log(`Fetched ${total} records across ${page} pages.`)
```

### Date Window Chunking

For historical backfills, split a large date range into smaller windows. This
keeps API responses bounded and makes failures easier to rerun.

```ts
type DateWindow = { after: Date; before: Date }

function buildDateWindows(after: Date, before: Date, chunkDays: number): DateWindow[] {
  const windows: DateWindow[] = []
  let cursor = new Date(after)

  while (cursor <= before) {
    const end = new Date(cursor)
    end.setDate(end.getDate() + chunkDays - 1)

    windows.push({
      after: new Date(cursor),
      before: end > before ? new Date(before) : end
    })

    cursor = new Date(end)
    cursor.setDate(cursor.getDate() + 1)
  }

  return windows
}
```

Combine windows with bounded concurrency when the API allows parallel ranges.

### Chunked Idempotent Writes

For large inserts, write chunks and use idempotent operations where the schema
supports them. With Prisma, `createMany` plus `skipDuplicates` is usually the
right fit for append-only backfills keyed by a unique constraint.

```ts
const WRITE_BATCH_SIZE = Number(process.env.BATCH_SIZE || 500)

async function storeRecords(records: StoredRecord[]) {
  let inserted = 0

  for (let i = 0; i < records.length; i += WRITE_BATCH_SIZE) {
    const chunk = records.slice(i, i + WRITE_BATCH_SIZE)
    const result = await prisma.someTable.createMany({
      data: chunk,
      skipDuplicates: true
    })

    inserted += result.count
    console.log(
      `Stored chunk ${Math.floor(i / WRITE_BATCH_SIZE) + 1}: ${result.count}/${chunk.length} new`
    )
  }

  return inserted
}
```

Use `$transaction` when multiple writes must succeed or fail together. Avoid one
huge transaction for an entire historical backfill unless rollback of the whole
job is actually required.

### Rate Limit and Retry Handling

If an API exposes rate-limit headers, respect them. Keep rate-limit state local
and visible in logs.

```ts
function parseRateLimitHeaders(response: Response) {
  const remaining = Number(response.headers.get('x-ratelimit-remaining') || '999')
  const resetSeconds = Number(response.headers.get('x-ratelimit-reset') || '0')

  return {
    remaining,
    resetAt: resetSeconds > 0 ? new Date(resetSeconds * 1000) : null
  }
}

async function fetchWithRateLimit(url: string, options: RequestInit, maxAttempts = 5) {
  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    const response = await fetch(url, options)
    const { remaining, resetAt } = parseRateLimitHeaders(response)

    if (remaining <= 10) {
      console.warn(`Rate limit low: ${remaining} remaining`)
    }

    if (response.status !== 429) {
      return response
    }

    const retryAfter = Number(response.headers.get('retry-after') || '0')
    const resetWaitMs = resetAt ? resetAt.getTime() - Date.now() : 0
    const waitMs = Math.max(retryAfter * 1000, resetWaitMs, 1000 * attempt)

    console.warn(`429 rate limited. Waiting ${Math.ceil(waitMs / 1000)}s...`)
    await sleep(waitMs)
  }

  throw new Error(`Rate limited after ${maxAttempts} attempts`)
}
```

For database deadlocks or transient write conflicts, retry only the smallest
operation that failed, with a capped backoff. Do not retry non-idempotent
external writes unless the API provides an idempotency key.

### Env-Tunable Knobs

Expose operational knobs through env vars for long jobs:

```ts
const DRY_RUN = process.env.DRY_RUN === 'true'
const PAGE_SIZE = Number(process.env.PAGE_SIZE || 500)
const BATCH_SIZE = Number(process.env.BATCH_SIZE || 500)
const CONCURRENCY = Math.min(50, Number(process.env.CONCURRENCY || 10))

console.log(
  `dryRun=${DRY_RUN} pageSize=${PAGE_SIZE} batchSize=${BATCH_SIZE} concurrency=${CONCURRENCY}`
)
```

Make defaults conservative. A user can raise them after a staging run proves the
script behaves correctly.

## Mutation Checklist

Before writing a script that updates records, deletes data, charges accounts,
places orders, sends notifications, or calls external write endpoints, include
the relevant safeguards:

- Target filter: require a user ID, email, date range, IDs file, or explicit CLI
  option instead of broad defaults.
- Preflight count: log how many records match before any write.
- Dry run: print intended changes without executing them.
- Confirmation: for interactive scripts, ask for the exact target or operation.
- Transaction: group database writes that must succeed or fail together.
- Audit output: write a CSV or structured log of successes, skips, and failures.

## Validation

Use the project's existing Bun-compatible validation path. If the repo uses
Prettier and Bun has trouble with shell shims in `node_modules/.bin`, call the
formatter's JavaScript entrypoint directly, for example:

```bash
bun node_modules/prettier/bin/prettier.cjs --check scripts/example-task.ts
```

Only run live script commands after the user approves the target environment and
credentials.
