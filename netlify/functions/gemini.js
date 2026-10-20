// Netlify Serverless Function: Google Gemini API Connector
// Securely reads GEMINI_API_KEY from Netlify Environment Variables

exports.handler = async (event) => {
  // Handle CORS Preflight
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'POST, OPTIONS'
  };

  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 204,
      headers: corsHeaders,
      body: ''
    };
  }

  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      headers: corsHeaders,
      body: JSON.stringify({ error: 'Method Not Allowed' })
    };
  }

  try {
    const payload = JSON.parse(event.body || '{}');
    const query = payload.query || '';
    const context = payload.context || '';
    const clientKey = payload.apiKey || '';

    // Prioritize Netlify Environment Variable GEMINI_API_KEY
    const apiKey = process.env.GEMINI_API_KEY || clientKey;

    if (!apiKey) {
      return {
        statusCode: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          fallback: true,
          error: 'GEMINI_API_KEY is not configured in Netlify environment variables.'
        })
      };
    }

    // Build the Grounded RAG Prompt matching SMU Assistant Standards
    const systemPrompt = `You are the official Saint Mary's University (SMU) Knowledge Assistant.
Your mission is to provide accurate, authoritative, student-focused answers synthesized strictly from verified SMU documentation.

Rules:
1. Base your answer ONLY on the verified context provided below.
2. If the context does not answer the question or lacks specific details, state clearly that the official FAQ dataset does not contain this information and refer them to smu.ca.
3. Always cite the relevant FAQ identifier (e.g. [SMU-FAQ-010]) when stating facts.
4. Keep the tone helpful, professional, and clear. Format with readable paragraphs or bullet points where appropriate.

Verified Knowledge Base Context:
${context}

User Question:
${query}

Answer:`;

    // Candidate Gemini models in order of priority
    const models = ['gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-2.0-flash'];
    let generatedText = null;
    let modelUsed = null;
    let lastError = null;

    for (const model of models) {
      try {
        const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`;
        const response = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            contents: [
              {
                role: 'user',
                parts: [{ text: systemPrompt }]
              }
            ],
            generationConfig: {
              temperature: 0.15,
              maxOutputTokens: 850
            }
          })
        });

        if (response.ok) {
          const data = await response.json();
          const candidate = data.candidates && data.candidates[0];
          if (candidate && candidate.content && candidate.content.parts && candidate.content.parts[0]) {
            generatedText = candidate.content.parts[0].text;
            modelUsed = model;
            break;
          }
        } else {
          const errData = await response.text();
          lastError = `Model ${model} returned HTTP ${response.status}: ${errData}`;
        }
      } catch (fetchErr) {
        lastError = fetchErr.message;
      }
    }

    if (generatedText) {
      return {
        statusCode: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          answer: generatedText,
          backend: `Google Gemini API (${modelUsed})`,
          model: modelUsed,
          is_grounded: true,
          fallback: false
        })
      };
    } else {
      return {
        statusCode: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          fallback: true,
          error: lastError || 'Gemini API call unsuccessful, triggering offline synthesizer.'
        })
      };
    }

  } catch (err) {
    return {
      statusCode: 200,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        fallback: true,
        error: `Serverless function error: ${err.message}`
      })
    };
  }
};
