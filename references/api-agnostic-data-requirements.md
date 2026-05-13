# API-Agnostic Data Requirements

This skill is intentionally neutral about API providers.

## The rule
Do not describe the workflow as dependent on one named vendor.
Describe the workflow as dependent on **information quality**.

## What the agent actually needs
The agent needs access to information that is:

- current enough for monitoring
- specific enough to support claims
- structured enough to compare across symbols
- broad enough to cover macro, crypto-native, and holdings context

## Acceptable source forms
The following are all acceptable if they provide the needed information:

- exchange APIs
- market-data APIs
- news search tools
- browser-based web search
- MCP services
- internal research databases
- manually provided operator notes
- pre-aggregated datasets

## Preferred source qualities
Prefer sources that are:

1. timely
2. directly relevant
3. cross-checkable
4. specific rather than vague
5. stable enough to cite or summarize reliably

## What not to do
Do not hard-code the skill around:
- one macro news provider
- one crypto news provider
- one social source
- one exchange analytics tool

If one source is unavailable, the agent should still be able to proceed using equivalent information from another source form.

## Practical fallback logic
If one category is missing:
- note the gap
- reduce confidence
- continue with the remaining categories
- avoid pretending the missing category was checked
