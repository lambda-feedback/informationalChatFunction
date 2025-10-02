"""
## Synthetic Dataset Generator ##
-> GOAL: Generate a synthetic dataset of conversations between a tutor and a student [both LLMs].

For each question/scenario example in the example_inputs folder, a pipeline of two agents will be invoked. 
The agents will play the role of a tutor and a student conversing about the question/scenario.

The conversations will be 20 turns long, with the tutor and student taking turns to send a message.

The tutor can be one of the following types:
- Informational Agent (base)
The tutor agent can be selected by changing the "agent_type" field in this script.

The student can have multiple skill levels and conversational styles. Those are defined by the prompts used by the LLM.

Any of the models accessible through the API calls defined in the 'llm_factory.py' can be used for either the tutor and the agent LLM.
"""

import csv
import json
try:
  from ..student_agent.student_agent import invoke_student_agent
  from .parse_json_context_to_prompt import parse_json_to_prompt
  from ..base_agent.base_agent import invoke_base_agent
except ImportError:
  from src.agents.student_agent.student_agent import invoke_student_agent
  from src.agents.utils.parse_json_context_to_prompt import parse_json_to_prompt
  from src.agents.base_agent.base_agent import invoke_base_agent
import os


def generate_synthetic_conversations(raw_text: str, num_turns: int, student_agent_type: str, tutor_agent_type: str):
  """
  Generate a synthetic dataset of conversations between a tutor and a student [both LLMs].
  """
  if tutor_agent_type == "base": 
    invoke_tutor_agent = invoke_base_agent
  else:
    raise ValueError("Invalid tutor agent type")
    
  parsed_json = json.loads(raw_text)
  params = parsed_json["params"]
  conversation_id = params["conversation_id"]
  include_test_data = params["include_test_data"]
  summary = ""
  conversational_style = ""
  question_response_details = params["question_response_details"]
  question_submission_summary = question_response_details["questionSubmissionSummary"] if "questionSubmissionSummary" in question_response_details else []
  question_information = question_response_details["questionInformation"] if "questionInformation" in question_response_details else {}
  question_access_information = question_response_details["questionAccessInformation"] if "questionAccessInformation" in question_response_details else {}
  question_response_details_prompt = parse_json_to_prompt(
    question_submission_summary,
    question_information,
    question_access_information
  )
  
  #  Generate Conversation
  conversation_history = []
  message = "Ask a question."
  for i in range(0,num_turns):
    print(f"Turn {i+1} of {num_turns}")
    if len(conversation_history) == 0:
      message = "Ask me a question regarding your thoughts on the learning materials that you are currently woking on."
    else:
      message = conversation_history[-1]["content"]

    if i % 2 == 0:
      # Student starts
      student_response = invoke_student_agent(message, conversation_history[:-1], summary, student_agent_type, question_response_details_prompt, conversation_id)
      conversation_history.append({
        "role": "user",
        "content": student_response["output"]
      })
    else:
      tutor_response = invoke_tutor_agent(message, conversation_history, summary, conversational_style, question_response_details_prompt, conversation_id)
      conversation_history.append({
        "role": "assistant",
        "content": tutor_response["output"]
      })

      if "summary" in tutor_response:
        summary = tutor_response["summary"]
      if "conversationalStyle" in tutor_response:
        conversational_style = tutor_response["conversationalStyle"]
  
  #  Save Conversation
  conversation_output = {
    "conversation_id": conversation_id+"_"+student_agent_type+"_"+tutor_agent_type+"_synthetic",
    "student_agent_type": student_agent_type,
    "tutor_agent_type": tutor_agent_type,
    "conversation": conversation_history
  }
  return conversation_output


if __name__ == "__main__":
  num_turns = 6
  tutor_agent_types   = ["base"]                           
  # Students can be "base", "curious", "contradicting", "reliant", "confused", "unrelated"
  student_agent_types = ["base", "curious", "contradicting", "reliant", "confused", "unrelated"]  

  #  Read all question files
  questions = []
  example_inputs_folder = "src/agents/utils/example_inputs/"
  output_folder = "src/agents/utils/synthetic_conversations/"
  for filename in os.listdir(example_inputs_folder):
    if filename.endswith("1.json"):
      questions.append(os.path.join(example_inputs_folder, filename))

    for tutor_agent_type in tutor_agent_types:
      # Open CSV file for writing
      csv_filename = os.path.join(output_folder, "all_conversations_"+tutor_agent_type+".csv")
      with open(csv_filename, "w", newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        # Write the header
        csv_writer.writerow(["tutor", "student", "conversation", "conversation_id"])
      
        for student_agent_type in student_agent_types:
          for question in questions:
            print(f"Generating synthetic conversation for {question} with tutor: {tutor_agent_type} and student: {student_agent_type}")
            with open(question, "r") as file:
              raw_text = file.read()

              conversation = generate_synthetic_conversations(raw_text, num_turns, student_agent_type, tutor_agent_type)

              conversation_output_filename = output_folder + question.split('/')[-1].replace(".json", "_"+student_agent_type+"_"+tutor_agent_type+"_conversation.json")
              with open(conversation_output_filename, "w") as file:
                json.dump(conversation, file, indent=2)

              # Write to CSV
              conversation_id = conversation["conversation_id"]
              csv_writer.writerow([tutor_agent_type, student_agent_type, conversation["conversation"], conversation_id])
