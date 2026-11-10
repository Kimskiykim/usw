#!/bin/sh

set -eu

MODE="all"
FORCE=0

case "$#" in
  0)
    ;;
  1)
    if [ "$1" = "--force" ]; then
      FORCE=1
    else
      MODE="$1"
    fi
    ;;
  2)
    MODE="$1"
    if [ "$2" = "--force" ]; then
      FORCE=1
    else
      echo "Usage: ./install.sh [all|qwen|codex|claude] [--force]" >&2
      exit 2
    fi
    ;;
  *)
    echo "Usage: ./install.sh [all|qwen|codex|claude] [--force]" >&2
    exit 2
    ;;
esac

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SKILL_NAMES="usw-initialize-project usw-manage-handoff usw-create-flow usw-run-flow usw-find-flow usw-assess-flow"
LEGACY_SKILL_NAMES="usw-init usw-refine-task usw-execute-task usw-verify-task usw-route-task usw-refine-intent usw-plan-small-steps usw-explain-me usw-structured-review"
COMMAND_NAMES="usw-init.md usw-handoff.md usw-resume.md usw-reviewer-llm-critic.md usw-find-flow.md usw-assess-flow.md usw-scout.md usw-hypothesis-checker.md usw-bounded-implementer.md usw-coverage-checker.md"
LEGACY_COMMAND_NAMES="usw-route-task.md usw-refine-intent.md usw-plan-small-steps.md usw-explain-me.md"
QWEN_HOME_DIR="${QWEN_HOME:-${HOME}/.qwen}"
QWEN_SKILLS_DIR="$QWEN_HOME_DIR/skills"
QWEN_COMMANDS_DIR="$QWEN_HOME_DIR/commands"
CODEX_SKILLS_DIR="${HOME}/.agents/skills"
CODEX_HOME_DIR="${CODEX_HOME:-${HOME}/.codex}"
CODEX_COMMANDS_DIR="$CODEX_HOME_DIR/prompts"
CLAUDE_HOME_DIR="${CLAUDE_HOME:-${HOME}/.claude}"
CLAUDE_SKILLS_DIR="$CLAUDE_HOME_DIR/skills"
CLAUDE_COMMANDS_DIR="$CLAUDE_HOME_DIR/commands"

usage() {
  echo "Usage: ./install.sh [all|qwen|codex|claude] [--force]" >&2
  exit 2
}

fail() {
  echo "USW installation failed for $1: $2. The installation may contain a mixed version; check it before use." >&2
  exit 1
}

check_sources() {
  for skill_name in $SKILL_NAMES; do
    source_path="$ROOT_DIR/skills/$skill_name"
    [ -d "$source_path" ] && [ -f "$source_path/SKILL.md" ] || fail "$source_path" "missing skill source"
  done
  for command_name in $COMMAND_NAMES; do
    source_path="$ROOT_DIR/commands/$command_name"
    [ -f "$source_path" ] || fail "$source_path" "missing command source"
  done
}

check_target() {
  target="$1"
  if [ "$FORCE" -eq 0 ] && { [ -e "$target" ] || [ -L "$target" ]; }; then
    echo "USW component is already installed at $target; refusing to overwrite it." >&2
    exit 1
  fi
}

check_agent_targets() {
  skills_dir="$1"
  commands_dir="$2"
  for skill_name in $SKILL_NAMES; do
    check_target "$skills_dir/$skill_name"
  done
  for command_name in $COMMAND_NAMES; do
    check_target "$commands_dir/$command_name"
  done
  for legacy_skill_name in $LEGACY_SKILL_NAMES; do
    check_target "$skills_dir/$legacy_skill_name"
  done
  for legacy_command_name in $LEGACY_COMMAND_NAMES; do
    check_target "$commands_dir/$legacy_command_name"
  done
}

install_component() {
  base_dir="$1"
  component="$2"
  kind="$3"
  source_path="$ROOT_DIR/${kind}s/$component"
  target="$base_dir/$component"
  mkdir -p "$base_dir" || fail "$target" "cannot create parent"
  stage=$(mktemp -d "$base_dir/.usw-install.$component.XXXXXX") || fail "$target" "cannot create staging directory"
  if [ "$kind" = skill ]; then
    if ! cp -R "$source_path" "$stage/new" ||
       ! find "$stage/new" -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete ||
       ! find "$stage/new" -type d -name '__pycache__' -empty -delete; then
      rm -rf "$stage" || echo "Cleanup failed; remaining path: $stage" >&2
      fail "$target" "cannot prepare skill"
    fi
  elif ! cp "$source_path" "$stage/new"; then
    rm -rf "$stage" || echo "Cleanup failed; remaining path: $stage" >&2
    fail "$target" "cannot prepare command"
  fi
  had_target=0
  if [ -e "$target" ] || [ -L "$target" ]; then
    if ! mv "$target" "$stage/backup"; then
      rm -rf "$stage" || echo "Cleanup failed; remaining path: $stage" >&2
      fail "$target" "cannot move previous component to backup"
    fi
    had_target=1
  fi
  if ! mv "$stage/new" "$target"; then
    if [ "$had_target" -eq 1 ] && ! mv "$stage/backup" "$target"; then
      rm -rf "$stage/new" || echo "Cleanup failed; remaining path: $stage/new" >&2
      fail "$target" "cannot restore previous component; backup retained at $stage/backup"
    fi
    rm -rf "$stage" || echo "Cleanup failed; remaining path: $stage" >&2
    fail "$target" "cannot activate component"
  fi
  rm -rf "$stage" || fail "$target" "cleanup failed; remaining path: $stage"
  echo "Installed USW $kind at $target"
}

install_agent() {
  skills_dir="$1"
  commands_dir="$2"
  if [ "$FORCE" -eq 1 ]; then
    for legacy_skill_name in $LEGACY_SKILL_NAMES; do
      if [ -e "$skills_dir/$legacy_skill_name" ] || [ -L "$skills_dir/$legacy_skill_name" ]; then
        rm -rf "$skills_dir/$legacy_skill_name" || fail "$skills_dir/$legacy_skill_name" "cannot remove legacy skill"
      fi
    done
    for legacy_command_name in $LEGACY_COMMAND_NAMES; do
      if [ -e "$commands_dir/$legacy_command_name" ] || [ -L "$commands_dir/$legacy_command_name" ]; then
        rm -f "$commands_dir/$legacy_command_name" || fail "$commands_dir/$legacy_command_name" "cannot remove legacy command"
      fi
    done
  fi
  for skill_name in $SKILL_NAMES; do
    install_component "$skills_dir" "$skill_name" skill
  done
  for command_name in $COMMAND_NAMES; do
    install_component "$commands_dir" "$command_name" command
  done
}

case "$MODE" in all|qwen|codex|claude) ;; *) usage ;; esac
check_sources

case "$MODE" in
  all)
    check_agent_targets "$QWEN_SKILLS_DIR" "$QWEN_COMMANDS_DIR"
    check_agent_targets "$CODEX_SKILLS_DIR" "$CODEX_COMMANDS_DIR"
    check_agent_targets "$CLAUDE_SKILLS_DIR" "$CLAUDE_COMMANDS_DIR"
    install_agent "$QWEN_SKILLS_DIR" "$QWEN_COMMANDS_DIR"
    install_agent "$CODEX_SKILLS_DIR" "$CODEX_COMMANDS_DIR"
    install_agent "$CLAUDE_SKILLS_DIR" "$CLAUDE_COMMANDS_DIR"
    ;;
  qwen)
    check_agent_targets "$QWEN_SKILLS_DIR" "$QWEN_COMMANDS_DIR"
    install_agent "$QWEN_SKILLS_DIR" "$QWEN_COMMANDS_DIR"
    ;;
  codex)
    check_agent_targets "$CODEX_SKILLS_DIR" "$CODEX_COMMANDS_DIR"
    install_agent "$CODEX_SKILLS_DIR" "$CODEX_COMMANDS_DIR"
    ;;
  claude)
    check_agent_targets "$CLAUDE_SKILLS_DIR" "$CLAUDE_COMMANDS_DIR"
    install_agent "$CLAUDE_SKILLS_DIR" "$CLAUDE_COMMANDS_DIR"
    ;;
esac

echo "Start a new agent session to load the installed USW commands."
