#!/usr/bin/env sh
# Append one timestamped line to a usage log. POSIX sh, works in bash, zsh, dash.
#
# Wiring it into your tool:
#
#   1. Copy this file into your project, then source it from your own script and
#      call log_use once per real use, after the work has succeeded:
#
#          #!/usr/bin/env sh
#          . "$(dirname "$0")/usage-log.sh"
#
#          rename_everything "$@"
#          log_use "run" "$# files"
#
#   2. Set USAGE_LOG to an absolute path. A shell tool gets run from whatever
#      directory you happen to be in, and the default is relative:
#
#          export USAGE_LOG="$HOME/code/mytool/usage.log"
#
#   3. If you would rather not source anything, this is the entire idea and you
#      can paste it straight into your script:
#
#          printf '%s\t%s\t%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "run" "$# files" \
#            >> "$HOME/code/mytool/usage.log"
#
# Log it after the work succeeds, not before. A log of attempts is a different
# number than a log of uses, and the claim you are making is about uses.
#
# Do not log: secrets, tokens, passwords, API keys, email addresses, anyone else's
# name, file contents, or absolute paths that expose a directory structure you
# would not want public. This file ends up in a public repository. Counts, flags,
# and durations are safe. "3 files" is evidence; "/Users/you/Desktop/tax-2025.pdf"
# is a leak.
#
# Every variable below is prefixed _ul_ so sourcing this cannot clobber yours.

# One use is one line, so tabs and newlines cannot survive in a field.
_ul_clean() {
	printf '%s' "$*" | tr -s ' \t\n\r' ' ' | sed -e 's/^ *//' -e 's/ *$//'
}

# log_use [event] [detail]
# Appends '<timestamp>\t<event>\t<detail>'. Never fails the calling script: a
# broken log should not take your tool down with it, but it should say so.
log_use() {
	_ul_file="${USAGE_LOG:-usage.log}"
	_ul_event="$(_ul_clean "${1:-run}")"
	_ul_detail="$(_ul_clean "${2:-}")"
	# UTC so the format matches the Python and JavaScript snippets and sorts
	# lexicographically. Use +%Y-%m-%dT%H:%M:%S%z instead if you want local time.
	_ul_stamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

	_ul_dir="$(dirname "$_ul_file")"
	[ -d "$_ul_dir" ] || mkdir -p "$_ul_dir" 2>/dev/null

	# The subshell keeps a failed redirection quiet so we can report it ourselves.
	( printf '%s\t%s\t%s\n' "$_ul_stamp" "${_ul_event:-run}" "$_ul_detail" >>"$_ul_file" ) 2>/dev/null \
		|| printf 'usage-log: could not write %s\n' "$_ul_file" >&2
}

# count_uses
# Prints how many times the tool has been used. This is <N> in your claim.
count_uses() {
	_ul_file="${USAGE_LOG:-usage.log}"
	if [ ! -f "$_ul_file" ]; then
		printf '0\n'
		return 0
	fi
	# grep exits 1 on a count of zero, which is not an error here.
	_ul_count="$(grep -c '[^[:space:]]' "$_ul_file" 2>/dev/null || true)"
	printf '%s\n' "${_ul_count:-0}"
}

# Self test. Sourcing this file does nothing but define the two functions above.
#   sh usage-log.sh selftest
if [ "${1:-}" = "selftest" ]; then
	log_use "selftest" "one line appended"
	printf '%s: %s uses logged\n' "${USAGE_LOG:-usage.log}" "$(count_uses)" >&2
fi
