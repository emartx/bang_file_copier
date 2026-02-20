# Step 11 — Manual Test Checklist

## Sandbox Setup

1. **Create a sandbox folder** (e.g., `test_sandbox/`).
2. Inside the sandbox, create these files:
   - `!a.txt`
   - `!!b.txt`
   - `!!!c.txt`
   - `!!!!d.txt`  *(should NOT match)*
   - `normal.txt`
3. Create two or more **existing destination folders** (e.g., `dest1/`, `dest2/`).
4. In one destination, pre-create a file with the same name as one of the planned destination filenames to test skip behavior.

## Test Scenarios

- **Normal run:**
  - Run the tool normally.
  - Expect: eligible files copied, renamed, logs created, skips if file exists.
- **Dry-run:**
  - Run with `--dry-run`.
  - Expect: actions printed, no files copied, no logs created.
- **Missing config:**
  - Remove or rename the config file.
  - Expect: exit code 2, error message.
- **Empty destinations:**
  - Use a config with an empty `destinations` list.
  - Expect: exit code 2, error message.
- **One missing destination folder:**
  - Set a destination in config that does not exist.
  - Expect: exit code 2, error message.
- **Permission error on one destination:**
  - Remove write permission from one destination folder.
  - Expect: error logged for that destination, exit code 1.

## Checklist Table

| Scenario                        | Expected Result                                 |
|---------------------------------|-------------------------------------------------|
| Normal run                      | Files copied, renamed, log created, skips work   |
| Dry-run                         | Actions printed, no files/logs created           |
| Missing config                  | Exit 2, error message                           |
| Empty destinations              | Exit 2, error message                           |
| Missing destination folder      | Exit 2, error message                           |
| Permission error on destination | Error logged, exit 1                            |

---

*See `produce_steps.md` for implementation details and requirements.*
