# Workflows waiting for the `workflow` scope

GitHub refuses pushes that create files under `.github/workflows/` unless the token has the `workflow` scope.
To turn the automation on, run once in a terminal: `gh auth refresh -s workflow -h github.com`, then:

    mkdir -p .github/workflows && git mv tools/workflows-pending/*.yml .github/workflows/ && git commit -m "Enable workflows" && git push

Then add the optional repo secret `ANTHROPIC_API_KEY` (Settings, Secrets and variables, Actions) so the daily news refresh uses model verification; without it the refresh runs in rules-only mode.
