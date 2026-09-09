# Changelog

All notable changes to this project are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

**This file is graded, and it is graded against your commit history.** A reviewer can check whether the entry dated the 14th matches a commit on the 14th. Write the entry on the day you make the change and it takes forty seconds. Write all of them on day twenty-nine and the dates will disagree with git, which is worse than having no changelog at all.

One rule for every entry: **name the behavior that changed.** Not the file you edited, not the feeling you had about it.

| Not this | This |
|---|---|
| Various fixes and improvements | Empty input folder now exits 0 with a message instead of throwing |
| Refactored the parser | Dates like `3/4/26` are read as March 4 rather than silently skipped |
| Better error handling | Missing config file now names the path it looked in |
| Updated dependencies | Dropped `chalk`, which was the only dependency, so install is now zero-step |

---

## Delete this section

The three releases below are examples showing the expected level of detail. They are not your history. Delete them before you commit anything of your own, then start with `[Unreleased]` and `[0.1.0]` at the bottom of this file.

The example project is a script that renames screenshots. Yours will be something else.

### [0.3.0] - 2026-03-21

#### Added
- Regression test for the two-screenshots-in-the-same-second case, which has now broken twice (#7, #11)

#### Fixed
- Two screenshots taken in the same second no longer overwrite each other. The second one gets a `-2` suffix instead of silently replacing the first. This is the bug that cost me a screenshot of a meeting whiteboard. (#11)

### [0.2.0] - 2026-03-14

#### Changed
- Running with no arguments now processes `~/Desktop` instead of printing usage. That is what I meant every single time, and typing the path 30 times taught me that the usage text was not the useful default. (#4)
- Renames are reported one per line as they happen, rather than as a count at the end, so an interrupted run tells you where it stopped.

#### Fixed
- Filenames containing a colon no longer produce a path the Finder cannot open. Colons are now replaced with a hyphen. (#3)

### [0.1.0] - 2026-03-09

#### Added
- First working version. Renames every `Screenshot 2026-03-09 at 4.31.02 PM.png` on the Desktop to `2026-03-09-1631.png`.
- Usage logging to `usage.log`, one line per run, so day one is on the record.

---

## [Unreleased]

### Added

### Changed

### Fixed

### Removed

---

## [0.1.0] - `<YYYY-MM-DD>`

### Added
- `<First working version. State what it did on the first day you used it, in one line.>`
- `<Usage logging, if you wired it in on day one. You should have.>`
