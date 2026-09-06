# Skill verification

Use these files to maintain the skills. They are not prerequisites for design or production.

| Check | Purpose |
| --- | --- |
| [Coverage](coverage.md) | Account for useful source topics and deliberate omissions |
| [Local review](review-results.md) | Record reader walkthroughs and executable checks |
| Per-skill `cases.json` | Exercise practical design and production tasks with a fresh reader/agent |
| [Initial evaluation history](history/README.md) | Preserve results for the earlier skill revision |

From the plugin root, run the design tests with Python's standard library. Run animation tests in a Python environment with Pillow:

```sh
python3 -m unittest discover -s skills/designing-visuals/tests -v
python3 -m unittest discover -s skills/producing-animations/tests -v
```

Run the GitHub notification example using the temporary-module procedure in the scene construction reference. Run the WAIT example, QA, packaging, and bundled compiler using the animation references. Run catalog checks only when a catalog repository and its tooling are supplied; use an isolated copy for example verification.

The case packs keep fresh-agent outcomes pending until that execution is performed. A maintainer walkthrough or passing example test must not be recorded as a fresh-agent behavioral PASS.
