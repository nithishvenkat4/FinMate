# FinMate Data Quality Engine & Rules Matrix

## The 11 Core Quality Rules

| Rule ID | Rule Name | Severity | Action Taken |
| :--- | :--- | :--- | :--- |
| **RULE 1** | Positive Amount | **ERROR** | Amount $\le 0.00$ is rejected from entering the clean dataset. |
| **RULE 2** | Valid Transaction Type | **ERROR** | Types outside `income`/`expense` are rejected. |
| **RULE 3** | Valid Calendar Date | **ERROR** | Malformed or impossible dates are rejected. |
| **RULE 4** | Non-empty Description | **ERROR** | Blank payees/descriptions are rejected. |
| **RULE 5** | Category Provisioning | **INFO** | Unmatched categories are defaulted and provisioned. |
| **RULE 6** | User Ownership Integrity | **ERROR** | Record must bind to a verified `user_id`. |
| **RULE 7** | Category Type Compatibility | **WARNING** | Flags income categories marked as expenses (e.g., Salary expense). |
| **RULE 8** | Currency Consistency | **INFO** | Default currency is `INR`. |
| **RULE 9** | High-Value Transaction Flag | **WARNING** | Transactions $\ge$ ₹10,00,000 generate review warning. |
| **RULE 10** | Future Transaction Date | **WARNING** | Dates beyond current local date generate review warning. |
| **RULE 11** | Potential Duplicate Heuristic | **WARNING** | Matching `(user_id, date, amount, description)` flagged as duplicate candidate. |

## Severity Classification Model

- **ERROR**: Prevents row from being saved into the database. Prevents database corruption.
- **WARNING**: Permitted to persist into clean dataset, but flagged with warning codes stored in `data_quality_flags` for human review.
- **INFO**: Non-blocking normalization notice (e.g. Category defaulted).

## Duplicate Detection Heuristic
The duplicate detection heuristic compares:
`user_id + transaction_date + amount + description`
- Evaluated both within the uploaded file batch and against existing database records.
- **No Automatic Deletion**: Candidate duplicates are flagged with `POSSIBLE_DUPLICATE_IN_BATCH` or `POSSIBLE_DUPLICATE_IN_DB`, allowing the human user to review and confirm or delete.
