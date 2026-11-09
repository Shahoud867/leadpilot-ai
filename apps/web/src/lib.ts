export type Row = Record<string, any>;
let csrf = "";
export function setCsrf(value: string) {
  csrf = value;
}
export async function api(
  path: string,
  body?: unknown,
  method = "POST",
): Promise<any> {
  const res = await fetch("/api/v1" + path, {
    method: body === undefined ? "GET" : method,
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
      ...(body === undefined
        ? {}
        : { "X-CSRF-Token": csrf, "Idempotency-Key": crypto.randomUUID() }),
    },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  const data = await res
    .json()
    .catch(() => ({ detail: "The server returned an unreadable response." }));
  if (!res.ok)
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : Array.isArray(data.detail)
          ? data.detail
              .map((x: Row) => `${x.loc?.slice(1).join(".")}: ${x.msg}`)
              .join("; ")
          : "Request failed",
    );
  return data;
}
export const money = (n: number) =>
  new Intl.NumberFormat("en-PK", {
    style: "currency",
    currency: "PKR",
    maximumFractionDigits: 0,
  }).format(n || 0);
export const num = (n: number) => new Intl.NumberFormat("en-PK").format(n || 0);
export const date = (s: string, full = false) =>
  s
    ? new Date(s).toLocaleString("en-PK", {
        timeZone: "Asia/Karachi",
        month: "short",
        day: "numeric",
        ...(full ? { hour: "2-digit", minute: "2-digit" } : {}),
      })
    : "—";
export const initials = (s: string) =>
  s
    ?.split(" ")
    .slice(0, 2)
    .map((s) => s[0])
    .join("") || "?";
export const label = (s: string) =>
  s?.replaceAll("_", " ").replace(/^./, (s) => s.toUpperCase()) || "—";
export const stages = [
  "new",
  "assigned",
  "contacted",
  "qualified",
  "appointment",
  "won",
  "lost",
  "dormant",
  "reopened",
  "archived",
];
export const nextStages: Record<string, string[]> = {
  new: ["dormant", "lost", "archived"],
  assigned: ["contacted", "dormant", "lost", "archived"],
  contacted: ["qualified", "dormant", "lost", "archived"],
  qualified: ["appointment", "lost", "archived"],
  appointment: ["won", "lost", "archived"],
  dormant: ["reopened", "archived"],
  reopened: ["contacted", "dormant", "lost", "archived"],
  archived: ["reopened"],
};
