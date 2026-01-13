import { Plugin, tool } from "@opencode-ai/plugin"

// Settling window: wait this long after first activity to collect all responses
const SETTLING_WINDOW_MS = 3 * 60 * 1000  // 3 minutes

export const PRReviewToolsPlugin: Plugin = async (ctx) => {
  return {
    tool: {
      await_pr_review: tool({
        description: `Block until Gemini posts activity on the specified PR, then collect all responses within a 3-minute settling window. Returns reviews, threads, and issue comments for the agent to interpret.`,
        args: {
          pr: tool.schema.number().describe("PR number"),
          owner: tool.schema.string().optional().describe("Repository owner (auto-detect if omitted)"),
          repo: tool.schema.string().optional().describe("Repository name (auto-detect if omitted)"),
          after: tool.schema.string().describe("ISO timestamp - ignore activity before this time"),
          timeout_minutes: tool.schema.number().default(120).describe("Maximum wait time in minutes"),
          poll_interval_seconds: tool.schema.number().default(30).describe("Seconds between GitHub API polls"),
        },
        async execute(args, toolCtx) {
          const startTime = Date.now()
          const timeoutMs = args.timeout_minutes * 60 * 1000
          const intervalMs = args.poll_interval_seconds * 1000
          
          // Auto-detect owner/repo from git remote if not provided
          const ownerRepo = args.owner && args.repo 
            ? { owner: args.owner, repo: args.repo }
            : await detectOwnerRepo(ctx)
          
          const { owner, repo } = ownerRepo
          
          let settlingStartTime: number | null = null
          let collectedData: CollectedData = {
            reviews: [],
            unresolved_threads: [],
            issue_comments: [],
          }
          
          while (true) {
            // 1. Check abort signal (user cancelled or terminal closed)
            if (toolCtx.abort.aborted) {
              return JSON.stringify({
                status: "cancelled",
                summary: "Operation cancelled by user",
                elapsed_minutes: Math.round((Date.now() - startTime) / 60000),
                ...collectedData,
              })
            }
            
            // 2. Check internal timeout
            const elapsedMinutes = Math.round((Date.now() - startTime) / 60000)
            if (Date.now() - startTime > timeoutMs) {
              return JSON.stringify({
                status: "timeout",
                summary: `Timeout after ${elapsedMinutes} minutes waiting for Gemini activity`,
                elapsed_minutes: elapsedMinutes,
                ...collectedData,
              })
            }
            
            // 3. Check if settling window has expired
            if (settlingStartTime && (Date.now() - settlingStartTime > SETTLING_WINDOW_MS)) {
              // Settling window complete - return everything collected
              const hasReviews = collectedData.reviews.length > 0
              const hasThreads = collectedData.unresolved_threads.length > 0
              const hasComments = collectedData.issue_comments.length > 0
              
              let summary = ""
              if (hasThreads) {
                summary = `Collected ${collectedData.unresolved_threads.length} unresolved threads`
              } else if (hasReviews) {
                summary = `Collected ${collectedData.reviews.length} review(s) with no unresolved threads`
              } else if (hasComments) {
                summary = `Collected ${collectedData.issue_comments.length} comment(s) only (no review threads)`
              }
              
              return JSON.stringify({
                status: "activity_detected",
                summary,
                elapsed_minutes: elapsedMinutes,
                ...collectedData,
              })
            }
            
            // 4. Poll GitHub for activity
            const result = await fetchGeminiActivity(ctx, owner, repo, args.pr, args.after)
            
            // 5. Check if there's new activity
            if (result.hasActivity) {
              // Start settling window if not already started
              if (!settlingStartTime) {
                settlingStartTime = Date.now()
              }
              
              // Merge new data into collected data
              collectedData = mergeCollectedData(collectedData, result)
            }
            
            // 6. Wait before next poll
            await sleep(intervalMs)
          }
        },
      }),
    },
  }
}

interface CollectedData {
  reviews: Review[]
  unresolved_threads: Thread[]
  issue_comments: IssueComment[]
}

interface Review {
  id: string
  state: string
  body: string
  submitted_at: string
}

interface Thread {
  id: string
  comment_id: number
  path: string
  line: number
  body: string
}

interface IssueComment {
  id: number
  body: string
  created_at: string
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

function mergeCollectedData(existing: CollectedData, newData: CollectedData): CollectedData {
  // Merge without duplicates based on IDs
  const existingReviewIds = new Set(existing.reviews.map(r => r.id))
  const existingThreadIds = new Set(existing.unresolved_threads.map(t => t.id))
  const existingCommentIds = new Set(existing.issue_comments.map(c => c.id))
  
  return {
    reviews: [
      ...existing.reviews,
      ...newData.reviews.filter(r => !existingReviewIds.has(r.id)),
    ],
    unresolved_threads: [
      ...existing.unresolved_threads,
      ...newData.unresolved_threads.filter(t => !existingThreadIds.has(t.id)),
    ],
    issue_comments: [
      ...existing.issue_comments,
      ...newData.issue_comments.filter(c => !existingCommentIds.has(c.id)),
    ],
  }
}

async function detectOwnerRepo(ctx: any): Promise<{ owner: string; repo: string }> {
  const result = await ctx.$`git remote get-url origin`.quiet()
  const url = result.stdout.toString().trim()
  const match = url.match(/github\.com[:/]([^/]+)\/([^/.]+)/)
  if (!match) throw new Error("Could not detect GitHub owner/repo from git remote")
  return { owner: match[1], repo: match[2] }
}

async function fetchGeminiActivity(
  ctx: any, 
  owner: string, 
  repo: string, 
  pr: number, 
  after: string
): Promise<{ hasActivity: boolean } & CollectedData> {
  // GraphQL query for reviews and review threads
  const graphqlQuery = `
    query($owner: String!, $repo: String!, $pr: Int!) {
      repository(owner: $owner, name: $repo) {
        pullRequest(number: $pr) {
          reviews(first: 100) {
            nodes {
              id
              author { login }
              state
              body
              submittedAt
            }
          }
          reviewThreads(first: 100) {
            nodes {
              id
              isResolved
              comments(first: 1) {
                nodes {
                  author { login }
                  body
                  databaseId
                  path
                  line
                }
              }
            }
          }
        }
      }
    }
  `
  
  // Fetch reviews and threads via GraphQL
  const graphqlResult = await ctx.$`gh api graphql -f query=${graphqlQuery} -f owner=${owner} -f repo=${repo} -F pr=${pr}`.quiet()
  const graphqlData = JSON.parse(graphqlResult.stdout.toString())
  const prData = graphqlData.data.repository.pullRequest
  
  // Fetch issue comments via REST (not available in same GraphQL query easily)
  const commentsResult = await ctx.$`gh api repos/${owner}/${repo}/issues/${pr}/comments`.quiet()
  const allComments = JSON.parse(commentsResult.stdout.toString())
  
  const afterDate = new Date(after)
  
  // Filter for Gemini reviews after timestamp
  // Note: GraphQL returns 'gemini-code-assist', REST returns 'gemini-code-assist[bot]'
  const geminiReviews = prData.reviews.nodes
    .filter((r: any) => 
      r.author?.login?.startsWith('gemini-code-assist') &&
      new Date(r.submittedAt) > afterDate
    )
    .map((r: any) => ({
      id: r.id,
      state: r.state.toLowerCase(),
      body: r.body,
      submitted_at: r.submittedAt,
    }))
  
  // Get unresolved threads from Gemini
  // Note: GraphQL returns 'gemini-code-assist', REST returns 'gemini-code-assist[bot]'
  const unresolvedThreads = prData.reviewThreads.nodes
    .filter((t: any) => 
      !t.isResolved && 
      t.comments.nodes[0]?.author?.login?.startsWith('gemini-code-assist')
    )
    .map((t: any) => ({
      id: t.id,
      comment_id: t.comments.nodes[0]?.databaseId,
      path: t.comments.nodes[0]?.path,
      line: t.comments.nodes[0]?.line,
      body: t.comments.nodes[0]?.body,
    }))
  
  // Filter for Gemini issue comments after timestamp
  // Note: REST API returns 'gemini-code-assist[bot]' with the suffix
  const geminiComments = allComments
    .filter((c: any) => 
      c.user?.login?.startsWith('gemini-code-assist') &&
      new Date(c.created_at) > afterDate
    )
    .map((c: any) => ({
      id: c.id,
      body: c.body,
      created_at: c.created_at,
    }))
  
  const hasActivity = geminiReviews.length > 0 || 
                      unresolvedThreads.length > 0 || 
                      geminiComments.length > 0
  
  return {
    hasActivity,
    reviews: geminiReviews,
    unresolved_threads: unresolvedThreads,
    issue_comments: geminiComments,
  }
}
