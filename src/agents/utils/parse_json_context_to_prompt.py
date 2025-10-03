"""
Refactored JSON to prompt parser using improved, clearer structure.
"""

from typing import List, Optional, Dict, Any, Union
from .prompt_context_templates import PromptFormatter

# Definitions questionSubmissionSummary type
class StudentLatestSubmission:
    def __init__(
        self,
        universalResponseAreaId: Optional[str] = None,
        answer: Optional[str] = None,
        submission: Optional[str] = None,
        feedback: Optional[str] = None,
        rawResponse: Optional[dict] = None,
    ):
        self.universalResponseAreaId = universalResponseAreaId
        self.answer = answer
        self.submission = submission
        self.feedback = feedback
        self.rawResponse = rawResponse

class StudentWorkResponseArea:
    def __init__(
        self,
        publishedPartId: Optional[str] = None,
        publishedPartPosition: Optional[int] = None,
        publishedResponseAreaId: Optional[str] = None,
        publishedResponseAreaPosition: Optional[int] = None,
        responseAreaUniversalId: Optional[str] = None,
        publishedResponseAreaPreResponseText: Optional[str] = None,
        publishedResponseType: Optional[str] = None,
        publishedResponseConfig: Optional[dict] = None,
        totalSubmissions: Optional[int] = None,
        totalWrongSubmissions: Optional[int] = None,
        latestSubmission: Optional[StudentLatestSubmission] = None,
    ):
        self.publishedPartId = publishedPartId
        self.publishedPartPosition = publishedPartPosition
        self.publishedResponseAreaId = publishedResponseAreaId
        self.publishedResponseAreaPosition = publishedResponseAreaPosition
        self.responseAreaUniversalId = responseAreaUniversalId
        self.publishedResponseAreaPreResponseText = publishedResponseAreaPreResponseText
        self.publishedResponseType = publishedResponseType
        self.publishedResponseConfig = publishedResponseConfig
        self.latestSubmission = StudentLatestSubmission(**latestSubmission) if latestSubmission else None
        self.totalSubmissions = totalSubmissions
        self.totalWrongSubmissions = totalWrongSubmissions

# questionInformation type
class ResponseAreaDetails:
    def __init__(
        self,
        id: Optional[str] = None,
        position: Optional[int] = None,
        universalResponseAreaId: Optional[str] = None,
        preResponseText: Optional[str] = None,
        responseType: Optional[str] = None,
        answer: Optional[dict] = None,
        Response: Optional[dict] = None,
    ):
        self.id = id
        self.position = position
        self.universalResponseAreaId = universalResponseAreaId
        self.preResponseText = preResponseText
        self.responseType = responseType
        self.answer = answer
        self.Response = Response

class PartDetails:
    def __init__(
        self,
        publishedPartId: Optional[str] = None,
        publishedPartPosition: Optional[int] = None,
        publishedPartContent: Optional[str] = None,
        publishedPartAnswerContent: Optional[str] = None,
        publishedWorkedSolutionSections: Optional[List[dict]] = [],
        publishedStructuredTutorialSections: Optional[List[dict]] = [],
        publishedResponseAreas: Optional[List[Optional[ResponseAreaDetails]]] = [],
    ):
        self.publishedPartId = publishedPartId
        self.publishedPartPosition = publishedPartPosition
        self.publishedPartContent = publishedPartContent
        self.publishedPartAnswerContent = publishedPartAnswerContent
        self.publishedWorkedSolutionSections = publishedWorkedSolutionSections
        self.publishedStructuredTutorialSections = publishedStructuredTutorialSections
        self.publishedResponseAreas = [ResponseAreaDetails(**publishedResponseArea) for publishedResponseArea in publishedResponseAreas]

class QuestionDetails:
    def __init__(
        self,
        setNumber: Optional[int] = None,
        setName: Optional[str] = None,
        setDescription: Optional[str] = None,
        questionNumber: Optional[int] = None,
        questionTitle: Optional[str] = None,
        questionGuidance: Optional[str] = None,
        questionContent: Optional[str] = None,
        durationLowerBound: Optional[int] = None,
        durationUpperBound: Optional[int] = None,
        parts: Optional[List[PartDetails]] = [],
    ):
        self.setNumber = setNumber
        self.setName = setName
        self.setDescription = setDescription
        self.questionNumber = questionNumber
        self.questionTitle = questionTitle
        self.questionGuidance = questionGuidance
        self.questionContent = questionContent
        self.durationLowerBound = durationLowerBound
        self.durationUpperBound = durationUpperBound
        self.parts = [PartDetails(**part) for part in parts] 

# questionAccessInformation type
class CurrentPart:
    def __init__(
        self, 
        id: str = None, 
        position: int = None, 
        universalPartId: Optional[str] = None,
        timeTakenPart: Optional[str] = None, 
        markedDonePart: Optional[str] = None
    ):
        self.id = id
        self.position = position
        self.universalPartId = universalPartId
        self.timeTakenPart = timeTakenPart
        self.markedDonePart = markedDonePart

class QuestionAccessInformation:
    def __init__(
        self,
        estimatedMinimumTime: Optional[str] = None,
        estimaredMaximumTime: Optional[str] = None,
        timeTaken: Optional[str] = None,
        accessStatus: Optional[str] = None,
        markedDone: Optional[str] = None,
        currentPart: Optional[Dict[str, Union[str, int]]] = {},
    ):
        self.estimatedMinimumTime = estimatedMinimumTime
        self.estimaredMaximumTime = estimaredMaximumTime
        self.timeTaken = timeTaken
        self.accessStatus = accessStatus
        self.markedDone = markedDone
        self.currentPart = CurrentPart(**currentPart)


def parse_json_to_structured_prompt(
    question_submission_summary: Optional[List[StudentWorkResponseArea]],
    question_information: Optional[QuestionDetails],
    question_access_information: Optional[QuestionAccessInformation]
) -> Optional[str]:
    """
    Parse JSON data into a well-structured, LLM-friendly prompt.
    
    Args:
        question_submission_summary: Student's work and submissions
        question_information: Question details and structure
        question_access_information: Current progress and timing info
        
    Returns:
        Formatted prompt string or error message
    """
    
    if not question_information:
        return PromptFormatter.format_error_message()
    
    # Convert to proper objects
    submission_summary = [StudentWorkResponseArea(**summary) for summary in question_submission_summary]
    question_info = QuestionDetails(**question_information)
    access_info = QuestionAccessInformation(**question_access_information) if question_access_information else None
    
    # TODO: EXPERIMENTAL - Remove later
    # if question_info.setNumber is not None:
    #     if (question_info.setNumber + 1) % 2 != 0:
    #         return PromptFormatter.format_no_context_message()
    
    # Build prompt sections
    sections = []
    
    # 1. Question Header
    current_part_letter = None
    if access_info and access_info.currentPart:
        current_part_letter = PromptFormatter.get_part_letter(access_info.currentPart.position)
    
    set_info = {
        'number': question_info.setNumber,
        'name': question_info.setName
    }
    
    question_data = {
        'number': question_info.questionNumber,
        'title': question_info.questionTitle,
        'guidance': question_info.questionGuidance,
        'content': question_info.questionContent,
        'duration_lower': question_info.durationLowerBound,
        'duration_upper': question_info.durationUpperBound
    }
    
    sections.append(PromptFormatter.format_question_header(
        set_info, 
        question_data, 
        current_part_letter
    ))
    
    # 2. Progress Summary (if available)
    if access_info:
        progress_section = PromptFormatter.format_progress_summary(
            access_info.timeTaken,
            access_info.accessStatus,
            access_info.markedDone
        )
        if progress_section:
            sections.append(progress_section)
    
    # 3. Parts Details
    for part in question_info.parts:
        sections.append(_format_single_part(
            part, 
            access_info.currentPart if access_info else None,
            submission_summary
        ))
    
    # 4. Combine into final prompt
    return PromptFormatter.format_complete_prompt(sections)


def _format_single_part(
    part: PartDetails, 
    current_part: Optional[CurrentPart],
    submissions: List[StudentWorkResponseArea]
) -> str:
    """Format a single part with all its components."""
    
    if not part:
        return ""
    
    part_sections = []
    part_letter = PromptFormatter.get_part_letter(part.publishedPartPosition)
    
    # Determine if this is the current part
    is_current = current_part and current_part.id == part.publishedPartId
    time_on_part = current_part.timeTakenPart if is_current and current_part else None
    
    # 1. Part Header
    part_sections.append(PromptFormatter.format_part_header(
        part_letter, 
        is_current, 
        time_on_part
    ))
    
    # 2. Part Content
    part_sections.append(PromptFormatter.format_part_content(part.publishedPartContent))
    
    # 3. Response Areas
    response_areas = []
    for response_area in part.publishedResponseAreas:
        student_work = _extract_student_work_for_area(response_area, submissions)
        response_areas.append(PromptFormatter.format_single_response_area(
            response_area.position,
            response_area.preResponseText,
            response_area.answer,
            student_work
        ))
    
    if response_areas:
        part_sections.append(PromptFormatter.format_response_areas(response_areas))
    
    # 4. Final Part Answer
    part_sections.append(PromptFormatter.format_part_answer(part.publishedPartAnswerContent))
    
    # 5. Worked Solutions
    solutions_data = []
    if part.publishedWorkedSolutionSections:
        for ws in part.publishedWorkedSolutionSections:
            solutions_data.append({
                'title': ws.get('title', ''),
                'content': ws.get('content', ''),
                'position': ws.get('position', 0)
            })

    #  6. Structured Tutorial Sections
    tutorial_data = []
    if part.publishedStructuredTutorialSections:
        for ts in part.publishedStructuredTutorialSections:
            tutorial_data.append({
                'title': ts.get('title', ''),
                'content': ts.get('content', ''),
                'position': ts.get('position', 0)
            })
    
    part_sections.append(PromptFormatter.format_worked_solutions(solutions_data))
    part_sections.append(PromptFormatter.format_structured_tutorials(tutorial_data))

    return "\n".join(part_sections) + "\n---\n"


def _extract_student_work_for_area(
    response_area: ResponseAreaDetails, 
    submissions: List[StudentWorkResponseArea]
) -> Dict[str, Any]:
    """Extract student work data for a specific response area."""
    
    for submission in submissions:
        if (submission.publishedResponseAreaId == response_area.id and 
            submission.latestSubmission):
            
            return {
                'has_submissions': True,
                'latest_response': submission.latestSubmission.submission,
                'latest_feedback': submission.latestSubmission.feedback,
                'total_submissions': submission.totalSubmissions,
                'total_wrong': submission.totalWrongSubmissions
            }
    
    return {'has_submissions': False}


# Convenience function that maintains the original interface
def parse_json_to_prompt(
    questionSubmissionSummary: Optional[List[StudentWorkResponseArea]],
    questionInformation: Optional[QuestionDetails],
    questionAccessInformation: Optional[QuestionAccessInformation]
) -> Optional[str]:
    """
    Legacy wrapper for backward compatibility.
    Recommended to use parse_json_to_structured_prompt for new code.
    """
    return parse_json_to_structured_prompt(
        questionSubmissionSummary,
        questionInformation,
        questionAccessInformation
    )
