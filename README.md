# Take-Home Exercise: Master Schedule Unfilled Shifts
You are tasked with developing a solution to minimize the number of unfilled cells in a schedule dataset. The dataset contains historical snapshots of scheduling information for six months (Apr 2024 to October 2024). Your goal is to assign employees to these unfilled cells, ensuring that the solution adheres to the following constraints:

## Constraints
1. **Weekly Hours:**
   No employee may be scheduled for more than **40 hours** within a single scheduling week.

2. **Work Days:**
   No employee may be assigned shifts on more than **5 days** within the scheduling week.

3. **Daily Shift Limit:**
   An employee may be assigned **no more than one shift per day**.

### Notes
* The scheduling week in the dataset runs **Friday (day 1) → Thursday (day 7)**. All weekly limits apply to this fixed week structure, not a rolling window.
* Some shifts span midnight. Such shifts are attributed **entirely to their start day** for the purpose of all constraints.
* It is allowed for an employee to work a shift that ends on one day and another shift that begins later on that same calendar day (as long as it does not violate the “one shift per day” rule, given attribution to the start day).

## Dataset
The dataset contains historical scheduling data for six months, with snapshots taken at an interval of a few days apart, with the snapshot date denoted in the `date` column. 

* A `JobPostID` is associated with a single `JobNumber`, and each `JobNumber` may have multiple `JobPostID`s.
* A `ScheduleDetailID` is associated with a single `JobPostID`, and each `JobPostID` may contain multiple `ScheduleDetailID`s.
* Each cell is defined by a unique ScheduleDetailID and DayNum. There might be multiple rows within the dataset with the same ScheduleDetailID and DayNum, but different CellInfoIDs. This indicates that there are more then 1 sub-cell under the cell. For the purposes of this exercise, you only need to consider 1 row per unique ScheduleDetailID/ DayNum combination
* Assume no employees exist beyond those listed in the `EmployeeNumber` column.
* A null value in `EmployeeNumber` indicates an unfilled cell. A cell may be unfilled either because a previously assigned employee refused the shift (for example, some employees tend to decline overnight shifts) or because no suitable employees remained available due to earlier assignment decisions.

## Project Requirements
1. **Filling Unfilled Shifts in the Latest Schedule:**
   * Using machine learning, optimization methods, or any other data-driven approach, develop a solution that recommends the most suitable employee for each currently unfilled shift in the latest schedule (dated 10/8/2024). The recommendations must honor all scheduling constraints described above and aim to assign employees who are most likely to accept the proposed shifts.
2. **Endpoint Development**:
   * Develop an API endpoint that can be called for any given cell in the schedule. The endpoint signature is up to you, but the response should indicate whether the slot was unfilled and your solution was run to fill it, or whether the slot in the dataset was already filled.
   * The endpoint should:
     * Validate that the requested cell exists.
     * If the requested cell is currently unfilled in the latest snapshot (i.e., `EmployeeNumber` is `null`), run your solution on demand to fill the unfilled cell. You do not need to update or modify the read-only dataset.
     * If the requested cell is already filled, return the assigned employee ID and indicate that it comes from the existing schedule.

## Deliverables
* **A working solution** that implements your approach to filling unfilled shifts.
  * The solution **must be written in Python**.
  * The solution **must satisfy all scheduling constraints**.
  * You may use any tools or frameworks you consider appropriate (e.g., machine learning models, optimization solvers, rule-based systems).
  * Include a **SOLUTION.md** with:
    * A high-level description of the solution
    * The rationale behind the methodology
    * An evaluation of results (including any metrics/observations you used)
    * Step-by-step instructions to:
      * create a virtual environment
      * build a Docker image
      * deploy and run the service locally
    * An example request (e.g., `curl`) demonstrating how to call the service endpoint
* **Push your code** to the provided repository in a **new branch**, and submit a **merge request to `main`**.
* Your work will be evaluated on:
  * **Solution quality** (how likely the recommended employee is to accept the assignment)
  * **Processing time**
