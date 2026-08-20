# Call Claude Skill Design

## Goal

Add a repository-owned `call-claude` skill under `dev/skills` for focused,
headless Claude requests from the current working tree.

## Structure

- `dev/skills/call-claude/SKILL.md` defines triggering conditions, invocation,
  prompt-scoping rules, and safety boundaries.
- `dev/skills/call-claude/agents/openai.yaml` provides matching UI metadata.
- No wrapper script is included: the skill invokes the installed Claude CLI
  directly with `claude -p` and does not duplicate CLI behavior.

## Behavior

The skill is appropriate for a scoped code review, focused file inspection, or
second opinion. It runs from the target repository root so Claude receives that
repository's context. Prompts identify exact files or a bounded diff and state
the expected output. Broad or ambiguous requests are narrowed before execution.

The default use is read-only analysis. The skill must not imply permission to
edit files, run destructive commands, or perform external actions; those require
an explicit user request and the normal approval boundaries.

## Verification

1. Record baseline behavior for a representative request without the new skill.
2. Validate the skill directory with the standard skill validator.
3. Repeat the representative request with the skill available and confirm the
   agent selects `claude -p`, uses a scoped prompt, and preserves approval
   boundaries.

## Done When

Both skill files exist, validation passes, and the forward test demonstrates the
intended invocation and scope without repository-specific absolute paths.
