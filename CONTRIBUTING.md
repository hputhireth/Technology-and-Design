# How we work

One issue, one branch, one pull request. Nothing reaches `main` without the checks green and a review recorded.

## 1. Start from an issue

Every piece of work is an issue first. A program of the pipeline is an issue with the label `program`; the work under it
is a sub-issue (Create sub-issue on the program's page). Write the acceptance criteria as things that can be checked.

## 2. Branch from an up-to-date main

```
git checkout main && git pull
git checkout -b <type>/<issue number>-<short-name>     # feat/12-store-rebuild
```

Types: `feat`, `fix`, `test`, `docs`, `chore`, `ci`.

## 3. Commit in steps

One commit per step that could be reviewed on its own, with a Conventional Commit message that refers to the issue:

```
feat(store): read the 3 November exports, refs #12
```

No login, host name, project path or allocation goes into a commit. No em dashes.

## 4. Open the pull request

Fill in the template, say `Closes #<issue>` in the body, and wait for the `checks` workflow. A red check is fixed on the
branch, never worked around.

## 5. Review

Read the diff in Files changed against the acceptance criteria and the evidence (logs, test output, a screenshot of the
application). Leave the review as a comment, resolve every thread, then squash and merge. The merge closes the issue and
the board moves the card to Done. When the last open sub-issue of a program closes, the `program-progress` workflow
closes the program.

## 6. Meetings

A meeting that touched a program is one row in the Meetings table of its issue and its page under `docs/programs/`:
the date, a rating from 1 (unsatisfied) to 5 (satisfied), and what was agreed.
