# Forge Transcript: User Profile Page

## Step 1: Setup

**Spec ID**: `user-profile-page`
**Prefix**: `PROF`

Collision check: No `.specs/` directory exists -- no collision possible.

Would initialize:
```bash
mkdir -p .specs/user-profile-page
```

Would create `.specs/registry.md` with empty table header since it does not exist yet.

---

## Step 2: Deep Research

Since there is no real Next.js project to scan, here is what the research phase would cover:

### Track A: Researcher Agent (would be spawned)

The researcher agent would be spawned with the Task tool to perform exhaustive codebase and internet research. It would:

1. **Map the project architecture**
   - Read `package.json` and `package-lock.json` / `pnpm-lock.yaml` for exact dependency versions (Next.js, Prisma, Tailwind, React)
   - Read `next.config.js` / `next.config.ts` for app configuration
   - Read `prisma/schema.prisma` for the existing data model -- specifically the User model and any existing profile fields
   - Read `tailwind.config.ts` for design tokens, custom theme, and plugin usage
   - Scan `app/` directory tree to understand the App Router layout structure, existing route groups, and middleware

2. **Read 15-30 relevant code files**
   - Existing user-related pages and components (e.g., `app/(auth)/`, `app/settings/`, `app/dashboard/`)
   - Auth configuration (NextAuth.js / Auth.js / custom auth) -- session handling, user object shape
   - Existing server actions (pattern used: file naming, error handling, revalidation)
   - Existing form components (any form library like react-hook-form, zod validation patterns)
   - File upload patterns if any exist (for avatar upload)
   - Layout files (`app/layout.tsx`, nested layouts) for navigation and shared UI
   - Existing API routes for user data
   - Middleware (`middleware.ts`) for auth protection patterns

3. **Run 3+ web searches**
   - "Next.js App Router server actions file upload best practices 2026"
   - "Prisma PostgreSQL image storage avatar upload pattern"
   - "Next.js App Router form validation server actions zod"
   - "Accessible profile edit form patterns WCAG"

4. **Compare library candidates**
   - Image upload: uploadthing vs S3 presigned URLs vs Cloudinary vs local storage
   - Image processing: sharp vs jimp vs browser-side cropping (react-avatar-editor, react-easy-crop)
   - Form validation: zod vs valibot vs yup (for server action validation)
   - Rich text for bio: plain textarea vs tiptap vs lexical (if rich bio is desired)

5. **Security and performance assessment**
   - File upload size limits and type validation
   - Image dimensions / aspect ratio enforcement
   - XSS risks in display name and bio fields
   - CSRF protection for server actions (built into Next.js)
   - Rate limiting on profile updates
   - Optimistic UI updates for better UX

Output would be saved to `.specs/user-profile-page/research-01.md`.

### Track B: Context7 and Cross-Skill Research (in parallel)

Would query Context7 for up-to-date docs on:

1. **Next.js** (`vercel/next.js`) -- App Router server actions, `useFormState`, `useFormStatus`, file uploads with server actions, `revalidatePath` / `revalidateTag`
2. **Prisma** (`prisma/prisma`) -- `@updatedAt`, file/blob handling, relation updates, `select` for partial returns
3. **Tailwind CSS** (`tailwindlabs/tailwindcss`) -- form styling, avatar components, responsive design utilities
4. **Zod** (`colinhacks/zod`) -- schema validation for server actions, file type/size validation schemas

Would also consider loading cross-skills:
- **frontend-design** -- for a professional, creative profile page UI
- **datasmith-pg** -- for any schema migration design (adding avatar_url, bio columns to User table)

---

## Step 3: Interview Round 1

### Research Summary

Based on standard Next.js App Router projects with Prisma and PostgreSQL, here is what I would expect and the assumptions I am making:

You want a user profile page where authenticated users can view and edit their display name, avatar, and bio. The app uses Next.js App Router with server actions for mutations, Prisma as the ORM with PostgreSQL, and Tailwind CSS for styling.

I am assuming the project already has authentication set up (likely NextAuth.js / Auth.js since that is the most common pattern with Next.js App Router), and that there is an existing User model in the Prisma schema with at least an `id`, `email`, and `name` field. The profile page would likely live at something like `app/profile/page.tsx` or `app/(dashboard)/profile/page.tsx` depending on the route group structure. Server actions would handle the form submission with Zod validation on both client and server.

For the avatar, there are several architectural decisions to make -- where to store the image file, how to handle upload, and whether to support cropping or resizing. The bio field could be a plain text area or support rich text, which significantly affects scope.

### Assumptions (please confirm or correct)

- **Auth**: The app already has authentication and session management. I would use the existing auth pattern to protect the profile route and identify the current user.
- **User model**: A `User` table exists in Prisma. I would add `displayName`, `avatarUrl`, and `bio` columns if they do not already exist (or use existing fields if they are already there).
- **Server actions**: I would follow the existing server action patterns in the codebase for the profile update mutation, with Zod validation.
- **Tailwind**: I would use the existing Tailwind config and design system for styling rather than introducing new UI libraries.

### Questions

1. **Avatar storage**: Where should avatar images be stored? Options include:
   - A cloud service like S3, Cloudinary, or Uploadthing (scalable, CDN-friendly)
   - Local filesystem / public directory (simpler but does not scale)
   - Database as a blob (generally not recommended)

   Do you already have a file storage solution in the project, or do you have a preference?

2. **Avatar UX**: Should users be able to crop or resize their avatar before uploading, or is a simple file picker sufficient? Also, what are the constraints -- max file size, accepted formats (JPEG, PNG, WebP), and desired display dimensions?

3. **Bio field**: Should the bio be plain text (textarea) or rich text (bold, links, etc.)? If plain text, is there a character limit you want enforced?

4. **Profile page routing and layout**: Where should the profile page live in the route structure? For example:
   - `/profile` -- standalone top-level route
   - `/settings/profile` -- nested under a settings section
   - `/dashboard/profile` -- within an existing dashboard layout

   Is the profile view-only for other users, or is it purely a self-edit page?

5. **Acceptance criteria -- what does "done" look like?** Specifically:
   - Should display name changes be reflected immediately across the app (e.g., in the navbar, comments)?
   - Are there validation rules for the display name (min/max length, allowed characters)?
   - Should there be a "save" confirmation or auto-save behavior?
   - Does the avatar need a default/fallback (e.g., initials or gravatar) when none is uploaded?
   - Are there any specific conditions that must be true for you to consider this feature complete? For example: "avatar uploads work under 5MB", "bio supports up to 500 characters", "profile updates take less than 2 seconds", etc.

6. **Public vs private**: Is the profile visible to other users (public profile page), or is it only visible to the account owner as a settings/edit page?

### Proposed Rough Approach

Based on typical Next.js App Router patterns, I would structure this as:

- **Phase 1: Database and Schema** -- Add profile fields to the Prisma User model, create and run the migration
- **Phase 2: Server Actions and Validation** -- Build the profile update server action with Zod validation, avatar upload handling
- **Phase 3: UI Components** -- Profile page with edit form, avatar upload component, bio editor, responsive layout with Tailwind
- **Phase 4: Testing and Polish** -- Unit tests for validation, integration tests for the server action, e2e test for the full edit flow, loading/error states

Does this phasing make sense, or would you structure it differently?

---

**[STOPPED -- Waiting for user responses before proceeding to Step 4 (deeper research) or Step 5 (writing the SPEC.md)]**

The interview questions above would be saved to `.specs/user-profile-page/interview-01.md` along with the user's answers once provided. No SPEC.md is written until the user answers these questions and any follow-up rounds resolve remaining ambiguity.
