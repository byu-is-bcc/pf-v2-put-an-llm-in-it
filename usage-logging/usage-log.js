/**
 * Append one timestamped line to a usage log. Node 14 or later, no dependencies.
 *
 * Wiring it into your tool:
 *
 *   1. Copy this file into your project next to your own code.
 *   2. Require it and call logUse() once per real use, at the point where the tool
 *      has actually done its job:
 *
 *          const { logUse } = require("./usage-log");
 *
 *          async function main() {
 *            const files = await processAll();
 *            logUse("run", `${files.length} files`);
 *          }
 *
 *      If your package.json has "type": "module", change the last two lines of
 *      this file to `export { logUse, countUses };` and import it instead:
 *
 *          import { logUse } from "./usage-log.js";
 *
 *   3. Set USAGE_LOG to an absolute path if you run your tool from more than one
 *      directory, which for a CLI tool you will:
 *
 *          export USAGE_LOG="$HOME/code/mytool/usage.log"
 *
 *      For a browser extension there is no filesystem. Log to chrome.storage.local
 *      with the same one-line-per-use shape and export it when you need the count.
 *
 * Log it after the work succeeds, not before. A log of attempts is a different
 * number than a log of uses, and the claim you are making is about uses.
 *
 * Do not log: secrets, tokens, passwords, API keys, email addresses, anyone else's
 * name, file contents, or absolute paths that expose a directory structure you
 * would not want public. This file ends up in a public repository. Counts, flags,
 * and durations are safe. "3 files" is evidence; "/Users/you/Desktop/tax-2025.pdf"
 * is a leak.
 */

const fs = require("fs");
const path = require("path");

// USAGE_LOG wins if set. Otherwise the log sits next to this file.
const LOG_PATH = process.env.USAGE_LOG || path.join(__dirname, "usage.log");

// One use is one line, so tabs and newlines cannot survive in a field.
function clean(value) {
  return String(value == null ? "" : value)
    .split(/\s+/)
    .filter(Boolean)
    .join(" ");
}

/**
 * Append '<timestamp>\t<event>\t<detail>' to the log. Returns the line written.
 *
 * Never throws. A broken log should not take your tool down with it, but it
 * should say so on stderr rather than failing silently.
 */
function logUse(event = "run", detail = "") {
  // UTC so the format is identical in all three snippets and sorts lexicographically.
  const timestamp = new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
  const line = `${timestamp}\t${clean(event) || "run"}\t${clean(detail)}\n`;
  try {
    fs.mkdirSync(path.dirname(LOG_PATH), { recursive: true });
    // "a" is append mode: each write lands at the end, even across concurrent runs.
    fs.appendFileSync(LOG_PATH, line, "utf8");
  } catch (error) {
    process.stderr.write(`usage-log: could not write ${LOG_PATH}: ${error.message}\n`);
  }
  return line;
}

/**
 * How many times the tool has been used. This is <N> in your claim.
 *
 * A log that does not exist yet is zero uses, not an error.
 */
function countUses() {
  try {
    return fs
      .readFileSync(LOG_PATH, "utf8")
      .split("\n")
      .filter((line) => line.trim() !== "").length;
  } catch (error) {
    if (error.code !== "ENOENT") {
      process.stderr.write(`usage-log: could not read ${LOG_PATH}: ${error.message}\n`);
    }
    return 0;
  }
}

// node usage-log.js [event] [detail...]
if (require.main === module) {
  const [event = "run", ...rest] = process.argv.slice(2);
  process.stdout.write(logUse(event, rest.join(" ")));
  process.stderr.write(`${LOG_PATH}: ${countUses()} uses logged\n`);
}

module.exports = { logUse, countUses, LOG_PATH };
