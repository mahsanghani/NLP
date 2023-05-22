import os
import openai

openai.api_key = os.getenv("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")

response = openai.Completion.create(
  model="text-davinci-003",
  prompt="Convert my short hand into a first-hand account of the meeting:\n\nTom: Profits up 50%\nJane: New servers are online\nKjel: Need more time to fix software\nJane: Happy to help\nParkman: Beta testing almost done",
  temperature=0,
  max_tokens=64,
  top_p=1.0,
  frequency_penalty=0.0,
  presence_penalty=0.0
)

# Prompt
# Convert my short hand into a first-hand account of the meeting:

# Tom: Profits up 50%
# Jane: New servers are online
# Kjel: Need more time to fix software
# Jane: Happy to help
# Parkman: Beta testing almost done
# Sample response
# At the meeting, Tom reported that profits had increased by 50%. Jane then mentioned that the new servers were online. Kjel mentioned that they needed more time to fix the software, and Jane offered to help. Finally, Parkman reported that the beta testing was almost done.