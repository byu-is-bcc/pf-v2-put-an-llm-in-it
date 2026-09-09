# Evidence

The running record for thirty days of use. **This file is filled in weekly, not at the end.**

That is not a style preference. Every number below is checkable against something with a timestamp on it: your usage log, your commit dates, your issue dates. Filling this in as you go takes about five minutes a week. Filling it in on day twenty-nine means reconstructing four weeks of numbers that have to agree with four weeks of git history you already published, and they will not agree, and the disagreement is the first thing a reviewer notices. **The honest path is the easy path here, which is the whole design.**

Pick a fixed time. Sunday night, five minutes, one commit per week that touches only this file.

---

## The project

| | |
|---|---|
| Tool | `<one line: what it does and whose problem it solves>` |
| Started | `<YYYY-MM-DD>` |
| Day 30 lands on | `<YYYY-MM-DD>` |
| Usage log lives at | `<path, committed>` |
| Current version | `<X>` |

---

## The tally

One row per week. Fill in the row at the end of that week, and do not touch earlier rows again.

| Week | Dates | Days used | Uses logged | Commits | Issues filed | Issues closed | Version at end |
|---|---|---|---|---|---|---|---|
| 1 | | | | | | | |
| 2 | | | | | | | |
| 3 | | | | | | | |
| 4 | | | | | | | |
| Tail (days 29-30) | | | | | | | |
| **Total** | | | | | | | |

The floors: **15 commits**, **5 issues filed and closed**, thirty days of use. Uses logged has no floor because the honest number varies enormously between a tool you run forty times a week and one you run once a day, and both are fine. What is not fine is a gap.

---

## Week 1

**Days used:** `[ ]` `[ ]` `[ ]` `[ ]` `[ ]` `[ ]` `[ ]`   (one box per day, tick the ones you actually used it)

**What annoyed me this week:**

- `<the specific friction, and the issue number you filed for it>`

**What I changed because of it:**

- `<the commit or the version, or "nothing yet, still deciding">`

**Commit distribution, run today:**

```
$ ./scripts/commit-distribution.sh
<paste the output>
```

---

## Week 2

**Days used:** `[ ]` `[ ]` `[ ]` `[ ]` `[ ]` `[ ]` `[ ]`

**What annoyed me this week:**

-

**What I changed because of it:**

-

**Commit distribution, run today:**

```
$ ./scripts/commit-distribution.sh
```

---

## Week 3

**Days used:** `[ ]` `[ ]` `[ ]` `[ ]` `[ ]` `[ ]` `[ ]`

**What annoyed me this week:**

-

**What I changed because of it:**

-

**Anything that has now broken twice:** `<name it. this is the thing that gets a test.>`

**Commit distribution, run today:**

```
$ ./scripts/commit-distribution.sh
```

---

## Week 4

**Days used:** `[ ]` `[ ]` `[ ]` `[ ]` `[ ]` `[ ]` `[ ]`

**What annoyed me this week:**

-

**What I changed because of it:**

-

**Commit distribution, run today:**

```
$ ./scripts/commit-distribution.sh
```

---

## Tail, days 29 and 30

**Days used:** `[ ]` `[ ]`

**Still using it now that the thirty days are up?** `<yes or no, and the honest reason>`

That question is not rhetorical. If the answer is no, say so in your README. "I stopped using it after the assignment ended, and here is what I would change to make it stick" is a real finding and reads far better than a claim of ongoing use that your log stops supporting on day thirty-one.

---

## Commit distribution

**15 commits across 30 days and 15 commits on one Saturday are the same number and different evidence.** Only one of them supports the claim this project makes, and anyone can tell which one you have by looking at the contribution graph on the front page of your repository. You do not get to explain that graph in an interview; it is read before you are in the room.

```bash
./scripts/commit-distribution.sh
```

Run it every week and paste the output above. The point of running it weekly is that a five-day gap in week two is fixable in week two and permanent in week four.

Commit on the day you change something. That produces an uneven, bursty history, which is what real maintenance looks like and is not the same as a cluster. What the rubric asks is whether the work happened across the period it claims, not whether it was evenly spaced.

| Pattern | What a reviewer concludes |
|---|---|
| 18 commits over 22 distinct days | Used the tool, fixed things as they came up |
| 18 commits over 4 distinct days, one per week | Batched the work but sustained the month |
| 18 commits over 2 distinct days | Built it twice, never used it |
| 18 commits, 14 of them on day 29 | Wrote the evidence, not the software |

Rows two and three have identical commit counts.

---

## The final numbers

Run these on day thirty. Every one of them is a command a reviewer can run too.

```bash
wc -l < usage.log                                   # <N> uses
head -1 usage.log && tail -1 usage.log              # first and last use, giving <M> days
cut -f1 usage.log | cut -dT -f1 | sort -u | wc -l   # distinct days used
git rev-list --count HEAD                           # total commits
./scripts/commit-distribution.sh                    # the distribution
gh issue list --state closed | wc -l                # <K> closed issues, if you use the gh CLI
```

| Claim number | Value | Where it comes from |
|---|---|---|
| `<N>` uses | | `usage.log` |
| `<M>` days | | first and last log dates |
| `<K>` issues filed and closed | | the Issues tab |
| `<X>` current version | | `CHANGELOG.md` |
| Commits | | `git rev-list --count HEAD` |
| Distinct days with a commit | | `commit-distribution.sh` |

Copy those four into the claim at the top of your README, unrounded.

---

## The verification list

The same list in your README, tracked here as you satisfy it.

- [ ] Usage evidence over 30 days: logs, commit dates, a screenshot of your shell history, anything real
- [ ] `CHANGELOG.md` with dated entries that reference actual changes
- [ ] At least 5 issues filed and closed, describing problems hit while using it
- [ ] At least 15 commits spread across the period, not clustered in one weekend
- [ ] Tests on whatever broke twice
- [ ] README that honestly says who this is for, which may legitimately be "me"
- [ ] Every date in this file agrees with git
- [ ] No secrets in git history: `git log --all --diff-filter=A --name-only | grep -i env`

---

## One note on honesty

Nothing in this file is hard to fake in isolation and all of it is hard to fake together, because the log dates, the commit dates, the issue dates, and the changelog dates all have to tell the same story. Constructing a consistent fake month is more work than living a real one and produces a worse project, since you end up with no tool you use and no month of evidence either.

If your thirty days went badly, write down what actually happened. A project that says "abandoned my first idea on day six because I never opened it, restarted with something I already did by hand every morning, used that one thirty-one days" is a stronger artifact than a clean fiction, and it is the version that survives being asked about.
