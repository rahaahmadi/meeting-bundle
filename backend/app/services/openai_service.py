import json
from json import JSONDecodeError

from openai import OpenAI

from app.core.config import settings
from app.schemas.schemas import GenerationResult


SYSTEM_PROMPT = """You are an assistant that turns meeting summaries into structured output.
Return valid JSON only matching this schema:
{
  \"summary\": string,
  \"crm\": {
    \"contact_type\": \"new\" | \"existing\",
    \"company\": string,
    \"contact_name\": string,
    \"contact_email\": string,
    \"recommended_services\": string,
    \"update_notes\": string,
    \"follow_up_date\": \"YYYY-MM-DD\" or null,
    \"follow_up_tasks\": string,
    \"next_step\": string
  },
  \"participant_tasks\": [{\"task_text\": string, \"is_checked\": false}],
  \"my_tasks\": [{\"task_text\": string, \"is_checked\": false}],
  \"emails\": [
    {\"template_key\": \"welcome\", \"subject\": string, \"body\": string},
    {\"template_key\": \"thank_you\", \"subject\": string, \"body\": string},
    {\"template_key\": \"next_steps\", \"subject\": string, \"body\": string},
    {\"template_key\": \"proposal_eta\", \"subject\": string, \"body\": string},
    {\"template_key\": \"follow_up_reminder\", \"subject\": string, \"body\": string}
  ]
}
Rules:
- participant_tasks = what the participant/client should do.
- my_tasks = what the meeting owner should do.
- next_step should contain concise notes for the next meeting/session.
- update_notes should emphasize important opportunities and lead progression for CRM, and must include:
  - recommended services/packages discussed by the call host
  - why each recommendation matches participant needs
  - lead progression stage or buying signals
- follow_up_tasks should include participant action items and any recommended package/service references when relevant.
- It is okay for a topic to appear in both task lists and CRM notes when useful.
- Keep language concise and practical."""


THANK_YOU_TEMPLATE_GUIDANCE = """
For the email with template_key = "thank_you", use this exact structure and fill placeholders with real values from the meeting context:

Hi {name},

Thank you so much for the fab chat today! I’ve made a note to follow up with you on [follow-up date] to check in on [their action items and suggested package they purchase].

In the meantime, I’ve included the AI summary of our meeting with action items here. [link to meeting summary]

Here are the resources I promised to send:
- [resource one]
- [resource two]
- [resource three]

Here are the action items for you to do that we discussed:
- [action item one]
- [action item two]
- [action item three]

Chat soon,

[name]

Template rules:
- Replace bracket placeholders with concrete values when known.
- If a value is unknown, keep a short editable placeholder like "<add follow-up date>".
- Include recommended services/packages in the line about suggested package purchase.
- In the thank_you email action section, include only participant_tasks.
- Do not include my_tasks / host actions in the thank_you email action section.
- Do not prefix items with "Participant:" or "Host:".
- Include all participant action items, do not omit for brevity.
"""


class OpenAIService:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=settings.openai_api_key, timeout=settings.openai_timeout_seconds)

    def generate_bundle(self, meeting_text: str) -> GenerationResult:
        response = self.client.responses.create(
            model=settings.openai_model,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "system", "content": THANK_YOU_TEMPLATE_GUIDANCE},
                {"role": "user", "content": f"Meeting summary:\n{meeting_text}"},
            ],
        )

        raw_text = (response.output_text or "").strip()
        if not raw_text:
            raise ValueError("Model returned an empty response.")

        # Allow fenced JSON responses by stripping markdown wrappers.
        if raw_text.startswith("```"):
            lines = raw_text.splitlines()
            if len(lines) >= 3 and lines[0].startswith("```") and lines[-1].strip() == "```":
                raw_text = "\n".join(lines[1:-1]).strip()
                if raw_text.lower().startswith("json"):
                    raw_text = raw_text[4:].strip()

        try:
            data = json.loads(raw_text)
        except JSONDecodeError as exc:
            raise ValueError(f"Model returned non-JSON output: {raw_text[:200]}") from exc

        return GenerationResult.model_validate(data)
