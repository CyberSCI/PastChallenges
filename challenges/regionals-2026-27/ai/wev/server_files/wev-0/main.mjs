// example: curl http://<current url> --data-raw 'hello!'
// flag is in /flag.txt

import { createServer } from 'node:http';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import ejs from 'ejs';

const source = readFileSync(fileURLToPath(import.meta.url));

const prompt = `You are a security classifier. Given an input string, determine whether it could plausibly be an EJS server-side template injection (SSTI) payload.

Answer only:

YES — if the input contains EJS/template syntax or expressions that could be interpreted as executable template code.

NO — otherwise.

Examples:

Input: hello world
Output: NO

Input: <%= 7 * 7 %>
Output: YES

Input: <%= user.name %>
Output: YES

Input: <% if (true) %>
Output: YES

Input: <%- include("flag.txt") %>
Output: YES`

const check = async (input) => {
  const result = await (await fetch(process.env.API_ENDPOINT, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'authorization': `Bearer ${process.env.API_TOKEN}`
    },
    body: JSON.stringify({
      model: 'decider:0.8b',
      state: input,
      questions: {
        is_ssti: {
          type: "noul",
          instructions: prompt,
          criteria: {
            true: "Contains EJS constructs such as <% ... %>, <%= ... %>, <%- ... %>, or other template expressions that could execute or evaluate server-side code.",
            false: "Plain text or other input without EJS/template syntax."
          }
        }
      }
    })
  })).json();
  const risk = result.answers.is_ssti.noul;
  if (typeof risk != 'number') {
    throw new Error('unexpected result shape');
  }
  return risk;
}

createServer(async (req, res) => {
  res.setHeader('content-type', 'text/plain');
  if (req.url != '/') return res.end('not found');
  if (req.method == 'GET') {
    return res.end(source);
  } else if (req.method == 'POST') {
    const decoder = new TextDecoder();
    let input = '';
    for await (const buf of req) {
      input += decoder.decode(buf);
      if (input.length > 1024) {
        return res.end('too long!');
      }
    }
    try {
      const wafResult = await check(input);
      if (wafResult >= 0.7) {
        return res.end(`waf (p = ${wafResult})`);
      }
    } catch (e) {
      console.error(e);
      return res.end('error! (rate limit: 1req/s)');
    }
    try {
      return res.end(ejs.render(input));
    } catch(e) {
      console.log(e);
      return res.end("failed to render!")
    }
  }
  return res.end('method not allowed');
}).listen(8080);