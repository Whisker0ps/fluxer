# Limits

This document summarizes known limits in Fluxer and points to their sources in code.
All from `packages/limits/src/LimitDefaults.tsx` unless noted.

Note: Some limits are enforced by shared constants, while others are enforced at the API schema/request layer. The schema layer may be stricter for specific requests.

## Guilds, Roles, Members
- Max guilds per user (defaults): 100 free / 200 premium
- Max guild members: 1,000,000 (and very large guilds: 10,000,000)
- Max guild roles: 250
- Roles per member (stored/response): max 250 role IDs
  - Source: `packages/schema/src/domains/guild/GuildMemberSchemas.tsx`
- Roles per member (update request): max 100 role IDs per update
  - Source: `packages/schema/src/domains/guild/GuildRequestSchemas.tsx`

## Channels
- Max guild channels: 500
- Max channels per category: 50

## DMs and Private Channels
- Max private channels per user: 250
- Max group DMs per user: 150
- Max DM recipients: 10
- Max group DM recipients: 25

## Related Defaults
- Default free/premium limit values (feature-tied limits)
