import { json, error } from '@sveltejs/kit';

// The browser never talks to the AI service directly — this route is the
// trust boundary (blueprint docs/BLUEPRINT.md §4.2). Local-first for now:
// no auth/Firestore/quota layer yet, since those depend on infrastructure
// decisions that are explicitly still open (memory/project_infra_open_questions.md).
const AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://127.0.0.1:8000';

const ACCEPTED_TYPES = ['image/png', 'image/jpeg', 'image/webp'];
const MAX_BYTES = 10 * 1024 * 1024;

export async function POST({ request }) {
	const formData = await request.formData();
	const file = formData.get('file');

	if (!file || typeof file === 'string') {
		error(422, 'No file provided');
	}
	if (!ACCEPTED_TYPES.includes(file.type)) {
		error(415, `Unsupported file type: ${file.type}`);
	}
	if (file.size > MAX_BYTES) {
		error(413, 'File too large (max 10MB)');
	}

	const upstreamForm = new FormData();
	upstreamForm.append('file', file, file.name);

	let response;
	try {
		response = await fetch(`${AI_SERVICE_URL}/v1/predict`, {
			method: 'POST',
			body: upstreamForm,
			signal: AbortSignal.timeout(30_000)
		});
	} catch (err) {
		console.error('AI service unreachable:', err);
		error(503, 'The analysis service is unavailable. Is the AI service running?');
	}

	if (!response.ok) {
		const detail = await response.text().catch(() => '');
		console.error('AI service error:', response.status, detail);
		error(response.status >= 500 ? 502 : response.status, 'Analysis failed');
	}

	const result = await response.json();
	return json(result);
}
