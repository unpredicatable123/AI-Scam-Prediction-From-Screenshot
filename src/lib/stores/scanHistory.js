import { browser } from '$app/environment';

// Local-only history — there is no backend database in this build (Firestore
// is still an unresolved infra decision, see memory/project_infra_open_questions.md).
// Scoped to this browser only, not synced to an account. Deliberately stores
// no image data (localStorage's ~5-10MB quota would blow past fast with
// base64 screenshots) — only the structured result, which is what actually
// matters for a history list.
const STORAGE_KEY = 'scam-detector:history';
const MAX_ENTRIES = 100;

function readAll() {
	if (!browser) return [];
	try {
		const raw = localStorage.getItem(STORAGE_KEY);
		return raw ? JSON.parse(raw) : [];
	} catch {
		return [];
	}
}

function writeAll(entries) {
	if (!browser) return;
	try {
		localStorage.setItem(STORAGE_KEY, JSON.stringify(entries.slice(0, MAX_ENTRIES)));
	} catch {
		// quota exceeded or storage disabled — history is a convenience
		// feature, failing silently here is preferable to breaking a scan
	}
}

export function saveScan(result, fileName = '') {
	if (!browser) return;
	const entry = {
		id: result.requestId,
		fileName,
		timestamp: result.scanTimestamp ?? new Date().toISOString(),
		label: result.prediction.label,
		category: result.prediction.category,
		riskBand: result.prediction.riskBand,
		riskScore: result.prediction.riskScore,
		confidence: result.prediction.confidence,
		reasonCount: result.explanation?.reasons?.length ?? 0,
		ocrSnippet: (result.ocr?.text ?? '').slice(0, 140)
	};
	const entries = readAll().filter((e) => e.id !== entry.id);
	writeAll([entry, ...entries]);
}

export function listScans() {
	return readAll().sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
}

export function deleteScan(id) {
	writeAll(readAll().filter((e) => e.id !== id));
}

export function clearHistory() {
	writeAll([]);
}

// User feedback ("was this correct?") stored against its scan's local
// record. This is real, local storage of a real user action — not a claim
// that it automatically retrains the model. Using it for retraining would be
// a genuine future pipeline step (pulling this data, relabeling, re-running
// ml/src/training/train.py), not something that happens on its own.
export function saveFeedback(scanId, wasCorrect) {
	const entries = readAll();
	const idx = entries.findIndex((e) => e.id === scanId);
	if (idx === -1) return;
	entries[idx] = { ...entries[idx], feedback: wasCorrect ? 'correct' : 'incorrect' };
	writeAll(entries);
}

export function getStats() {
	const entries = readAll();
	const total = entries.length;
	const highRisk = entries.filter((e) => e.riskBand === 'high' || e.riskBand === 'critical').length;
	const safe = entries.filter((e) => e.label === 'genuine').length;
	const categoryCounts = {};
	for (const e of entries) {
		if (!e.category) continue;
		categoryCounts[e.category] = (categoryCounts[e.category] ?? 0) + 1;
	}
	const topCategories = Object.entries(categoryCounts)
		.sort((a, b) => b[1] - a[1])
		.slice(0, 5)
		.map(([category, count]) => ({ category, count }));

	const now = Date.now();
	const weekMs = 7 * 24 * 60 * 60 * 1000;
	const scansThisWeek = entries.filter((e) => now - new Date(e.timestamp).getTime() < weekMs).length;
	const scansThisMonth = entries.filter((e) => now - new Date(e.timestamp).getTime() < 30 * 24 * 60 * 60 * 1000).length;

	// A simple, transparent formula, not a claimed ML score: fraction of
	// scans that were genuine, penalized slightly by how many were high-risk.
	const safetyScore = total === 0 ? null : Math.round(Math.max(0, (safe / total) * 100 - (highRisk / total) * 20));

	return { total, highRisk, safe, topCategories, scansThisWeek, scansThisMonth, safetyScore };
}
