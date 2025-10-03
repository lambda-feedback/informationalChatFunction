"""
Improved prompt templates with clearer structure for LLM consumption.
Uses hierarchical organization and consistent formatting.
"""

from typing import Optional, List, Dict, Any

class PromptFormatter:
    """Centralized prompt formatting with clear structure."""
    
    @staticmethod
    def format_error_message() -> str:
        """Return structured error message."""
        return """
# ERROR: Question details unavailable

Please describe the question you're working on so I can assist you effectively.
"""

    @staticmethod
    def format_no_context_message() -> str:
        """Return structured no-context message."""
        return """
# NOTICE: Question details not provided

Please tell me about the question you're working on. I'll use British English spellings.
"""

    @staticmethod
    def format_question_header(
        set_info: Dict[str, Any],
        question_info: Dict[str, Any],
        current_part: Optional[str] = None
    ) -> str:
        """Format the main question header with metadata."""
        
        # Build title components
        title_parts = []
        if set_info.get('number') is not None and set_info.get('name'):
            title_parts.append(f"## Set {set_info['number'] + 1}: {set_info['name']}")
        
        question_num = ""
        if set_info.get('number') is not None and question_info.get('number') is not None:
            question_num = f"{set_info['number'] + 1}.{question_info['number'] + 1}"
        
        title_parts.append(f"## Question {question_num}: {question_info['title']}")
        
        # Current progress indicator
        progress_indicator = ""
        if current_part:
            progress_indicator = f"### Currently working on: Part ({current_part})"
        
        # Question metadata
        guidance = question_info.get('guidance', 'None provided')
        content = question_info.get('content', 'No description available')
        
        # Duration formatting
        duration_text = "- Expected Duration: "
        if question_info.get('duration_lower') and question_info.get('duration_upper'):
            duration_text += f"{question_info['duration_lower']}-{question_info['duration_upper']} minutes"
        else:
            duration_text += "Not specified"
        
        return f"""
# Question Context

{"\n".join(title_parts)}

{progress_indicator}

### Question Details
- Guidance: {guidance}
- Description: {content}
{duration_text}

> Note: Mathematical equations are in KaTeX format, preserve them the same. Ensure mathematical equations are surrounded by one '$' for in-line equations and '$$' for block equations. 
Example: '$E=mc^2$' or '$$E=mc^2$$'.
Use British English spellings.

---
"""

    @staticmethod
    def format_progress_summary(
        time_taken: Optional[str] = None,
        access_status: Optional[str] = None,
        marked_done: Optional[str] = None
    ) -> str:
        """Format progress and timing information."""
        if not any([time_taken, access_status, marked_done]):
            return ""
        
        progress_items = []
        if time_taken:
            progress_items.append(f"- Time spent today: {time_taken}")
        if access_status:
            progress_items.append(f"- Status: {access_status}")
        if marked_done:
            progress_items.append(f"- Completion: {marked_done}")
        
        return f"""
# Progress Summary

{"\n".join(progress_items)}

---
"""

    @staticmethod
    def format_part_header(
        part_letter: str,
        is_current: bool = False,
        time_on_part: Optional[str] = None
    ) -> str:
        """Format part header with clear indicators."""
        
        status_text = " [CURRENTLY WORKING ON]" if is_current else ""
        
        header = f"## Part ({part_letter}){status_text}"
        
        if is_current and time_on_part:
            time_display = time_on_part if time_on_part != 'No recorded duration' else 'No time recorded'
            header += f"\n\n*Time spent on this part: {time_display}*"
        
        return header

    @staticmethod
    def format_part_content(content: Optional[str]) -> str:
        """Format part content with clear labeling."""
        if not content or not content.strip():
            return "### Part Content\n\nNo content provided"
        
        return f"### Part Content\n\n{content.strip()}"

    @staticmethod
    def format_response_areas(response_areas: List[str]) -> str:
        """Format multiple response areas with clear separation."""
        if not response_areas:
            return "### Response Areas\n\nNone defined"
        
        return f"""
### Response Areas

{"\n".join(response_areas)}
"""

    @staticmethod
    def format_single_response_area(
        position: int,
        task_description: Optional[str],
        expected_answer: Any,
        student_work: Dict[str, Any]
    ) -> str:
        """Format a single response area with student work."""
        
        # Format task description
        task_text = f"- Task: {task_description}" if task_description else "- Task: Not specified"
        
        # Format expected answer (keep secret)
        answer_text = f"- Expected Answer (confidential): {expected_answer}"
        
        # Format student submissions
        submission_text = PromptFormatter._format_student_submissions(student_work)
        
        return f"""
#### Response Area {position + 1}

{task_text}
{answer_text}
{submission_text}
"""

    @staticmethod
    def _format_student_submissions(student_work: Dict[str, Any]) -> str:
        """Format student submission history."""
        if not student_work.get('has_submissions'):
            return "- Your Work: No responses submitted yet"
        
        latest = student_work.get('latest_response', 'None')
        feedback = student_work.get('latest_feedback', 'None')
        total = student_work.get('total_submissions', 0)
        wrong = student_work.get('total_wrong', 0)
        
        return f"""- Your Work:
  - Latest response: {latest}
  - Latest feedback: {feedback}
  - Total attempts: {total}
  - Incorrect attempts: {wrong}"""

    @staticmethod
    def format_part_answer(answer_content: Optional[str]) -> str:
        """Format the final part answer."""
        if not answer_content:
            return "### Final Answer\n\nNo direct answer specified for this part"
        
        return f"### Final Answer\n\n{answer_content}"

    @staticmethod
    def format_worked_solutions(solutions: List[Dict[str, Any]]) -> str:
        """Format worked solutions section."""
        if not solutions:
            return "### Worked Solutions\n\nNone available"
        
        solution_texts = []
        for i, solution in enumerate(solutions):
            title = solution.get('title', f'Solution {i + 1}')
            content = solution.get('content', '').strip() or 'No content available'
            solution_texts.append(f"#### {title}\n\n{content}")
        
        return f"""### Worked Solutions

{"\n".join(solution_texts)}"""

    @staticmethod
    def format_structured_tutorials(tutorials: List[Dict[str, Any]]) -> str:
        """Format structured tutorials section."""
        if not tutorials:
            return "### Structured Tutorials\n\nNone available"
        
        tutorial_texts = []
        for i, tutorial in enumerate(tutorials):
            title = tutorial.get('title', f'Tutorial {i + 1}')
            content = tutorial.get('content', '').strip() or 'No content available'
            tutorial_texts.append(f"#### {title}\n\n{content}")
        
        return f"""### Structured Tutorials

{"\n".join(tutorial_texts)}"""

    @staticmethod
    def format_complete_prompt(sections: List[str]) -> str:
        """Combine all sections into a complete, well-structured prompt."""
        
        intro = """
# Personalized Learning Assistant

I have detailed information about your current question, including your progress, responses, and any feedback you've received. This context helps me provide targeted assistance based on your specific situation.

"""
        
        # Filter out empty sections and join
        valid_sections = [section.strip() for section in sections if section and section.strip()]
        
        content = intro + "\n".join(valid_sections)
        
        # Clean up formatting
        content = content.replace("&#x20;&#x20;", " ").replace("&#x20", " ")
        content = "\n".join(line for line in content.split("\n") if line.strip() or not line)
        
        return content.strip()

    @staticmethod
    def get_part_letter(position: int) -> str:
        """Convert position to lowercase letter (1-indexed)."""
        return chr(96 + (position + 1))


# Legacy function wrappers for backward compatibility
def get_error_prompt() -> str:
    return PromptFormatter.format_error_message()

def get_no_context_prompt() -> str:
    return PromptFormatter.format_no_context_message()
