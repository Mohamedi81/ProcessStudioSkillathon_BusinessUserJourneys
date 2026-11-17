# Portability Test Protocol

A skill is portable if a blueprint it has never seen produces a valid deck with zero residue
from the blueprint it was built on. Run all four tests; record results in the table at the end.

## T1. Regression (nothing lost)
Build `examples/drinkit/deck-spec.json` and compare to the harvested slide in v11.
Pass: validator PASS; layout identical (same CSS classes, same sign-off logic).

## T2. Foreign blueprint (does it generalise?)
Input: `examples/claims-test/blueprint.md` (insurance claims, no overlap with beverages).
Steps: harvest (checklist) -> write spec -> build -> validate with `--forbid references/drinkit-forbidden-terms.txt`.
Pass: validator PASS, 0 leakage hits, persona/slide counts differ from 6x3 and are derived from the blueprint.

## T3. Leakage grep (independent of the validator)
```
grep -n -i -E "drinkit|s/4hana|sap|bom|can|recipe" <built.html>
```
Pass: no hits other than words genuinely in the new blueprint (review each).

## T4. Shell integrity
Open the built HTML. Tabs switch, every sign-off box moves the meter, counter total == slide count.
Pass: `validate_deck.py --html` reports matching counts; manual browser check for tab switching.

## T5. Hold-out (recommended, needs the user)
Give a third real blueprint the author has not seen. Follow SKILL.md only. Record what the skill
failed to tell you; patch SKILL.md / references, not the output.

## Results log
| Date | Test | Blueprint | Result | Notes |
|---|---|---|---|---|
| 2026-11-15 | T1 Regression | Drinkit (slide 1.1 only) | PASS | Validator + build OK. Emoji glyphs in v11 replaced with words per design rule. Only 1 of 18 slides converted so far |
| 2026-11-15 | T2 Foreign blueprint | Claims (2 personas, 6 slides) | PASS | 21 forbidden terms, 0 hits. Counts (2x3) differ from Drinkit 6x3 |
| 2026-11-15 | T3 Leakage grep | Claims | PASS | Only false positive: "can start" |
| 2026-11-15 | Negative control | Drinkit spec vs forbidden list | FAIL as intended (11 issues) | Proves the leakage check can detect residue |
| 2026-11-15 | CSS class parity | v11 vs claims deck | PASS | No v11 class missing from output |
| pending | T4 Browser check | Claims | NOT RUN | Needs a human to open examples/claims-test/deck.html |
| pending | T5 Hold-out blueprint | Unseen real blueprint | NOT RUN | Needs a blueprint from the user |
