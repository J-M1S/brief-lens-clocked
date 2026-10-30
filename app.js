"use strict";
const brief = document.querySelector("#brief");
const count = document.querySelector("#count");
const consent = document.querySelector("#consent");
const error = document.querySelector("#error");
const analyze = document.querySelector("#analyze");
const sampleButton = document.querySelector("#sample");
const example = "Fictional request: Please prepare one 1,200-word article about caring for indoor plants. The budget is $240 for the first article. We can provide a style guide. AI-generated drafts are allowed, but a person must check all facts. Please send a short outline before writing.";
const labels = { budget: "Budget", deadline: "Deadline", deliverable: "Deliverable", revisions: "Revisions" };
function clearResults() {
  document.querySelector("#results").hidden = true;
  document.querySelector("#empty").hidden = false;
  document.querySelector("#badge").textContent = "AWAITING INPUT";
}
brief.addEventListener("input", () => {
  count.textContent = `${brief.value.length.toLocaleString()} / 6,000`;
  error.hidden = true;
  clearResults();
});

function node(tag, text, className) {
  const el = document.createElement(tag);
  if (className) el.className = className;
  el.textContent = text;
  return el;
}
function makeDemo() {
  function span(value) {
    const start = Array.from(example.slice(0, example.indexOf(value))).length;
    return { value, start, end: start + Array.from(value).length };
  }
  return { result: { steps: [
    { name: "evidence", result: { fields: { budget: span("$240"), deadline: { value: null }, deliverable: span("one 1,200-word article"), revisions: { value: null } } } },
    { name: "policy", result: { answers: { ai_permission: { choice: "allowed" }, external_contact: { choice: "not_stated" } } } },
    { name: "question", result: { fields: { follow_up: { value: "What is the expected delivery date and how many revisions are included?", source: "generated" } } } }
  ] } };
}
function resultOf(steps, name) {
  const step = steps.find(item => item && item.name === name);
  return step && step.result && typeof step.result === "object" ? step.result : null;
}
function verifiedSpan(text, field) {
  if (!field || typeof field.value !== "string" || !Number.isInteger(field.start) || !Number.isInteger(field.end)) return false;
  const chars = Array.from(text);
  return field.start >= 0 && field.end <= chars.length && chars.slice(field.start, field.end).join("") === field.value;
}
function render(data, text, mode) {
  const steps = Array.isArray(data?.result?.steps) ? data.result.steps : [];
  const extraction = resultOf(steps, "evidence");
  const decision = resultOf(steps, "policy");
  const generated = resultOf(steps, "question");
  const fields = extraction?.fields || {};
  document.querySelector("#empty").hidden = true;
  document.querySelector("#results").hidden = false;
  document.querySelector("#badge").textContent = mode === "recorded" ? "RECORDED EXAMPLE" : mode === "illustrative" ? "ILLUSTRATIVE" : "NEEDS REVIEW";
  document.querySelector("#notice").textContent = mode === "recorded" ? "Recorded Clocked response to a fictional brief (October 30, 2026). No new request was made." : mode === "illustrative" ? "Fictional demonstration. The values below are prewritten; no Clocked request was made." : `Clocked response received${data.credits ? ` · ${data.credits} credits reported` : ""}. Review each result against the original text.`;
  const facts = document.querySelector("#facts");
  facts.replaceChildren();
  const missing = [];
  Object.entries(labels).forEach(([key, label]) => {
    const field = fields[key];
    const card = node("div", "", "fact");
    card.append(node("strong", label));
    if (verifiedSpan(text, field)) {
      card.append(node("div", `“${field.value}”`));
      card.append(node("small", "Matched to source"));
    } else {
      missing.push(label.toLowerCase());
      card.append(node("div", extraction ? "Not established — ask" : "Extraction unavailable — review manually"));
      if (field?.value) card.append(node("small", "Returned text could not be matched to the source"));
    }
    facts.append(card);
  });
  const flags = document.querySelector("#flags");
  flags.replaceChildren();
  if (missing.length) flags.append(node("div", `Check ${missing.join(", ")}; the extraction did not establish them.`));
  const ai = decision?.answers?.ai_permission?.choice;
  if (ai === "allowed") flags.append(node("div", "AI use appears to be permitted; confirm scope and handling of private materials."));
  else if (ai === "restricted") flags.append(node("div", "AI use appears restricted; confirm the permitted workflow before proposing."));
  else flags.append(node("div", "AI permission is not established; ask before using AI."));
  const contact = decision?.answers?.external_contact?.choice;
  if (contact === "requested") flags.append(node("div", "Off-platform communication appears requested; review the platform’s rules first."));
  else if (!decision) flags.append(node("div", "Policy check unavailable; review communication and AI conditions yourself."));
  const suggestion = generated?.fields?.follow_up?.value;
  document.querySelector("#question").textContent = typeof suggestion === "string" && suggestion.trim() ? suggestion : "A generated question is unavailable. Ask the client about any condition you need before agreeing.";
}
sampleButton.addEventListener("click", async () => {
  brief.value = example;
  brief.dispatchEvent(new Event("input"));
  consent.checked = false;
  error.hidden = true;
  try {
    const response = await fetch("/live-check-fictional.json");
    if (!response.ok) throw new Error("Recorded example unavailable");
    render(await response.json(), example, "recorded");
  } catch (_) {
    render(makeDemo(), example, "illustrative");
  }
});
analyze.addEventListener("click", async () => {
  error.hidden = true;
  if (!brief.value.trim()) { error.textContent = "Add a project brief first, or try the fictional example."; error.hidden = false; return; }
  if (!consent.checked) { error.textContent = "Confirm the external-processing notice before sending the text."; error.hidden = false; return; }
  const submittedText = brief.value;
  clearResults();
  analyze.disabled = true;
  brief.disabled = true;
  consent.disabled = true;
  sampleButton.disabled = true;
  analyze.firstChild.textContent = "Analyzing… ";
  try {
    const response = await fetch("/api/analyze", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text: submittedText, consent: true }) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Analysis failed.");
    render(data, submittedText, "live");
  } catch (err) {
    error.textContent = err.message || "Analysis failed.";
    error.hidden = false;
  } finally {
    analyze.disabled = false;
    brief.disabled = false;
    consent.disabled = false;
    sampleButton.disabled = false;
    analyze.firstChild.textContent = "Analyze with Clocked ";
  }
});
