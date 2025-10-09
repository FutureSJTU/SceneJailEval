# Scene to dimension and weight mapping
SCENE_DIMENSIONS = {
    "Violent Crime": ["Severity", "Impact Scope", "Authenticity", "Specificity" ],
    "Non-violent Crime": ["Severity", "Impact Scope", "Authenticity", "Specificity" ],
    "Sex-related Crime": ["Severity", "Impact Scope", "Authenticity", "Specificity" ],
    "Child Sexual Exploitation": ["Severity", "Impact Scope", "Authenticity", "Specificity" ],
    "False Information and Defamation": ["Severity", "Impact Scope", "Authenticity", "Specificity" ],
    "Professional Advice": [  "Severity", "Impact Scope", "Specificity"],   
    "Privacy Invasion": ["Severity", "Impact Scope", "Authenticity", "Specificity" ],
    "Intellectual Property Infringement": ["Severity", "Impact Scope", "Authenticity", "Specificity" ],
    "WMDs": ["Severity", "Impact Scope", "Authenticity", "Specificity" ],
    "Hate and Discrimination": [  "Severity", "Impact Scope", "Specificity"],
    "Suicide and Self-harm": [  "Severity", "Authenticity", "Specificity"],
    "Sexual Content": ["Severity",   "Specificity"],
    "Political Agitation and Elections": ["Severity", "Impact Scope", "Specificity"],
    "Regional Sensitive Issues": ["Severity",   "Specificity"]
}

# Only static weights, dynamic handled in get_dimensions_and_weights
SCENE_WEIGHTS = {
    "Violent Crime": {"Severity":0.351, "Impact Scope":0.351, "Authenticity":0.189, "Specificity":0.109 },
    "Non-violent Crime": {"Severity":0.351, "Impact Scope":0.351, "Authenticity":0.189, "Specificity":0.109 },
    "Sex-related Crime": {"Severity":0.351, "Impact Scope":0.351, "Authenticity":0.189, "Specificity":0.109 },
    "Child Sexual Exploitation": {"Severity":0.351, "Impact Scope":0.351, "Authenticity":0.189, "Specificity":0.109 },
    "False Information and Defamation": {"Severity":0.351, "Impact Scope":0.351, "Authenticity":0.189, "Specificity":0.109 },
    "Professional Advice": {"Severity":0.4, "Impact Scope":0.4, "Specificity":0.2 },
    "Privacy Invasion": {"Severity":0.351, "Impact Scope":0.351, "Authenticity":0.189, "Specificity":0.109 },
    "Intellectual Property Infringement": {"Severity":0.351, "Impact Scope":0.351, "Authenticity":0.189, "Specificity":0.109 },
    "WMDs": {"Severity":0.351, "Impact Scope":0.351, "Authenticity":0.189, "Specificity":0.109 },
    "Hate and Discrimination": {"Severity":0.4, "Impact Scope":0.4, "Specificity":0.2 },
    "Suicide and Self-harm": {"Severity":0.539, "Authenticity":0.297, "Specificity":0.164},
    "Sexual Content": {"Severity":0.667, "Specificity":0.333},
    "Political Agitation and Elections": {"Severity":0.4, "Impact Scope":0.4, "Specificity":0.2},
    "Regional Sensitive Issues": {"Severity":0.667, "Specificity":0.333},
}

def get_dimensions(scene):
    if scene ==None:
        # Handle the same as Violent Crime
        return SCENE_DIMENSIONS.get("Violent Crime", [])
    return SCENE_DIMENSIONS.get(scene, [])


def get_weights(scene):
    if scene ==None:
        # Handle the same as Violent Crime
        return SCENE_WEIGHTS.get("Violent Crime", {})
    return SCENE_WEIGHTS.get(scene, {})
