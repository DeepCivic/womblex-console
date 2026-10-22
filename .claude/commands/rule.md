---
description: Add a modular engineering rule to agents/rules/
---

Add a rule following `agents/rules/_template.md`:

1. Name it `{section}-{name}.md` using a section ID from `agents/rules/_sections.md`
2. Fill the frontmatter: `title`, `impact`, `tags`
3. Explain the *consequence* of getting it wrong, not just the instruction
4. Give an incorrect and a correct example
5. State honestly what enforces it, or "convention only"
6. Add it to the index in `agents/README.md`

`.runwai/tools/validate_helpers.py` fails if the prefix is unknown, the frontmatter is unparseable,
or the rule is not linked from the index.

$ARGUMENTS
