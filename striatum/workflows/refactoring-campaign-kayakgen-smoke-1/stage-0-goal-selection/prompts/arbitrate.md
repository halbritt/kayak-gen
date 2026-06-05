# Arbitrate The Preferred Goal

Read the tradeoff ledger, the proposals, and the scorecards. Publish a
synthesis that selects exactly one refactoring goal for the campaign, or
refuses all three with reasons.

Selection rules:

- A goal with low `preservation_verifiability` cannot win: a refactor that
  cannot be verified behavior-preserving is an unverifiable rewrite and is
  out of scope for the campaign.
- Prefer goals whose biggest unverified assumption is cheap to check
  during stage-1 preflight over goals with higher payoff but unverifiable
  claims.
- Composing a narrower variant of one proposal is allowed; composing two
  proposals into a broader goal is not — the campaign executes one named
  goal.

State the selected goal in one sentence, the runner-up and why it lost,
and the conditions under which this arbitration should be revisited.
Include the exact lowercase `author:` byline near the top of the artifact.
