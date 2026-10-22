// Fixtures for controls/rules/path-traversal.yaml
//
// STEAL: IGNORE: Deliberately vulnerable by design. Every `ruleid:` case below is a working
// path traversal written so a rule can be asserted against it. Never lift it into real code.
//
// Run with: semgrep --test --config controls/rules controls/tests

const fs = require("fs");
const path = require("path");
const { readFileSync, createReadStream, unlinkSync } = require("fs");

const BASE = "/srv/app/data";

function readByTemplate(name) {
  // ruleid: runwai-js-path-traversal-sink
  return fs.readFileSync(`/srv/app/data/${name}`, "utf8");
}

function readByConcat(name) {
  // ruleid: runwai-js-path-traversal-sink
  return fs.readFileSync("/srv/app/data/" + name, "utf8");
}

function readAsyncByTemplate(name, cb) {
  // ruleid: runwai-js-path-traversal-sink
  return fs.readFile(`/srv/app/data/${name}`, "utf8", cb);
}

function writeByTemplate(name, body) {
  // ruleid: runwai-js-path-traversal-sink
  return fs.writeFileSync(`/srv/app/uploads/${name}`, body);
}

function streamByTemplate(name) {
  // ruleid: runwai-js-path-traversal-sink
  return fs.createReadStream(`/srv/app/data/${name}`);
}

function deleteByTemplate(name) {
  // ruleid: runwai-js-path-traversal-sink
  return fs.unlinkSync(`/tmp/uploads/${name}`);
}

function readDestructuredByTemplate(name) {
  // Destructuring is the dominant idiom, so the bare name is matched too.
  // ruleid: runwai-js-path-traversal-sink
  return readFileSync(`/srv/app/data/${name}`, "utf8");
}

function streamDestructuredByTemplate(name) {
  // ruleid: runwai-js-path-traversal-sink
  return createReadStream(`/srv/app/data/${name}`);
}

function deleteDestructuredByTemplate(name) {
  // ruleid: runwai-js-path-traversal-sink
  return unlinkSync(`/tmp/uploads/${name}`);
}

function readStaticPath() {
  // A literal path carries no caller-supplied segment.
  // ok: runwai-js-path-traversal-sink
  return fs.readFileSync("/etc/hostname", "utf8");
}

function readTemplateWithNoInterpolation() {
  // A template literal with nothing interpolated into it is still a literal.
  // ok: runwai-js-path-traversal-sink
  return fs.readFileSync(`/srv/app/data/schema.json`, "utf8");
}

function joinThenRead(name) {
  // ruleid: runwai-js-path-join-unresolved
  return fs.readFileSync(path.join(BASE, name), "utf8");
}

function joinThenReadAsync(name, cb) {
  // ruleid: runwai-js-path-join-unresolved
  return fs.readFile(path.join(BASE, name), "utf8", cb);
}

function joinThenStream(name) {
  // ruleid: runwai-js-path-join-unresolved
  return fs.createReadStream(path.join(BASE, name));
}

function joinThenDelete(name) {
  // ruleid: runwai-js-path-join-unresolved
  return fs.unlinkSync(path.join(BASE, name));
}

function joinThenReadDestructured(name) {
  // ruleid: runwai-js-path-join-unresolved
  return readFileSync(path.join(BASE, name), "utf8");
}

function joinOfLiteralsIsFine() {
  // Both segments are literals, so nothing a caller supplies reaches the sink.
  // ok: runwai-js-path-join-unresolved
  return fs.readFileSync(path.join("/srv/app/data", "schema.json"), "utf8");
}

function resolvedBeforeRead(name) {
  // path.resolve at the sink is what the rule asks for. Whether the caller then compares
  // the result to the resolved base is not something a sink match can see — see the header.
  // ok: runwai-js-path-join-unresolved
  return fs.readFileSync(path.resolve(BASE, name), "utf8");
}
