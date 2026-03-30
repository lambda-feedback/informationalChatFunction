from typing import Optional, Dict, Any, List

from src.agent.prompts import response_format_prompt


def parse_json_to_prompt(context: dict, task_progress: dict) -> str:
    """Convert muEd context and task progress directly into an LLM-friendly prompt string."""

    question = context.get("question")
    if not question:
        return "# ERROR: Question details unavailable\n\nPlease describe the question you're working on so I can assist you effectively."

    set_data = context.get("set", {})
    current_part = task_progress.get("currentPart", {}) if task_progress else {}
    current_part_position = current_part.get("position")
    submissions = current_part.get("responseAreas", [])

    sections = []

    # 1. Question header
    title_parts = []
    set_number = set_data.get("number")
    if set_number is not None and set_data.get("title"):
        title_parts.append(f"## Set {set_number + 1}: {set_data['title']}")

    question_num = ""
    q_number = question.get("number")
    if set_number is not None and q_number is not None:
        question_num = f"{set_number + 1}.{q_number + 1}"
    title_parts.append(f"### Question {question_num}: {question.get('title', '')}")

    current_part_letter = _part_letter(current_part_position) if current_part_position is not None else ""
    progress_indicator = f"Currently working on: Part ({current_part_letter})" if current_part_letter else ""

    estimated_time = question.get("estimatedTime", "Not specified")
    sections.append(f"""
# Question Context

{chr(10).join(title_parts)}

{progress_indicator}

### Question Details
- Guidance: {question.get('guidance') or 'None provided'}
- Description: {question.get('content') or 'No description available'}
- Expected Duration: {estimated_time}

---
""")

    # 2. Progress summary
    if task_progress:
        progress_items = []
        if task_progress.get("timeSpentOnQuestion"):
            progress_items.append(f"- Time spent today: {task_progress['timeSpentOnQuestion']}")
        if task_progress.get("accessStatus"):
            progress_items.append(f"- Status: {task_progress['accessStatus']}")
        if task_progress.get("markedDone"):
            progress_items.append(f"- Completion: {task_progress['markedDone']}")
        if progress_items:
            sections.append(f"\n## Progress Summary\n\n{chr(10).join(progress_items)}\n\n---\n")

    # 3. Parts
    for i, part in enumerate(question.get("parts", [])):
        part_position = part.get("position", i)
        is_current = current_part_position == part_position
        time_on_part = current_part.get("timeSpentOnPart") if is_current else None
        sections.append(_format_part(part, part_position, is_current, time_on_part, submissions))

    # Combine
    intro = (
        "\n# Personalized Learning Assistant\n\n"
        "I have detailed information about your current question, including your progress, responses, "
        "and any feedback you've received. This context helps me provide targeted assistance based on "
        "your specific situation.\n\n"
    )
    valid_sections = [s.strip() for s in sections if s and s.strip()]
    response_format = (
        "# Response Formatting\n" + response_format_prompt
        if response_format_prompt
        else ""
    )
    content = intro + "\n".join(valid_sections) + "\n" + response_format
    content = content.replace("&#x20;&#x20;", " ").replace("&#x20", " ")
    return "\n".join(line for line in content.split("\n") if line.strip() or not line).strip()


def _part_letter(position: int) -> str:
    return chr(96 + (position + 1))

def _format_part(part: dict, part_position: int, is_current: bool, time_on_part: Optional[str], submissions: list) -> str:
    letter = _part_letter(part_position)
    status_text = " [CURRENTLY WORKING ON]" if is_current else ""
    header = f"## Part ({letter}){status_text}"
    if is_current and time_on_part and time_on_part != "No recorded duration":
        header += f"\n\n*Time spent on this part: {time_on_part}*"

    content_text = part.get("content", "").strip()
    content = f"### Part Content\n\n{content_text}" if content_text else "### Part Content\n\nNo content provided"

    response_areas = []
    for j, ra in enumerate(part.get("responseAreas", [])):
        ra_position = ra.get("position", j)
        student_work = _get_student_work(ra_position, submissions)
        response_areas.append(_format_response_area(ra_position, ra.get("preResponseText"), ra.get("answer"), student_work))
    ra_block = f"\n### Response Areas\n\n{''.join(response_areas)}" if response_areas else ""

    answer = part.get("answerContent")
    answer_block = f"### Final Answer\n\n{answer}" if answer else "### Final Answer\n\nNo direct answer specified for this part"

    solutions = [
        f"{ws.get('title', f'#### Solution {i+1}')}\n\n{ws.get('content', '').strip() or 'No content available'}"
        for i, ws in enumerate(part.get("workedSolutionSections", []))
    ]
    solutions_block = "### Worked Solutions\n\n" + "\n".join(solutions) if solutions else "### Worked Solutions\n\nNone available"

    tutorials = [
        f"{ts.get('title', f'#### Tutorial {i+1}')}\n\n{ts.get('content', '').strip() or 'No content available'}"
        for i, ts in enumerate(part.get("structuredTutorialSections", []))
    ]
    tutorials_block = "### Structured Tutorials\n\n" + "\n".join(tutorials) if tutorials else "### Structured Tutorials\n\nNone available"

    return "\n".join([header, content, ra_block, answer_block, solutions_block, tutorials_block]) + "\n---\n"

def _get_student_work(ra_position: int, submissions: list) -> Dict[str, Any]:
    if ra_position < len(submissions):
        s = submissions[ra_position]
        latest = s.get("latestSubmission") or {}
        if latest:
            return {
                "has_submissions": True,
                "latest_response": latest.get("submission"),
                "latest_feedback": latest.get("feedback"),
                "total_submissions": s.get("totalSubmissions"),
                "total_wrong": s.get("wrongSubmissions"),
            }
    return {"has_submissions": False}

def _format_response_area(position: int, task_description: Optional[str], expected_answer: Any, student_work: Dict[str, Any]) -> str:
    task_text = f"- Task: {task_description}" if task_description else "- Task: Not specified"
    if not student_work.get("has_submissions"):
        submission_text = "- Your Work on this response area: No response submitted yet"
    else:
        submission_text = (
            f"- Your Work on this response area:\n"
            f"  - Latest response: {student_work.get('latest_response', 'None')}\n"
            f"  - Latest feedback: {student_work.get('latest_feedback', 'None')}\n"
            f"  - Total attempts: {student_work.get('total_submissions', 0)} out of which {student_work.get('total_wrong', 0)} were incorrect"
        )
    return (
        f"\n#### Response Area {position + 1}\n\n"
        f"{task_text}\n"
        f"- Expected Answer (confidential): {expected_answer}\n"
        f"{submission_text}\n"
    )
