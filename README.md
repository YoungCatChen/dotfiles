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

The installed `dotfiles` command applies or updates every source state it can
find:

```sh
dotfiles diff
dotfiles apply
dotfiles update
```

Third-party Fish plugins are declared in `~/.config/fish/fish_plugins` and
installed by Fisher. No Git submodules are required.
