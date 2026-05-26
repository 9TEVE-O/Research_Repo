import express from 'express';
import cors from 'cors';
import Anthropic from '@anthropic-ai/sdk';
import 'dotenv/config';

const app = express();
app.use(cors());
app.use(express.json());

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

const systemPrompt = `You are an academic research assistant. When given a research topic query, search for and return the 5 most recent and relevant academic papers from arXiv (Cornell), MIT, Harvard, IEEE, ACM and similar authoritative sources.

For each paper, return a JSON array with this EXACT structure:
[
  {
    "title": "Full paper title",
    "authors": "Author names (comma separated, max 3 then et al.)",
    "source": "arXiv / MIT / Harvard / IEEE / ACM / etc",
    "date": "Month Year or YYYY-MM-DD",
    "abstract": "2-3 sentence summary of the key findings or contribution",
    "url": "Direct URL to paper if known, otherwise empty string",
    "tags": ["tag1", "tag2", "tag3"]
  }
]

Return ONLY the JSON array. No preamble, no markdown, no explanation. Focus on papers from 2024-2026 where possible.`;

app.post('/api/papers', async (req, res) => {
  const { topicLabel } = req.body;
  if (!topicLabel) {
    return res.status(400).json({ error: 'topicLabel is required' });
  }

  try {
    const response = await client.messages.create({
      model: 'claude-sonnet-4-6',
      max_tokens: 1000,
      system: systemPrompt,
      tools: [{ type: 'web_search_20250305', name: 'web_search' }],
      messages: [
        {
          role: 'user',
          content: `Find the 5 most recent academic papers about: ${topicLabel}. Search for recent 2024-2026 papers from arXiv, MIT, Harvard, IEEE, and ACM. Return results as a JSON array.`,
        },
      ],
    });
    res.json(response);
  } catch (err) {
    console.error(`Error fetching papers for "${topicLabel}":`, err.message);
    res.status(500).json({ error: err.message });
  }
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => console.log(`Server running on http://localhost:${PORT}`));
