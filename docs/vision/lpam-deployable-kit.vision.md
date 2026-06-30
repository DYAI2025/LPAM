# Product Vision: LPAM Transferable Deployable Kit

Status: draft
Feature Slug: lpam-deployable-kit
Confirmation Status: pending-user-confirmation

> Context for the AgileTeam planner: LPAM is an **orchestration/deployment kit**, NOT
> an application. It turns one operator's working, bespoke "Hermes + gbrain on VPS + Mac"
> setup into something a stranger can `git clone` and stand up. Most of it is **already
> built and merged** to `main` (DYAI2025/LPAM) across PRs #6–#14 (see the PRD "Build
> Status" column and the Canvas). The remaining work is verification + doc coherence, not
> green-field build. Do not re-design what exists; plan around the OPEN requirements.

## Product Vision Board

| Area | ID | Value | Source Type | Source | User Decision Needed |
|---|---|---|---|---|---|
| Target Group | VIS-001 | Self-hosting operators/developers who run the **Nous Hermes** agent (or other MCP clients) and want a persistent, searchable long-term memory + local voice, deployed on **their own VPS + local Mac**. Primary persona today = the author (Benjamin); the kit's purpose is to generalize to other such operators. | EXPLICIT | SRC-001, SRC-004 | yes |
| User Needs | VIS-002 | (a) Reproducible deploy from one git repo instead of per-host hacking; (b) gbrain as Hermes' long-term memory (auto recall + consolidation); (c) a configurable model fallback chain that self-heals when free OpenRouter models get pulled/throttled; (d) the Hermes desktop app talking to their OWN VPS brain; (e) local live voice (push-to-talk → VPS brain → spoken reply). | EXPLICIT | SRC-001, SRC-003 | yes |
| Product / Feature | VIS-003 | LPAM: a deployment kit = config templates + systemd units + glue scripts + docs. It ships NO third-party binaries. backend (gbrain) + frontend (gbrain-atlas) are cloned by `install.sh`; Hermes itself is installed by the user with their own Nous account. | EXPLICIT | SRC-002, SRC-004 | yes |
| Product Value | VIS-004 | "Stand up exactly what we have" reproducibly and honestly: a working personal-AI memory+voice stack, with the third-party boundaries and two-machine topology made explicit so the adopter hits no hidden assumptions. | EXPLICIT | SRC-001 | yes |
| Business or Project Goals | VIS-005 | Open, MIT-licensed kit others can adopt; lower setup friction; reproducibility of the author's infra (survives machine loss). No revenue model — personal/open-source project. | ASSUMPTION | SRC-002 (LICENSE=MIT); business intent inferred, not stated | yes |
| Success Signals | VIS-006 | A new operator with a VPS + Mac + a Nous account can clone the repo and, following only the shipped docs, reach: gbrain MCP reachable, Hermes using gbrain as memory, the model fallback chain valid + self-healing, the desktop app driving the VPS brain, and one working push-to-talk turn — WITHOUT asking the author. (Quantitative target e.g. time-to-first-working-stack = not yet defined.) | EXPLICIT (qualitative); ASSUMPTION (quantitative target) | SRC-001 | yes |

## Confirmation

The assistant must not confirm this artifact.
