// Development-only rendered DOM fixtures. No user profile or live Copilot connection.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

const source = fs.readFileSync(path.resolve(process.argv[2] || path.join(__dirname, '..', 'App.ps1')), 'utf8');
const definitions = [...source.matchAll(/function Get-AgentCopilotDomPrelude \{\r?\n[\s\S]*?return @'\r?\n([\s\S]*?)\r?\n'@\r?\n\}/g)];
assert.equal(definitions.length, 1, 'Read exactly one production DOM prelude');
const snapshot = '(()=>{' + definitions[0][1] + '\nreturn {inputCount:inputs.length,inputText:inputText(),generating,sendReady:sends.length===1};})()';
const fixture = '<!doctype html><meta charset="utf-8"><style>body{margin:20px}#fixture>*{display:block;min-width:300px;min-height:40px;white-space:pre-wrap}p{margin:0}</style><main id="fixture"></main>';
const trustedUrl = 'https://m365.cloud.microsoft/chat/';

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  let checks = 0;
  let fulfilled = 0;
  let blocked = 0;
  const check = (actual, expected, label) => { assert.deepEqual(actual, expected, label); checks++; };
  try {
    const context = await browser.newContext({ serviceWorkers: 'block' });
    // Every page request ends here: there is deliberately no route.continue/fetch.
    await context.route('**/*', async route => {
      if (route.request().resourceType() === 'document') {
        fulfilled++;
        await route.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: fixture });
      } else {
        blocked++;
        await route.abort('blockedbyclient');
      }
    });
    const page = await context.newPage();
    const pageErrors = [];
    page.on('pageerror', error => pageErrors.push(error.message));
    await page.goto(trustedUrl);
    const render = async (html, setup) => {
      await page.locator('#fixture').evaluate((root, markup) => { root.innerHTML = markup; }, html);
      if (setup) await page.evaluate(setup);
      const raw = await page.evaluate(() => {
        const input = document.querySelector('#m365-chat-editor-target-element');
        return input ? { innerText: input.innerText, textContent: input.textContent, value: 'value' in input ? input.value : null } : null;
      });
      return { raw, state: await page.evaluate(snapshot) };
    };
    const span = html => '<span id="m365-chat-editor-target-element" contenteditable="true">' + html + '</span>';
    let observed = await render(span('<p><br></p>'));
    check(observed.raw, { innerText: '\n', textContent: '', value: null }, 'Reproduce the measured empty M365 DOM');
    check(observed.state.inputText, '', 'Only the measured empty editor becomes an empty string');
    check(observed.state.inputCount, 1, 'Measured editor remains unique');

    for (const value of ['', '日本語の入力', ' ', '\n', ' \n日本語\n ', '\u200b\u2060\ufeff']) {
      observed = await render('<textarea id="m365-chat-editor-target-element"></textarea>');
      await page.locator('textarea').evaluate((input, text) => { input.value = text; }, value);
      check((await page.evaluate(snapshot)).inputText, value, 'Preserve textarea value ' + JSON.stringify(value));
    }

    for (const value of [' ', '\n', ' \n ', '日本語の入力', '\u200b', '\u2060\ufeff', '日本語\n改行']) {
      observed = await render(span(''));
      await page.locator('#m365-chat-editor-target-element').evaluate((input, text) => { input.appendChild(document.createTextNode(text)); }, value);
      check(await page.locator('#m365-chat-editor-target-element').innerText(), value, 'Render actual text node ' + JSON.stringify(value));
      check((await page.evaluate(snapshot)).inputText, value, 'Preserve actual text node ' + JSON.stringify(value));
    }

    observed = await render(span('<p>日本語の一段落</p><p>次の段落</p>'));
    check(observed.state.inputText, observed.raw.innerText, 'Preserve multiple paragraphs exactly as rendered');
    check(observed.state.inputText.includes('日本語の一段落') && observed.state.inputText.includes('\n') && observed.state.inputText.endsWith('次の段落'), true, 'Multiple paragraph fixture contains its line separator');

    for (const [label, html, setup] of [
      ['empty paragraph', span('<p></p>')],
      ['direct break', span('<br>')],
      ['two breaks', span('<p><br><br></p>')],
      ['nested break', span('<p><span><br></span></p>')],
      ['comment sibling', span('<p><br></p><!--retain-->')],
      ['comment within paragraph', span('<p><br><!--retain--></p>')],
      ['empty text node sibling', span('<p><br></p>'), () => document.querySelector('#m365-chat-editor-target-element').appendChild(document.createTextNode(''))],
      ['empty text node within paragraph', span('<p><br></p>'), () => document.querySelector('#m365-chat-editor-target-element p').appendChild(document.createTextNode(''))],
      ['image markup', span('<p><img alt="image"><br></p>')],
      ['mention markup', span('<p><span contenteditable="false" data-mention="example"></span><br></p>')],
      ['div root', '<div id="m365-chat-editor-target-element" contenteditable="true"><p><br></p></div>'],
      ['noneditable root', '<span id="m365-chat-editor-target-element"><p><br></p></span>'],
      ['plaintext editor root', '<span id="m365-chat-editor-target-element" contenteditable="plaintext-only"><p><br></p></span>']
    ]) {
      observed = await render(html, setup);
      check(observed.state.inputText, observed.raw.innerText, 'Do not normalize unknown shape: ' + label);
    }

    observed = await render('<textarea></textarea>');
    check(observed.state.inputCount, 0, 'No generic textarea fallback');
    check(observed.state.inputText, null, 'Unselected input has no text');
    observed = await render(span('<p><br></p>') + '<div role="textbox" contenteditable="true">draft</div>');
    check(observed.state.inputCount, 2, 'Multiple supported inputs remain ambiguous');
    check(observed.state.inputText, null, 'Ambiguous input is never treated as empty');
    // The observed startup indicator has no id, stop button, or streaming attribute.
    // Keep treating it as busy until the page removes that signal, while retaining
    // the exact empty-editor contract used before any focus or input operation.
    observed = await render(span('<p><br></p>') + '<div role="status" aria-busy="true"></div>');
    check(observed.state, { inputCount: 1, inputText: '', generating: true, sendReady: false }, 'Measured startup status is busy and its editor remains empty');
    await page.locator('[role="status"]').evaluate(status => { status.setAttribute('aria-busy', 'false'); });
    check(await page.evaluate(snapshot), { inputCount: 1, inputText: '', generating: false, sendReady: false }, 'Startup aria-busy false clears generating without changing the editor');
    await page.locator('[role="status"]').evaluate(status => { status.setAttribute('aria-busy', 'true'); });
    check((await page.evaluate(snapshot)).generating, true, 'A returning startup busy signal is still detected');
    await page.locator('[role="status"]').evaluate(status => { status.removeAttribute('aria-busy'); });
    check(await page.evaluate(snapshot), { inputCount: 1, inputText: '', generating: false, sendReady: false }, 'Removing startup aria-busy clears generating without changing the editor');

    for (const [label, indicator] of [
      ['streaming state', '<div data-state="streaming"></div>'],
      ['streaming status', '<div data-status="streaming"></div>'],
      ['Japanese stop button', '<button aria-label="停止">停止</button>'],
      ['English stop button', '<button aria-label="Stop generating">Stop generating</button>']
    ]) {
      observed = await render(span('<p><br></p>') + indicator);
      check(observed.state, { inputCount: 1, inputText: '', generating: true, sendReady: false }, 'Continue detecting visible ' + label);
    }

    for (const [label, indicator] of [
      ['display-none startup status', '<div role="status" aria-busy="true" style="display:none"></div>'],
      ['visibility-hidden startup status', '<div role="status" aria-busy="true" style="visibility:hidden"></div>'],
      ['zero-size startup status', '<div role="status" aria-busy="true" style="min-width:0;min-height:0;width:0;height:0"></div>'],
      ['display-none streaming state', '<div data-state="streaming" style="display:none"></div>'],
      ['visibility-hidden streaming status', '<div data-status="streaming" style="visibility:hidden"></div>'],
      ['display-none stop button', '<button aria-label="停止" style="display:none">停止</button>']
    ]) {
      observed = await render(span('<p><br></p>') + indicator);
      check(observed.state, { inputCount: 1, inputText: '', generating: false, sendReady: false }, 'Exclude ' + label);
    }

    for (const [url, message] of [
      ['http://m365.cloud.microsoft/chat/', 'untrusted page'],
      ['https://m365.cloud.microsoft.evil.test/chat/', 'untrusted page'],
      ['https://m365.cloud.microsoft:444/chat/', 'untrusted page'],
      ['https://m365.cloud.microsoft/chatter', 'untrusted page'],
      ['https://m365.cloud.microsoft/chat%2fevil', 'untrusted page'],
      ['https://login.microsoftonline.com/common/oauth2/authorize', 'AGENT_AUTH_REQUIRED']
    ]) {
      await page.goto(url);
      await page.locator('#fixture').evaluate((root, markup) => { root.innerHTML = markup; }, span('<p><br></p>'));
      await assert.rejects(() => page.evaluate(snapshot), error => error.message.includes(message), 'Reject untrusted page ' + url);
      checks++;
    }
    check(pageErrors, [], 'No fixture JavaScript errors');
    check(fulfilled, 7, 'All document navigations were locally fulfilled');
    console.log(`PASS: ${checks} rendered Edge DOM checks; ${fulfilled} local document fulfillments; ${blocked} blocked other requests. No request was forwarded; no live Copilot or user profile was used.`);
  } finally { await browser.close(); }
})().catch(error => { console.error(error.stack); process.exitCode = 1; });
