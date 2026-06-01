import express from 'express';
import cors from 'cors';
import rateLimit from 'express-rate-limit';
import Anthropic from '@anthropic-ai/sdk';
import 'dotenv/config';

const app = express();

app.use(cors({
  origin: process.env.ALLOWED_ORIGIN || 'http://localhost:5173',
}));

app.use(express.json());

app.use(rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 30,
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: 'Too many requests — please wait before trying again.' },
}));

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

const systemPrompt = `You are an academic research assistant. When given a research topic, search for and return the 5 most recent relevant academic papers from arXiv (Cornell), MIT, Harvard, IEEE, ACM and similar authoritative sources.

For each paper, return a JSON array with this EXACT structure:
[
  {
    "title": "Full paper title",
    "authors": "Author names (comma separated, max 3 then et al.)",
    "source": "arXiv / MIT / Harvard / IEEE / ACM / etc",
    "date": "Month Year or YYYY-MM-DD",
    "abstract": "2-3 sentence summary of the key findings or contribution",
    "url": "Direct https:// URL to paper if confirmed by search results, otherwise empty string",
    "tags": ["tag1", "tag2", "tag3"],
    "evidence_map": ["Short verbatim excerpt from a web search result that confirms this paper exists"]
  }
]

Rules:
- Return ONLY the JSON array. No preamble, no markdown, no explanation.
- Focus on papers from 2024-2026 where possible.
- Only include a URL if a web search result directly confirms it. Use empty string otherwise.
- evidence_map must contain 1-3 short verbatim excerpts from actual web search results. If no search results confirm the paper, set evidence_map to [].
- Do NOT invent or guess paper URLs.`;

const SAFE_LABEL_RE = /^[\w\s\-,().]+$/;

function sanitizeTopicLabel(raw) {
  const trimmed = raw.trim().slice(0, 100);
  if (!SAFE_LABEL_RE.test(trimmed)) {
    return trimmed.replace(/[^\w\s\-,().]/g, ' ').replace(/\s+/g, ' ').trim();
  }
  return trimmed;
}

function sanitizePapers(papers) {
  return papers.map(p => ({
    ...p,
    url: typeof p.url === 'string' && /^https:\/\//i.test(p.url) ? p.url : '',
    evidence_map: Array.isArray(p.evidence_map) ? p.evidence_map.map(String).slice(0, 3) : [],
  }));
}

app.post('/api/papers', async (req, res) => {
  const { topicLabel } = req.body;
  if (!topicLabel || typeof topicLabel !== 'string') {
    return res.status(400).json({ error: 'topicLabel is required' });
  }

  const safeLabel = sanitizeTopicLabel(topicLabel);

  try {
    const response = await client.messages.create({
      model: 'claude-sonnet-4-6',
      max_tokens: 1200,
      system: systemPrompt,
      tools: [{ type: 'web_search_20250305', name: 'web_search' }],
      messages: [
        {
          role: 'user',
          content: `Find the 5 most recent academic papers about: ${safeLabel}. Search for recent 2024-2026 papers from arXiv, MIT, Harvard, IEEE, and ACM. Return results as a JSON array.`,
        },
      ],
    });

    const textBlocks = response.content?.filter(b => b.type === 'text') || [];
    const rawText = textBlocks.map(b => b.text).join('');

    let papers = [];
    try {
      const match = rawText.match(/\[[\s\S]*\]/);
      if (match) papers = JSON.parse(match[0]);
    } catch {
      try { papers = JSON.parse(rawText); } catch { papers = []; }
    }

    res.json({ papers: sanitizePapers(papers) });
  } catch (err) {
    console.error(`Error fetching papers for "${safeLabel}":`, err.message);
    res.status(500).json({ error: 'Failed to fetch papers. Please try again.' });
  }
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => console.log(`Server running on http://localhost:${PORT}`));
