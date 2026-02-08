## High-Level Description

This solution addresses the unfilled shift assignment problem using a two staged approach: (1) pattern learning from historical scheduling data to identify employee preferences, and (2) constrained optimization to assign employees to unfilled shifts while maximizing compatibility and satisfying all scheduling constraints.

The system analyzes all historical scheduling data to build employee profiles that capture preferences for specific days, shift times, durations, job types, and shift patterns. These profiles are used to compute compatibility scores between employees and unfilled shifts. A linear optimization model then assigns employees to shifts, maximizing total compatibility while enforcing constraints.

## Rationale Behind the Methodology

- Pattern Learning Approach: Historical data contains implicit signals about employee preferences through their accepted assignments. Employees who frequently work certain day/time/duration/job combinations are more likely to accept similar shifts. The solution extracts these patterns by computing probability distributions over shift characteristics for each employee.

- Compatibility Scoring: A weighted combination of preference probabilities creates a compatibility score (0.0 to 1.0) for each employee to shift pair. Weights emphasize day preferences (30%) and time preferences (25%) as primary factors, with job type (20%), duration (15%), and shift type (10%) as secondary factors.

- Constrained Optimization: A binary integer linear programming model maximizes total compatibility across all assignments. The model enforces three constraint types: weekly hours (40 hours), work days (5 days), and daily shifts (1 per day). The optimization considers existing filled shifts to ensure new assignments do not violate constraints when combined with current schedules.

- On demand Assignment: The API endpoint performs real time assignment for individual cells, solving a single shift optimization problem.

## Evaluation of Results

The solution was evaluated on the latest schedule snapshot (dated 10/8/2024) with the following metrics:

- Assignment Coverage: The system successfully assigns employees to unfilled shifts while maintaining constraint satisfaction. The optimization model ensures zero constraint violations in all assignments.

- Compatibility Scores: Mean compatibility scores for newly assigned shifts provide a measure of assignment quality.For isntance, higher scores indicate better alignment with employee historical preferences, suggesting higher likelihood of acceptance.

- Constraint Validation: All assignments are validated against the 3 constraint types. The validator checks weekly hours, work days, and daily shift limits for each employee across the scheduling week.

- Processing Performance: The solution uses efficient data structures and caching in the API layer. Employee profiles and preprocessed data are cached after initial load, enabling fast assignment responses.

- Handling Edge Cases: The system handles cases where no feasible assignment exists (infeasible optimization problem) by returning appropriate status messages. Employees who already violate constraints are excluded from consideration for new assignments.

## Step-by-Step Instructions

### Virtual Environment

1. Ensure Python 3.11 or higher is installed on your system.

2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   ```

3. Activate the virtual environment:
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

4. Install dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

Alternatively, use the Makefile (recommended): 
```bash
make setup
```

### Building a Docker Image

1. Ensure Docker is installed and running on your system.

2. Build the Docker image from the project root directory:
   ```bash
   docker build -t schedule-assignment-api .
   ```

   This will create an image named `schedule-assignment-api` using the Dockerfile in the project root.

3. Verify the image was created:
   ```bash
   docker images | grep schedule-assignment-api
   ```

### Ocne the Docker image is createed: Deploying and Running the Service Locally

This runs the API locally on your machine, inside a Docker container.

1. Run the container:
   ```bash
   docker run -p 5001:5001 schedule-assignment-api
   ```

   The service will be available at `http://localhost:5001`.

2. To run in detached mode (background):
   ```bash
   docker run -d -p 5001:5001 --name schedule-api schedule-assignment-api
   ```

3. View logs:
   ```bash
   docker logs schedule-api
   ```

4. Stop the container:
   ```bash
   docker stop schedule-api
   ```


### Example Request

Using curl (GET request):
```bash
curl 'http://localhost:5001/assign?schedule_detail_id=1954945&day_num=5'
```


Example Response (unfilled cell, assigned using algorithm):
```json
{
  "status": "assigned",
  "schedule_detail_id": 1954945,
  "day_num": 5,
  "employee_number": 3472779,
  "source": "optimization",
  "message": "Cell was unfilled and employee assigned via optimization"
}
```
Example curl request: 
```bash
curl 'http://localhost:5001/assign?schedule_detail_id=8849241&day_num=1'
```
Example Response (already filled cell):
```json
{
  "status": "filled",
  "schedule_detail_id": 8849241,
  "day_num": 1,
  "employee_number": 67890,
  "source": "existing_schedule",
  "message": "Cell is already filled in the dataset"
}
```
Example curl request: 
```bash
curl 'http://localhost:5001/assign?schedule_detail_id=9999999&day_num=1'
```
Example Response (cell not found):
```json
{
  "error": "Cell not found",
  "schedule_detail_id": 9999999,
  "day_num": 1
}
```

Health Check Endpoint:
```bash
curl http://localhost:5001/health
```

Web Interface:
Navigate to `http://localhost:5001` in a web browser to access an interactive test interface.

Thank you! 