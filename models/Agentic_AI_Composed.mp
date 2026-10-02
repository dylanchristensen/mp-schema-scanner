/* ═══════════════════════════════════════════════════════════════
   Agentic AI Tool-Orchestration — SoS Model
   NSA INSuRE+C | Summer 2026
   Dylan Christensen, Victor Sanchez

   Composed 8-ROOT model of an LLM agent orchestrating third-party
   tools. Under the Model Context Protocol the tools are independent
   servers owned and assured by different parties, so "independently
   owned components no single owner controls" is literal, not analogy.

   Sources:
     - Model Context Protocol (MCP): open standard for agent<->tool/data servers
     - OWASP Top 10 for LLM Applications: LLM01 Prompt Injection,
       LLM08 Excessive Agency, LLM06 Sensitive Information Disclosure
     - NIST AI 600-1 (Generative AI Profile): agent autonomy risks
     - Willison, "the lethal trifecta" (2025): private data + untrusted
       content + external communication -> exfiltration

   Components:
     - Orchestrator   -- the planning LLM (decomposes, dispatches tool calls)
     - Data           -- data the agent has loaded (public/private/secrets)
     - Content_Source -- provenance of ingested content (trusted/untrusted/tool)
     - Tool           -- a privileged tool call (read / external send / code exec)
     - Guardrail      -- safety/policy filter (enforce / block / advisory / bypass)
     - Memory         -- context and persistent memory store
     - Privilege      -- privilege the agent runs under (user/elevated/delegated)
     - Sub_Agent      -- a delegated agent the orchestrator spawns
═══════════════════════════════════════════════════════════════ */

SCHEMA Agentic_AI

/* ═══════════════════════════════════════════
   ROOT COMPONENTS
═══════════════════════════════════════════ */

ROOT Orchestrator :
    ( agent_waiting | agent_planning | agent_running | agent_delegating );

ROOT Data :
    ( data_none | data_public | data_private | data_secrets );

ROOT Content_Source :
    ( content_none | content_trusted | content_untrusted | content_tool_output );

ROOT Tool :
    ( tool_idle | tool_read | tool_send | tool_execute );

ROOT Guardrail :
    ( guard_enforcing | guard_blocking | guard_advisory | guard_bypassed );

ROOT Memory :
    ( memory_clean | memory_tainted | memory_persistent );

ROOT Privilege :
    ( priv_user | priv_elevated | priv_delegated );

ROOT Sub_Agent :
    ( subagent_idle | subagent_running | subagent_hijacked );

/* ═══════════════════════════════════════════
   COMPONENT BEHAVIORS (state -> events)
═══════════════════════════════════════════ */

/* --- Orchestrator --- */
agent_waiting :
    awaiting_user_request;
agent_planning :
    task_decomposed
    plan_formed;
agent_running :
    tool_calls_dispatched
    plan_in_progress;
agent_delegating :
    subtask_assigned
    delegation_dispatched;

/* --- Data --- */
data_none :
    no_data_loaded;
data_public :
    public_records_loaded;
data_private :
    private_records_loaded
    sensitive_context_present;
data_secrets :
    credentials_loaded
    api_keys_in_context;

/* --- Content_Source (OWASP LLM01) --- */
content_none :
    no_external_input;
content_trusted :
    vetted_content_ingested;
content_untrusted :
    web_content_ingested
    injected_instructions_present;
content_tool_output :
    tool_output_ingested
    unvetted_tool_result;

/* --- Tool (OWASP LLM08) --- */
tool_idle :
    no_action_taken;
tool_read :
    read_only_call;
tool_send :
    outbound_message_sent
    egress_channel_used;
tool_execute :
    code_executed
    shell_command_run;

/* --- Guardrail --- */
guard_enforcing :
    policy_scan_active
    action_approved;
guard_blocking :
    violation_flagged
    action_denied;
guard_advisory :
    advisory_logged;
guard_bypassed :
    guardrail_disabled;

/* --- Memory --- */
memory_clean :
    fresh_context;
memory_tainted :
    untrusted_retained_in_context;
memory_persistent :
    persistent_memory_written
    cross_session_state;

/* --- Privilege --- */
priv_user :
    user_privileges;
priv_elevated :
    elevated_privileges_active;
priv_delegated :
    delegated_token_active;

/* --- Sub_Agent --- */
subagent_idle :
    subagent_dormant;
subagent_running :
    subagent_executing;
subagent_hijacked :
    subagent_following_injected
    injection_propagated;

/* ═══════════════════════════════════════════
   ORDERING CONSTRAINTS (ENSURE FOREACH)
═══════════════════════════════════════════ */

/* A policy scan must run before an approval is issued (within Guardrail). */
ENSURE FOREACH $s: policy_scan_active, $a: action_approved
    ($s BEFORE $a);

/* ═══════════════════════════════════════════
   PRESENCE CONSTRAINTS (REJECT)
═══════════════════════════════════════════ */

/* An effector cannot act unless the orchestrator dispatched calls or delegated. */
IF #outbound_message_sent > 0
    AND #tool_calls_dispatched == 0
    AND #delegation_dispatched == 0 THEN
    REJECT;
FI;

IF #code_executed > 0
    AND #tool_calls_dispatched == 0
    AND #delegation_dispatched == 0 THEN
    REJECT;
FI;

IF #read_only_call > 0
    AND #tool_calls_dispatched == 0
    AND #delegation_dispatched == 0 THEN
    REJECT;
FI;

/* Loading credentials requires elevated or delegated privilege. */
IF #credentials_loaded > 0
    AND #elevated_privileges_active == 0
    AND #delegated_token_active == 0 THEN
    REJECT;
FI;

/* Code execution requires elevated or delegated privilege. */
IF #code_executed > 0
    AND #elevated_privileges_active == 0
    AND #delegated_token_active == 0 THEN
    REJECT;
FI;

/* A sub-agent can only run if the orchestrator delegated to it. */
IF #subagent_executing > 0 AND #delegation_dispatched == 0 THEN
    REJECT;
FI;

IF #injection_propagated > 0 AND #delegation_dispatched == 0 THEN
    REJECT;
FI;

/* An approval cannot be issued without a policy scan. */
IF #action_approved > 0 AND #policy_scan_active == 0 THEN
    REJECT;
FI;

/* An action cannot be denied without a flagged violation. */
IF #action_denied > 0 AND #violation_flagged == 0 THEN
    REJECT;
FI;

/* Persistent memory can only be written during active execution. */
IF #persistent_memory_written > 0 AND #tool_calls_dispatched == 0 THEN
    REJECT;
FI;

/* ═══════════════════════════════════════════
   CROSS-COMPONENT COORDINATION (COORDINATE ... PRECEDES)
   Sequences approval ahead of the action WHEN BOTH occur, without
   excluding the approved-action path (a bare cross-ROOT BEFORE would
   delete it, leaving a guardrail that can never approve anything).
═══════════════════════════════════════════ */

/* The guardrail approves before an outbound action leaves the system. */
IF #action_approved > 0 AND #outbound_message_sent > 0 THEN
    COORDINATE $a : action_approved       FROM Guardrail,
               $e : outbound_message_sent FROM Tool
        DO ADD $a PRECEDES $e; OD;
FI;

/* The guardrail approves before code is executed. */
IF #action_approved > 0 AND #code_executed > 0 THEN
    COORDINATE $a : action_approved FROM Guardrail,
               $c : code_executed   FROM Tool
        DO ADD $a PRECEDES $c; OD;
FI;

/* NOTE (intended-but-UNWRITTEN -- the emergent behaviors the flags recover):
   no rule forbids the "lethal trifecta": private data (or secrets) +
   untrusted content (or tool output) + external egress (or code exec)
   co-occurring in one execution. The composition is an exfiltration
   channel; no component fails. */