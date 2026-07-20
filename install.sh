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
      echo "Usage: ./install.sh [all|qwen|codex] [--force]" >&2
      exit 2
    fi
    ;;
  *)
    echo "Usage: ./install.sh [all|qwen|codex] [--force]" >&2
    exit 2
    ;;
esac

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SKILL_NAMES="usw-initialize-project usw-manage-handoff usw-brainstorm-solutions usw-refine-task usw-plan-small-steps usw-explain-me"
LEGACY_SKILL_NAME="usw-init"
COMMAND_NAMES="usw-init.md usw-handoff.md usw-resume.md"
QWEN_HOME_DIR="${QWEN_HOME:-${HOME}/.qwen}"
QWEN_SKILLS_DIR="$QWEN_HOME_DIR/skills"
QWEN_COMMANDS_DIR="$QWEN_HOME_DIR/commands"
CODEX_SKILLS_DIR="${HOME}/.agents/skills"
CODEX_HOME_DIR="${CODEX_HOME:-${HOME}/.codex}"
CODEX_COMMANDS_DIR="$CODEX_HOME_DIR/prompts"

usage() {
  echo "Usage: ./install.sh [all|qwen|codex] [--force]" >&2
  exit 2
}

check_target() {
  target="$1"
  if [ "$FORCE" -eq 0 ] && [ -e "$target" ]; then
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
  check_target "$skills_dir/$LEGACY_SKILL_NAME"
}

install_skill() {
  base_dir="$1"
  skill_name="$2"
  source_skill_dir="$ROOT_DIR/skills/$skill_name"
  target="$base_dir/$skill_name"
  mkdir -p "$base_dir"
  if [ "$FORCE" -eq 1 ] && [ -e "$target" ]; then
    rm -rf "$target"
  fi
  cp -R "$source_skill_dir" "$target"
  echo "Installed USW skill at $target"
}

install_command() {
  base_dir="$1"
  command_name="$2"
  source_command="$ROOT_DIR/commands/$command_name"
  target="$base_dir/$command_name"
  mkdir -p "$base_dir"
  if [ "$FORCE" -eq 1 ] && [ -e "$target" ]; then
    rm -f "$target"
  fi
  cp "$source_command" "$target"
  echo "Installed USW command at $target"
}

install_agent() {
  skills_dir="$1"
  commands_dir="$2"
  if [ "$FORCE" -eq 1 ] && [ -e "$skills_dir/$LEGACY_SKILL_NAME" ]; then
    rm -rf "$skills_dir/$LEGACY_SKILL_NAME"
  fi
  for skill_name in $SKILL_NAMES; do
    install_skill "$skills_dir" "$skill_name"
  done
  for command_name in $COMMAND_NAMES; do
    install_command "$commands_dir" "$command_name"
  done
}

case "$MODE" in
  all)
    check_agent_targets "$QWEN_SKILLS_DIR" "$QWEN_COMMANDS_DIR"
    check_agent_targets "$CODEX_SKILLS_DIR" "$CODEX_COMMANDS_DIR"
    install_agent "$QWEN_SKILLS_DIR" "$QWEN_COMMANDS_DIR"
    install_agent "$CODEX_SKILLS_DIR" "$CODEX_COMMANDS_DIR"
    ;;
  qwen)
    check_agent_targets "$QWEN_SKILLS_DIR" "$QWEN_COMMANDS_DIR"
    install_agent "$QWEN_SKILLS_DIR" "$QWEN_COMMANDS_DIR"
    ;;
  codex)
    check_agent_targets "$CODEX_SKILLS_DIR" "$CODEX_COMMANDS_DIR"
    install_agent "$CODEX_SKILLS_DIR" "$CODEX_COMMANDS_DIR"
    ;;
  *)
    usage
    ;;
esac

echo "Start a new agent session to load /usw-init, /usw-handoff, and /usw-resume."
