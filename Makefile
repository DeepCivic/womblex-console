# runwAI — the first session's mechanical steps, as deterministic targets.
#
# `make first-session` replicates what AGENTS.md tells the setup agent to run: install
# the pinned toolchain, install the commit hook, run every check over the whole tree,
# prove the rules catch their committed fixtures, audit the dependencies, check the
# environment, and regenerate the security report. An agent transcribing commands from
# prose is where a wrong flag or a stale pin slips in; a target is the same command
# every time.
#
# Each target wraps exactly one documented step and adds nothing of its own — the
# canonical command list, with exit codes and what each check covers, stays in
# agents/running-the-checks.md. Every version below is pinned: `setup`,
# `setup-audit-tools` and `setup-audit-dbs` need the network, and everything after them
# is offline, deterministic, and calls no model.

PYTHON ?= python3

# The toolchain installs into a project-local virtual environment rather than into the
# machine's Python. Two separate failures made `make setup` — the first command of the
# first session — die on the Linux images most adopters actually run:
#
#   * a distro-installed package pip cannot replace, because apt's copy carries no RECORD
#     file ("Cannot uninstall PyYAML 6.0.1"); and
#   * PEP 668's externally-managed marker, which refuses the install outright wherever
#     `python3` is the distribution's own.
#
# Neither message is one a non-technical user can act on, and the usual workaround —
# `--break-system-packages`, or dropping the version pin to get past it — un-pins a
# scanner and takes the determinism guarantee with it. A venv fixes both, and nothing
# outside this directory is touched.
#
# .venv/bin goes on PATH for every recipe rather than being spelled out per target,
# because verify.py locates its scanners with shutil.which rather than through $(PYTHON).
# Prepending a directory that does not exist is a no-op, so this stays correct in CI,
# which installs its pins globally and never runs `make setup`.
VENV ?= .venv
# .audit-cache/bin is on PATH here for the same reason .venv/bin is, and it was missing:
# `setup-audit-tools` installs trivy and syft there, and every target that needs them —
# `setup-audit-dbs` and `audit` — could not see them. Run verbatim, the documented order
# exited 2 with "trivy is not installed", advising the target the reader had just run.
# A directory that does not exist is a no-op to prepend, so this stays correct before
# the tools are installed and in CI, which installs its own.
AUDIT_BIN ?= .audit-cache/bin
export PATH := $(CURDIR)/$(VENV)/bin:$(CURDIR)/$(AUDIT_BIN):$(PATH)

# --- check mode ----------------------------------------------------------------------
#
# A check runs by default when `make setup` can bind its tooling to .venv/. That is the
# whole test, and it is mechanical rather than a judgement: pre-commit, semgrep,
# detect-secrets and pyyaml are packages, so pip pins them into the project's own
# environment and they run on every session, on any machine, with nothing else arranged.
#
# The dependency audit cannot be bound that way. trivy and syft are architecture-specific
# release binaries rather than packages — which is why they have their own install target
# and their own directory — and the advisory database is about a gigabyte from a container
# registry that corporate and cloud networks routinely block. A check whose tooling cannot
# live in .venv/ is environment-constrained, and environment-constrained means off by
# default: the machine decides whether it can run, so the session must not assume it did.
#
# Off is not quiet. `first-session` prints what did not run, what that leaves unknown, and
# the command that turns it on — replacing an exit code that `|| true` swallowed, which
# read as a failed step rather than as an unmade measurement. Nothing here is a gate being
# moved after it went red: the audit blocks nothing, has never blocked anything, and is
# louder in default mode than it was before.
#
#   make first-session                 the venv-bound set; the audit reports NOT RUN
#   make first-session CHECK_MODE=full the same, with the audit attempted inline
#   make audit                         always runs when named — naming it is the opt-in
CHECK_MODE ?= default

# The dependency scanners ship as release binaries rather than packages, so the pin has
# to name a version, a platform and a checksum. Pinning to the tag alone would trust
# whatever the release assets are today; the checksum is what makes the install
# reproducible. Both are Apache-2.0, read from LICENSE in each upstream tree at the tag
# below. Change these and you are changing a control's tooling — see MAINTAINERS.md.
TRIVY_VERSION ?= 0.72.0
SYFT_VERSION ?= 1.50.0
#
# The four allowlist pragmas below are the one place in this repository where a secret
# scanner is told to stand down, so the reason is here rather than implied: these are
# published artefact digests from each release's own checksums.txt. A SHA-256 of a public
# tarball is high-entropy hex and nothing else — detect-secrets cannot tell it from a key,
# and suppressing it in the baseline instead would hide it from review.
#
# Make ends a variable's value at the '#', but keeps the space before it, so each value
# below carries a trailing space. `$(strip ...)` at the use site removes it — sha256sum
# tolerates the extra space today and there is no reason to depend on that.
TRIVY_SHA256_amd64 ?= bbb64b9695866ce4a7a8f5c9592002c5961cab378577fa3f8a040df362b9b2ea # pragma: allowlist secret
TRIVY_SHA256_arm64 ?= 2ca2c023109c2db6b2b77366b6717291452d4531167377d95c79547f0c8e3467 # pragma: allowlist secret
SYFT_SHA256_amd64 ?= bf7b29ff57f06da30918266a0e1c2885a8f99784798d1bdb1628886aa015d788 # pragma: allowlist secret
SYFT_SHA256_arm64 ?= 887c57cbcc2d0e8c5c110a4571a3fc7150058b24d74f993ee4663516e5c8ce86 # pragma: allowlist secret

.PHONY: first-session setup hook check verify report audit doctor \
        setup-audit-tools setup-audit-dbs

# audit and doctor are not allowed to abort the session. Both report on things a first
# session cannot be expected to have got right yet — a dependency with a CVE, an unset
# environment variable — and neither is a reason to stop setting up.
#
# doctor stays on by default: bash and coreutils are not installed into anything, so it
# binds to the machine trivially and runs everywhere. The audit is the one check in this
# file that fails the .venv/ test above, so it is the one the mode gates.
#
# `report` runs after the audit and not before, because it reads what the audit wrote. The
# other order produced a report whose Dependency posture section said no audit output was
# supplied, immediately after one had been. In default mode nothing was supplied and the
# report says exactly that, which is the true statement.
first-session: setup hook check verify
	@if [ "$(CHECK_MODE)" = "full" ]; then \
	  $(MAKE) --no-print-directory audit || true; \
	else \
	  printf '%s\n' \
	    "Dependency audit: NOT RUN — environment-constrained, so it is off by default." \
	    "  It needs trivy and syft, which are release binaries rather than packages and" \
	    "  cannot be installed into .venv/, plus about a gigabyte of vulnerability" \
	    "  database over the network." \
	    "  So you do not yet know whether the packages you depend on carry known" \
	    "  vulnerabilities. That is not the same as knowing they carry none." \
	    "  Turn it on — once per machine, then it stays available:" \
	    "      make setup-audit-tools && make setup-audit-dbs && make audit" \
	    "  Or run this whole session with it:  make first-session CHECK_MODE=full"; \
	fi
	@$(MAKE) --no-print-directory doctor || true
	@$(MAKE) --no-print-directory report

setup: ## Install the pinned toolchain into .venv/ (the one step that needs the network)
	@set -eu; \
	if [ ! -x "$(VENV)/bin/python" ]; then \
	  "$(PYTHON)" -m venv "$(VENV)" || { \
	    echo ""; \
	    echo "Could not create the $(VENV)/ environment."; \
	    echo "On Debian and Ubuntu the venv module is packaged separately from Python."; \
	    echo "Install it, then run 'make setup' again:"; \
	    echo "    sudo apt install python3-venv"; \
	    exit 2; \
	  }; \
	fi; \
	"$(VENV)/bin/python" -m pip install \
	  pre-commit==4.6.1 semgrep==1.171.0 detect-secrets==1.5.0 pyyaml==6.0.3
	@echo ""
	@echo "Toolchain installed in $(VENV)/. Every make target finds it without being told."
	@echo "To run the commands in agents/running-the-checks.md by hand, put it on PATH once:"
	@echo "    export PATH=\"\$$PWD/$(VENV)/bin:\$$PATH\""

hook: ## Install the commit hook — the only thing here that ever stops an action
	pre-commit install

check: ## Run every commit-time check, over the whole tree rather than staged files
	pre-commit run --all-files

verify: ## Prove each rule catches its committed vulnerable examples — the receipt for IT
	$(PYTHON) .github/scripts/verify.py

audit: ## Scan dependencies for known CVEs and write the SBOM (environment-constrained; off by default in first-session)
	$(PYTHON) .github/scripts/audit.py

doctor: ## Compare the declared environment to the actual one (reports, never blocks)
	bash .github/scripts/doctor.sh

report: ## Regenerate docs/security-report.md (coverage only; CI adds scan findings)
	$(PYTHON) .github/scripts/security_report.py --audit .audit-cache/audit.json

# --- the two networked audit steps, kept separate from `setup` -----------------------
#
# Separate because they are large and because `make audit` must be honest about being
# offline. The database is roughly a gigabyte on disk; downloading it as part of every
# `setup` would make the first session slow for a project that may have no dependency
# manifests at all.

setup-audit-tools: ## Install trivy and syft at the pinned versions, checksum-verified
	@set -eu; \
	mkdir -p "$(AUDIT_BIN)"; \
	case "$$(uname -m)" in \
	  x86_64|amd64) \
	    trivy_arch=Linux-64bit; syft_arch=linux_amd64; \
	    trivy_sha=$(strip $(TRIVY_SHA256_amd64)); syft_sha=$(strip $(SYFT_SHA256_amd64)) ;; \
	  aarch64|arm64) \
	    trivy_arch=Linux-ARM64; syft_arch=linux_arm64; \
	    trivy_sha=$(strip $(TRIVY_SHA256_arm64)); syft_sha=$(strip $(SYFT_SHA256_arm64)) ;; \
	  *) echo "unsupported architecture $$(uname -m); install trivy and syft by hand" >&2; exit 2 ;; \
	esac; \
	tmp=$$(mktemp -d); \
	curl -fsSL -o "$$tmp/trivy.tgz" \
	  "https://github.com/aquasecurity/trivy/releases/download/v$(TRIVY_VERSION)/trivy_$(TRIVY_VERSION)_$$trivy_arch.tar.gz"; \
	curl -fsSL -o "$$tmp/syft.tgz" \
	  "https://github.com/anchore/syft/releases/download/v$(SYFT_VERSION)/syft_$(SYFT_VERSION)_$$syft_arch.tar.gz"; \
	echo "$$trivy_sha  $$tmp/trivy.tgz" | sha256sum -c -; \
	echo "$$syft_sha  $$tmp/syft.tgz" | sha256sum -c -; \
	tar -xzf "$$tmp/trivy.tgz" -C "$(AUDIT_BIN)" trivy; \
	tar -xzf "$$tmp/syft.tgz" -C "$(AUDIT_BIN)" syft; \
	rm -rf "$$tmp"; \
	echo "trivy $(TRIVY_VERSION) and syft $(SYFT_VERSION) installed in $(AUDIT_BIN)/."; \
	echo "Every make target finds them without being told. To run the underlying"; \
	echo "commands by hand, put them on PATH once per shell:"; \
	echo "    export PATH=\"\$$PWD/$(AUDIT_BIN):\$$PATH\""

setup-audit-dbs: ## Download the vulnerability database once (the only network call `audit` needs)
	$(PYTHON) .github/scripts/audit.py --setup
