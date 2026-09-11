# PolicyTrace

PolicyTrace is a local privacy auditing tool that compares what a website's privacy policy says with what the website actually does in the browser.

The project focuses on collecting evidence rather than making legal claims.

## Problem

A privacy policy tells users how a website claims to handle data, but reading the policy alone does not show what happens technically when the website is opened.

A website may:

- Load third-party services
- Send requests to external domains
- Use analytics or tracking services
- Load embedded content
- Behave differently before and after consent

Manually investigating these behaviors is difficult for normal users and time-consuming for researchers.

## Proposed Solution

PolicyTrace performs an automated audit:

```
                    Website URL
                         |
                         v
                 HTTP Crawler
                         |
                         v
              Privacy Policy Discovery
                         |
                         v
               Policy Text Extraction
                         |
                         v
                Rule-Based Analysis
                  (structured claims:
                   actor / action / data / entity)
                         |
                         v
                 Policy Claims
                         |
                         |
        +----------------+
        |
        v
 (compared against)
        |
        v
                 Playwright Browser
                         |
                         v
              Network Monitoring
             (pre-consent / accept / reject)
                         |
                         v
               Domain Extraction
                         |
                         v
             First-Party / Third-Party
                         |
                         v
                  EasyPrivacy
                         |
                         v
              Tracker Evidence
                         |
        +----------------+
        |
        v
                Alignment Engine
                         |
                         v
                Local LLM (narrative)
                         |
                         v
                Evidence-Based Report
                         |
                         v
                  Streamlit UI
```

**Note on where the LLM sits:** claim extraction from policy text is rule-based
(fast, deterministic, no prompt-tuning needed), not LLM-based. The LLM's role
is narrower and comes after the Alignment Engine — it turns the structured
evidence (claims + tracker findings + flagged contradictions) into readable
report prose. This was a deliberate scope decision to fit a one-week build:
rule-based extraction is far less risky to get working reliably than iterating
LLM prompts under time pressure, and it keeps the "evidence, not legal
conclusions" philosophy easy to enforce, since every claim traces back to a
regex match on a specific sentence rather than a model's interpretation.

## Current Status

The project is being developed incrementally.

### Completed

- HTTP website fetching
- Website link extraction
- Privacy policy link discovery
- Privacy policy fetching
- Privacy policy text extraction
- Basic rule-based policy analysis
- Playwright browser automation
- Network request capture
- Request URL/domain extraction
- First-party / third-party classification

### Currently Working On

- EasyPrivacy integration
- Tracker/request matching
- Structured network evidence

### Future

- Cookie/consent detection
- Before-consent vs after-consent comparison
- Structured privacy-policy claims (actor/action/data/entity pattern)
- Policy vs observed behavior alignment
- SQLite audit storage
- Streamlit dashboard
- Local LLM report narrative
- Agent-based audit orchestration

## Technology Stack

| Component | Technology | Why this instead of hand-rolled code |
|---|---|---|
| Programming language | Python | — |
| HTTP crawler | Requests | — |
| HTML parsing | BeautifulSoup | — |
| Policy text extraction | **trafilatura** | Automatically strips nav/footer/boilerplate from policy pages; hand-tuned tag-stripping breaks per-site and produces the "content too short" failure mode |
| Domain classification | **tldextract** | Correctly handles multi-part suffixes (e.g. `.co.uk`) and subdomains; naive string splitting misclassifies these |
| Browser automation | Playwright | Executes JS, so it sees JS-injected trackers a raw HTTP fetch would miss |
| Browser | Chromium | — |
| Policy claim extraction | Rule-based, pattern inspired by PolicyLint's `[actor][action][data_object][entity]` sentence structure | Produces structured, polarity-aware claims ("does NOT share email with third parties") instead of flat keyword hits; simple enough to hand-code without an NLP pipeline |
| Tracker/entity knowledge | **DuckDuckGo Tracker Radar** (`entities/*.json` for ownership, `domains/*.json` for category/fingerprinting data), plus **Disconnect's `services.json`** as a lightweight fallback for domains Tracker Radar doesn't cover | Static JSON, no filter-syntax parsing needed (dropped `adblockparser`/EasyPrivacy as primary — that library is unmaintained). Solves both tracker categorization and the same-owner-different-domain problem in one dataset. Licensed CC BY-NC-SA 4.0 — cited in the report, fine for non-commercial student use. |
| Database | SQLite (stdlib `sqlite3`, no ORM) | Small enough scale that SQLAlchemy adds overhead without benefit |
| LLM | Ollama | Local, free, no API key — appropriate for a student project |
| LLM framework | LangChain | Single prompt template for report narrative generation, not multi-step chains yet |
| Dashboard | Streamlit | `st.dataframe()`/`st.json()` cover most display needs with minimal custom UI |
| Visualization | Plotly | — |

## Project Philosophy

PolicyTrace should distinguish between:

- Observed evidence
- Known information
- Unknown information
- Possible inconsistency

The system should not make unsupported statements such as:

"No tracker exists."

Instead, it should say:

"No known tracker was identified using the current detection method."

Similarly:

"Privacy policy not found"

should not automatically mean:

"The website has no privacy policy."

It means:

"The current discovery method could not confidently identify a privacy policy."

## Current Network Monitoring

Example (from a real test run):

Website: a college site

Observed:

```
Total requests: 156
First-party requests: 97
Third-party requests: 59
```

Third-party domains included Meta Pixel (`connect.facebook.net`), Facebook CDN,
and YouTube embeds — a genuine finding, not a synthetic example.

These observations are collected through Playwright.

## First Party vs Third Party

The current implementation compares the registrable domain (via `tldextract`)
of each request against the registrable domain of the site being audited.

**Known limitation, observed directly during testing — now solved:** a
site's own infrastructure spread across multiple owned domains (e.g.
`chatgpt.com` calling `cdn.openai.com` and `bzr.openai.com`) was originally
classified as third-party, even though it belongs to the same organization.
Pure domain-matching cannot tell "different domain, same owner" apart from
"different domain, actual third party."

**This is solved by DuckDuckGo Tracker Radar's entity data.** Each entity
file (e.g. `entities/Google LLC.json`) lists every domain a company owns.
Classification now checks entity ownership, not just domain strings: two
different domains are still "first-party (same owner)" if the same entity
owns both. Tested directly against the domains from a real chatgpt.com audit:
`cdn.openai.com` and `bzr.openai.com` now correctly resolve to
`first-party (same owner)` instead of being misflagged as third-party, while
`accounts.google.com` correctly stays flagged as `third-party (Google)`.

Tracker Radar's own dataset only covers ad-tech/tracking companies, so a
small `data/custom_entities/` folder (same JSON schema) supplements it for
non-tracking organizations like a site's own CDN — the same technique
Tracker Radar uses internally (`entity_map.json`), just scoped to the sites
this project actually audits.

Third-party does NOT automatically mean tracker. A third-party domain may
provide fonts, video, CDN resources, social content, analytics, advertising,
or tracking — tracker identification is a separate stage (EasyPrivacy
matching).

## Tracker Radar / entity resolution

DuckDuckGo Tracker Radar is used both to classify third-party domains by
category (advertising, analytics, social, etc. — from `domains/*.json`) and,
just as importantly, to resolve domain *ownership* (`entities/*.json`) so
that a company's own infrastructure spread across multiple domains isn't
misclassified as an unrelated third party.

Important limitation, same spirit as before:

```
Tracker Radar category match      !=   Proof of malicious tracking
No Tracker Radar match            !=   Proof that no tracking exists
```

PolicyTrace preserves this uncertainty in its reporting language.

## Example Future Report

```
Website: example.com

Privacy Policy: Found

Network Requests: 156
First-party: 97
Third-party: 59
Known filter-list matches: 3
Unknown third-party requests: 4

Potential policy inconsistency: Detected

Evidence:
  Policy claim (extracted): actor=we, action=NOT share, data=analytics
    information, entity=third parties
  Observed: a network request matched a known analytics/tracking rule
```

The system provides evidence for further investigation, not a legal
conclusion.

## Privacy

The intended architecture is local-first. Website data, browser observations,
and reports should remain on the user's computer. The project is not intended
to be a legal compliance certification system.

## Project Goals

### College Project

Demonstrate: web crawling, rule-based analysis, browser automation, network
monitoring, open-source AI, LLM integration, SQLite, Streamlit, AI agents.

### Long-Term Goal

Develop PolicyTrace into an evidence-based privacy auditing platform that can
automatically investigate discrepancies between privacy claims and observable
website behavior.

## Limitations

The project may not detect:

- Every tracking mechanism
- Tracking performed entirely inside first-party infrastructure
- Behavior hidden behind authentication
- All JavaScript-generated behavior
- All consent mechanisms
- All privacy-policy claims

Results depend on browser configuration, website state, network conditions,
filter-list coverage, policy extraction quality, and detection rules.
Therefore results should be treated as automated evidence, not legal
conclusions.