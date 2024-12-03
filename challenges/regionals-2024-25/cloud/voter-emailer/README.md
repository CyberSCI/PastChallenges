# Voter Emailer
## Challenge Description
We've been trying to leverage AI to help automate emailing voters to make sure they know all the important campaign dates and details. 

A developer has setup a FastAPI endpoint `http://10.0.2.21:8000` and that VM should have restricted access to `https://rgnl2025voteremailer.blob.core.windows.net/voters/voters.txt` but we're not sure they know what they're doing.

Note: This challenge is running its own LLM and queries may take a while to come back (the first few might be 30 seconds to a minute).

## Flag 1
What is the request URL for tool calling?

Format: `http://10.0.2.21:8000/<PathValueHereWithoutParameters>`

Answer: `http://10.0.2.21:8000/tools`

## Flag 2
Who is the 33rd person in the `voters.txt` file?

Format: `<Name> - <email address>`

Answer: `Charlie Lane - charlie.lane@cyberemail.io`
