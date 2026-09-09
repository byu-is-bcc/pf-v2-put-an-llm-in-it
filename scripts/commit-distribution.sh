#!/usr/bin/env sh
# Print your commits per week over the last 30 days, so you can see your own
# distribution before a reviewer does.
#
#   ./scripts/commit-distribution.sh          # last 30 days
#   ./scripts/commit-distribution.sh 45       # any window you want
#
# The rubric asks for at least 15 commits spread across the period. A repository
# with 15 commits across 30 days looks different from one with 15 commits on a
# Saturday, and this tells you which one you currently have.
#
# Run it weekly. On day 29 it can only tell you your score.

set -u

DAYS="${1:-30}"

case "$DAYS" in
	'' | *[!0-9]*) printf 'Usage: %s [days]   (days must be a positive whole number)\n' "$0" >&2; exit 2 ;;
esac
[ "$DAYS" -ge 1 ] || { printf 'Usage: %s [days]   (days must be at least 1)\n' "$0" >&2; exit 2; }

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
	printf 'Not a git repository. Run this from inside your project.\n' >&2
	exit 1
fi

# An unborn branch is the normal state on day one, not an error.
if ! git rev-parse --verify --quiet HEAD >/dev/null 2>&1; then
	printf 'No commits yet. Come back after your first one.\n'
	exit 0
fi

# %ct is the commit timestamp in UTC seconds, %ad the author date for labels.
git log --since="$DAYS days ago" --date=short --pretty=format:'%ct %ad' |
	awk -v days="$DAYS" -v now="$(date +%s)" '
	{
		age = int((now - $1) / 86400)          # 0 means within the last 24 hours
		if (age < 0) age = 0                   # a commit dated in the future
		if (age >= days) next                  # --since is generous at the edge
		total++
		week = int(age / 7)
		if (week > maxweek) maxweek = week
		perweek[week]++
		if (perweek[week] > peakweek) peakweek = perweek[week]
		perday[age]++
		if (perday[age] == 1) activedays++
		if (perday[age] > peakday) { peakday = perday[age]; peakdate = $2 }
	}
	END {
		unit = (days == 1 ? "day" : "days")
		printf "\n"
		printf "Commits in the last %d %s:   %d\n", days, unit, total + 0
		if (total == 0) {
			printf "\nNothing in the window. If you are using the tool, something should be changing.\n\n"
			exit 0
		}
		printf "Days with at least one commit: %d of %d\n", activedays, days
		printf "Busiest single day:            %s, %d commit%s (%d%% of the total)\n",
			peakdate, peakday, (peakday == 1 ? "" : "s"), int(peakday * 100 / total + 0.5)

		# Weeks run from today back to the week holding your oldest commit in the
		# window, so an empty row is a week you worked around but not in.
		printf "\nCommits per week, most recent first:\n\n"
		bars = 34
		for (week = 0; week <= maxweek; week++) {
			lo = week * 7 + 1
			hi = (week + 1) * 7
			if (hi > days) hi = days
			count = perweek[week] + 0
			label = sprintf("Days %2d-%d", lo, hi)
			if (count == 0) {
				printf "  %-11s %3d\n", label, count
				continue
			}
			width = int(count * bars / peakweek + 0.5)
			if (width < 1) width = 1
			bar = ""
			for (i = 0; i < width; i++) bar = bar "#"
			printf "  %-11s %3d  %s\n", label, count, bar
		}

		strip = ""
		for (age = days - 1; age >= 0; age--) {
			count = perday[age] + 0
			strip = strip (count == 0 ? "." : (count > 9 ? "+" : count))
		}
		printf "\nDay by day, oldest on the left:\n  %s\n", strip

		printf "\n"
		gaps = 0
		for (week = 0; week <= maxweek; week++) if (perweek[week] + 0 == 0) gaps++
		if (total < 15)
			printf "%d short of the 15-commit floor.\n", 15 - total
		if (gaps == 1)
			printf "One week in this window has no commits at all. That gap is on your GitHub profile too.\n"
		if (gaps > 1)
			printf "%d weeks in this window have no commits at all. Those gaps are on your GitHub profile too.\n", gaps
		# Below five commits there is no distribution to judge yet, only a start.
		if (total >= 5 && peakday * 2 > total)
			printf "More than half of your commits are on one day. That is the pattern the rubric is looking for and not finding.\n"
		if (total >= 15 && gaps == 0 && peakday * 2 <= total && activedays >= 8)
			printf "This reads as sustained work. Keep committing on the day you change something.\n"
		printf "\n"
	}'
