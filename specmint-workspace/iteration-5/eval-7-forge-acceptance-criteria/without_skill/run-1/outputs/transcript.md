# Forge Transcript: User Profile Page

## Task

Forge a spec for adding a user profile page to a Next.js app. Users should be able to edit their display name, avatar, and bio. Stack: Prisma + PostgreSQL, Tailwind CSS, Next.js App Router with server actions.

---

## Phase 1: Research Plan

Since there is no real Next.js project to inspect, here is what I would research before writing a spec:

### Codebase Research (if project existed)

1. **Existing user model** -- Read the Prisma schema (`prisma/schema.prisma`) to understand the current `User` model and what fields already exist (display name, avatar URL, bio, etc.).
2. **Auth setup** -- Identify the authentication library in use (NextAuth.js, Clerk, Lucia, custom) by searching for auth config files, session helpers, and middleware. This determines how we get the current user's ID.
3. **Existing route structure** -- Glob `app/**/page.tsx` and `app/**/layout.tsx` to understand the routing conventions, whether there are route groups (e.g., `(dashboard)`), and where a profile page would logically fit.
4. **Existing UI patterns** -- Look for form components, input components, and any form library usage (react-hook-form, Zod validation, etc.). Check if there is a shared component library or design system.
5. **File upload patterns** -- Search for any existing image/file upload handling (S3, Cloudinary, local uploads, UploadThing, etc.) since avatar upload is required.
6. **Server action patterns** -- Search for existing `"use server"` files to understand how the project structures server actions (co-located vs. separate `actions/` directory).
7. **Existing middleware** -- Check for route protection patterns (middleware.ts, auth guards).
8. **Database migration history** -- Review `prisma/migrations/` to understand the migration workflow.
9. **Testing setup** -- Check for test framework (Jest, Vitest, Playwright) and existing test patterns.

### External Research

1. **Next.js App Router server actions** -- Confirm current best practices for form handling with server actions, especially for file uploads.
2. **Prisma file/image handling** -- Whether to store avatar as a URL string (pointing to cloud storage) or as binary data (not recommended).
3. **Image upload services** -- Compare UploadThing, Cloudinary, AWS S3, Vercel Blob for avatar storage, depending on what the project already uses.
4. **Image optimization** -- Next.js `<Image>` component requirements for external image domains.
5. **Input validation** -- Zod schema patterns for profile fields (display name length, bio length, allowed image types/sizes).

---

## Phase 2: Preliminary Analysis

### Feature Scope (Initial Understanding)

The user profile page involves:

- **Read path**: A page at something like `/profile` or `/settings/profile` that displays the current user's display name, avatar, and bio.
- **Write path**: A form (or inline editing) that lets the user update these three fields via a server action.
- **Avatar upload**: File input for uploading an image, which needs storage (cloud or local), validation (file type, file size), and potentially cropping/resizing.
- **Database changes**: Possibly adding `displayName`, `avatarUrl`, and `bio` columns to the `User` table if they don't exist.
- **Auth guard**: The page must be protected -- only authenticated users can view/edit their own profile.

### Key Technical Decisions Needed

1. Where does the avatar file get stored?
2. What are the validation constraints (name length, bio length, image size)?
3. Is this a dedicated `/profile` page or part of a settings section?
4. Should there be a public-facing profile view (read-only for other users) or is this private/self-only?
5. What happens to the old avatar when a new one is uploaded?
6. Optimistic UI updates or wait for server confirmation?

---

## Phase 3: Clarifying Questions

Before writing the spec, I need answers to the following questions:

### Authentication and Authorization

1. **What auth library is the project using?** (NextAuth.js / Auth.js, Clerk, Lucia, Supabase Auth, custom?) This affects how we retrieve the current user session and protect the route.

2. **Should there be a public profile page viewable by other users**, or is the profile page strictly private (only the logged-in user sees and edits their own profile)?

### Data Model

3. **Does the `User` model in your Prisma schema already have `displayName`, `avatarUrl`, or `bio` fields?** If not, we will need a migration. If some exist, I want to know what is already there so the spec covers only the delta.

4. **Are there any constraints you want on these fields?** For example:
   - Display name: max length? Required or optional? Uniqueness?
   - Bio: max length? Markdown support or plain text?
   - Avatar: max file size? Allowed formats (JPEG, PNG, WebP)?

### File Storage

5. **How should avatar images be stored?** Options include:
   - A cloud service already in use (S3, Cloudinary, Vercel Blob, UploadThing)
   - A new service you prefer
   - If you have no preference, I will research and recommend one that fits your stack

6. **Should we support avatar cropping/resizing on upload**, or just accept the image as-is (with size/dimension validation)?

### UI and Routing

7. **Where should the profile page live in the route hierarchy?** For example:
   - `/profile`
   - `/settings/profile`
   - `/dashboard/profile`
   - Something else?

8. **What is the desired UX for editing?** Options:
   - A single form with all fields and a "Save" button
   - Inline editing (click a field to edit it)
   - A modal/drawer that opens from a settings menu

9. **Should avatar changes take effect immediately on upload**, or only when the user clicks "Save" along with the other fields?

### Scope and Priority

10. **Are there any related features you want included in this spec?** For example:
    - Email change
    - Password change
    - Account deletion
    - Profile completeness indicator
    - Or should this be strictly limited to display name, avatar, and bio?

11. **Do you have an existing design or wireframe for this page**, or should the spec include a proposed layout?

---

**[STOPPED]** -- Waiting for user answers before proceeding to write the spec. Once these questions are answered, I would proceed to write a full SPEC.md with architecture diagrams, task breakdown, testing strategy, and acceptance criteria.
