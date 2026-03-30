# Commenting System Specification

## Overview

Add a commenting system to the existing Next.js 14 blog/content platform. Users can leave rich-text comments on posts, reply to comments (up to 3 levels deep), receive real-time updates via Pusher, and track read/unread state per comment.

### Goals

- Rich text comments using Tiptap editor
- Nested replies up to 3 levels; replies beyond level 3 are flattened to level 3
- Real-time comment delivery via Pusher (serverless-compatible on Vercel)
- Per-user per-comment read/unread tracking
- Basic moderation: report button, soft delete by author or admin
- Data model designed to support @mentions in a future v2

### Non-Goals (v1)

- @mentions and notifications
- Collaborative/simultaneous editing of a single comment
- ML-based moderation or spam filtering
- Comment reactions/emoji

## Tech Stack

| Concern         | Choice              | Notes                              |
|-----------------|---------------------|------------------------------------|
| Rich text editor| Tiptap              | 45kB bundle, Yjs collab built-in   |
| Real-time       | Pusher              | Existing account, serverless-ready |
| ORM             | Prisma 5.8.1        | Already in project                 |
| Database        | PostgreSQL 15       | Already in project                 |
| Auth            | NextAuth.js v5      | Already in project                 |
| Styling         | Tailwind CSS 3.4.1  | Already in project                 |

## Data Model

### Prisma Schema Additions

```prisma
model Comment {
  id        String   @id @default(cuid())
  body      Json     // Tiptap JSON document
  bodyHtml  String   // Pre-rendered HTML for fast display
  postId    String
  authorId  String
  parentId  String?  // null for top-level comments
  depth     Int      @default(0) // 0, 1, or 2 (max 3 levels: 0-indexed)
  deleted   Boolean  @default(false) // soft delete
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  post     Post      @relation(fields: [postId], references: [id], onDelete: Cascade)
  author   User      @relation(fields: [authorId], references: [id], onDelete: Cascade)
  parent   Comment?  @relation("CommentReplies", fields: [parentId], references: [id], onDelete: Cascade)
  replies  Comment[] @relation("CommentReplies")
  reads    CommentRead[]
  reports  CommentReport[]

  @@index([postId, createdAt])
  @@index([parentId])
}

model CommentRead {
  id        String   @id @default(cuid())
  userId    String
  commentId String
  readAt    DateTime @default(now())

  user    User    @relation(fields: [userId], references: [id], onDelete: Cascade)
  comment Comment @relation(fields: [commentId], references: [id], onDelete: Cascade)

  @@unique([userId, commentId])
  @@index([userId])
}

model CommentReport {
  id        String   @id @default(cuid())
  userId    String
  commentId String
  reason    String?  // optional description
  createdAt DateTime @default(now())

  user    User    @relation(fields: [userId], references: [id], onDelete: Cascade)
  comment Comment @relation(fields: [commentId], references: [id], onDelete: Cascade)

  @@unique([userId, commentId]) // one report per user per comment
}
```

### Key Data Model Decisions

- **`body` as `Json`**: Store the Tiptap document as JSON for future re-rendering and migration. `bodyHtml` is a pre-rendered cache for display performance.
- **`depth` field**: Enforced at the application layer. If `parent.depth >= 2`, the new reply is attached at depth 2 (flattened).
- **Soft delete**: `deleted` flag preserves the comment row so replies remain intact. The UI shows "This comment was deleted" in place of the body.
- **`@@unique([userId, commentId])` on reads**: Prevents duplicate read records; upsert pattern for marking as read.

## API Design

### Server Actions (`src/lib/actions/comments.ts`)

Server actions are preferred over API routes for mutations (Next.js 14 pattern).

| Action | Input | Behavior |
|--------|-------|----------|
| `createComment` | `{ postId, parentId?, body }` | Validate auth, enforce depth limit, save comment, trigger Pusher event |
| `updateComment` | `{ commentId, body }` | Validate ownership, update body + bodyHtml, trigger Pusher event |
| `deleteComment` | `{ commentId }` | Validate ownership or admin role, soft delete, trigger Pusher event |
| `reportComment` | `{ commentId, reason? }` | Validate auth, create report (idempotent via unique constraint) |
| `markCommentsRead` | `{ commentIds[] }` | Bulk upsert CommentRead records for current user |

### API Routes (read-only, for real-time hydration)

| Route | Method | Response |
|-------|--------|----------|
| `GET /api/posts/[postId]/comments` | GET | Paginated top-level comments with nested replies (eager-loaded to depth 2) |
| `GET /api/comments/[commentId]/replies` | GET | Paginated replies for a specific comment (for lazy-loading deep threads) |
| `GET /api/posts/[postId]/comments/unread-count` | GET | Count of unread comments for current user on a post |

### Pagination Strategy

- Cursor-based pagination using `createdAt` + `id` as cursor
- Default page size: 20 top-level comments
- Replies loaded eagerly up to depth 2 (all nested in single query)

## Component Architecture

```
src/components/comments/
  CommentSection.tsx       — Container: fetches comments, manages real-time subscription
  CommentList.tsx          — Renders list of top-level comments
  CommentThread.tsx        — Single comment + its nested replies (recursive, max depth 2)
  CommentItem.tsx          — Individual comment display (avatar, author, timestamp, body, actions)
  CommentEditor.tsx        — Tiptap editor wrapper for creating/editing comments
  CommentActions.tsx       — Reply, Edit, Delete, Report buttons
  UnreadBadge.tsx          — Unread count indicator
```

### Component Details

**CommentSection.tsx** (Client Component)
- Fetches initial comments via server component data or client-side fetch
- Subscribes to Pusher channel `post-{postId}` on mount
- Handles `new-comment`, `update-comment`, `delete-comment` events
- Passes comment tree + callbacks down to children

**CommentEditor.tsx** (Client Component)
- Wraps Tiptap with extensions: StarterKit, Placeholder, Link
- Toolbar: bold, italic, code, link, ordered list, unordered list
- Submit triggers `createComment` or `updateComment` server action
- Cancel button clears editor and collapses reply form

**CommentItem.tsx** (Client Component)
- Renders `bodyHtml` via `dangerouslySetInnerHTML` (HTML is server-generated from trusted Tiptap JSON, not user-supplied raw HTML)
- Shows "This comment was deleted" placeholder for soft-deleted comments
- Intersection Observer triggers `markCommentsRead` when comment scrolls into view

## Real-Time Architecture

### Pusher Channels

| Channel | Event | Payload | Trigger |
|---------|-------|---------|---------|
| `post-{postId}` | `new-comment` | Full comment object | After `createComment` succeeds |
| `post-{postId}` | `update-comment` | Updated comment object | After `updateComment` succeeds |
| `post-{postId}` | `delete-comment` | `{ commentId }` | After `deleteComment` succeeds |

### Client-Side Handling

- On `new-comment`: Insert into comment tree at correct position based on `parentId`
- On `update-comment`: Replace comment in tree by `id`
- On `delete-comment`: Set `deleted: true` on local comment, re-render as deleted placeholder
- Deduplicate: If the current user authored the action, ignore the Pusher event (optimistic update already applied)

### Server-Side Trigger

```typescript
// src/lib/pusher.ts
import PusherServer from "pusher";

export const pusher = new PusherServer({
  appId: process.env.PUSHER_APP_ID!,
  key: process.env.NEXT_PUBLIC_PUSHER_KEY!,
  secret: process.env.PUSHER_SECRET!,
  cluster: process.env.NEXT_PUBLIC_PUSHER_CLUSTER!,
  useTLS: true,
});
```

Triggered after each successful mutation in server actions.

## Mark-as-Read Tracking

### Strategy

- Use Intersection Observer on each `CommentItem`
- When a comment enters the viewport for > 500ms, add its ID to a batch queue
- Flush the batch every 2 seconds (or on page visibility change) via `markCommentsRead` server action
- On initial load, fetch read status alongside comments and visually distinguish unread comments (e.g., left border accent)

### Unread Count

- `UnreadBadge` component fetches count from `/api/posts/[postId]/comments/unread-count`
- Updated optimistically when `markCommentsRead` fires
- Refreshed on Pusher `new-comment` event (increment by 1 for comments not authored by current user)

## Moderation

### Report Flow

1. User clicks "Report" on a comment
2. Optional reason modal appears
3. `reportComment` server action creates a `CommentReport` record
4. UI shows "Reported" state (disabled button) -- idempotent via unique constraint
5. Admin dashboard (out of scope for v1, but reports are queryable)

### Soft Delete

- Author can delete their own comments
- Admin role users can delete any comment
- `deleteComment` sets `deleted: true`, does not remove the row
- UI renders deleted comments as "This comment was deleted" with no body, preserving reply tree structure

## Security Considerations

- All mutations require authenticated session (NextAuth.js v5)
- Ownership checks on update/delete (or admin role for delete)
- Tiptap JSON is server-validated before saving; `bodyHtml` is rendered server-side from the JSON, never from raw user HTML
- Rate limiting on comment creation: 5 comments per minute per user (middleware or server action check)
- XSS: `bodyHtml` is generated server-side from Tiptap's structured JSON output, which only allows whitelisted node types
- CSRF: Server actions use Next.js built-in CSRF protection

## Implementation Plan

### Phase 1: Data Model and Basic CRUD
- Add Prisma models (Comment, CommentRead, CommentReport)
- Run migration
- Create server actions: `createComment`, `updateComment`, `deleteComment`
- Create API route: `GET /api/posts/[postId]/comments`
- Unit tests for server actions

### Phase 2: UI Components
- Build `CommentEditor` with Tiptap
- Build `CommentItem`, `CommentThread`, `CommentList`, `CommentSection`
- Wire up to server actions
- Handle nesting depth enforcement in UI (hide reply button at depth 2, or flatten)
- Integration tests for comment CRUD flow

### Phase 3: Real-Time
- Set up Pusher server and client libraries
- Add Pusher triggers to server actions
- Subscribe to channel in `CommentSection`
- Handle optimistic updates and deduplication
- Test real-time delivery across browser tabs

### Phase 4: Read Tracking and Moderation
- Implement Intersection Observer batching for mark-as-read
- Build `UnreadBadge` component
- Add unread visual styling
- Implement report flow (`reportComment` action + UI)
- Implement soft delete UI
- End-to-end tests for read tracking and moderation

## File Inventory

New files to create:

| File | Purpose |
|------|---------|
| `prisma/migrations/XXX_add_comments/migration.sql` | Generated migration |
| `src/lib/actions/comments.ts` | Server actions for comment CRUD |
| `src/lib/pusher.ts` | Pusher server instance |
| `src/lib/pusher-client.ts` | Pusher client instance |
| `src/components/comments/CommentSection.tsx` | Container component |
| `src/components/comments/CommentList.tsx` | Top-level comment list |
| `src/components/comments/CommentThread.tsx` | Recursive thread rendering |
| `src/components/comments/CommentItem.tsx` | Single comment display |
| `src/components/comments/CommentEditor.tsx` | Tiptap editor wrapper |
| `src/components/comments/CommentActions.tsx` | Action buttons |
| `src/components/comments/UnreadBadge.tsx` | Unread count badge |
| `src/app/api/posts/[postId]/comments/route.ts` | GET comments endpoint |
| `src/app/api/comments/[commentId]/replies/route.ts` | GET replies endpoint |
| `src/app/api/posts/[postId]/comments/unread-count/route.ts` | GET unread count |

Files to modify:

| File | Change |
|------|--------|
| `prisma/schema.prisma` | Add Comment, CommentRead, CommentReport models + relations on User/Post |
| `src/components/PostCard.tsx` | Add comment count display and link to comments |
| `package.json` | Add `@tiptap/*` and `pusher` / `pusher-js` dependencies |

## v2 Considerations

- **@mentions**: `body` JSON already supports inline nodes; add a `Mention` Tiptap extension and a `CommentMention` join table for notifications
- **Collaborative editing**: Tiptap has built-in Yjs support; evaluate whether collaborative comment editing is desired
- **Email notifications**: Hook into `createComment` to queue notification emails for post authors and thread participants
- **Admin moderation dashboard**: Query `CommentReport` records, bulk actions
- **Spam filtering**: Integrate with Akismet or similar service
