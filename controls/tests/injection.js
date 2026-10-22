// Fixtures for controls/rules/injection.yaml
//
// STEAL: IGNORE: Deliberately vulnerable by design. Every `ruleid:` case below is a working
// injection written so a rule can be asserted against it. Never lift it into real code.
//
// Run with: semgrep --test --config controls/rules controls/tests

function sqlTemplateLiteral(db, id) {
  // ruleid: runwai-js-sql-template-literal
  return db.query(`SELECT * FROM users WHERE id = ${id}`);
}

function sqlConcat(db, id) {
  // ruleid: runwai-js-sql-template-literal
  return db.query("SELECT * FROM users WHERE id = " + id);
}

function sqlKnexRaw(db, id) {
  // ruleid: runwai-js-sql-template-literal
  return db.raw(`SELECT * FROM users WHERE id = ${id}`);
}

function sqlPlaceholders(db, id) {
  // ok: runwai-js-sql-template-literal
  return db.query("SELECT * FROM users WHERE id = ?", [id]);
}

function sqlStatic(db) {
  // ok: runwai-js-sql-template-literal
  return db.query("SELECT count(*) FROM users");
}

function xssInnerHtml(el, val) {
  // ruleid: runwai-js-dangerous-html-sink
  el.innerHTML = val;
}

function xssInsertAdjacent(el, val) {
  // ruleid: runwai-js-dangerous-html-sink
  el.insertAdjacentHTML("beforeend", val);
}

function xssDocumentWrite(val) {
  // ruleid: runwai-js-dangerous-html-sink
  document.write(val);
}

function htmlStaticIsFine(el) {
  // A literal carries no untrusted data, so it must not be flagged.
  // ok: runwai-js-dangerous-html-sink
  el.innerHTML = "<b>static markup</b>";
}

function textContentIsFine(el, val) {
  // ok: runwai-js-dangerous-html-sink
  el.textContent = val;
}

const child_process = require("child_process");
const { exec, execSync, execFile } = child_process;

function shellTemplate(userInput) {
  // ruleid: runwai-js-shell-injection
  exec(`ls -la ${userInput}`);
}

function shellConcat(userInput) {
  // ruleid: runwai-js-shell-injection
  exec("ls -la " + userInput, (err, stdout) => stdout);
}

function shellSyncTemplate(userInput) {
  // ruleid: runwai-js-shell-injection
  execSync(`cat ${userInput}`);
}

function shellQualifiedTemplate(userInput) {
  // ruleid: runwai-js-shell-injection
  child_process.exec(`rm -f ${userInput}`);
}

function shellStaticIsFine() {
  // A static command carries no untrusted data, so it must not be flagged.
  // ok: runwai-js-shell-injection
  exec("ls -la");
}

function shellSyncStaticIsFine() {
  // ok: runwai-js-shell-injection
  execSync("git status --short");
}

function shellArgvIsFine(userInput) {
  // execFile passes the value as an argument, never through a shell.
  // ok: runwai-js-shell-injection
  execFile("ls", ["-la", userInput]);
}

function regexExecIsFine(pattern, userInput) {
  // RegExp.prototype.exec is not child_process; the receiver anchor keeps it out.
  // ok: runwai-js-shell-injection
  return pattern.exec(`prefix ${userInput}`);
}
