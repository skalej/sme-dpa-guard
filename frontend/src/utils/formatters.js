const STATUS_MAP = {
  green: "green",
  pass: "green",
  ok: "green",
  yellow: "yellow",
  warn: "yellow",
  warning: "yellow",
  red: "red",
  fail: "red",
  failed: "red",
};

export function normalizeStatus(status) {
  if (!status) return "yellow";
  const key = String(status).toLowerCase();
  return STATUS_MAP[key] || "yellow";
}

export function statusLabel(status) {
  return normalizeStatus(status).toUpperCase();
}

export function statusPillClasses(status) {
  const normalized = normalizeStatus(status);
  if (normalized === "green") {
    return "bg-emerald-50 text-emerald-700 border border-emerald-200";
  }
  if (normalized === "red") {
    return "bg-red-50 text-red-700 border border-red-200";
  }
  return "bg-amber-50 text-amber-700 border border-amber-200";
}

export function extractTopRisks(items, maxItems = 3) {
  const scored = items.filter((item) => normalizeStatus(item.status) !== "green");
  const order = { red: 0, yellow: 1 };
  scored.sort((a, b) => {
    const aKey = normalizeStatus(a.status);
    const bKey = normalizeStatus(b.status);
    return (order[aKey] ?? 2) - (order[bKey] ?? 2);
  });
  return scored.slice(0, maxItems);
}

export function buildCopyTable(items, includePassed = false) {
  const rows = items.filter((item) =>
    includePassed ? true : normalizeStatus(item.status) !== "green"
  );
  const lines = [
    "Title\tStatus\tAnalysis\tSuggested Change",
    ...rows.map((item) => {
      const analysis = (item.analysis || "").replace(/\s+/g, " ").trim();
      const suggestion = (item.suggestedChange || "").replace(/\s+/g, " ").trim();
      return `${item.title}\t${statusLabel(item.status)}\t${analysis}\t${suggestion}`;
    }),
  ];
  return lines.join("\n");
}

const DECISION_MAP = {
  approve: "Sign",
  approved: "Sign",
  sign: "Sign",
  ok: "Sign",
  needs_changes: "Sign with changes",
  sign_with_changes: "Sign with changes",
  changes: "Sign with changes",
  review: "Sign with changes",
  reject: "Do not sign (request major changes)",
  denied: "Do not sign (request major changes)",
};

const TOP_RISK_MAP = {
  BREACH_NOTIFICATION: "Missing specific breach notification timeline",
  TRANSFERS: "International transfer terms may be insufficient",
  SECURITY_TOMS: "Security measures appear incomplete or vague",
  SUBPROCESSORS: "Subprocessor controls may be missing or too permissive",
  DELETION_RETURN: "Deletion/return obligations are unclear",
  AUDIT_RIGHTS: "Audit rights are limited or missing",
  LIABILITY: "Liability allocation is unclear or missing",
  GOVERNING_LAW: "Governing law may not align with GDPR protections",
};

export function recommendationText(decision) {
  if (!decision) return "Review";
  const key = String(decision).toLowerCase();
  return DECISION_MAP[key] || decision;
}

export function humanizeCheckId(value) {
  if (!value) return "Review issue";
  const raw = String(value).toUpperCase();
  if (TOP_RISK_MAP[raw]) return TOP_RISK_MAP[raw];
  const spaced = raw.replace(/_/g, " ").toLowerCase();
  return spaced.replace(/\b\w/g, (char) => char.toUpperCase());
}

export function normalizeExplain(data, uploadedFileName) {
  const docFileName =
    data?.document?.original_filename ||
    data?.file_name ||
    data?.document?.filename ||
    data?.filename ||
    uploadedFileName ||
    null;
  const baseTitle = docFileName ? stripExtension(docFileName) : "DPA Review";
  const docTitle = data?.document?.name || baseTitle;
  const recommendation = recommendationText(data?.decision || data?.recommendation);
  const rawItems = data?.evaluations || data?.findings || [];

  const clauses = rawItems.map((item) => {
    const title =
      item.title ||
      item.clause_title ||
      item.check_id ||
      item.clause_type ||
      item.id ||
      "Clause";
    const status = normalizeStatus(
      item.status || item.risk_label || item.risk || item.severity
    );
    const analysis =
      item.analysis || item.rationale || item.notes || item.short_reason || "";
    const suggestedChange =
      item.suggested_change || item.suggestion || item.ask || "";
    const evidence = normalizeEvidence(item.evidence || item.evidence_spans);

    return {
      id: item.check_id || item.id || item.key || title,
      title: String(title).toUpperCase(),
      severity: status,
      status,
      analysis,
      suggestedChange,
      evidence,
    };
  });

  const topRisks = extractTopRisks(clauses, 5).map((item) => ({
    text:
      item.risk_summary ||
      item.summary ||
      humanizeCheckId(item.title || item.id),
    severity: item.status === "red" ? "fail" : "warn",
  }));

  return {
    docTitle,
    docFileName,
    recommendationText: recommendation,
    topRisks,
    clauses,
    totals: {
      totalClauses: clauses.length,
      status: recommendation,
    },
  };
}

function normalizeEvidence(input) {
  if (!input) return [];
  if (typeof input === "string") {
    return [{ quote: input }];
  }
  if (Array.isArray(input)) {
    return input.map((item) => {
      if (typeof item === "string") {
        return { quote: item };
      }
      return {
        label: item.label || item.section,
        quote: item.quote || item.snippet || item.text,
      };
    });
  }
  if (typeof input === "object") {
    return [
      {
        label: input.label || input.section,
        quote: input.quote || input.snippet || input.text,
      },
    ];
  }
  return [];
}

function stripExtension(fileName) {
  if (!fileName) return "DPA Review";
  const parts = String(fileName).split(".");
  if (parts.length <= 1) return fileName;
  parts.pop();
  return parts.join(".") || fileName;
}
