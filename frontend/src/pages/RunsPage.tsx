import { useEffect, useState } from "react";
import { listRuns } from "../lib/api";

type Run = {
  id: string;
  kind: string;
  status: string;
  session_id: string;
  created_at: number;
};

export function RunsPage() {
  const [runs, setRuns] = useState<Run[]>([]);
  useEffect(() => {
    listRuns().then(setRuns).catch(() => setRuns([]));
  }, []);

  return (
    <div className="runs-page">
      <h2>Runs</h2>
      {runs.length === 0 ? (
        <div className="runs-empty">No runs yet. Ask the agent to build a report.</div>
      ) : (
        <table className="runs-table">
          <thead>
            <tr>
              <th>Run</th>
              <th>Kind</th>
              <th>Status</th>
              <th>When</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((r) => (
              <tr key={r.id}>
                <td>
                  <code>{r.id.slice(0, 8)}</code>
                </td>
                <td>{r.kind}</td>
                <td>
                  <span className={`status status-${r.status}`}>{r.status}</span>
                </td>
                <td>{new Date(r.created_at * 1000).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
