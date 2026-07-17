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
SKILL_NAME="usw-initialize-project"
LEGACY_SKILL_NAME="usw-init"
COMMAND_NAME="usw-init.md"
SOURCE_SKILL_DIR="$ROOT_DIR/skills/$SKILL_NAME"
SOURCE_COMMAND="$ROOT_DIR/commands/$COMMAND_NAME"
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
  check_target "$skills_dir/$SKILL_NAME"
  check_target "$commands_dir/$COMMAND_NAME"
  check_target "$skills_dir/$LEGACY_SKILL_NAME"
}

install_skill() {
  base_dir="$1"
  target="$base_dir/$SKILL_NAME"
  legacy_target="$base_dir/$LEGACY_SKILL_NAME"
  mkdir -p "$base_dir"
  if [ "$FORCE" -eq 1 ]; then
    if [ -e "$target" ]; then
      rm -rf "$target"
    fi
    if [ -e "$legacy_target" ]; then
      rm -rf "$legacy_target"
    fi
  fi
  cp -R "$SOURCE_SKILL_DIR" "$target"
  echo "Installed USW skill at $target"
}

install_command() {
  base_dir="$1"
  target="$base_dir/$COMMAND_NAME"
  mkdir -p "$base_dir"
  if [ "$FORCE" -eq 1 ] && [ -e "$target" ]; then
    rm -f "$target"
  fi
  cp "$SOURCE_COMMAND" "$target"
  echo "Installed USW command at $target"
}

install_agent() {
  skills_dir="$1"
  commands_dir="$2"
  install_skill "$skills_dir"
  install_command "$commands_dir"
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

echo "Start a new agent session to load /usw-init."
