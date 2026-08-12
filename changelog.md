# Changelog 0.5.4

- Some commands need permission to be used
- Rename `revokem` to `removem`
- Shorten some commands' description

## Bug fixed:

- Permission won't override

    Hierarchy:
    - User -> Roles (Allowed) -> Roles (Denied)
- `mplay` don't respond if user outside the voice channel
- Fix queue skipper don't skip queue
- Remove queue can also remove the current audio