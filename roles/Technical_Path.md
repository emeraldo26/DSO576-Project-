# Technical Path

## Selected project area

AI Workforce Investment Planner

## Candidate Vision A

A company workforce strategy manager in a specific industry must decide which occupations should be prioritized for AI-enabled workflow redesign and employee AI training.

## Candidate Vision B

A workforce development director at a public workforce agency must decide which occupations should be prioritized for AI-transition reskilling support based on AI exposure and labor-market outlook.

## Source and access checks

| Source | Access and owner | Available data and apparent row grain | Smallest access check | Blocker or next check |
|---|---|---|---|---|
| [Anthropic Economic Index](https://www.anthropic.com/economic-index) | Anthropic provides public research pages and downloadable data. The pages and files I checked did not require a login. Redistribution terms still need to be confirmed before any raw file is placed in the team repository. | The available CSV files include occupation-level AI exposure and task-level AI penetration. In the samples inspected, `job_exposure.csv` has one row per six-digit SOC occupation, while `task_penetration.csv` has one row per task. | I successfully opened the Economic Index page and inspected the small occupation and task CSV files with pandas. | Confirm the license and citation requirements. Test whether its SOC codes and task text match the O*NET and BLS versions we plan to use. |
| [OpenAI Signals](https://openai.com/signals/data-download/) | OpenAI provides downloadable CSV files without a login. Its data page states that the data is available under CC BY 4.0 with attribution. | The data includes monthly measures connected to O*NET intermediate work activities. One row appears to represent one activity-period observation rather than one occupation. | I successfully opened the official data-download page and data dictionary. | The activity identifiers may not connect directly to six-digit SOC occupations. We need to find and test a reliable activity-to-occupation crosswalk before treating this as a core source. |
| [O*NET Database](https://www.onetcenter.org/database.html) | The O*NET Resource Center provides public downloads in CSV, Excel, JSON, and database formats under the O*NET database license. | Task Statements connect an `O*NET-SOC Code` and occupation title to an individual task statement, so one row represents one occupation-task link. | I successfully opened the O*NET database page and the Task Statements CSV documentation. | O*NET codes may include suffixes such as `.00`, while other sources use six-digit SOC codes. We need to standardize the codes and check whether task wording is consistent across files. |
| [BLS Employment Projections](https://www.bls.gov/emp/tables/occupational-projections-and-characteristics.htm) | The U.S. Bureau of Labor Statistics provides public tables and XLSX downloads without a login. | Table 1.2 contains occupation codes, employment, projected employment change, annual openings, wages, education, and training. A row may be an individual occupation or a summary category. | I successfully opened Table 1.2 and confirmed that an XLSX version is available. | Keep only detailed occupational line items before joining. Test whether the National Employment Matrix codes match the Anthropic six-digit SOC codes. |

## Scale and likely technical approach

The files inspected are small enough for an initial course project using flat files and pandas. A database does not appear necessary for the first exploration because the data is mostly read-only and can fit in memory. We can keep downloaded data in a local `data/` folder, exclude it from Git with `.gitignore`, and store only code and documentation in the private team repository.

If the joins work, pandas can be used to clean SOC codes, inspect missing and duplicate values, connect occupation-level files, and summarize task-level data. Plotting packages could support later comparisons, and Streamlit may be useful for a later interactive prototype. These are possible options, not tools the team needs to install or use at this stage.

## Technical assessment of Candidate Vision A

**What appears feasible:** Anthropic and O*NET could help identify occupations and tasks with observed AI use, while BLS could add employment and wage context. These sources could support a broad comparison of occupations.

**What remains uncertain:** Public occupation data does not describe one company's employees, workflows, technology, costs, or training readiness. Therefore, it may not be enough to recommend workflow redesign for a specific company or industry without company-level data. This is a feasibility concern, not a conclusion that the Vision is impossible.

**Next technical check:** Determine whether the team can obtain a manageable company- or industry-specific source that connects jobs, tasks, and AI training needs. If not, Candidate Vision A may need a broader stakeholder or narrower claim.

## Technical assessment of Candidate Vision B

**What appears feasible:** Anthropic and O*NET use occupational and task concepts, while BLS provides public labor-market measures by occupation. If the occupation codes and task statements can be connected reliably, these sources could support a comparison of AI exposure, task exposure, workforce size, wages, and labor-market outlook.

**What remains uncertain:** A high AI-exposure value does not by itself prove that workers will lose jobs or need a specific training program. We still need to test code compatibility, task-text matching, missing values, and the treatment of BLS summary rows. OpenAI Signals should remain optional until its activity data can be connected reliably to occupations.

**Next technical check:** Use a small pandas exploration to standardize SOC codes and task text, then report matched records, unmatched records, and match rates across Anthropic, O*NET, and BLS.

## Current technical recommendation

Candidate Vision B appears more technically promising for the available public data because its stakeholder and decision can be studied at the occupation level. Candidate Vision A may require company-specific operational data that is not present in the confirmed public sources. This is a preliminary technical assessment; the team should also consider the other role findings before choosing a final Vision.

## What was checked and what remains uncertain

**Checked:** The official source pages opened successfully; small files or documentation were available; the core sources use occupation, task, or work-activity concepts; and a flat-file pandas workflow appears appropriate for an initial exploration.

**Still uncertain:** licensing details for every downloaded Anthropic file, compatibility across SOC versions, exact task-text match rates, the OpenAI activity-to-occupation connection, and whether Candidate Vision A can obtain company-specific evidence.
