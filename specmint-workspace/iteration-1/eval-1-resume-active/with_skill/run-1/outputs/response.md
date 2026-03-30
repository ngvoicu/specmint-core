Resuming: User Auth System (user-auth-system)
Progress: 5/12 tasks
Phase: OAuth Integration [in-progress]
Current: [AUTH-06] Implement Google OAuth callback handler in `src/auth/oauth/google.ts`
Context: Token exchange is working (tested manually). Next step is handling
the user lookup/creation in the callback handler and connecting it to the
JWT system. The handler needs to fetch the Google userinfo profile, find or
create the user in the database, then generate access + refresh tokens.
Next file: `src/auth/oauth/google.ts`

[READY TO CONTINUE WORKING - STOPPING HERE]
