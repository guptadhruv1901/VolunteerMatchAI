const localHost = ["localhost", "127.0.0.1"].includes(window.location.hostname)
  ? "127.0.0.1"
  : window.location.hostname;
const API = import.meta.env.VITE_API_URL
  || `${window.location.protocol}//${localHost}:8000/api`;

export async function api(path, options = {}) {
  const request = () => fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  let response;
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      response = await request();
      break;
    } catch {
      if (attempt === 2) {
        throw new Error(`Cannot reach VolunteerMatchAI backend at ${API}. Start the FastAPI server and try again.`);
      }
      await new Promise(resolve => setTimeout(resolve, 300));
    }
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${response.status})`);
  }
  return response.status === 204 ? null : response.json();
}
