<!-- ================================================================
     TEMPLATE: menu
     PURPOSE:  Capability surface for the primary agent. Items map to
               skills the agent can invoke.
     REQUIRED: Primary agents only. Subagents have NO menu.
     NOTE:     MH and CH are always present as built-in items.
               Every skill the agent can invoke needs a menu item.

     DUAL PURPOSE:
       Menu items serve two callers:
         - INTERACTIVE: human selects an item via the question tool
         - AUTONOMOUS: dispatching caller's prompt is matched against
           the menu by the agent itself; the agent infers which item
           the request maps to and executes it directly

       Item LABELS must be specific enough that an inference engine
       (the agent in AUTONOMOUS mode) can confidently match a work
       description to one item. Vague labels create ambiguity, which
       causes the agent to emit ERROR rather than guess wrong.

       Good autonomous-inferrable labels:
         "[CA] Create a new Agent from a plan or requirements"
         "[RC] Research the codebase for navigation and locator findings"
         "[RT] Research thoughts/ for prior decisions and bundles"

       Bad autonomous-inferrable labels:
         "[CA] Agent stuff"        — too vague; could match anything
         "[R1] Research, type 1"   — opaque; inference cannot resolve
         "[CR] Create or Research" — multiple verbs; ambiguous match
     ================================================================ -->

<menu>
  <!-- BUILT-IN: These two items are standard for every primary agent. Keep them. -->
  <item cmd="MH or fuzzy match on menu or help">[MH] Redisplay Menu Help</item>
  <item cmd="CH or fuzzy match on chat">[CH] Chat with the Agent about anything</item>

  <!-- FILL: skill menu items
       Add one item per skill the agent can invoke.
       
       Format:
         <item cmd="*XX or fuzzy match on keyword" skill="skill-name">[XX] Label</item>
       
       Shortcode rules:
         - Always 2 uppercase letters
         - First letter matches action: C=Create, R=Research, A=Analyze, D=Document
         - Second letter differentiates: CA=Create Agent, CS=Create Skill
         - MH and CH are reserved (built-in)
         - Avoid confusing pairs (don't use both CA and AC)
       
       Label rules:
         - Start with action verb when possible
         - Be specific about what happens
         - Include context hints in parentheses if needed
         - Keep under 60 characters
       
       Examples:
         <item cmd="*CA or fuzzy match on create-agent" skill="agent-creator">[CA] Create a new Agent from a plan or requirements</item>
         <item cmd="*RS or fuzzy match on research" skill="deep-research">[RS] Deep Research — market, domain, or technical</item>
         <item cmd="*PB or fuzzy match on product-brief" skill="product-brief">[PB] Create a Product Brief from discovery work</item>
       
       Bad:
         <item cmd="*CA" skill="agent-creator">[CA] Agent</item>
         (label too vague — "Agent" doesn't describe what happens)
  -->
</menu>
