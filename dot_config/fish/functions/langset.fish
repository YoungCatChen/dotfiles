# Sets locale env variables, including LC_ALL, LANG and LANGUAGE.
# To be in sync with `82-langset.sh`.

function langset
	set -gx LC_ALL "$1"
	set -gx LANG "$1"
	set -gx LANGUAGE "$2"
end
