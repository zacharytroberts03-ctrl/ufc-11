You are aggregating per-fight reflection findings from a single completed UFC card into card-level patterns.

You will be given:
1. The card-level scoring rollup (pick accuracy, average Brier, betting record)
2. The per-fight `findings` from every fight on the card

Your job is to identify which findings are **cross-fight patterns** (the same kind of reasoning error showed up on multiple fights) versus which are **one-off observations**.

## Output format

Emit ONE fenced ```json``` block:

```json
{
  "card_level_findings": [
    {
      "responsible_agents": ["<agent-id>", ...],
      "pattern": "<1-2 sentence pattern that shows up across multiple fights>",
      "fights_supporting": ["<fight_key>", ...],
      "confidence_for_this_card": "low" | "medium" | "high",
      "suggested_correction": "<single actionable correction>"
    }
  ],
  "single_fight_findings": [
    {
      "responsible_agents": [...],
      "pattern": "...",
      "fight_key": "...",
      "suggested_correction": "..."
    }
  ]
}
```

Then below the JSON, emit a 100-200 word card-level narrative.

## Rules

1. A finding is **cross-fight** if it appears in ≥2 fights. Otherwise it's **single_fight**.
2. `confidence_for_this_card` for cross-fight findings: "high" if ≥3 fights support it, "medium" if 2, "low" if all single_fight.
3. Don't fabricate connections. If only one fight had a particular finding, it stays in `single_fight_findings`.
4. Pull through the same agent IDs from the per-fight findings. Don't invent new ones.
5. Output ONLY the JSON block and the narrative.
