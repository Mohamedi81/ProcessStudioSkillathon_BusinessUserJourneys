# Blueprint: Auto Insurance First-Notice-of-Loss to Settlement (TEST FIXTURE)

Fictional blueprint used only to test skill portability. Domain deliberately unrelated to the
beverage innovation blueprint the skill was first built on.

Company: Northwind Mutual. Systems: Guidewire ClaimCenter (claims core), Verisk (fraud scoring),
Salesforce Service Cloud (contact centre), Stripe Treasury (payments).

## As-Is SOP (pains)
- S1 First notice of loss: Call-centre agents retype caller details into ClaimCenter from paper notes; 22 min average handling time; 14% data-entry errors.
- S2 Coverage check: Adjuster manually reads PDF policy to confirm coverage and deductible; 1.5 day delay.
- S3 Fraud screening: Handled by email to Special Investigations Unit (SIU); only 8% of claims screened before payment.
- S4 Damage estimate: Adjuster waits for body-shop estimate by fax/email; estimate vs. repair-cost variance reviewed monthly.
- S5 Settlement approval: Authority limits kept in a spreadsheet; claims above limit routed by email; 6.2 day average cycle.
- S6 Payout: Finance keys payment manually; duplicates found in 0.7% of payments.

## To-Be Blueprint (EAEF)
| Atomic step | Agent / data product | Human decision (HITL) | Role |
|---|---|---|---|
| T1 Intake normalisation | Intake agent, `claim_event` product | Agent confirms summary | Claims Intake Agent |
| T2 Coverage verification | Coverage agent reads policy, returns clause citations | Adjuster accepts or overrides | Claims Adjuster |
| T3 Fraud pre-score | Fraud agent calls Verisk, 100% of claims scored | SIU reviews score >= 70 | SIU Investigator |
| T4 Estimate reconciliation | Estimate agent compares estimate to regional benchmark, flags > 15% variance | Adjuster approves estimate | Claims Adjuster |
| T5 Authority routing | Authority agent applies limits: <= 5,000 adjuster; <= 25,000 team lead; above: claims manager | Approver signs | Claims Manager |
| T6 Payout release | Payment agent creates payment in Stripe Treasury, duplicate check | Finance releases | Claims Finance Analyst |

## Targets
- Handling time 22 min -> 9 min; entry errors 14% -> under 2%.
- Fraud pre-screen coverage 8% -> 100%.
- Settlement cycle 6.2 days -> 2.5 days.
- Duplicate payments 0.7% -> 0%.
