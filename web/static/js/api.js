// Thin client for the Python server in web/server.py.

async function request(path, body) {
  const res = await fetch(path, body === undefined
    ? { cache: "no-store" }
    : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  let data;
  try {
    data = await res.json();
  } catch {
    throw new Error(`The server sent an unreadable reply (${res.status}).`);
  }
  if (!res.ok) throw new Error(data.error || `Request failed (${res.status}).`);
  return data;
}

export const api = {
  levels: () => request("/api/levels"),
  level: id => request(`/api/levels/${encodeURIComponent(id)}`),
  options: () => request("/api/options"),
  step: (level, state, action) => request("/api/step", { level, state, action }),
  solve: (level, solver, cost, heuristic) => request("/api/solve", { level, solver, cost, heuristic }),
};
