# Team change requests

## Claims

| Author | Feature | Number | Distinct scope or new evidence |
| --- | --- | --- | --- |
| Xiru Zhang | Filters and summary cards | Total employment in included occupations (2025) | Test exposure filtering, employment totals, and missing-value handling using a three-occupation sample. |

## Requests

### AUDIT-XZ-01 Show employment data coverage

- Author: Xiru Zhang
- Status: open
- App version or commit checked: Supplied app.py and analysis/backend.py reviewed on October 25, 2026; app.py commit not provided.
- Feature or number and its intended behavior or definition: The employment summary card adds reported 2025 employment for filtered occupations. It should also indicate when some included occupations have missing employment data.
- Inputs and steps to reproduce: Create three sample occupations with employment values of 1,000, NaN, and 3,000. Call summary_metrics() and inspect how app.py displays the returned employment total and coverage count.
- Expected result: The total should be 4,000, with a note such as "Employment reported for 2 of 3 included occupations."
- Actual result: The AI-assisted backend test returned employment_2025 = 4000 and employment_value_count = 2. Code review showed that the summary cards display the total but do not display this coverage count. The live interface was not tested.
- Evidence (including file, function, and relevant lines if code was checked): analysis/backend.py, summary_metrics(), lines 149–151; app.py, lines 189–196. The backend returns both the total and the count of non-missing employment values, but the card code uses only the total.
- Likely cause, if established, and remaining uncertainty: app.py does not display the employment_value_count returned by the backend. The frequency of missing employment values in the real dataset remains unverified.
- Requested change: Add a caption below the employment card showing "Employment reported for X of Y included occupations," using employment_value_count and occupation_count.
- Verification check and expected result: With employment values of 1,000, NaN, and 3,000, show a total of 4,000 and coverage of 2 of 3 occupations. With all three values present, show coverage of 3 of 3. Confirm that coverage updates when filters change.
- Implementation commit and verification result, if resolved: Not implemented or verified yet; request remains open.
