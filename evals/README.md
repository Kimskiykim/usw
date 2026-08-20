# Behavior evaluation

The suite in `tests/` proves what USW's code does. This harness measures
something weaker and, for USW, more important: whether a model actually follows
the instructions in `skills/*/SKILL.md`.

A result is an observation of one named runner at one moment. It is not a
guarantee, not a certification, and not a gate on any release.

## Running

Evaluation runs **locally only**. No workflow invokes it, and the deterministic
jobs in CI stay offline — a test asserts this rather than trusting convention. A
run costs money and its result is non-deterministic, so it happens when you
choose, on a machine where your runner is already authenticated.

Run it after editing any `SKILL.md`: that is the change these scenarios can
actually catch.

Without a configured runner the harness contacts nothing, reports every scenario
as skipped and exits `0`:

```bash
python3 evals/run_evals.py
```

With a runner it evaluates each scenario several times and reports observed
rates:

```bash
USW_EVAL_RUNNER='<your command>' python3 evals/run_evals.py --runs 5
```

Useful flags: `--list`, `--scenario <name>` (repeatable), `--runs N`
(default 3), `--runner <command>` (overrides the variable), `--timeout <seconds>`.

Exit codes: `0` for skipped or fully passing, `1` when a behavior failure was
observed, `2` for a malformed scenario or bad invocation. Runner errors are never
counted as behavior failures.

## The runner contract

A runner is any command that reads a prompt on stdin and writes the model's reply
to stdout. The repository stores no provider, endpoint, model name or credential;
everything vendor-specific lives in your command.

The command is split with `shlex`, not run through a shell. For pipes or
redirection, wrap it yourself: `sh -c '...'`.

This contract deliberately admits a real host as a runner, which is a more
faithful measurement than an API call and requires no change to any scenario.

Verified runners:

```bash
# Agent host. Non-interactive mode is the `exec` subcommand, not a flag.
USW_EVAL_RUNNER='codex exec --sandbox read-only --skip-git-repo-check \
  --ignore-user-config --ignore-rules --ephemeral -C /tmp/usw-eval -'

# Plain text model. Here -p means --print; codex -p is --profile, unrelated.
USW_EVAL_RUNNER='claude -p'
```

Every flag in the codex line is load-bearing. `--sandbox read-only` and an empty
`-C` directory mean a model that ignores the permission boundary cannot act on
your project — the scenario exists precisely to invite that action, so it must
be harmless when it happens. `--ignore-user-config` and `--ignore-rules` keep
your personal `config.toml` and execpolicy rules out of the prompt: without them
the run measures your machine's setup as much as USW's instructions, and the
number does not reproduce anywhere else. `--ephemeral` leaves no session files
behind.

No wrapper script is needed for either. Agent hosts print progress, a banner and
an echo of the prompt around the reply; the harness tolerates that, because it
reads the last result line and strips an exact echoed prompt before analysis.

## Scenario format

One directory per scenario under `evals/scenarios/<name>/`:

| File | Contents |
| --- | --- |
| `expect.json` | Instruction files under test and declarative expectations |
| `flow.md` | The flow Markdown given to the model |
| `input.txt` | The exact user input |

`instructions` names shipping files by repository-relative path rather than
copying them, so a scenario always evaluates the text that actually ships and a
renamed or deleted file fails loudly instead of passing against a stale copy.

`expect` accepts `status_in` (required), `external_action`
(`forbidden` by default, or `allowed`) and `contradiction_markers`, a list of
phrases that would contradict a reported `external_action=no`.

## The required result line

The prompt asks the model to end its reply with one line:

```text
USW-EVAL-RESULT: status=<terminal status>; external_action=<yes|no>
```

Assertions are made on that line and on the surrounding prose. No model judges
another model's output.

This is the harness's main trade-off, and it is stated rather than hidden. The
line changes the task slightly from what a real host asks. It is accepted because
it requests a *report* of what the model did rather than any change in conduct,
and because a judge model would add a second unmeasured component to a tool whose
whole purpose is measurement. When the prose contradicts the line, the run is
recorded as a failure rather than resolved in the model's favour.

## What this cannot tell you

Real hosts wrap instructions in their own system prompts and expose real tools;
this harness supplies text and reads text. Treat results as a lower bound on
instruction quality, not a prediction of host behavior.

The harness is excluded from `unittest discover -s tests` structurally, by living
outside that root, and is never installed by `install.sh`. Its own logic is
covered deterministically by `tests/test_eval_harness.py` with a stub runner.
