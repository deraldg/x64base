# LabTalk LMS Work Lane

Status: **reserved / local-only**
Candidate provider: **Moodle LMS**
Live communications: **disabled**

This lane gives LabTalk a small, explicit boundary for future learning-management
system work. Moodle is the first candidate because Moodle LMS is free and open
source and provides an external web-services framework. The lane remains
provider-neutral so a different LMS can be added without changing lesson or
portal records.

## What exists now

- a versioned `labtalk.lms.message.v1` envelope;
- a durable JSON outbox under `lms/queue/outbox`;
- a transport protocol for a future provider adapter;
- a reserved transport that prevents accidental network delivery;
- a CLI for status, outbox inspection, and controlled enqueue operations;
- a LabTalk Portal section backed by `registries/lms.yaml`.

No Moodle URL, access token, student record, grade, or live network operation is
present in this slice.

## Boundary

```text
LabTalk lesson/assignment intent
             |
             v
labtalk.lms.message.v1
             |
             v
local JSON outbox  --->  reserved transport  -X->  Moodle web services
                                                future, separately approved
```

Queue files are integration artifacts, not proof that Moodle accepted an
operation. A future adapter must produce a provider receipt before LabTalk marks
delivery as successful.

## Simple interface

From `D:/code/ccode/labtalk`:

```powershell
python ..\src\labtalk\lms\cli.py --queue .\lms\queue\outbox status
python ..\src\labtalk\lms\cli.py --queue .\lms\queue\outbox list
```

Queue a harmless development envelope:

```powershell
python ..\src\labtalk\lms\cli.py `
  --queue .\lms\queue\outbox `
  enqueue `
  --operation course.preview `
  --subject '{"course_key":"database-literacy"}' `
  --payload '{"title":"Database Literacy Starter"}'
```

The portal exposes the status command as **LMS -> Check LMS Pipe Status** and
captures its output as a normal LabTalk proof transcript.

## Future Moodle adapter gates

Before live delivery is implemented:

1. Select and administer a Moodle site.
2. Approve the exact Moodle web-service functions LabTalk may call.
3. Map each LabTalk operation to one approved Moodle function.
4. Store the Moodle token outside source control and logs.
5. Add retry, idempotency, receipt, redaction, and audit behavior.
6. Add a sandbox integration test before enabling student or grade data.

Moodle references:

- https://moodle.com/solutions/lms/
- https://moodledev.io/docs/5.0/apis/subsystems/external
