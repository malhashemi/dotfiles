<investigation-methodologies>

<overview>
A comprehensive investigation selects ONE methodology by the shape of
the research question. The methodology supplies two things: the
sub-question generators (what to decompose the question into) and the
section structure (how the synthesized document is organized). Each
sub-question routes to a child subagent per child-subagent-dispatch.
</overview>

<selection>
Match the question shape to a methodology. When a question spans
shapes, pick the dominant one and fold secondary concerns in as
sub-questions. When nothing fits cleanly, use `general`.

| Question shape | Methodology |
|---|---|
| "industry / sector analysis of X" | domain |
| "market for X; customers; competitors" | market |
| "X vs Y technology; how to architect Z; should we adopt W" | technical |
| "how does our {system} work; trace X end-to-end in our code" | codebase |
| anything that fits none cleanly | general |
</selection>

<methodology name="domain">
  <when>Industry or sector landscape; the question is about a market space, not a product or a codebase.</when>
  <sub-questions>
    - Industry structure: key players, value chain, market size (web)
    - Regulatory environment: compliance regimes, standards, legal constraints (web)
    - Technology trends: innovation patterns, adoption curves (web)
    - Economic factors: growth, cost structures, margins (web)
    - Supply chain / ecosystem: partnerships, dependencies (web)
  </sub-questions>
  <sections>Industry Structure · Regulatory Environment · Technology Trends · Economic Factors · Supply Chain &amp; Ecosystem</sections>
</methodology>

<methodology name="market">
  <when>Customers and competition for a product or category; who buys, why, and who else sells.</when>
  <sub-questions>
    - Customer behavior &amp; segments: demographics, psychographics (web)
    - Customer pain points: unmet needs, friction (web)
    - Customer decision drivers: what triggers purchase, switching costs (web)
    - Competitive landscape: key players, positioning, share (web)
  </sub-questions>
  <sections>Customer Behavior &amp; Segments · Customer Pain Points · Decision Drivers · Competitive Landscape</sections>
</methodology>

<methodology name="technical">
  <when>Technology selection, architecture, or adoption; "X vs Y", "how to build Z", "should we use W".</when>
  <sub-questions>
    - Technology landscape: candidate languages, frameworks, tools (web; codebase-pattern-finder if comparing to current stack)
    - Integration patterns: APIs, protocols, interoperability (web)
    - Architectural patterns: structure, scalability, tradeoffs (web)
    - Implementation approaches: adoption strategy, migration, tooling (web; codebase-analyzer for current-state grounding)
  </sub-questions>
  <sections>Technology Landscape · Integration Patterns · Architectural Patterns · Implementation Approaches</sections>
</methodology>

<methodology name="codebase">
  <when>How our own system works; tracing behavior, mapping a feature, reconstructing a subsystem end-to-end.</when>
  <sub-questions>
    - Where does it live: files, modules, entry points (codebase-locator)
    - How does it work: control flow, data flow, integrations (codebase-analyzer)
    - What patterns surround it: similar implementations, conventions (codebase-pattern-finder)
    - What have we decided about it: prior tickets, research, PRs (thoughts-locator then thoughts-analyzer)
  </sub-questions>
  <sections>Detailed Findings (by component) · Code References · Architecture Insights · Historical Context (from thoughts/)</sections>
</methodology>

<methodology name="general">
  <when>The question fits no specialized methodology; decompose on its own terms.</when>
  <sub-questions>
    - Decompose the question into 2-5 independent sub-questions, each routed to the child whose shape matches it per child-subagent-dispatch.
  </sub-questions>
  <sections>Findings by Sub-Topic · Cross-Cutting Themes</sections>
</methodology>

<waves>
Sub-questions that are independent run in the same wave (parallel child
dispatch). A sub-question that depends on a prior finding (e.g.,
thoughts-analyzer needs the artifact paths thoughts-locator surfaces)
runs in a later wave. Most investigations are one or two waves.
</waves>

</investigation-methodologies>
