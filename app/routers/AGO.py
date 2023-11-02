from fastapi import APIRouter, HTTPException
from app.schemas.AGO import AGOCreateSchema, AGOListCreateSchema

router = APIRouter()

mocked_AGOs = {'AGOs': [
    {
        'AGO_id': 0,
        'goal': "By 4/21/2022, during activities like reading or games, he will answer age-appropriate wh-questions (who, what, where, when, why) logically and appropriately using multimodal communication", 
        'areasOfNeed': "Receptive Language", 
        'baseline': "He struggles with basic wh-questions. In assessments, he often misidentifies colors and animals, improving with a model. His teacher notes difficulties with book-related questions and overall verbal understanding, but he can answer some simple questions, like identifying the bear's color in 'Brown Bear, Brown Bear, What do you see?'", 
        'shortTermObjective': "By the first reporting period, during structured activities (e.g., book reading, playing a game, in response to picture scenes) will respond to early developing wh- questions (i.e., who, what, where) with a logical and appropriate response using multimodal communication (e.g., low-tech communication tools, spoken language) in 4 out of 5 opportunities, when given repetitions on the question and verbal cues as needed.", 
        'role': "Speech-Language Pathologist"
    },
    {
        'AGO_id': 1,
        'goal': 'By April 21, 2022, the individual will use three-word utterances for various communication needs in response to verbal prompts in 4 out of 5 trials, with consistency across three sessions.', 
        'areasOfNeed': "Expressive language, Pragmacs, Behavior", 
        'baseline': "The child primarily uses single words for naming objects and engaging in social routines but doesn't use verbs to express or describe actions, either his own or others', or to narrate play. He shows frustration and tantrums, especially during transitions or when introduced to new activities, both at home and in school. He does not use language to manage his frustration, and his behavior disrupts his own learning and that of his classmates.", 
        'shortTermObjective': "By the first reporting period, the goal is for the individual to use two-word utterances or more in response to verbal prompts for various communicative purposes, employing different communication methods, in 4 out of 5 instances when prompted, possibly with additional cues for expansion of the utterance.", 
        'role': "Speech-Language Pathologist"
    },
    {
        'AGO_id': 2,
        'goal': "By 4/21/2022, aim for 90 percent speech intelligibility in structured activities, using intelligibility strategies with one verbal reminder across three consecutive sessions if necessary.", 
        'areasOfNeed': "Intelligibility", 
        'baseline': "The individual displays age-appropriate phonological processes with one unusual palatalization process. Speech is rated as 60-70 percent intelligible by the mother and 60 percent intelligible by the speech-language pathologist in known contexts to unfamiliar listeners.", 
        'shortTermObjective': "By the first reporting period, aim for 75 percent intelligibility during structured activities using intelligibility strategies with advance reminders and one verbal reminder if necessary, along with recasted models of speech as needed.", 
        'role': "Speech-Language Pathologist"
    }
]}

@router.post("/AGOs/", response_model=AGOListCreateSchema)
async def create_AGOs(AGOs_data: AGOListCreateSchema):
    created_AGOs = []
    for AGO_data in AGOs_data:
        created_AGOs.append(AGO_data)
    return created_AGOs

@router.get("/AGOs/", response_model=AGOListCreateSchema)
async def read_AGO():
    return mocked_AGOs