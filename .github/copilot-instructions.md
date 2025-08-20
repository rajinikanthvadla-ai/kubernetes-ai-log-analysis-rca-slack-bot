## Diagram Generation for PRs

When a Pull Request is created or updated, generate a visual diagram that summarizes the architectural or workflow changes introduced. This diagram should include:

- Modified components (e.g., Slack bot logic, RCA pipeline, Kubernetes log ingestion)
- Data flow between services (e.g., Prometheus → RCA → Slack)
- Any new endpoints, triggers, or anomaly detection logic added
- Highlighted areas of change compared to the base branch

### Tools & Format
- Use Mermaid.js syntax for inline diagrams in markdown
- Embed the diagram in the PR description under a collapsible section
- Example trigger: If files in `src/rca/`, `src/slack/`, or `src/k8s/` are modified, include a diagram

### Example Mermaid Block
<details>
<summary>📊 Architecture Changes</summary>

```mermaid
graph TD
    Prometheus -->|logs| RCA
    RCA -->|alerts| SlackBot
    SlackBot -->|messages| SlackChannel
    RCA -->|new| AnomalyDetector
