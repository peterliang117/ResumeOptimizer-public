# Workstation Migration and Sharing

GitHub should carry the reusable workflow. Personal facts, resumes, application
history, and credentials must remain outside Git.

## Choose the Transfer Type

### Share With a Friend

Share the GitHub repository only. The recipient creates their own private files
from the examples and connects their own Outlook and browser sessions.

Before sharing an existing GitHub repository publicly, inspect its full Git
history as well as the current tree. Removing a private file in a new commit
does not remove it from older commits. If private research, profile, resume,
tracker, mailbox, or credential data was ever pushed, keep the repository
private until its history is scrubbed with an approved rewrite, or create a
new sanitized public repository from the clean tree and verify it from a fresh
clone.

```powershell
git clone https://github.com/peterliang117/ResumeOptimizer.git
Set-Location ResumeOptimizer
Set-ExecutionPolicy -Scope Process Bypass -Force
.\scripts\bootstrap_workstation.ps1
```

The Windows bootstrap creates `.venv`, installs dependencies, initializes local
SQLite state, copies missing example files to ignored private paths, and
validates the clean public checkout. It never overwrites existing profile files
and never opens a browser or submits an application.

Give the recipient this Codex prompt if they want Codex to guide the setup:

```text
Set up this public ResumeOptimizer checkout for my own local workflow.
First read AGENTS.md, DATA_CONTRACT.md, docs/workstation_migration.md,
docs/local_automation.md, and automation/reconcile-job-application-emails.prompt.md.
Then run the documented Windows bootstrap command from the repository root.
Do not inspect, copy, upload, publish, email, submit, or commit any private
profile, resume, tracker, mailbox, browser, database, job-history, or credential
file. Do not ask me to paste private values into chat. After setup, report only
the validation results and the local files I need to fill on this machine.
Do not create a second scheduler if a Codex heartbeat already owns the browser
workflow. Only create or change a Codex heartbeat after I explicitly request it.
If I explicitly request recurring Codex automation in this conversation, create
exactly one heartbeat from the sanitized prompt and do not install the Windows
task alongside it. Otherwise, stop after the local setup checks.
```

The recipient must then:

1. Replace generated profile files with truthful local values.
2. Add `resumes\master.docx`.
3. Run `.\.venv\Scripts\python.exe scripts\resume_evidence.py init`.
4. Connect Outlook and Chrome in their own Codex installation.
5. Review `docs\real_application_runbook.md` before enabling automation.

The Windows task is an alternative local-maintenance runner, not the full
browser workflow. If the recipient does not use a Codex heartbeat, they can
install it after bootstrap with:

```powershell
.\scripts\install_local_automation_task.ps1 -Action Install -EveryHours 4 -RunNow
```

If they want the Codex Outlook/browser coordinator, they must explicitly ask
their own Codex to create one heartbeat using the sanitized prompt in
`automation\reconcile-job-application-emails.prompt.md`; they should not also
install the Windows task.

### Move Your Own State

Clone and bootstrap the repository on the new workstation first. On the old
workstation, export an encrypted archive:

```powershell
.\scripts\export_private_state.ps1
```

Add `-IncludePackets` only when application packets and tailored resumes must
move too. Copy the generated `.rostate` file through a private channel, then
import it on the new workstation:

```powershell
.\scripts\verify_private_state.ps1 -Archive .\backups\resume_optimizer_state_<timestamp>.rostate
.\scripts\import_private_state.ps1 -Archive D:\Transfer\resume_optimizer_state.rostate
```

The archive uses AES-256-GCM authenticated encryption with a key derived by
scrypt. Use a unique passphrase of at least 12 characters and transfer the
passphrase separately from the archive. The importer refuses to overwrite
existing private state unless `-Force` is supplied.

Export does not move, rename, or delete any source file. It verifies the
passphrase, authentication tag, manifest, and every file checksum before it
reports success. The standalone verification command performs the same check
without extracting anything.

There is intentionally no backdoor or project-held recovery key. Store the
passphrase in a password manager you control. Keep the original workstation
and at least two encrypted archive copies until the archive verifies and a test
import on the new workstation passes.

After a successful import, securely remove every transfer copy that is no
longer needed. The local archive directory is ignored by Git.

## What Moves

The encrypted archive can contain:

- private profile and search-criteria files
- master resume files
- a consistent SQLite snapshot
- optionally, application packets and tailored resumes

The archive never contains:

- browser profiles, cookies, or signed-in sessions
- Outlook OAuth tokens or connector credentials
- API keys or `.env` files
- OTP or authentication codes
- virtual environments, logs, or temporary files

Reconnect Outlook, Chrome, and Codex on the destination workstation. Recreate
the Codex heartbeat from `automation/reconcile-job-application-emails.prompt.md`;
the Windows Task Scheduler helper is separate and only runs local maintenance.

## Verification

Run these checks after setup or import:

```powershell
.\.venv\Scripts\python.exe scripts\security_check.py --fail-on-finding
.\.venv\Scripts\python.exe scripts\security_check.py --fail-on-finding --check-history
.\.venv\Scripts\python.exe scripts\doctor.py
.\.venv\Scripts\python.exe scripts\verify_tracker.py
```

Do not share an existing repository until both security scans pass and
`git status --short --ignored` shows private files as ignored. The history scan
is intentionally stricter: if it reports an old private path, use a new
sanitized repository or an explicitly approved history rewrite before sharing.
