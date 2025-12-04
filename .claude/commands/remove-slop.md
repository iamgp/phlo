---
description: Remove AI-generated code slop from the current branch
---

# Remove AI Code Slop

Check the diff against main and remove all AI-generated slop introduced in this branch.

First, get the diff:

1. Run `git diff main...HEAD` to see all changes in this branch
2. Analyze each modified file for AI-generated patterns

Then identify and remove:

- Extra comments that a human wouldn't add or are inconsistent with the rest of the file
- Extra defensive checks or try/catch blocks that are abnormal for that area of the codebase (especially if called by trusted/validated codepaths)
- Casts to `any` to get around type issues
- Any other style that is inconsistent with the file
- Any unnecessary summary markdown files etc.

For each file with slop:

1. Read the entire file to understand the existing style and patterns
2. Remove the slop while preserving necessary changes
3. Ensure the code still functions correctly

After cleaning all files, report ONLY a 1-3 sentence summary of what you changed. No additional commentary.
