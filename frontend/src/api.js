const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request(
  path,
  { method = "GET", headers = {}, body, isMultipart = false } = {}
) {
  const url = `${API_BASE_URL}${path}`;
  const fetchOptions = { method, headers: { ...headers } };

  if (body !== undefined) {
    if (isMultipart) {
      fetchOptions.body = body;
    } else if (typeof body === "object" && body !== null) {
      fetchOptions.body = JSON.stringify(body);
      fetchOptions.headers["Content-Type"] = "application/json";
    } else {
      fetchOptions.body = body;
    }
  }

  const res = await fetch(url, fetchOptions);
  let payload;
  try {
    payload = await res.json();
  } catch (err) {
    payload = await res.text();
  }

  if (!res.ok) {
    const message =
      (payload && payload.message) ||
      (payload && payload.detail) ||
      (typeof payload === "string" ? payload : "Request failed");
    const error = new Error(`HTTP ${res.status} ${res.statusText}: ${message}`);
    error.status = res.status;
    error.payload = payload;
    throw error;
  }

  return payload;
}

export function isRetryableHttpStatus(status) {
  return [408, 429, 500, 502, 503, 504].includes(status);
}

export function formatApiError(err) {
  if (!err) {
    return "Unknown error";
  }
  if (err.status) {
    return `${err.message} (status ${err.status})`;
  }
  return err.message || "Unknown error";
}

export async function healthLive() {
  return request("/health/live");
}

export async function healthReady() {
  return request("/health/ready");
}

export async function createReview(contextJson) {
  if (contextJson === undefined) {
    return request("/reviews", { method: "POST" });
  }
  return request("/reviews", {
    method: "POST",
    body: { context_json: contextJson },
  });
}

export async function getReview(reviewId) {
  return request(`/reviews/${reviewId}`);
}

export async function uploadReviewDoc(reviewId, file) {
  const formData = new FormData();
  formData.append("file", file);
  return request(`/reviews/${reviewId}/upload`, {
    method: "POST",
    body: formData,
    isMultipart: true,
  });
}

export async function startReview(reviewId) {
  return request(`/reviews/${reviewId}/start`, { method: "POST" });
}

export async function getJob(reviewId) {
  return request(`/reviews/${reviewId}/job`);
}

export async function getResults(reviewId) {
  return request(`/reviews/${reviewId}/results`);
}

export async function getExplain(reviewId) {
  return request(`/reviews/${reviewId}/explain`);
}
