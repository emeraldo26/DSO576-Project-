# Data Fit

## Team Vision

A workforce-development agency must identify occupations that may need AI-transition training and reskilling support using observed AI use, task exposure, employment size, wages, and labor-market outlook.

Program managers will filter and compare occupations, then view the tasks contributing to each result. The output will be a shortlist for human review—not a prediction that workers will be replaced.

## Selected Data Sources

We selected two complementary sources that provide the main information required for the project.

### 1. Anthropic Economic Index

**Source:** Anthropic Economic Index

| **File**                 | **Information provided**                             | **Project use**                           |
|--------------------------|------------------------------------------------------|-------------------------------------------|
| job_exposure.csv         | Occupation title, SOC code, and observed AI exposure | Compare AI exposure across occupations    |
| task_penetration.csv     | Occupational tasks and AI-penetration values         | Identify tasks contributing to exposure   |
| onet_task_statements.csv | O\*NET task statements linked to occupations         | Connect task exposure to occupation codes |

This dataset supports the observed AI-use and task-exposure portions of the project.

### 2. BLS Employment Projections

**Source:** BLS Occupational Projections and Worker Characteristics

We will use Table 1.2: Occupational Projections and Worker Characteristics in XLSX format.

| **Information provided**                      | **Project use**                          |
|-----------------------------------------------|------------------------------------------|
| 2025 National Employment Matrix code          | Join BLS and Anthropic occupations       |
| Employment, 2025                              | Show workforce size                      |
| Employment change, percent, 2025–35           | Show projected growth or decline         |
| Occupational openings, 2025–35 annual average | Show continuing worker demand            |
| Median annual wage, dollars, 2025             | Provide economic context                 |
| Education and on-the-job training fields      | Describe entry and training requirements |

BLS provides the employment, wage, training, and labor-market information missing from the Anthropic data.

## What One Row Represents

Based on the documentation:

- job_exposure.csv: one six-digit SOC occupation.

- task_penetration.csv: one O\*NET task.

- onet_task_statements.csv: a connection between a task and occupation.

- BLS Table 1.2: either a detailed occupation or broader occupational summary. Only detailed occupations will be retained.

The exact row structure and column names will be confirmed after downloading the files.

## Observed Scope

The Anthropic data reflects Claude use connected with occupational tasks. It does not observe every worker, employer, occupation, or workplace AI system. The data release and observation period will be recorded after download.

BLS Table 1.2 provides national U.S. employment data for 2025 and projections for 2025–35. It describes occupations nationally, not individual workers or state labor markets.

## How the Data Will Connect

The main occupation-level join is expected to be:

**Anthropic occ_code = BLS 2025 National Employment Matrix code**

Both use SOC-based codes such as 15-1252.

The task-level connection will be:

**task_penetration.csv task**  
↓  
**onet_task_statements.csv Task**  
↓  
**O\*NET-SOC Code**

Occupation codes will be stored as text to preserve punctuation and leading zeros. Task text will be standardized by removing unnecessary spaces and making capitalization consistent.

## Required Join Checks

Before confirming feasibility, we will:

1.  Verify row structures and column names.

2.  Check occupation-code uniqueness and duplicates.

3.  Measure the Anthropic–BLS occupation-code match rate.

4.  Review occupations appearing in only one dataset.

5.  Determine whether different SOC versions require a crosswalk.

6.  Measure task-description match rates.

7.  Check whether tasks connect to multiple occupations.

8.  Confirm that joins do not duplicate employment or wage values.

9.  Review unmatched records before calculating a priority score.

The final analysis will report actual matching rates rather than assume that all records match. The number of usable occupations and tasks is currently unknown.

## What the Combined Data Supports

If the joins work as expected, the combined data should support:

- An occupation ranking based on AI exposure and labor-market need.

- Comparison of AI exposure with projected employment change.

- Employment, wage, and annual-opening context.

- Occupation detail pages showing contributing tasks.

- A shortlist of occupations for program review.

The project must distinguish AI exposure from reskilling need. High exposure alone does not mean immediate reskilling is required. Employment size, outlook, wages, openings, and task characteristics must also be considered.

## Planned Measures

Anthropic is expected to provide occupation exposure, task-level AI penetration, and occupation-task connections. BLS should provide employment size, projected change, annual openings, wages, education, and training requirements.

These measures may later be standardized and combined into a priority score. However, this score does not exist in either dataset. The team must choose the measures and weights after exploring the data.

## Data-Fit Boundaries

**Supported:** Comparisons of AI exposure, employment size, wages, annual openings, employment projections, and occupation-level tasks, leading to a shortlist for review.

**Partly supported:** A reskilling-priority score could be created, but its measures and weights would reflect team and stakeholder decisions. The data does not directly measure reskilling need.

**Outside the data’s scope:** Worker skills, employer automation plans, state-level demand, program costs and capacity, and evidence that training improves employment outcomes. Therefore, the data cannot make final funding decisions.

## Association Versus Causation

High AI exposure combined with weak employment growth would show an association, not prove that AI caused the decline. Employment can also be affected by economic conditions, employer demand, regulation, demographic change, and other technologies.

The data also cannot prove that funding a reskilling program will improve worker outcomes. The dashboard should support human review rather than make causal claims or automatic funding decisions.

## Data Limitations

- Anthropic measures observed Claude use, not all workplace AI use.

- AI exposure does not automatically mean automation, job loss, or reskilling need.

- Zero exposure may mean qualifying use was not observed; it does not prove that AI cannot affect the occupation.

- Task descriptions may not match perfectly across files.

- Tasks may connect to multiple occupations, creating many-to-many relationships.

- The datasets may use different dates or SOC versions.

- BLS projections are estimates, not guaranteed outcomes.

- BLS data is national; state or local data may be needed for regional funding decisions.

## Questions Still to Be Decided

1.  Which measures should increase or decrease priority?

2.  How should the measures be weighted?

3.  Should wages affect the score or serve only as context?

4.  Which state or region will use the dashboard?

5.  What outcome would define a successful reskilling program?

## Data-Fit Conclusion

The Anthropic Economic Index and BLS Employment Projections appear to fit the team’s vision. Anthropic provides occupation-level AI exposure and task information, while BLS provides employment, wages, openings, education, training, and projected labor-market change.

Together, they may support a national screening tool that identifies occupations for further review. The output should remain a human-reviewed shortlist—not proof of worker replacement or an automatic funding decision.

Final feasibility will be confirmed after downloading the files and testing the occupation-code and task-description joins.
