OMO executor spawn template (Prometheus fills this when delegating from the plan):

```
TASK: <single objective from plan>
EXPECTED OUTCOME: Markdown in state/current/draft.md (section: <name>)
REQUIRED SKILLS: []
REQUIRED TOOLS: read, glob, grep, websearch, webfetch
MUST DO:
  - Execute only this plan task
  - Write or append to state/current/draft.md
MUST NOT DO:
  - No /init-deep or AGENTS.md
  - No writes to .omo/plans/ (planner only)
CONTEXT:
  - pipeline/, eval/, README.md
```

**Read-only research:**

```
call_omo_agent(subagent_type="explore", load_skills=[], run_in_background=true, prompt="...")
call_omo_agent(subagent_type="librarian", load_skills=[], run_in_background=true, prompt="...")
```

**Write draft section:**

```
task(category="unspecified-high", load_skills=[], run_in_background=false,
  description="...", prompt="... EXPECTED OUTCOME: state/current/draft.md#section ...")
```

Verification-first: every spawn must state how success will be checked.
