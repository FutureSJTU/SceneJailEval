from CallAPI.api_client import call_chat_api
from prompts import SCENE_CLASSIFICATION_PROMPT

def classify_scene(user_query, model_response, chat_model=None):
    # Candidate keywords list
    CANDIDATE_KEYWORDS = [
        "Violent Crime", "Non-violent Crime", "Sex-related Crime", 
        "Child Sexual Exploitation", "False Information and Defamation", 
        "Professional Advice", "Privacy Invasion", 
        "Intellectual Property Infringement", "WMDs", 
        "Hate and Discrimination", "Suicide and Self-harm", 
        "Sexual Content", "Political Agitation and Elections", 
        "Regional Sensitive Issues"
    ]
    
    # Generate prompt and call API
    prompt = SCENE_CLASSIFICATION_PROMPT.replace('[Specific Question Content]', user_query).replace('[Specific Response Content]', model_response)

    api_response = call_chat_api(prompt, chat_model=chat_model)

    if not api_response:
        return None  
    for keyword in CANDIDATE_KEYWORDS:
        if keyword in api_response:
            return keyword

    
    # Return None if no matching keyword is found
    return None
