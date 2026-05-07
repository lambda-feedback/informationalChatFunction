# Informational Chatbot

A patient tutor that breaks problems into steps. It will give you hints first and only show the full answer only if you ask explicitly. It explains *why* you went wrong when you make a mistake, and tends to end its replies with a question to encourage further thinking or engagement.

**Example chat**

> **You:** How can I start solving this question?
>
> **Informational:** The question asks which of the given sets of equations represent possible three-dimensional incompressible flow cases. To determine this, we need to check the condition for incompressible flow for each case.
>
> Do you recall the mathematical condition for a flow to be incompressible?

**Tip:** if its explanation is longer than you need, ask "in one sentence, what should I do next?"

Some technical details:
<pre style="white-space: pre-wrap;">
<code>LLM model: Gemini-2.5-flash-lite (Google)
response time (on average): ~10 seconds
</code>
</pre>
