# dotfiles (public)

Public, machine-independent dotfiles managed by
[chezmoi](https://www.chezmoi.io/). Files are copied into place by chezmoi;
the repository is not part of the shell's runtime configuration.

This layer contains the common Fish/Bash setup, Git and SSH defaults, small
command-line tools, and minimal Vim/tmux configuration. Private and
organization-specific configuration live in separate source states.

## Install from a clone

```sh
./install.sh
```

On first install, validation stops with commands to copy the repository's
example to chezmoi's local config. Edit the required location before applying
again:

```toml
[data.machine]
location = "local" # or "remote" for a hosted/SSH machine
```

This config is deliberately local and is not owned by any layer. Inspect the
merged result with `chezmoi data`; change it later with
`chezmoi edit-config`, then run `dotfiles-layers apply`.

The installed `dotfiles-layers` command applies or updates every source state
it can find:

```sh
dotfiles-layers diff
dotfiles-layers apply
dotfiles-layers update
```

Third-party Fish plugins are declared in `~/.config/fish/fish_plugins` and
installed by Fisher. No Git submodules are required.

## Add another layer

Each layer is an independent Git repository whose root is a chezmoi source
state. To add one:

1. Create the repository and put chezmoi source files at its root (for
   example, `dot_config/example/config`).
2. Add `dot_config/dotfiles-layers/sources.d/NN-name.txt.tmpl` containing
   `{{ .chezmoi.sourceDir }}`. The numeric prefix defines apply order.
3. Make its installer apply prerequisite layers first, then run
   `chezmoi --source "$repo_dir" apply` for itself.
4. Avoid owning the same target file in multiple layers. Prefer fragments,
   application commands, or a `modify_` script when configuration must be
   shared.

The repository may be cloned anywhere because chezmoi is always given an
explicit source directory. Installers that need to clone this prerequisite use
`~/Code/dotfiles` by default.

## Design and style

- Keep layers independent and ordered from general to specific.
- Manage ordinary files as ordinary chezmoi files; use links only when a
  program genuinely requires one.
- Keep secrets out of Git and derive them from an authenticated local tool.
- Keep user-selected environment facts small and owned by the layer that uses
  them. Public configuration distinguishes `machine.location`; other layers
  may add independent namespaces. Use `.chezmoi.os`/`.chezmoi.arch` for facts
  chezmoi can detect itself.
- Use two spaces for indentation in hand-written shell, Fish, Git config,
  YAML, and similar configuration. Generated application files may retain
  their native formatting.
- `.profile` and the small `/bin/sh` utilities avoid Bash syntax and are tested
  with dash and BusyBox ash. Shared rc fragments also use the widely supported
  `local` extension to keep setup variables private. Fish configuration
  requires Fish; `git-master` requires Fish; and the legacy `mailafter` utility
  requires Bash.

## Command organization

- `~/.local/bin` contains standalone commands that must work from scripts and
  without interactive shell initialization. Small wrappers such as `dfh` are
  allowed here when their command-like behavior is useful across shells.
- `~/.config/shell/init.sh` is the single dispatcher for Bash, Dash, and
  BusyBox ash. Ordered fragments live in `~/.config/shell/rc.d`; `.sh` files
  are shared by all three shells and `.bash` files are loaded only by Bash.
- Shell fragments declare their scope with `is_login`, `is_interactive`, and
  `is_bash`, whose cached values are initialized by `init.sh`. Files are
  grouped by domain rather than split one alias per file. Static shortcuts
  shared with Fish come from one chezmoi template.
- `~/.config/fish` remains separate and uses Fish's native `status is-login`
  and `status is-interactive` guards.

## Shell startup behavior

- `.profile` and `.bash_profile` mark the shell as a login shell and invoke the
  shared dispatcher. `.bashrc` invokes the same dispatcher without that mark.
  The dispatcher is idempotent, so manually crossing entry points does not
  initialize the shell twice.
- Bash loads both shared `.sh` and Bash-specific `.bash` fragments. Dash and
  BusyBox ash load only `.sh` fragments, so they never parse Bash syntax.
- Environment fragments run for login shells. Prompt, aliases, and shell
  functions run only for interactive shells. Uptime requires both modes, so a
  non-interactive login never prints it.
- Bash additionally gets status-aware prompt coloring and directory history.
  `cdh` displays the stack; `CD_HISTORY_SIZE` defaults to 50, with zero meaning
  unlimited.
- Non-interactive, non-login Dash and BusyBox `ash` do not load startup files.
  They inherit exported environment from their parent, but aliases and shell
  functions require the caller to source a file explicitly. A shell cannot be
  made to load dotfiles before any dotfile code has run.
- Interactive, non-login POSIX shells may use the `ENV` variable for an rc
  file. This configuration does not set `ENV` because such shells are not a
  primary interactive entry point.

Interactive shells detect supported grep options and put them directly in a
shell alias. `GREP_OPTIONS` is intentionally not set because grep has
deprecated it.
