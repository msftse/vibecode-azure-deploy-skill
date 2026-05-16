async function getHello() {
  const base = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";
  try {
    const res = await fetch(`${base}/api/hello`, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return (await res.json()) as { count: number; timestamp: string };
  } catch (e) {
    return { error: String(e) };
  }
}

export default async function Page() {
  const data = await getHello();
  return (
    <main style={{ maxWidth: 640, margin: "10vh auto", padding: "0 1.5rem" }}>
      <h1 style={{ fontSize: "2.25rem", marginBottom: "0.5rem" }}>
        hello-fullstack
      </h1>
      <p style={{ opacity: 0.7, marginTop: 0 }}>
        Next.js → FastAPI → Postgres, deployed to Azure.
      </p>
      <section
        style={{
          marginTop: "2rem",
          padding: "1.5rem",
          borderRadius: 12,
          background: "#11161f",
          border: "1px solid #1f2937",
        }}
      >
        {"error" in data ? (
          <code style={{ color: "#f87171" }}>{data.error}</code>
        ) : (
          <>
            <div style={{ fontSize: "3rem", fontWeight: 700 }}>
              {data.count}
            </div>
            <div style={{ opacity: 0.6, fontSize: "0.85rem" }}>
              as of {data.timestamp}
            </div>
          </>
        )}
      </section>
      <p style={{ marginTop: "2rem", opacity: 0.5, fontSize: "0.85rem" }}>
        Refresh to increment the counter — backed by Postgres Flexible Server.
      </p>
    </main>
  );
}
