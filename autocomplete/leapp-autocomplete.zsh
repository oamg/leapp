_python_argcomplete_leapp_zsh() {
    local COMP_LINE=$BUFFER
    local COMP_POINT=$(expr "$BUFFER" : ".*")
    #local COMP_TYPE=9
    #local COMP_WORDBREAKS="\"'><=;|&(:"
    local COMP_CMD=$words[1]

    local IFS=$'\013'
    local SUPPRESS_SPACE=1
    local COMPREPLY=( $(IFS="$IFS" \
                  COMP_LINE="$COMP_LINE" \
                  COMP_POINT="$COMP_POINT" \
                  COMP_TYPE="$COMP_TYPE" \
                  _ARGCOMPLETE_COMP_WORDBREAKS="$COMP_WORDBREAKS" \
                  _ARGCOMPLETE=1 \
                  _ARGCOMPLETE_SUPPRESS_SPACE=$SUPPRESS_SPACE \
                  "$COMP_CMD" 8>&1 9>&2 1>/dev/null 2>/dev/null) )

    if [[ $? == 0 ]]; then
        compadd -- $COMPREPLY
    fi
}
compdef _python_argcomplete_leapp_zsh leapp-tool
