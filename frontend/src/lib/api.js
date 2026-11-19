const API = import.meta.env.VITE_API_URL
  || `${window.location.protocol}//${window.location.hostname}:8000/api`;

export async function api(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API}${path}`, {
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      ...options,
    });
  } catch {
    throw new Error(`Cannot reach VolunteerMatchAI backend at ${API}. Start the FastAPI server and try again.`);
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${response.status})`);
  }
  return response.status === 204 ? null : response.json();
}
