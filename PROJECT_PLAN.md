# PolicyTrace — Implementation Plan (Revised)

## 1. What changed from the original plan

Two corrections from the earlier version, both driven by the 1-week timeline
and by researching how existing tools solve these exact problems:

1. **Claim extraction moved from LLM to rule-based.** LLM prompt iteration is
   the highest-risk, most time-consuming part of a pipeline like this to get
   right. Academic tool PolicyLint proved that a sentence-pattern approach —
   decomposing each policy sentence into `[actor] [action] [data_object]
   [entity]` (e.g. "we [actor] do not sell [negated action] your email [data]
   to third parties [entity]") — catches real, structured claims without any
   ML model. This is fast to hand-code and fully deterministic, which also
   makes it easier to defend in a report ("this claim came from matching this
   exact sentence pattern," not "the model inferred this").
2. **The LLM's role moved to report narrative generation**, after the
   Alignment Engine, not before it. It takes the structured evidence
   (claims + tracker findings + flagged contradictions) and turns it into
   readable prose for the final report. This still satisfies the AI-504
   LLM/prompt-engineering requirement — the deliverable is a well-designed
   prompt template that reliably narrates structured JSON, which is its own
   nontrivial skill — just without the schedule risk of using an LLM for the
   harder, more ambiguous extraction step.

## 2. Corrected architecture

```
Website URL
     |
     v
HTTP Crawler (requests + BeautifulSoup)
     |
     v
Privacy Policy Discovery (link-text/href keyword scan)
     |
     v
Policy Text Extraction (trafilatura, with block-detection)
     |
     v
Rule-Based Analysis --------------------> Policy Claims
(actor/action/data/entity                (structured, polarity-aware)
 pattern matching)                             |
                                                |
Playwright Browser                             |
     |                                         |
     v                                         |
Network Monitoring                             |
(pre-consent / accept / reject)                |
     |                                         |
     v                                         |
Domain Extraction (tldextract)                 |
     |                                         |
     v                                         |
First-Party / Third-Party Classification       |
     |                                         |
     v                                         |
EasyPrivacy Matching (adblockparser)           |
     |                                         |
     v                                         |
Tracker Evidence  ------------------------------
     |
     v
Alignment Engine (rule-based comparison)
     |
     v
Local LLM (Ollama + LangChain) — report narrative only
     |
     v
Evidence-Based Report
     |
     v
Streamlit Dashboard (SQLite-backed)
```

## 3. Tool choices and why (researched, not assumed)

| Stage | Tool | Rationale |
|---|---|---|
| Policy text extraction | `trafilatura` | Auto-removes boilerplate; avoids the "extracted content too short" bug class from hand-tuned BeautifulSoup selectors |
| Domain classification | `tldextract` | Correctly parses multi-part suffixes (`.co.uk` etc.) — string-splitting misclassifies these |
| Tracker classification + ownership | **DuckDuckGo Tracker Radar** (`entities/*.json` + `domains/*.json`), **Disconnect `services.json`** as fallback | Confirmed real schema by fetching actual files: `entities/Google LLC.json` lists every domain a company owns under `properties`; `domains/US/doubleclick.net.json` gives category, fingerprinting score, and owner. Static JSON — no filter-rule parser needed, so `adblockparser` (found to be archived/unmaintained, with a known issue parsing some real EasyPrivacy rules) was dropped entirely rather than mitigated. Tested and confirmed this fixes the exact misclassification hit on the chatgpt.com run: `cdn.openai.com`/`bzr.openai.com` now resolve to `first-party (same owner)` via a small supplementary `custom_entities/` file (same schema as Tracker Radar's own `entity_map.json` technique), since Tracker Radar's real dataset only covers ad-tech/tracking companies, not OpenAI's own infrastructure. |
| Policy claim extraction | Hand-coded regex following PolicyLint's `[actor][action][data_object][entity]` pattern | Validated academic approach, but scoped down to hand-codable regex instead of PolicyLint's full ontology-generation system, which is out of scope for a week |
| LLM | Ollama (local) + LangChain (single `PromptTemplate`) | No API key/cost; scoped to one prompt, one `.invoke()` call — not a multi-step chain yet |
| Storage | stdlib `sqlite3` | No ORM needed at this scale |
| Dashboard | Streamlit | `st.dataframe()`/`st.json()` cover most needs with minimal UI code |

## 4. The PolicyLint-inspired claim pattern, concretely

Rather than flat keyword matching (`"share" in text`), extract structured
claims using regex over sentence-level text:

```python
# Simplified illustration, not final code
import re

NEGATION = r"(?:do not|does not|never|will not|won't)"
ACTIONS = r"(share|sell|collect|disclose|transfer)"
ENTITY = r"(third[- ]part(?:y|ies)|advertisers|affiliates|partners)"

# e.g. matches: "We do not sell your personal information to third parties."
pattern = re.compile(
    rf"we\s+{NEGATION}\s+{ACTIONS}\s+(?P<data>[\w\s]+?)\s+(?:to|with)\s+{ENTITY}",
    re.IGNORECASE
)

for sentence in policy_sentences:
    m = pattern.search(sentence)
    if m:
        claims.append({
            "actor": "we",
            "action": m.group(2),
            "polarity": "negative",   # negation matched
            "data_object": m.group("data").strip(),
            "entity": m.group(3),
            "source_sentence": sentence,
        })
```

Each claim carries its own source sentence — this is what lets the report say
"this claim came from this exact sentence" rather than a vague summary,
matching the project's evidence-based philosophy.

## 5. SQLite schema (unchanged from prior plan)

```
audits(id, url, run_at, policy_url, policy_fetch_status)
tracker_events(id, audit_id, state, domain, category)
policy_claims(id, audit_id, actor, action, polarity, data_object, entity, source_sentence)
flags(id, audit_id, severity, issue, evidence)
```

## 6. One-week phased plan

| Day | Deliverable |
|---|---|
| 1 | Project setup, folder skeleton, Phase 1 (tracker capture) migrated and re-tested — done |
| 2 | Policy discovery + trafilatura-based extraction with block detection — checkpoint report |
| 3 | Rule-based claim extraction (actor/action/data/entity regex) |
| 4 | EasyPrivacy matching via adblockparser (with error-handling fallback) + tracker categorization |
| 5 | Alignment engine (claims vs. tracker evidence) + SQLite persistence |
| 6 | LLM report narrative (single prompt template) + Streamlit dashboard |
| 7 | Polish, test against several real sites, prepare final report/demo |

## 7. Course requirement mapping (AI-504) — unchanged

| Requirement | Where it lives |
|---|---|
| Open Source AI Tools | Ollama, LangChain, EasyPrivacy (open dataset) |
| Large Language Models | Report narrative generation stage |
| Prompt Engineering | Single, iterated prompt template for turning structured evidence into report prose |
| AI Agents | Optional stretch goal if time remains after Day 7 — agent-lite wrapper around the pipeline stages |
| LangChain/Ollama/HuggingFace | `llm/` layer |

## 8. Honest risk notes

- Tracker Radar's `domains/` directory is region-sharded and large (many
  thousands of files) — only clone/load it if category labels are actually
  needed; ownership resolution alone only needs the much smaller `entities/`
  folder.
- Tracker Radar won't have entities for non-ad-tech organizations (e.g. a
  site's own CDN under a different domain) — this requires maintaining a
  small `custom_entities/` file per site tested, by hand, using the same
  schema. Not automatic; budget time for this per site in the demo.
- Rule-based claim extraction will miss claims phrased in ways the regex
  patterns don't anticipate — this is expected and should be stated plainly
  in the final report as a known limitation, not hidden.
- Agent orchestration is explicitly deprioritized to a stretch goal given the
  timeline — better to have Days 1–7 solid than to have a half-working agent
  layered on top of an unfinished core pipeline.


                           WEBSITE URL
                              │
             ┌────────────────┴────────────────┐
             │                                 │
             ▼                                 ▼
      POLICY SIDE                       BROWSER SIDE
             │                                 │
      Website Crawler                    Playwright
             │                                 │
      Find Privacy Policy                Live Website
             │                                 │
      Extract Policy Text               Network Requests
             │                                 │
      Split into Sentences                    │
             │                                 │
      Relevance Filter                        │
             │                                 ▼
             │                         First / Third Party
             ▼                                 │
      spaCy Dependency                        │
      Extraction                              ▼
             │                         Tracker Radar
             ▼                                 │
      Claim Validator                         │
             │                                 ▼
       ┌─────┴─────┐                       Cookies
       │           │                         │
    Complete   Incomplete                    │
       │           │                         │
       │        Mistral                       │
       │        Repair                        │
       │           │                         │
       └─────┬─────┘                         │
             ▼                               │
        FINAL POLICY CLAIMS                  │
             │                               │
             └──────────────┬────────────────┘
                            ▼
                 CLAIM ↔ BEHAVIOR
                    ALIGNMENT
                            │
                            ▼
                     AUDIT FINDINGS
                            │
                            ▼
                     FINAL REPORT