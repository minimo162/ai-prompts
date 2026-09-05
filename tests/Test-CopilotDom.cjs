// Development-only rendered DOM fixtures. No user profile or live Copilot connection.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

const source = fs.readFileSync(path.resolve(process.argv[2] || path.join(__dirname, '..', 'App.ps1')), 'utf8');
const definitions = [...source.matchAll(/function Get-AgentCopilotDomPrelude \{\r?\n[\s\S]*?return @'\r?\n([\s\S]*?)\r?\n'@\r?\n\}/g)];
assert.equal(definitions.length, 1, 'Read exactly one production DOM prelude');
const snapshotDefinitions = [...source.matchAll(/function Get-AgentCopilotSnapshot \{\r?\n[\s\S]*?\$body = @'\r?\n([\s\S]*?)\r?\n'@\r?\n/g)];
assert.equal(snapshotDefinitions.length, 1, 'Read exactly one production snapshot body');
const snapshot = '(()=>{' + definitions[0][1] + '\n' + snapshotDefinitions[0][1] + '})()';
const fixture = '<!doctype html><meta charset="utf-8"><style>body{margin:20px}#fixture>*{display:block;min-width:300px;min-height:40px;white-space:pre-wrap}p{margin:0}#fixture .measured-reply,#fixture .measured-reply *{white-space:normal;opacity:1}#fixture .measured-reply{display:block}#fixture .measured-reply>.reply-wrapper{display:flex}#fixture .measured-reply>.reply-wrapper>p{display:block}</style><main id="fixture"></main>';
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
    // Evaluate the actual production snapshot, then keep the existing input assertions scoped.
    const inputState = async () => {
      const { inputCount, inputText, generating, sendReady } = await page.evaluate(snapshot);
      return { inputCount, inputText, generating, sendReady };
    };
    const render = async (html, setup) => {
      await page.locator('#fixture').evaluate((root, markup) => { root.innerHTML = markup; }, html);
      if (setup) await page.evaluate(setup);
      const raw = await page.evaluate(() => {
        const input = document.querySelector('#m365-chat-editor-target-element');
        return input ? { innerText: input.innerText, textContent: input.textContent, value: 'value' in input ? input.value : null } : null;
      });
      return { raw, state: await inputState() };
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

    const escapeText = value => value.replace(/[&<>]/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[character]));
    const lexicalMarker = '\u200b\u200c';
    const lexicalBody = value => '<span data-lexical-text="true">' + escapeText(value) + '</span>';
    const lexicalTail = '<span data-lexical-text="true" aria-hidden="true">' + lexicalMarker + '</span>';
    const markedEditor = value => span('<p>' + lexicalBody(value) + lexicalTail + '</p>');
    // This synthetic text has the measured body length without copying a live prompt.
    for (const value of ['文'.repeat(1271), '先頭行\n次の行', ' \n日本語 \n ', '本文\u200b途中\u200cと\u2060\ufeff ', '本文の末尾\u200b\u200c', '本文 <入力> & 値']) {
      observed = await render(markedEditor(value));
      check(observed.raw, { innerText: value + lexicalMarker, textContent: value + lexicalMarker, value: null }, 'Reproduce the separate Lexical marker after ' + JSON.stringify(value.length > 80 ? '1271-character synthetic body' : value));
      check(observed.state, { inputCount: 1, inputText: value, generating: false, sendReady: false }, 'Remove only the observed marker and preserve the complete body');
    }

    const body = lexicalBody('保持する本文');
    for (const [label, html, setup] of [
      ['body lacks Lexical attribute', span('<p><span>保持する本文</span>' + lexicalTail + '</p>')],
      ['body Lexical attribute is false', span('<p><span data-lexical-text="false">保持する本文</span>' + lexicalTail + '</p>')],
      ['marker lacks Lexical attribute', span('<p>' + body + '<span aria-hidden="true">' + lexicalMarker + '</span></p>')],
      ['marker lacks aria-hidden', span('<p>' + body + '<span data-lexical-text="true">' + lexicalMarker + '</span></p>')],
      ['marker aria-hidden is false', span('<p>' + body + '<span data-lexical-text="true" aria-hidden="false">' + lexicalMarker + '</span></p>')],
      ['marker precedes body', span('<p>' + lexicalTail + body + '</p>')],
      ['extra root sibling', span('<p>' + body + lexicalTail + '</p><!--retain-->')],
      ['extra paragraph child', span('<p>' + body + lexicalTail + '<!--retain--></p>')],
      ['extra body text node', markedEditor('保持する本文'), () => document.querySelector('#m365-chat-editor-target-element p > span').appendChild(document.createTextNode(''))],
      ['extra marker child', span('<p>' + body + '<span data-lexical-text="true" aria-hidden="true">' + lexicalMarker + '<!--retain--></span></p>')],
      ['nested body markup', span('<p><span data-lexical-text="true"><em>保持する本文</em></span>' + lexicalTail + '</p>')],
      ['empty body text node', markedEditor(''), () => document.querySelector('#m365-chat-editor-target-element p > span').appendChild(document.createTextNode(''))],
      ['ordinary user suffix', span('保持する本文' + lexicalMarker)],
      ['user suffix inside a single Lexical span', span('<p>' + lexicalBody('保持する本文' + lexicalMarker) + '</p>')],
      ['different marker sequence', span('<p>' + body + '<span data-lexical-text="true" aria-hidden="true">\u200c\u200b</span></p>')],
      ['incomplete marker', span('<p>' + body + '<span data-lexical-text="true" aria-hidden="true">\u200b</span></p>')],
      ['marker with extra whitespace', span('<p>' + body + '<span data-lexical-text="true" aria-hidden="true">' + lexicalMarker + ' </span></p>')],
      ['different root element', '<div id="m365-chat-editor-target-element" contenteditable="true"><p>' + body + lexicalTail + '</p></div>'],
      ['different paragraph element', span('<div>' + body + lexicalTail + '</div>')],
      ['multiple paragraphs', span('<p>' + body + lexicalTail + '</p><p>次の段落</p>')]
    ]) {
      observed = await render(html, setup);
      check(observed.state.inputText, observed.raw.innerText, 'Retain rendered input for unrecognized marker shape: ' + label);
    }
    observed = await render(markedEditor('Body'), () => { document.querySelector('#m365-chat-editor-target-element p > span').style.textTransform = 'uppercase'; });
    check(observed.raw.textContent, 'Body' + lexicalMarker, 'Mismatched rendering fixture retains its original text node');
    check(observed.raw.innerText, 'BODY' + lexicalMarker, 'Mismatched rendering fixture actually changes innerText');
    check(observed.state.inputText, observed.raw.innerText, 'Do not remove a marker when innerText differs from textContent');

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
    check(await inputState(), { inputCount: 1, inputText: '', generating: false, sendReady: false }, 'Startup aria-busy false clears generating without changing the editor');
    await page.locator('[role="status"]').evaluate(status => { status.setAttribute('aria-busy', 'true'); });
    check((await page.evaluate(snapshot)).generating, true, 'A returning startup busy signal is still detected');
    await page.locator('[role="status"]').evaluate(status => { status.removeAttribute('aria-busy'); });
    check(await inputState(), { inputCount: 1, inputText: '', generating: false, sendReady: false }, 'Removing startup aria-busy clears generating without changing the editor');

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

    const reply = (value, messageId = 'reply-fixture') => '<div dir="auto" aria-hidden="false" class="measured-reply" data-testid="markdown-reply" data-message-id="' + messageId + '" data-message-type="Chat"><div class="reply-wrapper"><p>' + escapeText(value) + '</p></div></div>';
    const renderReply = async (html, setup, css = '') => {
      await page.evaluate(({ markup, extraCss }) => {
        const previousStyle = document.querySelector('#response-case-style');
        if (previousStyle) previousStyle.remove();
        document.querySelector('#fixture').innerHTML = markup;
        if (extraCss) {
          const style = document.createElement('style');
          style.id = 'response-case-style';
          style.textContent = extraCss;
          document.head.appendChild(style);
        }
      }, { markup: html, extraCss: css });
      if (setup) await page.evaluate(setup);
      const raw = await page.evaluate(() => {
        const root = document.querySelector('#fixture .measured-reply') || document.querySelector('#fixture').firstElementChild;
        const paragraph = root && root.querySelector('p');
        return root ? {
          innerText: root.innerText,
          textContent: root.textContent,
          nodeValue: paragraph && paragraph.firstChild && paragraph.firstChild.nodeValue,
          path: paragraph ? [root, paragraph.parentElement, paragraph].map(element => {
            const style = getComputedStyle(element);
            return { tag: element.tagName, attributes: element.attributes.length, children: element.childNodes.length, display: style.display, whiteSpace: style.whiteSpace, visibility: style.visibility, opacity: style.opacity };
          }) : []
        } : null;
      });
      return { raw, state: await page.evaluate(snapshot) };
    };
    const requestId = '0123456789abcdef0123456789abcdef';
    const responseJson = JSON.stringify({ request_id: requestId, state: 'DONE', message: '日本語の fixture', robin: '', artifacts: [] });
    const marker = 'AGENT_END_' + requestId;
    const responseText = responseJson + '\n' + marker;
    let response = await renderReply(reply(responseText));
    check(response.raw.path, [
      { tag: 'DIV', attributes: 6, children: 1, display: 'block', whiteSpace: 'normal', visibility: 'visible', opacity: '1' },
      { tag: 'DIV', attributes: 1, children: 1, display: 'flex', whiteSpace: 'normal', visibility: 'visible', opacity: '1' },
      { tag: 'P', attributes: 0, children: 1, display: 'block', whiteSpace: 'normal', visibility: 'visible', opacity: '1' }
    ], 'Reproduce the measured assistant element path and computed styles');
    check(response.raw.innerText, responseJson + ' ' + marker, 'Normal white-space really collapses the response LF to a space');
    check(response.raw.textContent, responseText, 'The measured response textContent retains its LF');
    check(response.raw.nodeValue, responseText, 'The measured paragraph has the complete original text node');
    check(response.state.assistants, [{ key: 'reply-fixture', text: responseText, collapsed: false }], 'Production snapshot returns the original response node without guessing a marker boundary');

    for (const value of [
      responseJson,
      responseJson + ' ' + marker,
      '  日本語 "引用" O\'Brien C:\\path\\raw %FileContents%  \n' + marker,
      'actual\nLF and literal \\n stay distinct\n\n' + marker,
      ' \n日本語  の本文\n\n末尾 \n ',
      '本文\u200b途中\u200cと\u2060\ufeff\n' + marker,
      '<JSON> & "quotes" \\ %\n' + marker
    ]) {
      response = await renderReply(reply(value));
      check(response.raw.nodeValue, value, 'Fixture retains the complete response text node ' + JSON.stringify(value));
      check(response.state.assistants, [{ key: 'reply-fixture', text: value, collapsed: false }], 'Preserve every original response character ' + JSON.stringify(value));
    }

    const measuredReply = reply(responseText);
    for (const [label, html, setup, css] of [
      ['different supported selector', measuredReply.replace('data-testid="markdown-reply"', 'data-content="ai-message"')],
      ['different root element', measuredReply.replace(/^<div /, '<section ').replace(/<\/div>$/, '</section>')],
      ['different direction', measuredReply.replace('dir="auto"', 'dir="ltr"')],
      ['missing root aria-hidden', measuredReply.replace(' aria-hidden="false"', '')],
      ['root aria-hidden true', measuredReply.replace('aria-hidden="false"', 'aria-hidden="true"')],
      ['empty root class', measuredReply.replace('class="measured-reply"', 'class=""')],
      ['empty message id', measuredReply.replace('data-message-id="reply-fixture"', 'data-message-id=""')],
      ['different message type', measuredReply.replace('data-message-type="Chat"', 'data-message-type="Other"')],
      ['extra root attribute', measuredReply.replace('dir="auto"', 'dir="auto" title="extra"')],
      ['hidden root attribute', measuredReply.replace('dir="auto"', 'dir="auto" hidden')],
      ['extra root child', measuredReply.replace(/<\/div>$/, '<span>extra</span></div>')],
      ['root comment child', measuredReply.replace(/<\/div>$/, '<!--retain--></div>')],
      ['wrapper comment child', measuredReply.replace('</p>', '</p><!--retain-->')],
      ['empty root text sibling', measuredReply, () => document.querySelector('.measured-reply').appendChild(document.createTextNode(''))],
      ['extra wrapper attribute', measuredReply.replace('class="reply-wrapper"', 'class="reply-wrapper" title="extra"')],
      ['empty wrapper class', measuredReply.replace('class="reply-wrapper"', 'class=""')],
      ['missing wrapper class', measuredReply.replace(' class="reply-wrapper"', '')],
      ['different wrapper type', measuredReply.replace('<div class="reply-wrapper">', '<section class="reply-wrapper">').replace('</p></div>', '</p></section>')],
      ['paragraph attribute', measuredReply.replace('<p>', '<p class="extra">')],
      ['different paragraph type', measuredReply.replace('<p>', '<div>').replace('</p>', '</div>')],
      ['paragraph comment child', measuredReply.replace('</p>', '<!--retain--></p>')],
      ['split paragraph text', measuredReply, () => document.querySelector('.measured-reply p').firstChild.splitText(1)],
      ['nested paragraph markup', measuredReply.replace('<p>', '<p><span>').replace('</p>', '</span></p>')],
      ['empty paragraph', reply('')],
      ['empty paragraph text node', reply(''), () => document.querySelector('.measured-reply p').appendChild(document.createTextNode(''))],
      ['hidden injected span', reply(responseJson).replace('</p>', '<span hidden style="display:none">\n' + marker + '</span></p>')],
      ['root display none', measuredReply, null, '.measured-reply{display:none!important}'],
      ['root visibility hidden', measuredReply, null, '.measured-reply{visibility:hidden!important}'],
      ['root opacity zero', measuredReply, null, '.measured-reply{opacity:0!important}'],
      ['root opacity partial', measuredReply, null, '.measured-reply{opacity:.5!important}'],
      ['root display flex', measuredReply, null, '.measured-reply{display:flex!important}'],
      ['wrapper display block', measuredReply, null, '.reply-wrapper{display:block!important}'],
      ['paragraph display grid', measuredReply, null, '.measured-reply p{display:grid!important}'],
      ['root pre-wrap', measuredReply, null, '.measured-reply{white-space:pre-wrap!important}'],
      ['wrapper pre-wrap', measuredReply, null, '.reply-wrapper{white-space:pre-wrap!important}'],
      ['paragraph pre-wrap', measuredReply, null, '.measured-reply p{white-space:pre-wrap!important}'],
      ['wrapper opacity partial', measuredReply, null, '.reply-wrapper{opacity:.5!important}'],
      ['paragraph opacity partial', measuredReply, null, '.measured-reply p{opacity:.5!important}'],
      ['hidden ancestor', '<section hidden>' + measuredReply + '</section>'],
      ['aria-hidden ancestor', '<section aria-hidden="true">' + measuredReply + '</section>'],
      ['display-none ancestor', '<section style="display:none">' + measuredReply + '</section>'],
      ['visibility-hidden ancestor with visible reply', '<section style="visibility:hidden">' + measuredReply + '</section>', null, '.measured-reply{visibility:visible!important}'],
      ['partial-opacity ancestor', '<section style="opacity:.5">' + measuredReply + '</section>']
    ]) {
      response = await renderReply(html, setup, css);
      // A flex item with display:inline computes to block, so use and verify a truly different computed display.
      if (label === 'paragraph display grid') check(response.raw.path[2].display, 'grid', 'The ineligible paragraph really computes to grid');
      check(response.state.assistants.length, 1, 'Retain the existing assistant candidate for ineligible shape: ' + label);
      // Legacy innerText can itself include text for an entirely hidden root. This
      // assertion preserves that behavior; it does not claim to reject hidden replies.
      check(response.state.assistants[0].text, response.raw.innerText || '', 'Use exactly the legacy rendered text for ineligible shape: ' + label);
      if (label === 'hidden injected span') {
        check(response.raw.textContent.includes(marker), true, 'Hidden injection fixture actually contains a marker in textContent');
        check(response.state.assistants[0].text.includes(marker), false, 'A hidden injected marker is not promoted into the extracted response');
      }
    }

    for (const [label, html] of [
      ['BR separator', measuredReply.replace(escapeText(responseText), escapeText(responseJson) + '<br>' + marker)],
      ['paragraph separator', measuredReply.replace(escapeText(responseText), escapeText(responseJson) + '</p><p>' + marker)]
    ]) {
      response = await renderReply(html);
      check(response.raw.innerText.includes('\n'), true, 'Structural response fixture renders an LF: ' + label);
      check(response.raw.textContent, responseJson + marker, 'Structural response textContent omits the rendered separator: ' + label);
      check(response.state.assistants[0].text, response.raw.innerText, 'Preserve structural response line breaks with the legacy fallback: ' + label);
    }

    response = await renderReply(measuredReply.replace('data-testid="markdown-reply"', 'data-testid="unrelated"'));
    check(response.state.assistants, [], 'Do not select unrelated content as an assistant');
    response = await renderReply('<article data-message-author-role="assistant">outer-prefix' + measuredReply + 'outer-suffix</article>');
    check(response.state.assistants, [{ key: 'reply-fixture', text: responseText, collapsed: false }], 'Nested supported assistant selectors keep only their leaf response');
    const priorText = 'Earlier response\nAGENT_END_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa';
    response = await renderReply(reply(priorText, 'prior-reply') + reply(responseText, 'current-reply'));
    check(response.state.assistants, [
      { key: 'prior-reply', text: priorText, collapsed: false },
      { key: 'current-reply', text: responseText, collapsed: false }
    ], 'Keep separate assistant turns and their exact texts in document order');
    for (const [label, control, collapsed] of [
      ['collapsed button', '<button aria-expanded="false">Expand</button>', true],
      ['collapsed state', '<span data-state="collapsed">More</span>', true],
      ['expanded button', '<button aria-expanded="true">Collapse</button>', false]
    ]) {
      response = await renderReply(measuredReply.replace(/<\/div>$/, control + '</div>'));
      check(response.state.assistants, [{ key: 'reply-fixture', text: response.raw.innerText, collapsed }], 'Preserve production collapsed detection and fallback text: ' + label);
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
