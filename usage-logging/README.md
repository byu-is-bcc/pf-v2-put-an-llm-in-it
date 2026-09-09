# Usage logging

Three copies of the same twelve-line idea: append one timestamped line to a file every time you use the tool. Pick the one that matches your language, copy it into your project, delete the other two.

| File | Wire it in with |
|---|---|
| `usage_log.py` | `from usage_log import log_use` then `log_use("run", "3 files")` |
| `usage-log.js` | `const { logUse } = require("./usage-log")` then `logUse("run", "3 files")` |
| `usage-log.sh` | `. ./usage-log.sh` then `log_use "run" "3 files"` |

Full wiring instructions are in the comment at the top of each file, including the ES module version for JavaScript and the two-line inline version for shell.

**This is plumbing, not the assignment.** These are finished on purpose. Copy them and move on to the part that is actually yours.

---

## Do this on day one

The log is the primary evidence for this entire project, and it is the only piece you cannot reconstruct later. Wire it in before you write the second feature.

```bash
export USAGE_LOG="$HOME/code/mytool/usage.log"   # absolute path, in your shell profile
```

Set the absolute path even if it feels like overkill. The default is relative, so a CLI tool run from three different directories writes three different logs, and you will find that out on day thirty when you go to count.

---

## The format

```
2026-03-09T22:14:03Z	run	3 files
2026-03-10T08:02:41Z	run	17 files
2026-03-10T08:31:55Z	run	--dry-run
```

Tab separated, one line per use, UTC. All three snippets produce exactly this, so the counting commands below work regardless of which one you copied.

UTC because it is identical across the three languages and sorts lexicographically. Each file has a comment showing the one-line change if you would rather log local time.

```bash
wc -l < usage.log                                  # <N> in your claim
head -1 usage.log && tail -1 usage.log             # first and last use, which gives you <M>
cut -f1 usage.log | cut -dT -f1 | sort -u | wc -l  # how many distinct days you actually used it
awk -F'\t' '{print $2}' usage.log | sort | uniq -c # uses broken down by event
```

That third one is the number that matters most, and it is the one that will surprise you. It is also the number a reviewer can compute from your committed log in four seconds, so know it before they do.

---

## What not to log

The log goes in a public repository. Everything in it is public forever, and `git rm` does not undo that.

**Never:** passwords, tokens, API keys, session cookies, connection strings, email addresses, phone numbers, anyone else's name, the contents of the files you processed, or the text of anything you typed.

**Be careful with absolute paths.** `/Users/jsmith/Desktop/2025-tax-return.pdf` leaks your name, your directory layout, and your tax situation. If you need to know which folder a run touched, log the basename or a count instead.

**Safe, and enough:** timestamps, event names, counts, durations, exit codes, flags used, error types without their messages.

The test: read the line you are about to write and ask whether you would be fine with it appearing in a screenshot in a job interview. That is not a hypothetical. This log is going in your portfolio.

---

## Committing the log

Commit it. It is the evidence, and a log nobody can see proves nothing.

If your detail field ended up with local paths in it despite the advice above, do not commit the file and do not rewrite it into something cleaner either, because a hand-edited log is not evidence. Instead: uncomment `usage.log` in `.gitignore`, fix the logging call so future lines are safe, and put a screenshot of the raw log in the repository with the paths blacked out. Say in your README that you did that and why. An honest redaction reads better than a suspiciously tidy file.

---

## Other shapes of tool

**Browser extension.** No filesystem. Use `chrome.storage.local`, keep the same one-line-per-use shape, and export it to a file when you need the count.

**Mobile app.** Append to a file in the app's documents directory, or log to whatever analytics tier is free. Screenshot the count.

**A tool you did not write the entry point for,** like a git hook or a cron job: wrap it in a two-line shell script that calls `log_use` and then the real thing. The inline version in `usage-log.sh` exists for exactly this.

**Something with no code you control at all.** Then your evidence is shell history, commit dates, and screenshots. That is allowed. The verification list says "logs, commit dates, a screenshot of your shell history, anything real."
