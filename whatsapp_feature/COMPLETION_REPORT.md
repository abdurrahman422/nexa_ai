# Initial Add-only Snapshot (2026-09-28)

At initial implementation, only `whatsapp_feature/` was added. The SHA-256 comparison at that time found **34,902 readable original files; 0 modified, 0 missing, 0 added outside the new folder.** Two pre-existing pytest-cache directories were inaccessible both before and after and were not covered by that hash claim.

On 2026-10-04, the user requested normal-app integration. The backend launcher, app bootstrap, PyInstaller spec, phone normalization, WhatsApp tests, Settings UI, and project documentation were intentionally updated outside this folder. The original preservation report below describes only the 2026-09-28 snapshot, not the current tree.

Implemented: robust pre-click waits, exact recipient/text validation, login retry, durable duplicate protection, conservative acknowledgement handling, failure recovery, offline tests, CLI, optional original-app runtime adapter and updated standalone documentation/status guide.

The optional new launcher binds the sender/parser/composer and permission/skill wording in memory. It does not patch existing files. Runtime state is isolated under this folder; starting the old launcher still uses the original behavior. Existing static frontend wording and packaged app remain unchanged.

Final automated run: **63 tests passed**. Original backend integration is tested with mocks; real WhatsApp login and delivery remain **unverified**. No live message has been sent. This is not a claim that all eight items have passed live acceptance.

Next step: user-approved recipient and exact test message, QR login if needed, then one supervised live send and result verification. Any selector issues found during that test should be fixed only inside this new folder.
