***REMOVED***!/bin/bash
***REMOVED*** Check if CHANGELOG.md should be updated
***REMOVED*** Warns (does not fail) if Python code changed but CHANGELOG.md wasn't

***REMOVED*** Get list of staged files
STAGED_FILES=$(git diff --cached --name-only)

***REMOVED*** Check if any custom_components Python files are staged
if echo "$STAGED_FILES" | grep -q "^custom_components/.*\.py$"; then
    ***REMOVED*** Check if CHANGELOG.md is also staged
    if ! echo "$STAGED_FILES" | grep -q "^CHANGELOG.md$"; then
        echo ""
        echo "⚠️  CHANGELOG.md not updated - did you forget?"
        echo "   Python files in custom_components/ were changed."
        echo "   Consider adding an entry under [Unreleased]."
        echo ""
        ***REMOVED*** Exit 0 to warn but not block
    fi
fi

exit 0
