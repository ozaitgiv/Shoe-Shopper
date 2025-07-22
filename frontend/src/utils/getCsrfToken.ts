export async function getCsrfToken() {
  console.log("Calling /api/csrf/");
  const res = await fetch("http://127.0.0.1:8000/api/csrf/", {
    credentials: "include",
  });
  const data = await res.json();
  return data.csrfToken;
}
