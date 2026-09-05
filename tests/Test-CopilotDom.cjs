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
const expandDefinitions = [...source.matchAll(/function Invoke-AgentCopilotExpand \{\r?\n[\s\S]*?\$body\s*=\s*@'\r?\n([\s\S]*?)\r?\n'@\r?\n/g)];
assert.equal(expandDefinitions.length, 1, 'Read exactly one production expansion body');
assert.equal(expandDefinitions[0][1].split('EXPAND_ARGUMENTS').length, 2, 'Production expansion has one structured argument insertion');
const expandExpression = (key, text, requestId) => '(()=>{' + definitions[0][1] + '\n' + expandDefinitions[0][1]
  .replace('EXPAND_ARGUMENTS', () => JSON.stringify({ key, text, request_id: requestId })) + '})()';
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
    check(response.state.assistants, [{ key: 'reply-fixture', text: responseText, collapsed: false, source_kind: 'rendered' }], 'Production snapshot returns the original response node without guessing a marker boundary');

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
      check(response.state.assistants, [{ key: 'reply-fixture', text: value, collapsed: false, source_kind: 'rendered' }], 'Preserve every original response character ' + JSON.stringify(value));
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
    check(response.state.assistants, [{ key: 'reply-fixture', text: responseText, collapsed: false, source_kind: 'rendered' }], 'Nested supported assistant selectors keep only their leaf response');
    const priorText = 'Earlier response\nAGENT_END_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa';
    response = await renderReply(reply(priorText, 'prior-reply') + reply(responseText, 'current-reply'));
    check(response.state.assistants, [
      { key: 'prior-reply', text: priorText, collapsed: false, source_kind: 'rendered' },
      { key: 'current-reply', text: responseText, collapsed: false, source_kind: 'rendered' }
    ], 'Keep separate assistant turns and their exact texts in document order');
    for (const [label, control, collapsed] of [
      ['collapsed button', '<button aria-expanded="false">Expand</button>', true],
      ['collapsed state', '<span data-state="collapsed">More</span>', true],
      ['expanded button', '<button aria-expanded="true">Collapse</button>', false]
    ]) {
      response = await renderReply(measuredReply.replace(/<\/div>$/, control + '</div>'));
      check(response.state.assistants, [{ key: 'reply-fixture', text: response.raw.innerText, collapsed, source_kind: 'rendered' }], 'Preserve production collapsed detection and fallback text: ' + label);
    }

    // Semantic reproduction of the observed 64-node code block (a7d402...,
    // observation-1). Classes, generated button IDs, icon paths and geometry
    // deliberately differ from the live page. No .work evidence is a test input.
    const icon = (size = '20', kind = 'icon-regular') => '<svg class="' + kind + '" fill="currentColor" aria-hidden="true" data-fui-icon="" width="' + size + '" height="' + size + '" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg"><path d="M1 1h3v3H1z" fill="currentColor"></path></svg>';
    const pairedIcons = size => icon(size, 'icon-filled') + icon(size);
    const item = markup => '<div class="header-item" data-overflow-item="">' + markup + '</div>';
    const fencedReply = (line0, line1 = marker, key = 'fenced-fixture') =>
      '<div dir="auto" aria-hidden="false" class="fenced-reply" data-testid="markdown-reply" data-message-id="' + key + '" data-message-type="Chat">' +
      '<div class="fenced-wrapper"><div class="fenced-inner"><div role="group" aria-label="コードのプレビュー" tabindex="0" class="fenced-preview"><div>' +
      '<div tabindex="-1" class="scriptor-component-code-block fixture-code scriptor-codeblock-virtualized">' +
      '<div class="code-live"><div aria-live="assertive" class="live-assertive"></div><div aria-live="polite" class="live-polite"></div></div>' +
      '<div class="code-header"><div class="header-flex"><div class="header-block"><div class="fui-Overflow header-controls">' +
      item('<button type="button" id="synthetic-goto" role="button" aria-label="行に移動  (Ctrl+G)" class="goto-button"><span class="button-icon">' + pairedIcons('1em') + '</span></button>') +
      item('<button type="button" id="synthetic-copy" role="button" aria-label="コードをコピー" class="copy-button"><span class="button-icon">' + pairedIcons('20') + '</span></button>') +
      item('<button type="button" role="button" class="display-menu" tabindex="0" aria-haspopup="menu" aria-expanded="false" id="synthetic-menu" aria-label="表示オプション">' + pairedIcons('20') + '<span class="menu-chevron">' + icon('1em') + '</span></button>') +
      item('<div id="language-badge" aria-label="Plain Text" class="fui-Badge language-badge"><span class="badge-icon">' + icon('20') + '</span><span class="badge-label"><span class="badge-text">Plain Text</span></span></div>') +
      '<div class="header-spacer"></div></div></div></div></div>' +
      '<div class="code-body"><div class="body-scroll" style="height: 100%; width: 100%; flex-grow: 1;"><div class="code-find" data-virtualized-code-find-root="true">' +
      '<div class="body-spacer"></div><div class="code-editor" tabindex="0" role="textbox" aria-readonly="true" aria-multiline="true" aria-label="コード エディター">' +
      '<div class="gutter">1</div><div data-line-index="0" class="code-line">' + escapeText(line0) + '</div><div class="gutter">2</div><div data-line-index="1" class="code-line">' + escapeText(line1) + '</div></div>' +
      '<div class="more-holder"><button type="button" role="button" aria-label="その他の行を表示する" class="more-button"><span class="button-icon">' + icon('1em') + '</span>その他の行を表示する</button></div>' +
      '</div></div></div></div></div></div></div></div></div>';
    const fencedCss = `
      #fixture .fenced-reply,#fixture .fenced-reply *{white-space:normal;opacity:1;content-visibility:visible}
      #fixture .fenced-reply{display:block;width:640px}
      .fenced-wrapper,.fixture-code,.code-body,.body-scroll,.code-find{display:flex;flex-direction:column}
      .fenced-inner,.fenced-preview,.code-header,.header-block{display:block}
      .header-flex,.header-controls,.header-item,.header-spacer,.button-icon,.badge-icon,.badge-label,.language-badge{display:flex}
      .header-controls{align-items:center;justify-content:flex-end;min-height:36px}
      .goto-button,.copy-button,.display-menu{display:flex;align-items:center;height:30px}
      .menu-chevron,.badge-text{display:block}
      .fenced-reply .icon-filled{display:none}.fenced-reply .icon-regular{display:block}
      .fenced-reply .menu-chevron>svg{display:inline}
      .code-live,.live-assertive,.live-polite,.body-spacer{display:block}
      .body-scroll{overflow:auto}.code-find{overflow:hidden}
      .code-editor{display:grid;grid-template-columns:24px minmax(0,1fr);overflow:hidden;max-height:300px}
      .gutter{display:block}#fixture .fenced-reply .code-line{display:block;white-space:pre-wrap;overflow-wrap:anywhere}
      .more-holder{display:none}.more-button{display:inline-flex;overflow:hidden}
    `;
    const fixtureMessage = '  日本語 "引用" O\'Brien C:\\path\\raw literal\\n %FileContents% *_`\r\n末尾\\  ';
    const fencedJson = JSON.stringify({ request_id: requestId, state: 'BLOCKED', message: fixtureMessage, robin: '', artifacts: [] });
    const fencedPayload = fencedJson + '\n' + marker;
    const renderFenced = async (markup = fencedReply(fencedJson), setup, css = '') => renderReply(markup, setup, fencedCss + css);
    response = await renderFenced();
    const fencedShape = await page.locator('.fenced-reply').evaluate(root => {
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_ALL);
      let count = 1; while (walker.nextNode()) count++;
      const editor = root.querySelector('[aria-label="コード エディター"]');
      return { count, editorChildren: [...editor.childNodes].map(node => [node.nodeName, node.getAttribute('data-line-index'), node.childNodes.length, node.firstChild.nodeType]), lines: [...editor.querySelectorAll('[data-line-index]')].map(node => ({ display: getComputedStyle(node).display, whiteSpace: getComputedStyle(node).whiteSpace, value: node.firstChild.nodeValue })), menuExpanded: root.querySelector('[aria-label="表示オプション"]').getAttribute('aria-expanded'), moreRects: root.querySelector('[aria-label="その他の行を表示する"]').getClientRects().length };
    });
    check(fencedShape.count, 64, 'Rendered fixture retains the measured complete 64-node topology');
    check(fencedShape.editorChildren, [['DIV', null, 1, 3], ['DIV', '0', 1, 3], ['DIV', null, 1, 3], ['DIV', '1', 1, 3]], 'Editor has alternating real gutters and two direct text-only logical rows');
    check(fencedShape.lines, [{ display: 'block', whiteSpace: 'pre-wrap', value: fencedJson }, { display: 'block', whiteSpace: 'pre-wrap', value: marker }], 'Rendered payload rows preserve exact node values and measured white-space');
    check({ expanded: fencedShape.menuExpanded, moreRects: fencedShape.moreRects }, { expanded: 'false', moreRects: 0 }, 'Closed display menu is distinct from an effectively hidden more-lines control');
    check(response.state.assistants, [{ key: 'fenced-fixture', text: fencedPayload, collapsed: false, source_kind: 'fenced_plaintext' }], 'Recognized code block returns only its two payload rows, without badge, gutters or hidden control text');
    check(JSON.parse(response.state.assistants[0].text.split('\n')[0]).message, fixtureMessage, 'Decoded fenced text preserves Japanese, quotes, apostrophe, path, trailing backslash, outer spaces, literal escape, CRLF, percent and backtick');
    check(response.state.assistants[0].text.split('\n').length, 2, 'An encoded CRLF inside JSON never becomes extra transport rows');

    response = await renderFenced(undefined, () => {
      for (const element of document.querySelectorAll('.fenced-reply [class]')) element.classList.add('different-generated-token');
      for (const element of document.querySelectorAll('.fenced-reply button[id]')) element.id += '-changed';
      for (const element of document.querySelectorAll('.fenced-reply path')) element.setAttribute('d', 'M2 2h4v4H2z');
    });
    check(response.state.assistants[0], { key: 'fenced-fixture', text: fencedPayload, collapsed: false, source_kind: 'fenced_plaintext' }, 'Generated class, control ID and SVG path values do not define payload ownership');
    response = await renderFenced(fencedReply(fencedJson) + '<button aria-label="Other display options" aria-haspopup="menu" aria-expanded="false">Options</button>');
    check(response.state.assistants[0].source_kind, 'fenced_plaintext', 'An unrelated closed display-options menu outside the assistant does not imply folded code');

    for (const [label, setup, css, wrap] of [
      ['missing first index', () => document.querySelector('[data-line-index="0"]').removeAttribute('data-line-index')],
      ['duplicate index', () => document.querySelector('[data-line-index="1"]').setAttribute('data-line-index', '0')],
      ['reversed indices', () => { const rows = document.querySelectorAll('[data-line-index]'); rows[0].setAttribute('data-line-index', '1'); rows[1].setAttribute('data-line-index', '0'); }],
      ['noncanonical zero index', () => document.querySelector('[data-line-index="0"]').setAttribute('data-line-index', '00')],
      ['missing logical row', () => document.querySelector('[data-line-index="1"]').remove()],
      ['unexpected second index', () => document.querySelector('[data-line-index="1"]').setAttribute('data-line-index', '2')],
      ['extra indexed row', () => document.querySelector('.code-editor').appendChild(document.querySelector('[data-line-index="1"]').cloneNode(true))],
      ['reordered direct rows', () => { const editor = document.querySelector('.code-editor'); editor.insertBefore(editor.lastChild, editor.firstChild); }],
      ['wrong first gutter', () => { document.querySelector('.gutter').firstChild.nodeValue = '01'; }],
      ['wrong second gutter', () => { document.querySelectorAll('.gutter')[1].firstChild.nodeValue = '3'; }],
      ['indexed gutter', () => document.querySelector('.gutter').setAttribute('data-line-index', '0')],
      ['wrapped payload span', () => { const row = document.querySelector('[data-line-index="0"]'); const span = document.createElement('span'); span.textContent = row.textContent; row.replaceChildren(span); }],
      ['split payload text nodes', () => document.querySelector('[data-line-index="0"]').firstChild.splitText(20)],
      ['payload comment', () => document.querySelector('[data-line-index="0"]').appendChild(document.createComment('extra'))],
      ['payload empty text node', () => document.querySelector('[data-line-index="0"]').appendChild(document.createTextNode(''))],
      ['editor comment', () => document.querySelector('.code-editor').appendChild(document.createComment('extra'))],
      ['editor blank node', () => document.querySelector('.code-editor').appendChild(document.createTextNode(' '))],
      ['unknown row attribute', () => document.querySelector('[data-line-index="0"]').setAttribute('title', 'unknown')],
      ['actual LF in logical row', () => { document.querySelector('[data-line-index="0"]').firstChild.nodeValue += '\n'; }],
      ['actual CR in logical row', () => { document.querySelector('[data-line-index="0"]').firstChild.nodeValue += '\r'; }],
      ['empty logical row', () => { document.querySelector('[data-line-index="0"]').firstChild.nodeValue = ''; }],
      ['second code block', () => { const code = document.querySelector('.fixture-code'); code.parentElement.appendChild(code.cloneNode(true)); }],
      ['second editor', () => { const editor = document.querySelector('.code-editor'); editor.parentElement.appendChild(editor.cloneNode(true)); }],
      ['plain text beside code', () => document.querySelector('.fenced-inner').appendChild(document.createTextNode('extra explanation'))],
      ['root comment', () => document.querySelector('.fenced-reply').appendChild(document.createComment('extra'))],
      ['root empty node', () => document.querySelector('.fenced-reply').appendChild(document.createTextNode(''))],
      ['nonempty live region', () => { document.querySelector('[aria-live="polite"]').textContent = 'extra model text'; }],
      ['nonempty body spacer', () => document.querySelector('.body-spacer').appendChild(document.createTextNode(''))],
      ['header unknown text', () => document.querySelector('.header-spacer').appendChild(document.createTextNode('extra explanation'))],
      ['header hidden text', () => { const hidden = document.createElement('span'); hidden.hidden = true; hidden.textContent = 'hidden text'; document.querySelector('.header-spacer').appendChild(hidden); }],
      ['header duplicate known text', () => document.querySelector('.header-spacer').appendChild(document.createTextNode('Plain Text'))],
      ['header unknown control', () => document.querySelector('.header-controls').appendChild(document.createElement('button'))],
      ['badge unknown markup', () => document.querySelector('.badge-text').appendChild(document.createElement('span'))],
      ['different language badge', () => { document.querySelector('.badge-text').firstChild.nodeValue = 'JavaScript'; }],
      ['extra icon text', () => document.querySelector('.copy-button path').appendChild(document.createTextNode('payload'))],
      ['unknown menu owner', () => document.querySelector('.display-menu').setAttribute('aria-label', 'Other menu')],
      ['extra body collapsed signal', () => document.querySelector('.code-body').setAttribute('data-state', 'collapsed')],
      ['visible more-lines holder', null, '.more-holder{display:block!important}'],
      ['disabled visible more-lines', () => { document.querySelector('.more-button').disabled = true; }, '.more-holder{display:block!important}'],
      ['partially visible more-lines', null, '.more-holder{display:block!important;opacity:.5!important}'],
      ['body content-visibility auto', null, '.code-body{content-visibility:auto!important}'],
      ['editor content-visibility hidden', null, '.code-editor{content-visibility:hidden!important}'],
      ['line content-visibility auto', null, '.code-line{content-visibility:auto!important}'],
      ['line visibility hidden', null, '.code-line{visibility:hidden!important}'],
      ['line opacity partial', null, '.code-line{opacity:.5!important}'],
      ['line white-space normal', null, '#fixture .fenced-reply .code-line{white-space:normal!important}'],
      ['line display grid', null, '#fixture .fenced-reply .code-line{display:grid!important}'],
      ['hidden ancestor', null, '', '<section class="fenced-outer" hidden>'],
      ['aria-hidden ancestor', null, '', '<section class="fenced-outer" aria-hidden="true">'],
      ['display-none ancestor', null, '.fenced-outer{display:none!important}', '<section class="fenced-outer">'],
      ['hidden ancestor with visible descendants', null, '.fenced-outer{visibility:hidden!important}.fenced-reply{visibility:visible!important}', '<section class="fenced-outer">'],
      ['zero-opacity ancestor', null, '.fenced-outer{opacity:0!important}', '<section class="fenced-outer">'],
      ['partial-opacity ancestor', null, '.fenced-outer{opacity:.5!important}', '<section class="fenced-outer">'],
      ['auto-content ancestor', null, '.fenced-outer{content-visibility:auto!important}', '<section class="fenced-outer">'],
      ['hidden-content ancestor', null, '.fenced-outer{content-visibility:hidden!important}', '<section class="fenced-outer">']
    ]) {
      response = await renderFenced((wrap || '') + fencedReply(fencedJson) + (wrap ? '</section>' : ''), setup, css);
      check(response.state.assistants.length, 1, 'Keep the diagnostic assistant without promoting an ineligible code shape: ' + label);
      check(response.state.assistants[0].source_kind, 'rendered', 'Never expose ineligible content as fenced payload: ' + label);
    }

    for (const selector of ['.fenced-reply', '.fixture-code', '.code-body', '.code-editor']) {
      for (const declaration of ['display:none', 'visibility:hidden', 'opacity:0', 'opacity:.5', 'content-visibility:auto', 'content-visibility:hidden']) {
        response = await renderFenced(undefined, null, `${selector}{${declaration}!important}`);
        check(response.state.assistants[0].source_kind, 'rendered', 'Reject an ineffective or unmeasured visible payload path without adding attributes: ' + selector + ' ' + declaration);
      }
    }

    for (const [label, line0, line1] of [
      ['missing marker', fencedJson, 'not an end marker'],
      ['wrong request marker', fencedJson, 'AGENT_END_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'],
      ['invalid JSON escape', '{"request_id":"' + requestId + '","path":"C:\\Users"}', marker]
    ]) {
      response = await renderFenced(fencedReply(line0, line1));
      check(response.state.assistants[0], { key: 'fenced-fixture', text: line0 + '\n' + line1, collapsed: false, source_kind: 'fenced_plaintext' }, 'DOM extraction never repairs parser-owned invalidity: ' + label);
    }
    response = await renderFenced(fencedReply(fencedJson, marker, 'earlier-code') + fencedReply(fencedJson, marker, 'later-code'));
    check(response.state.assistants.map(({ key, source_kind, text }) => ({ key, source_kind, text })), [
      { key: 'earlier-code', source_kind: 'fenced_plaintext', text: fencedPayload },
      { key: 'later-code', source_kind: 'fenced_plaintext', text: fencedPayload }
    ], 'Each assistant owns its code block independently; turn and nonce filtering remains the adapter responsibility');

    // A separate real observation (7688... / b213572...) confirmed one More click:
    // the same 64 nodes and two logical rows survive the folded -> expanded change.
    // Only observed control/state differences are modeled; no live response is copied.
    const expansionMessage = fixtureMessage.repeat(14) + " EXPAND_ARGUMENTS REQUEST_ID RESPONSE_TEXT $& $$ $` $'";
    const expansionJson = JSON.stringify({ request_id: requestId, state: 'BLOCKED', message: expansionMessage, robin: '', artifacts: [] });
    const expansionText = expansionJson + '\n' + marker;
    const expandedReply = (line0 = expansionJson, line1 = marker, key = 'fenced-fixture') => fencedReply(line0, line1, key)
      .replace('aria-label="その他の行を表示する"', 'aria-label="簡易表示" data-fui-focus-visible="true"')
      .replace('</span>その他の行を表示する</button>', '</span>簡易表示</button>');
    const visibleMoreCss = '.more-holder{display:flex;justify-content:center}.more-button{display:flex;height:32px}.code-editor{overflow:auto;max-height:300px}.code-editor.expanded-code{overflow:visible;max-height:none}';
    const expandedCss = visibleMoreCss + '.code-editor{overflow:visible;max-height:none}';
    const renderFolded = (markup = fencedReply(expansionJson), setup, css = '') => renderFenced(markup, setup, visibleMoreCss + css);
    const renderExpanded = (markup = expandedReply(), setup, css = '') => renderFenced(markup, setup, expandedCss + css);
    const expansionShape = () => page.locator('.fenced-reply').evaluate(root => {
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_ALL);
      let nodeCount = 1; while (walker.nextNode()) nodeCount++;
      const editor = root.querySelector('.code-editor'), holder = root.querySelector('.more-holder'), button = holder.firstElementChild;
      const box = editor.getBoundingClientRect(), rows = [...editor.children].map(row => row.getBoundingClientRect());
      return { nodeCount, rowValues: [...editor.querySelectorAll('[data-line-index]')].map(row => row.firstChild.nodeValue), editor: { overflow: getComputedStyle(editor).overflow, maxHeight: getComputedStyle(editor).maxHeight, display: getComputedStyle(editor).display }, finalRowClipped: rows[3].bottom > box.bottom, allRowsContained: rows.every(row => row.left >= box.left && row.right <= box.right && row.top >= box.top && row.bottom <= box.bottom), holderDisplay: getComputedStyle(holder).display, buttonDisplay: getComputedStyle(button).display, label: button.getAttribute('aria-label'), text: button.lastChild.nodeValue, focusVisible: button.getAttribute('data-fui-focus-visible') };
    });
    response = await renderFolded();
    check(await expansionShape(), { nodeCount: 64, rowValues: [expansionJson, marker], editor: { overflow: 'auto', maxHeight: '300px', display: 'grid' }, finalRowClipped: true, allRowsContained: false, holderDisplay: 'flex', buttonDisplay: 'flex', label: 'その他の行を表示する', text: 'その他の行を表示する', focusVisible: null }, 'Reproduce the measured folded editor with a visible More control');
    check(response.state.assistants[0], { key: 'fenced-fixture', text: expansionText, source_kind: 'fenced_collapsed', collapsed: true }, 'Known folded code exposes exact logical text but cannot yet be accepted as expanded');
    response = await renderExpanded();
    check(await expansionShape(), { nodeCount: 64, rowValues: [expansionJson, marker], editor: { overflow: 'visible', maxHeight: 'none', display: 'grid' }, finalRowClipped: false, allRowsContained: true, holderDisplay: 'flex', buttonDisplay: 'flex', label: '簡易表示', text: '簡易表示', focusVisible: 'true' }, 'Reproduce the measured expanded editor and unchanged node/row structure');
    check(response.state.assistants[0], { key: 'fenced-fixture', text: expansionText, source_kind: 'fenced_plaintext', collapsed: false }, 'Only the fully expanded measured state becomes fenced plaintext');
    check(JSON.parse(response.state.assistants[0].text.split('\n')[0]).message, expansionMessage, 'Expansion preserves every decoded character, including literal escapes and encoded CRLF');
    response = await renderExpanded(undefined, () => document.querySelector('.more-button').removeAttribute('data-fui-focus-visible'));
    check(response.state.assistants[0].source_kind, 'fenced_plaintext', 'Removing a transient focus-visible flag does not fold an expanded editor');
    response = await renderFolded(fencedReply(fencedJson));
    check((await expansionShape()).finalRowClipped, false, 'A short synthetic body does not overflow merely because More is visible');
    check(response.state.assistants[0].source_kind, 'rendered', 'A More label and capped overflow style alone do not prove the measured folded geometry');

    for (const [label, expanded, setup, css] of [
      ['only aria-label changed', false, () => document.querySelector('.more-button').setAttribute('aria-label', '簡易表示')],
      ['only button text changed', false, () => { document.querySelector('.more-button').lastChild.nodeValue = '簡易表示'; }],
      ['label and text changed without editor expansion', false, () => { const button = document.querySelector('.more-button'); button.setAttribute('aria-label', '簡易表示'); button.lastChild.nodeValue = '簡易表示'; }],
      ['editor expanded while More label remains', false, null, '.code-editor{overflow:visible;max-height:none}'],
      ['folded editor overflow changed alone', false, null, '.code-editor{overflow:visible}'],
      ['folded editor max-height removed alone', false, null, '.code-editor{max-height:none}'],
      ['expanded editor still capped', true, null, '.code-editor{max-height:300px}'],
      ['expanded editor retains scrollbar overflow', true, null, '.code-editor{overflow:auto}'],
      ['expanded style but rows extend below editor', true, null, '.code-editor{height:100px}'],
      ['expanded row extends outside editor horizontally', true, null, '.code-line{position:relative;left:4px}'],
      ['folded editor was scrolled to an unmeasured state', false, () => { const editor = document.querySelector('.code-editor'); editor.scrollTop = editor.scrollHeight; }],
      ['expanded label hidden in holder', true, null, '.more-holder{display:none}'],
      ['unmeasured holder block display', true, null, '.more-holder{display:block}'],
      ['unknown focus-visible value', true, () => document.querySelector('.more-button').setAttribute('data-fui-focus-visible', 'false')],
      ['unrecognized expanded button attribute', true, () => document.querySelector('.more-button').setAttribute('title', 'unknown')],
      ['extra expanded row', true, () => document.querySelector('.code-editor').appendChild(document.querySelector('[data-line-index="1"]').cloneNode(true))],
      ['unknown expanded text', true, () => document.querySelector('.header-spacer').appendChild(document.createTextNode('unowned explanation'))],
      ['expanded root comment', true, () => document.querySelector('.fenced-reply').appendChild(document.createComment('unowned'))],
      ['expanded payload wrapper', true, () => { const row = document.querySelector('[data-line-index="0"]'); const child = document.createElement('span'); child.textContent = row.textContent; row.replaceChildren(child); }],
      ['expanded line hidden', true, null, '.code-line{visibility:hidden!important}'],
      ['expanded holder opacity changed', true, null, '.more-holder{opacity:.5!important}'],
      ['expanded ancestor content visibility changed', true, null, '.fixture-code{content-visibility:hidden!important}']
    ]) {
      response = await (expanded ? renderExpanded : renderFolded)(undefined, setup, css || '');
      check(response.state.assistants[0].source_kind, 'rendered', 'Never infer expansion from a partial or unknown state: ' + label);
    }

    await page.setViewportSize({ width: 1280, height: 1000 });
    const renderExpansionAction = async (markup = fencedReply(expansionJson) + span('<p><br></p>'), setup, css = '', transition = true) => {
      await renderFolded(markup, null, css);
      await page.evaluate(changeUi => {
        window.expansionActions = { more: 0, copy: 0, menu: 0, goto: 0, inputFocus: 0, keys: [] };
        for (const button of document.querySelectorAll('.fenced-reply button')) {
          button.addEventListener('click', () => {
            const counts = window.expansionActions;
            if (button.classList.contains('copy-button')) counts.copy++;
            if (button.classList.contains('display-menu')) counts.menu++;
            if (button.classList.contains('goto-button')) counts.goto++;
            if (button.classList.contains('more-button')) {
              counts.more++;
              const root = button.closest('.fenced-reply');
              counts.keys.push(root.getAttribute('data-message-id'));
              if (changeUi) {
                root.querySelector('.code-editor').classList.add('expanded-code');
                button.setAttribute('aria-label', '簡易表示');
                button.setAttribute('data-fui-focus-visible', 'true');
                button.lastChild.nodeValue = '簡易表示';
              }
            }
          });
        }
        for (const input of document.querySelectorAll('[contenteditable="true"]')) input.addEventListener('focus', () => { window.expansionActions.inputFocus++; });
      }, transition);
      if (setup) await page.evaluate(setup);
    };
    const expansionCounts = () => page.evaluate(() => window.expansionActions);
    const noExpansionActions = { more: 0, copy: 0, menu: 0, goto: 0, inputFocus: 0, keys: [] };
    await renderExpansionAction();
    const expand = expandExpression('fenced-fixture', expansionText, requestId);
    check(await page.evaluate(expand), true, 'Actual production expansion code acknowledges one click on the measured More control');
    check(await expansionCounts(), { more: 1, copy: 0, menu: 0, goto: 0, inputFocus: 0, keys: ['fenced-fixture'] }, 'Expansion triggers one More UI event without copy, menu, input focus or a second click');
    check((await page.evaluate(snapshot)).assistants[0], { key: 'fenced-fixture', text: expansionText, source_kind: 'fenced_plaintext', collapsed: false }, 'The production snapshot recognizes the actual click handler transition and unchanged raw body');
    check((await expansionShape()).nodeCount, 64, 'One expansion changes control state without adding or dropping response nodes');
    await assert.rejects(() => page.evaluate(expand), error => error.message.includes('expand unavailable'), 'An already expanded response cannot receive another More click');
    checks++;
    check((await expansionCounts()).more, 1, 'Refusing a second expansion preserves the first click count');

    const otherId = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa';
    const otherJson = JSON.stringify({ request_id: otherId, state: 'BLOCKED', message: 'Earlier independent response ' + expansionMessage, robin: '', artifacts: [] });
    await renderExpansionAction(fencedReply(otherJson, 'AGENT_END_' + otherId, 'prior-fenced') + fencedReply(expansionJson) + span('<p><br></p>'));
    check(await page.evaluate(expand), true, 'A prior assistant with another nonce does not prevent expanding the one matching current response');
    check((await expansionCounts()).keys, ['fenced-fixture'], 'Only the current response More control receives the click');
    check((await page.evaluate(snapshot)).assistants.map(({ key, source_kind }) => ({ key, source_kind })), [{ key: 'prior-fenced', source_kind: 'fenced_collapsed' }, { key: 'fenced-fixture', source_kind: 'fenced_plaintext' }], 'An older folded response remains untouched while the current one expands');

    const wrongJson = JSON.stringify({ request_id: otherId, state: 'BLOCKED', message: expansionMessage, robin: '', artifacts: [] });
    for (const [label, options] of [
      ['expected key belongs to another response', { key: 'another-key' }],
      ['expected body differs', { text: expansionText + ' ' }],
      ['expected request differs', { requestId: otherId }],
      ['current key changed since the stable reads', { setup: () => document.querySelector('.fenced-reply').setAttribute('data-message-id', 'changed-key') }],
      ['current body changed since the stable reads', { setup: () => { document.querySelector('[data-line-index="0"]').firstChild.nodeValue += ' '; } }],
      ['wrong marker despite unchanged expected body', { markup: fencedReply(expansionJson, 'AGENT_END_' + otherId) + span('<p><br></p>'), text: expansionJson + '\nAGENT_END_' + otherId }],
      ['JSON request differs from marker', { markup: fencedReply(wrongJson) + span('<p><br></p>'), text: wrongJson + '\n' + marker }],
      ['missing marker', { markup: fencedReply(expansionJson, 'not a marker') + span('<p><br></p>'), text: expansionJson + '\nnot a marker' }],
      ['missing input', { markup: fencedReply(expansionJson) }],
      ['two visible inputs', { markup: fencedReply(expansionJson) + span('<p><br></p>') + '<div role="textbox" contenteditable="true">draft</div>' }],
      ['nonempty draft', { setup: () => { document.querySelector('#m365-chat-editor-target-element').textContent = 'unsubmitted'; } }],
      ['whitespace draft', { setup: () => { document.querySelector('#m365-chat-editor-target-element').textContent = ' '; } }],
      ['hidden input', { setup: () => { const input = document.querySelector('#m365-chat-editor-target-element'); input.hidden = true; input.style.display = 'none'; } }],
      ['generation still active', { markup: fencedReply(expansionJson) + span('<p><br></p>') + '<div role="status" aria-busy="true"></div>' }],
      ['visible stop-generation control', { markup: fencedReply(expansionJson) + span('<p><br></p>') + '<button aria-label="停止">停止</button>' }],
      ['button disabled', { setup: () => { document.querySelector('.more-button').disabled = true; } }],
      ['button aria-disabled', { setup: () => document.querySelector('.more-button').setAttribute('aria-disabled', 'true') }],
      ['button hidden', { setup: () => { document.querySelector('.more-button').hidden = true; } }],
      ['button inert', { setup: () => { document.querySelector('.more-button').inert = true; } }],
      ['inert response ancestor', { markup: '<section inert>' + fencedReply(expansionJson) + '</section>' + span('<p><br></p>') }],
      ['hidden response ancestor', { markup: '<section hidden>' + fencedReply(expansionJson) + '</section>' + span('<p><br></p>') }],
      ['aria-hidden response ancestor', { markup: '<section aria-hidden="true">' + fencedReply(expansionJson) + '</section>' + span('<p><br></p>') }],
      ['transparent response ancestor', { markup: '<section class="ineligible-ancestor">' + fencedReply(expansionJson) + '</section>' + span('<p><br></p>'), css: '.ineligible-ancestor{opacity:0}' }],
      ['button opacity zero', { css: '.more-button{opacity:0!important}' }],
      ['button visibility hidden', { css: '.more-button{visibility:hidden!important}' }],
      ['button has no hit-test participation', { css: '.more-button{pointer-events:none}' }],
      ['button outside viewport vertically', { css: '.more-holder{position:relative;top:10000px}' }],
      ['button outside viewport horizontally', { css: '.more-holder{position:relative;left:-10000px}' }],
      ['button covered by another element', { markup: fencedReply(expansionJson) + span('<p><br></p>') + '<div class="expansion-overlay"></div>', css: '.expansion-overlay{position:fixed;inset:0;z-index:999;background:transparent}' }],
      ['second button within response', { setup: () => { const button = document.querySelector('.more-button'); button.parentElement.appendChild(button.cloneNode(true)); } }],
      ['same nonce in two assistant replies', { markup: fencedReply(expansionJson) + fencedReply(expansionJson, marker, 'duplicate-nonce') + span('<p><br></p>') }],
      ['same key in two assistant replies', { markup: fencedReply(expansionJson) + fencedReply(otherJson, 'AGENT_END_' + otherId) + span('<p><br></p>') }],
      ['payload no longer a direct text node', { setup: () => { const row = document.querySelector('[data-line-index="0"]'); const inner = document.createElement('span'); inner.textContent = row.textContent; row.replaceChildren(inner); } }],
      ['unrecognized empty node beside payload', { setup: () => document.querySelector('[data-line-index="0"]').appendChild(document.createTextNode('')) }],
      ['already expanded state', { markup: expandedReply() + span('<p><br></p>'), css: '.code-editor{overflow:visible;max-height:none}' }],
      ['unknown partial expansion', { css: '.code-editor{overflow:visible}' }]
    ]) {
      await renderExpansionAction(options.markup, options.setup, options.css || '');
      const operation = expandExpression(options.key || 'fenced-fixture', options.text || expansionText, options.requestId || requestId);
      await assert.rejects(() => page.evaluate(operation), error => error.message.includes('expand unavailable'), 'Production expansion rejects an unconfirmed state: ' + label);
      checks++;
      check(await expansionCounts(), noExpansionActions, 'A rejected expansion has no UI side effects: ' + label);
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
      await assert.rejects(() => page.evaluate(expand), error => error.message.includes(message), 'Expansion also rejects untrusted page ' + url);
      checks++;
    }
    check(pageErrors, [], 'No fixture JavaScript errors');
    check(fulfilled, 7, 'All document navigations were locally fulfilled');
    console.log(`PASS: ${checks} rendered Edge DOM checks; ${fulfilled} local document fulfillments; ${blocked} blocked other requests. No request was forwarded; no live Copilot or user profile was used.`);
  } finally { await browser.close(); }
})().catch(error => { console.error(error.stack); process.exitCode = 1; });
