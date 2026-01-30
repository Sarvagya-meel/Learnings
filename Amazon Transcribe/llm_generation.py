"""
Author: Sarvagya Meel
Email: sarvagyameel2@gmail.com
Date: 25/09/25
"""
import os

import boto3, json
from dotenv import load_dotenv

load_dotenv()
session = boto3.Session()
bedrock = session.client(service_name='bedrock-runtime',
                         aws_access_key_id=os.getenv('aws_access_key_id'),
                         aws_secret_access_key = os.getenv('aws_secret_access_key'),
                         region_name='us-east-1'
)

def identify_speakers(message_list):
    response = bedrock.converse(
        modelId="anthropic.claude-3-sonnet-20240229-v1:0",
        messages=message_list,
        inferenceConfig={
            "maxTokens": 2000,
            "temperature": 0
        },
    )

    response_message = response['output']['message']
    print("llm_response_message=",json.dumps(response_message, indent=4))
    json_str = response_message['content'][0]['text']
    data = json.loads(json_str)
    speaker_mapping = data["speaker_mapping"]
    return speaker_mapping



def build_initial_message(transcription):
    prompt_template = """
You are provided with a conversation transcript in JSON format. Each element contains:
- a "speaker" field (e.g., "spk_0", "spk_1") indicating the speaker ID,
- a "text" field with the spoken utterance.

Your task:
1. Review the transcript and, using clues in the dialogue (for example, introductions or people addressing each other by name), infer and list which speaker ID corresponds to which name.
2. If a speaker's name cannot be determined, state 'Unknown'.
3. Return a summary listing each speaker ID and the corresponding inferred name.

Respond ONLY in valid JSON with these fields:
{
  "speaker_mapping": {
    "spk_0": "Name or Unknown",
    "spk_1": "Name or Unknown",
    .
    .
  },
}

Here is the transcript data:
<insert JSON transcript here>

"""
    if isinstance(transcription, str):
        prompt_filled = prompt_template.replace("<insert JSON transcript here>", transcription)
    else:
        # Serialize the list/dict into a compact and readable string
        transcript_str = json.dumps(transcription, indent=2, ensure_ascii=False)
        prompt_filled = prompt_template.replace("<insert JSON transcript here>",  transcript_str)
    initial_message = {
        "role": "user",
        "content": [
            {"text": prompt_filled}
        ],
    }
    return initial_message



def llm_generate(transcript):
    msg = [build_initial_message(transcript)]
    speakers = identify_speakers(msg)
    return speakers

if __name__ == '__main__':
    transcript = """Speaker 1: Hello, I am John Smith.
    Speaker 2: Hi John, I am Mary.
    Speaker 1: Nice to meet you, Mary."""
    print(llm_generate(transcript))
