# Attaches `-H` to `ps` for hierarchy, if supported.
# To be in sync with `ps.sh`.

if command ps -H &> /dev/null
  function ps; command ps -H $argv; end
else
  function ps; command ps $argv; end
end
