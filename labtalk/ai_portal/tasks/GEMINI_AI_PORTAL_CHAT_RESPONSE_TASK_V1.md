# Gemini Task Packet — Respond to ChatGPT Through AI Portal Chat v1

Status: **Assigned**  
Assignee: **Gemini**  
Recipient: **ChatGPT / BETA_Work**  
Maintainer: **Derald**  
Task ID: `task.ai_portal.gemini_chat_response.v1`  
Thread ID: `chat.ai_portal.gemini_to_chatgpt.20260722.v1`

## Authority and Baseline

```text
Authoritative development source: D:\code\ccode
Curated publication staging:     C:\x64base
Public repository:                https://github.com/deraldg/x64base
Public branch:                    main
Code/context baseline:            45de569abab982dea744850b673aa26351611d2d
AI Portal entry:                  https://github.com/deraldg/x64base/blob/main/AI_PORTAL.md
Chat thread:                      labtalk/ai_portal/chat/threads/CHAT_GEMINI_TO_CHATGPT_20260722_V1.md
```

The public repository is the context available to Gemini. It is not stronger or
newer authority than the current contents of `D:/code/ccode`.

## Assignment

Gemini shall perform a small cross-agent communication test:

1. read the AI Portal entry and the mandatory authority/SDLC material required for
   this task;
2. read the chat thread named above;
3. prepare a concise structured response addressed to
   `assistant.openai.chatgpt.beta_work` and copied to `human.derald`;
4. submit that response through the AI Portal chat using the exact thread ID;
5. state honestly whether direct portal-chat delivery succeeded.

Gemini must not answer only inside its own provider-hosted conversation and call
the task complete. The response must enter the AI Portal communication lane, or
Gemini must report `delivery_blocked` using the required envelope.

## Questions Gemini Must Answer

1. What exact AI Portal and authority files did Gemini read?
2. Can Gemini post directly to the specified AI Portal chat thread?
3. Was the response actually entered into that thread?
4. What is the smallest missing capability, if delivery was blocked?
5. What one improvement would make cross-agent task responses more reliable while
   preserving Derald's authority and the public/local source distinction?

## Required Response Route

Primary route:

```text
AI Portal chat
thread_id: chat.ai_portal.gemini_to_chatgpt.20260722.v1
recipient: assistant.openai.chatgpt.beta_work
cc: human.derald
```

The response format is defined in:

```text
labtalk/ai_portal/chat/threads/CHAT_GEMINI_TO_CHATGPT_20260722_V1.md
```

If Gemini cannot access a portal chat write action, it must:

- use `status: delivery_blocked`;
- return the complete response envelope to Derald without changing its routing
  fields;
- identify the unavailable action or interface;
- refrain from claiming successful delivery;
- recommend the smallest concrete remedy.

## Required Reads

At minimum:

- `AI_README.md`
- `AI_PORTAL.md`
- `labtalk/ai_portal/README.md`
- `labtalk/ai_portal/SDLC_FAST_START_SEED_V1.md`
- `labtalk/ai_portal/DEVELOPMENT_FLOW_AUTHORITY_SEEDS_V1.md`
- `labtalk/ai_portal/AI_REPORT_AUDIT_CONTRACT_V1.md`
- `labtalk/ai_portal/EXTERNAL_AI_CHANGE_PACKAGE_V1.md`
- `labtalk/ai_portal/chat/threads/CHAT_GEMINI_TO_CHATGPT_20260722_V1.md`
- `labtalk/registries/ai_portal_tasks.yaml`

Gemini must list only files actually read.

## SDLC Envelope

```text
id: task.ai_portal.gemini_chat_response.v1
title: Respond to ChatGPT through the AI Portal chat
area: labtalk/ai_portal/chat/cross-agent-communication
owning_lifecycle: LabTalk SDLC / AI Portal hardening lane
sdlc_lane: proof
truth_state: requested_chat_route_defined_live_cross-provider_delivery_unproven
proof_state: awaiting_round_trip_response
risk_class: low
source_path: D:/code/ccode/labtalk/ai_portal
website_path: unknown
next_gate: Gemini posts the response or returns a delivery_blocked envelope; Derald then asks ChatGPT to read and acknowledge it
owner: Gemini
status: assigned
```

## Allowed Scope

- reading the public AI Portal and task artifacts;
- posting one structured response to the named AI Portal chat thread;
- reporting delivery capability and limitations;
- recommending one bounded improvement to the response route.

## Excluded Scope

- source-code changes;
- DBF, index, LMDB, HELP, metadata, or runtime-data mutation;
- branch creation or switching;
- commit, push, staging promotion, or publication;
- secrets, credentials, private data, or raw-chat archival;
- claims that ChatGPT received the response unless the portal route confirms it;
- claims of autonomous or background inter-provider communication.

## Completion Criteria

The task is complete only when one of these states is recorded:

### `responded`

- Gemini's envelope is present in the named AI Portal chat thread;
- sender, recipient, task ID, thread ID, provider/product/model, files read, proof
  boundary, and next action are present;
- Derald can direct ChatGPT to read the thread.

### `delivery_blocked`

- Gemini supplies the complete envelope to Derald;
- the exact missing portal action or interface is identified;
- no successful-delivery claim is made;
- the task remains open for relay or portal implementation.

## ChatGPT Readback

The receiving identity is the current ChatGPT operator assisting Derald in the
`BETA_Work` project context. ChatGPT does not poll asynchronously. After Gemini's
response is posted or relayed, Derald must ask ChatGPT to read the named thread.
ChatGPT will then acknowledge the response and identify the next gate.
