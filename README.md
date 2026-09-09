# V2 — The Thing You Actually Use

**Portfolio Factory · Development · Practitioner tier · 20 to 25 hours plus 30 days of use · Extends IS 401 or IS 403, or standalone**

> **Prerequisite: [Project 000](https://github.com/byu-is-bcc/pf-000-portfolio-site).** Build your site first. This project ships with an entry on it.

**There is no application in this template, and that is deliberate.** Every other starter in this program hands you a working reference implementation to rewrite. This one cannot, because the tool you build has to be one you personally want, and nobody can pick that for you.

What ships here is the evidence apparatus: a changelog, issue templates, usage logging in three languages, a commit-distribution helper, and a 30-day record in `EVIDENCE.md`. The deliverable of this project is proof of sustained use. The code is just what generates it.

---

## Replace everything above this line with your own README

The shape below is what a finished version looks like. Fill in the angle brackets, delete the italic notes, keep the headings.

---

## What this is

`<One sentence. What the tool does and what problem of yours it solves.>`

*Not "a productivity tool built with Python." Something closer to "renames the screenshots on my desktop into dated, searchable filenames, because I take about forty a week and could never find any of them."*

## Who this is for

`<Who should use this.>`

*This is the section the rest of your portfolio does not have, and the reason it is here: the honest answer is allowed to be "me."*

*"For me. I am the only user and I have no plans to add a second one" is a complete and respectable answer. It is more respectable than inventing a target market for a script that renames your screenshots. If other people do use it, say how many and who they are. If it is one roommate, say one roommate.*

*State the limits here too. What it does not handle, what it assumes about your machine, what would break on someone else's setup. A tool that only works on your laptop is fine. A tool that only works on your laptop and does not say so is not.*

## The claim

> Used `<N>` times over `<M>` days. `<K>` issues filed and closed. Current version `<X>`, changelog in the repository.

*Every number in that sentence is checkable by a stranger in under a minute, which is the entire point. `<N>` comes from your usage log, `<M>` from its first and last dates, `<K>` from your closed issues, `<X>` from `CHANGELOG.md`. Do not round any of them up.*

*One number belongs in the first line of this README and on your Project 000 site: how many times you used it. Not the feature count.*

## How to verify this

Same list an alumni reviewer will use.

- [ ] Usage evidence over 30 days: logs, commit dates, a screenshot of your shell history, anything real
- [ ] A `CHANGELOG.md` with dated entries that reference actual changes
- [ ] At least 5 issues filed and closed in the repository, describing problems you hit while using it
- [ ] At least 15 commits spread across the period, not clustered in one weekend
- [ ] Tests on whatever broke twice, because the second break is the signal
- [ ] A README that honestly says who this is for, which may legitimately be "me"
- [ ] `EVIDENCE.md` filled in week by week, with dates that match your git history
- [ ] No secrets in git history: `git log --all --diff-filter=A --name-only | grep -i env`

**Every item on that list is a public artifact with a timestamp on it.** Issues have dates. Commits have dates. Changelog entries can be checked against the commits they claim to describe. This rubric is unusually hard to fake and unusually easy to satisfy honestly, and both of those are on purpose.

---

## Start here

Nothing to install. There is no application to run.

```bash
git clone <your-repo-url> && cd <your-repo>
./scripts/commit-distribution.sh     # one commit, from the template. Day one looks like this.
```

Then, in order:

**1. Decide what you are building** and write the one sentence at the top of this README. Before any code.

**2. Wire up usage logging.** Copy one snippet out of `usage-logging/` into your tool on day one. Day-one logs cannot be recreated on day thirty, and the log is the primary evidence for this entire project.

**3. Open `EVIDENCE.md` and fill in the start date.** Then use it.

---

## Your job

**1. Pick something you would use even if nobody were grading it.** This is the whole constraint, and it is the one people fail. A habit tracker you do not open is worth nothing here. A script that renames your screenshots, which you run forty times a week, is worth a great deal.

The test: if the course ended tomorrow, would you keep running it? If the honest answer is no, pick something else. You will find out on day nine either way, and day one is the cheaper time to find out.

**2. Scope it small enough that you will actually use it.** Small enough to finish version 0.1 in the first three or four days, because the thirty days of use start after that. The evidence is the usage, not the feature list.

**3. Use it every day.** Actually use it. The log will tell the truth about this.

**4. File issues against yourself.** When it annoys you, open an issue right then, from the "Something annoyed me while using it" template. Not at the end of the week and not from memory. The friction you notice at 11pm on a Tuesday is the specific thing a hiring manager wants to see you write down, and it is gone by Thursday.

Then close them, referencing the commit that fixed each one. Five filed and closed is the floor.

**5. Keep `CHANGELOG.md` dated.** Entries that name the behavior that changed. "Various fixes" is not an entry.

**6. Write tests on whatever broke twice.** Not on everything. The second break is the signal that a case is genuinely hard and you will keep getting it wrong from memory. One test on the thing that bit you twice reads better than forty on things that never broke, and it is the honest reason to write a test.

**7. Add it to your Project 000 site** with the claim from above.

---

## What is here

```
CHANGELOG.md                    Keep a Changelog format, with example entries to delete
EVIDENCE.md                     your 30-day record. Fill in weekly, not at the end.
.github/ISSUE_TEMPLATE/
  annoyed-me.yml                the one that matters. Self-filed friction reports.
  bug-report.yml                for things that are actually broken
  config.yml                    turns off blank issues, so every issue has a shape
usage-logging/
  usage_log.py                  Python. Copy in, call log_use().
  usage-log.js                  Node. Same idea.
  usage-log.sh                  Shell. Source it, or inline the two lines.
  README.md                     wiring instructions and what not to log
scripts/
  commit-distribution.sh        prints your commits per week over the last 30 days
.gitignore                      covers .env, and read the usage.log comment before you commit
```

No `src/`, no `app/`, no `index.html`. That is yours to create, in whatever language and shape fits the thing you picked.

---

## Stack

Whatever fits. This is one of the few projects in the program where a CLI tool, a browser extension, a mobile app, and a shell script all qualify equally.

Pick the one that removes the most friction between you and daily use, because daily use is the deliverable. A shell script you run from the terminal you already have open beats a mobile app you have to install on a phone you have to unlock. Familiarity is a feature here. Twenty-five hours is not enough to learn a new framework and also sustain thirty days of use, and if you spend the first two weeks on tooling you will have no usage evidence at all.

---

## Picking the thing

The good ones are almost always smaller than you expect and solve a problem you have already complained about out loud.

Shapes that have worked:

- Renames or files something you download constantly: screenshots, receipts, PDFs from Learning Suite
- Turns one format you are handed into the format you actually need
- Checks something you keep forgetting to check, and says nothing when it is fine
- Answers a question you look up more than once a week, from data only you have
- Automates the four commands you type in the same order every morning

**The disqualifier: if it is a category rather than a problem, it is wrong.** "A finance tracker" is a category. "Tells me how much of this month's food budget is left, from the CSV my bank exports" is a problem. You know which one you will still be running on day thirty.

---

## The commit distribution is part of the rubric

A repository with 15 commits across 30 days looks different from one with 15 commits on a Saturday, and only one of them is evidence of the thing this project claims. Anyone reading your repository can see which one you have in about four seconds, because GitHub graphs it on the front page.

```bash
./scripts/commit-distribution.sh          # last 30 days, commits per week, with the gaps
./scripts/commit-distribution.sh 45       # or any window you want
```

Run it weekly, not on day twenty-nine. It exists so you catch a five-day gap while there are still twenty-five days left to fix it. On day twenty-nine it only tells you what your rubric score already is.

Commit when you change something, which if you are genuinely using the tool will happen at an uneven, bursty, real-looking rate. That is fine. Uneven is not the same as clustered. What the rubric is looking for is whether the work happened over the period it claims.

---

## Core-extension path

If you took **IS 401**, your team's README probably has a "Not Complete" list. Finishing your own team's stated backlog is a legitimate and unusually honest version of this project: the problems are already documented, by you, from real use.

Two conditions, and they are not negotiable:

**Get permission from every contributor.** All of them, in writing, before you start.

**Start a fresh repository.** Author metadata survives a fork, and a repository full of your teammates' commits presented as your portfolio project is the kind of thing that ends an interview. Copy the code you have permission to copy, credit the original team in your README, and let your own commit history start on day one.

The same applies to **IS 403** group work.

---

## Resume one-liners

Written after you have your real numbers. Examples of the shape:

- Built and maintained a personal CLI tool used 213 times over 34 days, filing and closing 9 issues from problems encountered in daily use.
- Maintained a tool past its first working version for 30 days, with a dated changelog across 4 releases and regression tests added on the two failures that recurred.
- Shipped and sustained a personal utility with 22 commits distributed across a month, driven by self-reported friction rather than a feature plan.

The second one is the strongest. Almost every student portfolio contains projects that were finished and abandoned; very few contain evidence of a project that was maintained.

---

## Who hires for this

**Startups and enterprise SaaS.** Named accounts hiring BYU IS students into engineering: **Epic Systems**, **Enzy**, **nCino**, **Redo**, **Acima Credit**, **BambooHR**, **Podium**.

At a startup, the person who maintains what they ship is worth several people who ship and move on, and everyone doing the hiring has been burned by the second kind. Development is still the largest single track at roughly 25% of BYU IS placements.

Those names illustrate the kind of work, not a target list. 73% of the companies that hired BYU IS students in the last five years hired exactly one.

---

## Where people get stuck

**"I cannot think of anything."** You are looking for something impressive. Look instead for something you complained about in the last week. Check your downloads folder, your shell history, and the note on your phone where you keep the same three reminders. There is a project in one of them.

**"I stopped using it on day six."** Then it was the wrong thing and you learned that cheaply. Say so in your changelog, pick something else, and restart the thirty days. Two false starts and a real thirty days is a better project than thirty days of pretending.

**"Nothing annoys me about it."** Either you are not using it or you are not paying attention. Nobody uses their own software for a week without wanting to change something. Look at the moments you hesitated, retyped a flag, or checked the output twice because you did not trust it.

**"Can I backfill the changelog?"** You can, and it will not survive contact with a reviewer, because your changelog dates get compared to your commit dates. Fifteen entries added in one commit on day twenty-nine is a specific and legible failure. Writing the entry takes forty seconds on the day it happens.

**"My tool is too simple to have issues."** Issues here are not bug reports about a complex system. They are "the output has no newline at the end and it eats my prompt," "I always have to remember the path, it should default to the current directory," "it fails silently when the folder is empty." Those are the real ones. Write them exactly that plainly.

---

## License

MIT. The template is yours to modify. The work you do with it is yours.
