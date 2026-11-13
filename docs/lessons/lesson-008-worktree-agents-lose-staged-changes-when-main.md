---
id: "lesson-008-worktree-agents-lose-staged-changes-when-main"
type: lesson
status: active
title: "Worktree agents lose staged changes when main repo branch operations interfere"
created: "2026-03-14"
owner: manu
tags: [pdf-modifier-mcp, lesson, git, worktree, parallel-agents, pattern]
---

# Worktree agents lose staged changes when main repo branch operations interfere

**Context:** Running two parallel agents in git worktrees while also creating branches in the main repo
**Problem:** When I created a branch in the main repo with the same name the worktree agent was going to use, the worktree's staged changes were lost. Git worktrees share the same repository, so branch operations in one worktree can affect others.
**Solution:** Do NOT create branches in the main repo while worktree agents are running. Let the agents finish first, then create branches from their output. Use git stash to extract changes from worktrees safely. Always check worktree status before manipulating shared branches.
**Tags:** `#git` `#worktree` `#parallel-agents` `#pattern`
