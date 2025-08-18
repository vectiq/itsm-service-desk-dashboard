**AI for ITSM Demo Pack — Instructions (v2)**

*Includes Runbook overview — UC-02, UC-21, UC-31*

12 Aug 2025

1) What this pack is

A small, consistent ITSM data universe that supports three AI demos:

• UC-02 – Incident Triage & Assignment

• UC-21 – Automated KB from Ticket Clusters

• UC-31 – Agent Skill Matching Engine

Everything is CSV, no ServiceNow required. Use dataset_catalog.csv as the index.

2) Load order (one-time setup)

Reference data first (used by all use-cases):

1) services_catalog.csv

2) category_tree.csv

3) cmdb_ci.csv

4) users_agents.csv, assignment_groups.csv, agent_group_membership.csv

5) skills_catalog.csv, agent_skills.csv

6) (Optional NLP) synonyms_glossary.csv

7) priority_matrix.csv

Then the “facts”:

8) incidents_resolved.csv (historical corpus, 300 rows)

Then the live/demo inputs:

9) workload_queue.csv (open items to assign)

10) agent_capacity_snapshots.csv, agent_performance_history.csv, schedules.csv

For KB drafting:

11) kb_templates.csv (scaffolds)

12) kb_articles.csv (empty target the AI will write to)

3) How the files relate (mental model)

Think lookups + facts + live queue:

• Lookups: services, categories, CIs, agents, groups, skills.

• Facts: incidents_resolved.csv (titles, descriptions, labels, resolution).

• Live work: workload_queue.csv (items needing assignment now).

• Operational context: capacity, performance history, schedules.

• Knowledge: templates → articles.

Flow:

text (incidents, workload) → normalise (synonyms, categories)

→ UC-02 triage (priority, group) + UC-21 clusters → UC-21 KB drafts (templates)

→ UC-31 matching (skills + capacity + schedule + quality)

4) Use-case runbooks

UC-02 — Incident Triage & Assignment

Data: incidents_resolved.csv; priority_matrix.csv; category_tree.csv; services_catalog.csv; cmdb_ci.csv; (optional) synonyms_glossary.csv

Pipeline: Clean text → features (text + categorical) → predict priority & group → evaluate → export triage_predictions.csv

UC-21 — Automated KB Article Creation from Ticket Clusters

Data: incidents_resolved.csv; kb_templates.csv; (optional) category_tree.csv

Pipeline: Clean text → embed + cluster → rank clusters → summarise → draft KB → export kb_articles.csv (drafts)

UC-31 — Agent Skill Matching Engine

Data: workload_queue.csv; users/skills/groups; capacity; schedules; performance

Pipeline: Score agents (skill, capacity, availability, quality, SLA) → route → export routing_decisions.csv

5) Minimal demo script (10–15 minutes)

1) Load all CSVs and run QA checks

2) Show lookups (services, categories, people/skills)

3) UC-02: triage predictions on sample incidents

4) UC-21: cluster corpus; draft 3 KBs via templates

5) UC-31: route a P1 item with rationale

6) File cheat-sheet (key columns)

incidents_resolved.csv → short_description, description, service_id, ci_id, category_id, impact, urgency, true_priority, true_assignment_group_id, time_to_resolve_mins

workload_queue.csv → required_skills, priority, sla_due, service_id, category_id, ci_id

agent_skills.csv → agent_id, skill_id, level, certified

agent_capacity_snapshots.csv → open_tasks, wip_limit, available

agent_performance_history.csv → avg_handle_time_mins, fcr_rate, csat, success_rate

schedules.csv → local working hours per agent

kb_templates.csv → title/body sections for KB scaffolding

7) Outputs to produce (deliverables)

• triage_predictions.csv (UC-02)

• kb_articles.csv populated with drafts (UC-21)

• routing_decisions.csv (UC-31)

8) Guardrails & tips

• Keep runs deterministic (fix random seeds)

• Reuse the same text normalisation across UC-02 and UC-21

• Use ids for joins; avoid hard-coded names

• Treat ground_truth_cluster as evaluation-only for UC-21

• AU timestamps; no PII included

9) About Runbook.xlsx — what’s inside and how to use it

Tabs you’ll find:

• Overview — what the pack is, the three use-cases, where to start.

• Load Order — exact sequence to import CSVs (lookups → facts → live inputs).

• Data Dictionary — every file and column, meaning, and an example value pulled from the data.

• Joins & Keys — foreign-key relationships and purpose (e.g., incidents.service_id → services.service_id).

• Use-Cases — inputs, pipeline steps, and expected outputs for UC-02/21/31.

• Quality Checks — quick QA tests (row counts, uniqueness, null thresholds) to run post-load.

• Deliverables — output file specs your pipelines should emit.

• Demo Script — a 10–15 minute sequence for the live demo.

• Tips & Pitfalls — guardrails to keep results consistent and explainable.

• Changelog — note changes to data/assumptions for repeatability.

How to use it:

1) Open ‘Load Order’ and import the CSVs in order.

2) Validate with ‘Quality Checks’ (copy checks into your notebooks/pipelines).

3) Implement each use-case using the ‘Use-Cases’ tab as your checklist.

4) Produce the three deliverables (triage_predictions.csv, kb_articles.csv, routing_decisions.csv).

5) Record any changes in ‘Changelog’.

