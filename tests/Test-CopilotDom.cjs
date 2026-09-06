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
    const composerSend = '<button id="chat-send" type="submit" aria-label="送信" class="fai-SendButton fai-BebopLiteChatInput__send">送信</button>';
    const surveySend = '<div role="alertdialog" aria-modal="false" data-testid="DxToastContentContainer"><button id="survey-send" type="button" aria-label="送信" data-testid="obf-DxTFormSubmitButton">送信</button></div>';
    const composer = controls => '<div class="fai-BebopLiteChatInput"><div class="fai-BebopLiteChatInput__inputWrapper">' + span('test prompt') + controls + '</div></div>';
    const selectedSends = '(()=>{' + definitions[0][1] + 'return sends.map(e=>e.id);})()';
    await render(composer(composerSend) + surveySend);
    check(await page.evaluate(selectedSends), ['chat-send'], 'Known composer excludes the measured survey Send button');
    check((await inputState()).sendReady, true, 'Survey does not make the known chat sender ambiguous');
    await page.evaluate(() => { window.chatClicks = 0; window.surveyClicks = 0; document.querySelector('#chat-send').onclick = e => { e.preventDefault(); window.chatClicks++; }; document.querySelector('#survey-send').onclick = () => window.surveyClicks++; });
    await page.evaluate('(()=>{' + definitions[0][1] + 'if(!input||generating||sends.length!==1)throw new Error("send unavailable");sends[0].click();})()');
    check(await page.evaluate(() => [window.chatClicks, window.surveyClicks]), [1, 0], 'The resolved send action never submits survey feedback');
    for (const [controls, label] of [
      ['', 'missing composer send'],
      [composerSend.replace('type="submit"', 'type="button"'), 'unexpected button type'],
      [composerSend.replace('fai-SendButton ', ''), 'missing measured send class'],
      [composerSend.replace('id="chat-send"', 'disabled id="chat-send"'), 'disabled composer send'],
      [composerSend.replace('id="chat-send"', 'aria-disabled="true" id="chat-send"'), 'aria-disabled composer send'],
      [composerSend.replace('id="chat-send"', 'style="display:none" id="chat-send"'), 'hidden composer send']
    ]) {
      await render(composer(controls) + surveySend);
      check((await inputState()).sendReady, false, label + ' cannot fall back to the survey');
    }
    await render(composer(composerSend + composerSend.replace('chat-send', 'duplicate-send')) + surveySend);
    check((await inputState()).sendReady, false, 'Duplicate send controls inside the composer remain ambiguous');
    await render(composer(composerSend) + '<div class="fai-BebopLiteChatInput">' + composerSend.replace('chat-send', 'other-send') + '</div>');
    check(await page.evaluate(selectedSends), ['chat-send'], 'Another composer cannot receive this input');
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
    const fencedRows = (rows, key = 'fenced-fixture') =>
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
      rows.map((line, index) => '<div class="gutter">' + (index + 1) + '</div><div data-line-index="' + index + '" class="code-line">' + escapeText(line) + '</div>').join('') + '</div>' +
      '<div class="more-holder"><button type="button" role="button" aria-label="その他の行を表示する" class="more-button"><span class="button-icon">' + icon('1em') + '</span>その他の行を表示する</button></div>' +
      '</div></div></div></div></div></div></div></div></div>';
    const fencedReply = (line0, line1 = marker, key = 'fenced-fixture') => fencedRows([line0, line1], key);
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
      return { nodeCount, rowValues: [...editor.querySelectorAll('[data-line-index]')].map(row => row.firstChild.nodeValue), editor: { overflow: getComputedStyle(editor).overflow, maxHeight: getComputedStyle(editor).maxHeight, display: getComputedStyle(editor).display }, finalRowClipped: rows[rows.length - 1].bottom > box.bottom, allRowsContained: rows.every(row => row.left >= box.left && row.right <= box.right && row.top >= box.top && row.bottom <= box.bottom), holderDisplay: getComputedStyle(holder).display, buttonDisplay: getComputedStyle(button).display, label: button.getAttribute('aria-label'), text: button.lastChild.nodeValue, focusVisible: button.getAttribute('data-fui-focus-visible') };
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

    // A real 32px scroll-to-bottom control covered the 192px More button's center.
    // Keep the overlay outside the owned response and exercise actual browser hit testing.
    const addMoreCenterOverlay = () => {
      const r = document.querySelector('.more-button').getBoundingClientRect();
      const overlay = document.createElement('button');
      overlay.className = 'more-center-overlay';
      overlay.setAttribute('aria-label', '一番下までスクロール');
      overlay.style.cssText = `position:fixed;left:${r.x + r.width / 2 - 16}px;top:${r.y + r.height / 2 - 16}px;width:32px;height:32px;min-width:0;min-height:0;padding:0;border:0;z-index:999;background:#ddd`;
      window.moreOverlayClicks = 0;
      overlay.addEventListener('click', () => { window.moreOverlayClicks++; });
      document.querySelector('#fixture').appendChild(overlay);
    };
    const moreHitPoints = () => page.evaluate(() => {
      const more = document.querySelector('.more-button'), r = more.getBoundingClientRect();
      return [1 / 2, 1 / 4, 3 / 4].map(fraction => {
        const hit = document.elementFromPoint(r.x + r.width * fraction, r.y + r.height / 2);
        return !!hit && (hit === more || more.contains(hit));
      });
    });
    const measuredMoreWidth = '.more-button{width:192px;min-width:192px}';
    await renderExpansionAction(undefined, addMoreCenterOverlay, measuredMoreWidth);
    check(await moreHitPoints(), [false, true, true], 'Measured 32px overlay blocks only the center, leaving both quarter points on the owned More');
    check(await page.evaluate(expand), true, 'Partly covered More can expand through an uncovered quarter point');
    check(await expansionCounts(), { more: 1, copy: 0, menu: 0, goto: 0, inputFocus: 0, keys: ['fenced-fixture'] }, 'Partial overlay permits one owned More click and no other action');
    check(await page.evaluate(() => window.moreOverlayClicks), 0, 'The overlapping scroll-to-bottom control receives no click');
    check((await page.evaluate(snapshot)).assistants[0], { key: 'fenced-fixture', text: expansionText, source_kind: 'fenced_plaintext', collapsed: false }, 'Partial-overlay expansion preserves the complete response and exact key');
    await assert.rejects(() => page.evaluate(expand), error => error.message.includes('expand unavailable'), 'Partial-overlay expansion cannot be repeated');
    checks++;
    check((await expansionCounts()).more, 1, 'Partial-overlay retry rejection leaves the single click unchanged');

    await renderExpansionAction(undefined, addMoreCenterOverlay, measuredMoreWidth);
    await page.evaluate(() => {
      const r = document.querySelector('.more-button').getBoundingClientRect(), overlay = document.querySelector('.more-center-overlay');
      overlay.style.left = r.x + 'px'; overlay.style.width = r.width * 0.6 + 'px';
    });
    check(await moreHitPoints(), [false, false, true], 'A separate overlay leaves only the right quarter of More available');
    check(await page.evaluate(expand), true, 'Right-quarter hit remains available when center and left quarter are covered');
    check(await expansionCounts(), { more: 1, copy: 0, menu: 0, goto: 0, inputFocus: 0, keys: ['fenced-fixture'] }, 'Right-quarter fallback still emits exactly one owned More click');

    for (const [label, setup] of [
      ['fully covered', () => { const r = document.querySelector('.more-button').getBoundingClientRect(), overlay = document.querySelector('.more-center-overlay'); overlay.style.left = r.x + 'px'; overlay.style.width = r.width + 'px'; }],
      ['hidden', () => { document.querySelector('.more-button').hidden = true; }],
      ['disabled', () => { document.querySelector('.more-button').disabled = true; }],
      ['unknown attribute', () => { document.querySelector('.more-button').setAttribute('title', 'unrecognized'); }]
    ]) {
      await renderExpansionAction(undefined, addMoreCenterOverlay, measuredMoreWidth);
      await page.evaluate(setup);
      if (label === 'fully covered') check(await moreHitPoints(), [false, false, false], 'Full overlay blocks all three permitted hit-test points');
      await assert.rejects(() => page.evaluate(expand), error => error.message.includes('expand unavailable'), 'Quarter-point fallback cannot authorize More when ' + label);
      checks++;
      check(await expansionCounts(), noExpansionActions, 'Rejected partial-overlay state emits no owned UI actions: ' + label);
      check(await page.evaluate(() => window.moreOverlayClicks), 0, 'Rejected partial-overlay state never clicks the covering control: ' + label);
    }

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

    // Observation 2551... / 0836a159... has exactly one additional gutter/row:
    // gutter "3", canonical index "2", and a single U+00A0 text node. Preserve it.
    const nbsp = '\u00a0';
    const withTrailingRow = (markup, text = nbsp) => markup.replace('</div><div class="more-holder">', () => '<div class="gutter">3</div><div data-line-index="2" class="code-line">' + escapeText(text) + '</div></div><div class="more-holder">');
    const shortNbspText = fencedJson + '\n' + marker + '\n' + nbsp;
    const longNbspText = expansionJson + '\n' + marker + '\n' + nbsp;
    for (const [state, renderState, markup, json, sourceKind, collapsed] of [
      ['hidden More', renderFenced, withTrailingRow(fencedReply(fencedJson)), fencedJson, 'fenced_plaintext', false],
      ['folded More', renderFolded, withTrailingRow(fencedReply(expansionJson)), expansionJson, 'fenced_collapsed', true],
      ['expanded', renderExpanded, withTrailingRow(expandedReply()), expansionJson, 'fenced_plaintext', false]
    ]) {
      response = await renderState(markup);
      const shape = await expansionShape();
      check(shape.nodeCount, 68, 'Retain the observed complete 68-node structure with trailing NBSP: ' + state);
      check(shape.rowValues, [json, marker, nbsp], 'Read all three original node values without dropping the NBSP: ' + state);
      check(response.state.assistants[0], { key: 'fenced-fixture', text: json + '\n' + marker + '\n' + nbsp, source_kind: sourceKind, collapsed }, 'Keep the third line in the exact snapshot transport text: ' + state);
      check({ lines: response.state.assistants[0].text.split('\n').length, finalCodePoint: response.state.assistants[0].text.codePointAt(response.state.assistants[0].text.length - 1) }, { lines: 3, finalCodePoint: 160 }, 'The observed NBSP remains U+00A0 rather than an empty row or ordinary space: ' + state);
    }
    response = await renderFenced(withTrailingRow(fencedReply(fencedJson)).replace(nbsp, '&nbsp;'));
    check(response.state.assistants[0].text, shortNbspText, 'Recognition uses the actual NBSP text node even when HTML represents it as an entity');

    for (const [label, tail] of [
      ['empty', ''], ['ordinary space', ' '], ['two NBSPs', nbsp + nbsp], ['tab', '\t'], ['LF', '\n'], ['CR', '\r'],
      ['zero-width space', '\u200b'], ['figure space', '\u2007'], ['narrow NBSP', '\u202f'], ['BOM', '\ufeff'], ['NBSP and content', nbsp + 'x']
    ]) {
      for (const [state, renderState, base] of [['hidden', renderFenced, fencedReply(fencedJson)], ['folded', renderFolded, fencedReply(expansionJson)], ['expanded', renderExpanded, expandedReply()]]) {
        response = await renderState(withTrailingRow(base, tail));
        check(response.state.assistants[0].source_kind, 'rendered', 'Never treat an unobserved trailing value as NBSP: ' + state + ' / ' + label);
      }
    }
    for (const [label, setup, css] of [
      ['missing index', () => document.querySelector('[data-line-index="2"]').removeAttribute('data-line-index')],
      ['duplicate index', () => document.querySelector('[data-line-index="2"]').setAttribute('data-line-index', '1')],
      ['noncanonical index', () => document.querySelector('[data-line-index="2"]').setAttribute('data-line-index', '02')],
      ['index hole', () => document.querySelector('[data-line-index="2"]').setAttribute('data-line-index', '3')],
      ['tail before marker', () => { const editor = document.querySelector('.code-editor'); editor.insertBefore(editor.lastChild, editor.children[3]); }],
      ['missing third gutter', () => document.querySelector('.code-editor').children[4].remove()],
      ['noncanonical gutter text', () => { document.querySelector('.code-editor').children[4].firstChild.nodeValue = '03'; }],
      ['indexed third gutter', () => document.querySelector('.code-editor').children[4].setAttribute('data-line-index', '2')],
      ['unknown tail attribute', () => document.querySelector('[data-line-index="2"]').setAttribute('title', 'unknown')],
      ['wrapped NBSP', () => { const row = document.querySelector('[data-line-index="2"]'); const child = document.createElement('span'); child.textContent = row.textContent; row.replaceChildren(child); }],
      ['second tail text node', () => document.querySelector('[data-line-index="2"]').appendChild(document.createTextNode(''))],
      ['tail comment', () => document.querySelector('[data-line-index="2"]').appendChild(document.createComment('extra'))],
      ['editor trailing blank node', () => document.querySelector('.code-editor').appendChild(document.createTextNode(' '))],
      ['second NBSP row', () => { const editor = document.querySelector('.code-editor'); editor.appendChild(editor.children[4].cloneNode(true)); editor.appendChild(editor.children[5].cloneNode(true)); }],
      ['hidden tail', null, '[data-line-index="2"]{display:none!important}'],
      ['invisible tail', null, '[data-line-index="2"]{visibility:hidden!important}'],
      ['transparent tail', null, '[data-line-index="2"]{opacity:0!important}'],
      ['partial-opacity tail', null, '[data-line-index="2"]{opacity:.5!important}'],
      ['unmeasured tail content-visibility', null, '[data-line-index="2"]{content-visibility:auto!important}'],
      ['tail white-space changed', null, '[data-line-index="2"]{white-space:normal!important}'],
      ['third gutter hidden', null, '.code-editor>.gutter:nth-child(5){visibility:hidden!important}']
    ]) {
      for (const [state, renderState, base] of [['hidden', renderFenced, fencedReply(fencedJson)], ['folded', renderFolded, fencedReply(expansionJson)], ['expanded', renderExpanded, expandedReply()]]) {
        response = await renderState(withTrailingRow(base), setup, css || '');
        check(response.state.assistants[0].source_kind, 'rendered', 'Reject an incomplete or modified third row: ' + state + ' / ' + label);
      }
    }

    // Isolate the third row geometry: both protocol rows fit but the NBSP is clipped.
    const tailOnlyClippedCss = '.code-editor{grid-template-rows:260px 40px 20px}';
    response = await renderFolded(withTrailingRow(fencedReply(fencedJson)), null, tailOnlyClippedCss);
    const tailGeometry = await page.locator('.code-editor').evaluate(editor => {
      const box = editor.getBoundingClientRect();
      return { protocolRowsFit: [...editor.querySelectorAll('[data-line-index="0"],[data-line-index="1"]')].every(row => row.getBoundingClientRect().bottom <= box.bottom), tailClipped: editor.querySelector('[data-line-index="2"]').getBoundingClientRect().bottom > box.bottom };
    });
    check(tailGeometry, { protocolRowsFit: true, tailClipped: true }, 'Only the third NBSP row is clipped in this folded regression fixture');
    check(response.state.assistants[0], { key: 'fenced-fixture', text: shortNbspText, source_kind: 'fenced_collapsed', collapsed: true }, 'The final NBSP row participates in folded geometry even when both protocol rows fit');
    for (const [label, css] of [
      ['tail below editor', '[data-line-index="2"]{position:relative;top:4px}'],
      ['third gutter left of editor', '.code-editor>.gutter:nth-child(5){position:relative;left:-4px}']
    ]) {
      response = await renderExpanded(withTrailingRow(expandedReply()), null, css);
      check(response.state.assistants[0].source_kind, 'rendered', 'Expanded geometry includes the complete third row and gutter: ' + label);
    }

    for (const [label, markup, expectedText, css] of [
      ['long JSON with NBSP', withTrailingRow(fencedReply(expansionJson)), longNbspText, ''],
      ['only third row clipped', withTrailingRow(fencedReply(fencedJson)), shortNbspText, tailOnlyClippedCss]
    ]) {
      await renderExpansionAction(markup + span('<p><br></p>'), null, css);
      const expandNbsp = expandExpression('fenced-fixture', expectedText, requestId);
      check(await page.evaluate(expandNbsp), true, 'Production expansion accepts the exact optional NBSP frame: ' + label);
      check(await expansionCounts(), { more: 1, copy: 0, menu: 0, goto: 0, inputFocus: 0, keys: ['fenced-fixture'] }, 'The three-row response gets exactly one More click: ' + label);
      check((await page.evaluate(snapshot)).assistants[0], { key: 'fenced-fixture', text: expectedText, source_kind: 'fenced_plaintext', collapsed: false }, 'Expansion retains the entire frame including the third NBSP: ' + label);
      check({ nodes: (await expansionShape()).nodeCount, rowsInside: (await expansionShape()).allRowsContained }, { nodes: 68, rowsInside: true }, 'All six row/gutter elements survive expansion and fit inside the editor: ' + label);
      await assert.rejects(() => page.evaluate(expandNbsp), error => error.message.includes('expand unavailable'), 'A three-row response is never expanded twice: ' + label);
      checks++;
      check((await expansionCounts()).more, 1, 'Rejecting a second three-row expansion adds no click: ' + label);
    }
    for (const [label, setup, expectedText] of [
      ['tail dropped from expected text', null, expansionText],
      ['tail changed since stable read', () => { document.querySelector('[data-line-index="2"]').firstChild.nodeValue = ' '; }, longNbspText],
      ['tail removed since stable read', () => { const editor = document.querySelector('.code-editor'); editor.lastChild.remove(); editor.lastChild.remove(); }, longNbspText],
      ['extra NBSP row since stable read', () => { const editor = document.querySelector('.code-editor'); editor.appendChild(editor.children[4].cloneNode(true)); editor.appendChild(editor.children[5].cloneNode(true)); }, longNbspText],
      ['NBSP row wrapped since stable read', () => { const row = document.querySelector('[data-line-index="2"]'); const child = document.createElement('span'); child.textContent = row.textContent; row.replaceChildren(child); }, longNbspText]
    ]) {
      await renderExpansionAction(withTrailingRow(fencedReply(expansionJson)) + span('<p><br></p>'), setup);
      await assert.rejects(() => page.evaluate(expandExpression('fenced-fixture', expectedText, requestId)), error => error.message.includes('expand unavailable'), 'The optional NBSP is still part of the exact pre-click response identity: ' + label);
      checks++;
      check(await expansionCounts(), noExpansionActions, 'A changed three-row frame receives no expansion: ' + label);
    }

    // Observation 1be3... reproduced 14 direct rows and 112 total nodes.
    // Preserve that topology with synthetic values; never read live evidence here.
    const prettyRows = (message, robin = '', nonce = requestId) => [
      '{', '  "request_id":', '    ' + JSON.stringify(nonce) + ',',
      '  "state":', '    "BLOCKED",', '  "message":', '    ' + JSON.stringify(message) + ',',
      '  "robin":', '    ' + JSON.stringify(robin) + ',', '  "artifacts":', '    [', '    ]', '}', 'AGENT_END_' + nonce
    ];
    const shortRows = prettyRows(fixtureMessage);
    const shortRowsText = shortRows.join('\n');
    response = await renderFenced(fencedRows(shortRows));
    check({ rows: shortRows.length, nodes: (await expansionShape()).nodeCount }, { rows: 14, nodes: 112 }, 'Reproduce the observed complete 14-row topology');
    check((await expansionShape()).rowValues, shortRows, 'Every original short row retains its complete direct text node');
    check(response.state.assistants[0], { key: 'fenced-fixture', text: shortRowsText, source_kind: 'fenced_plaintext', collapsed: false }, 'Short pretty JSON preserves all formatting rows and its terminal marker');
    check(JSON.parse(response.state.assistants[0].text.split('\n').slice(0, -1).join('\n')).message, fixtureMessage, 'Pretty JSON decoding preserves original whitespace, escapes and Unicode');

    const longRowsMessage = fixtureMessage.repeat(85);
    const longRowsRobin = fixtureMessage.repeat(85);
    const longRows = prettyRows(longRowsMessage, longRowsRobin);
    const longRowsText = longRows.join('\n');
    check(longRowsText.length > 10000 && longRows.every(line => line.length > 0 && line.length < 10000), true, 'Large synthetic transport exceeds 10000 characters while every complete row stays below 10000');
    const expandedRows = rows => fencedRows(rows)
      .replace('aria-label="その他の行を表示する"', 'aria-label="簡易表示" data-fui-focus-visible="true"')
      .replace('</span>その他の行を表示する</button>', '</span>簡易表示</button>');
    for (const [label, rows] of [['multiline', longRows], ['multiline with NBSP', [...longRows, nbsp]]]) {
      const text = rows.join('\n');
      response = await renderFolded(fencedRows(rows));
      check(response.state.assistants[0], { key: 'fenced-fixture', text, source_kind: 'fenced_collapsed', collapsed: true }, 'Folded multiline transport exposes all exact rows: ' + label);
      await renderExpansionAction(fencedRows(rows) + span('<p><br></p>'));
      const operation = expandExpression('fenced-fixture', text, requestId);
      check(await page.evaluate(operation), true, 'Actual expansion accepts complete multiline JSON before the final marker: ' + label);
      check(await expansionCounts(), { more: 1, copy: 0, menu: 0, goto: 0, inputFocus: 0, keys: ['fenced-fixture'] }, 'Multiline expansion receives exactly one More click: ' + label);
      const after = (await page.evaluate(snapshot)).assistants[0];
      check(after, { key: 'fenced-fixture', text, source_kind: 'fenced_plaintext', collapsed: false }, 'Expansion preserves every multiline transport character: ' + label);
      check((await expansionShape()).rowValues, rows, 'Expansion neither drops nor reorders any middle row: ' + label);
      const decoded = JSON.parse(after.text.split('\n').slice(0, label.endsWith('NBSP') ? -2 : -1).join('\n'));
      check({ message: decoded.message, robin: decoded.robin }, { message: longRowsMessage, robin: longRowsRobin }, 'Large multiline values roundtrip without truncation or escape normalization: ' + label);
      await assert.rejects(() => page.evaluate(operation), error => error.message.includes('expand unavailable'), 'Already expanded multiline response cannot receive a second click: ' + label);
      checks++;
      check((await expansionCounts()).more, 1, 'Second multiline expansion is side-effect free: ' + label);
    }
    for (const [label, setup] of [
      ['middle row removed', () => document.querySelector('[data-line-index="6"]').remove()],
      ['middle pair removed', () => { const row = document.querySelector('[data-line-index="6"]'); row.previousSibling.remove(); row.remove(); }],
      ['middle gutter removed', () => document.querySelector('[data-line-index="6"]').previousSibling.remove()],
      ['middle index missing', () => document.querySelector('[data-line-index="6"]').removeAttribute('data-line-index')],
      ['middle index duplicate', () => document.querySelector('[data-line-index="6"]').setAttribute('data-line-index', '5')],
      ['middle index hole', () => document.querySelector('[data-line-index="6"]').setAttribute('data-line-index', '7')],
      ['middle index noncanonical', () => document.querySelector('[data-line-index="6"]').setAttribute('data-line-index', '06')],
      ['middle gutter noncanonical', () => { document.querySelector('[data-line-index="6"]').previousSibling.firstChild.nodeValue = '07'; }],
      ['middle row wrapped', () => { const row = document.querySelector('[data-line-index="6"]'); const child = document.createElement('span'); child.textContent = row.textContent; row.replaceChildren(child); }],
      ['middle row extra text node', () => document.querySelector('[data-line-index="6"]').appendChild(document.createTextNode(''))],
      ['middle row comment', () => document.querySelector('[data-line-index="6"]').appendChild(document.createComment('unknown'))],
      ['middle row unknown attribute', () => document.querySelector('[data-line-index="6"]').setAttribute('title', 'unknown')]
    ]) {
      response = await renderExpanded(expandedRows(longRows), setup);
      check(response.state.assistants[0].source_kind, 'rendered', 'Incomplete or unrecognized multiline DOM is never promoted: ' + label);
      await renderExpansionAction(fencedRows(longRows) + span('<p><br></p>'), setup);
      await assert.rejects(() => page.evaluate(expandExpression('fenced-fixture', longRowsText, requestId)), error => error.message.includes('expand unavailable'), 'Damaged multiline DOM cannot be expanded: ' + label);
      checks++;
      check(await expansionCounts(), noExpansionActions, 'Damaged multiline DOM has no UI side effects: ' + label);
    }
    const wrongMultiline = [...longRows]; wrongMultiline[wrongMultiline.length - 1] = 'AGENT_END_' + otherId;
    const mismatchedMultiline = prettyRows(longRowsMessage, longRowsRobin, otherId); mismatchedMultiline[mismatchedMultiline.length - 1] = marker;
    const malformedMultiline = [...longRows]; malformedMultiline.splice(6, 1);
    for (const [label, rows, expectedText] of [
      ['wrong terminal nonce', wrongMultiline, wrongMultiline.join('\n')],
      ['JSON nonce differs from terminal nonce', mismatchedMultiline, mismatchedMultiline.join('\n')],
      ['middle value missing despite contiguous indices', malformedMultiline, malformedMultiline.join('\n')],
      ['middle value changed since stable read', prettyRows(longRowsMessage + ' changed', longRowsRobin), longRowsText]
    ]) {
      response = await renderExpanded(expandedRows(rows));
      check(response.state.assistants[0].text, rows.join('\n'), 'DOM observation leaves parser-owned multiline invalidity unchanged: ' + label);
      await renderExpansionAction(fencedRows(rows) + span('<p><br></p>'));
      await assert.rejects(() => page.evaluate(expandExpression('fenced-fixture', expectedText, requestId)), error => error.message.includes('expand unavailable') || (label === 'middle value missing despite contiguous indices' && error.message.includes('SyntaxError')), 'Multiline expansion rejects invalid or changed response identity: ' + label);
      checks++;
      check(await expansionCounts(), noExpansionActions, 'Invalid multiline response receives no action: ' + label);
    }

    // Observed capped expansion: 33 direct rows / 188 nodes, 3050px CSS height,
    // 3070px client height and 4080px scroll content. Use only synthetic text.
    const cappedRowsFor = (message, robin) => {
      const rows = prettyRows(message, robin);
      rows.splice(11, 0, ...Array.from({ length: 19 }, (_, index) => '      ' + JSON.stringify('C:\\fixture\\artifact-' + String(index + 1).padStart(2, '0') + '.txt') + (index < 18 ? ',' : '')));
      return rows;
    };
    const cappedRobinPrefix = fixtureMessage + '  CAP_SCOPE EXPAND_ARGUMENTS REQUEST_ID RESPONSE_TEXT $& $$ $` $\' ';
    const cappedRobin = cappedRobinPrefix + 'r'.repeat(8424 - ('    ' + JSON.stringify(cappedRobinPrefix) + ',').length);
    const cappedMessagePrefix = fixtureMessage;
    const cappedBaseRows = cappedRowsFor(cappedMessagePrefix, cappedRobin);
    const cappedMessage = cappedMessagePrefix + 'm'.repeat(12560 - cappedBaseRows.slice(0, -1).join('\n').length);
    const cappedRows = cappedRowsFor(cappedMessage, cappedRobin);
    const cappedText = cappedRows.join('\n');
    check({ rows: cappedRows.length, longest: Math.max(...cappedRows.map(row => row.length)), jsonLength: cappedRows.slice(0, -1).join('\n').length }, { rows: 33, longest: 8424, jsonLength: 12560 }, 'Synthetic capped fixture matches the measured complete row count and transport lengths');
    const cappedTrackSizes = cappedRows.map((row, index) => index === 6 ? '840px' : index === 8 ? '2600px' : '20px').join(' ');
    const cappedLayoutCss = '#fixture .fenced-reply{width:706px}.code-editor{grid-template-columns:38px minmax(0,1fr);grid-template-rows:' + cappedTrackSizes + ';padding:12px 0 8px;box-sizing:content-box;align-content:start;scrollbar-gutter:stable}.code-editor::-webkit-scrollbar{width:10px;height:10px}.code-line,.gutter{line-height:20px;font-family:monospace;font-size:14px}';
    const cappedCss = cappedLayoutCss + '.code-editor{height:3050px;max-height:3050px;overflow:auto}';
    const cappedTransitionCss = cappedLayoutCss + '.code-editor.expanded-code{height:3050px;max-height:3050px;overflow:auto}';
    const cappedMetrics = () => page.locator('.code-editor').evaluate(editor => {
      const rect = editor.getBoundingClientRect(), first = editor.querySelector('[data-line-index="0"]').getBoundingClientRect(), last = editor.querySelector('[data-line-index="32"]').getBoundingClientRect();
      return { height: getComputedStyle(editor).height, maxHeight: getComputedStyle(editor).maxHeight, overflow: getComputedStyle(editor).overflow, rectHeight: rect.height, rectWidth: rect.width, clientHeight: editor.clientHeight, scrollHeight: editor.scrollHeight, scrollTop: editor.scrollTop, clientWidth: editor.clientWidth, scrollWidth: editor.scrollWidth, scrollLeft: editor.scrollLeft, offsetHeight: editor.offsetHeight, offsetWidth: editor.offsetWidth, firstTop: first.top - rect.top, lastBottom: last.bottom - rect.top, lastBelowClient: last.bottom > rect.top + editor.clientHeight, lastBelowViewport: last.bottom > innerHeight };
    });
    const expectedCappedMetrics = { height: '3050px', maxHeight: '3050px', overflow: 'auto', rectHeight: 3070, rectWidth: 706, clientHeight: 3070, scrollHeight: 4080, scrollTop: 0, clientWidth: 696, scrollWidth: 696, scrollLeft: 0, offsetHeight: 3070, offsetWidth: 706, firstTop: 12, lastBottom: 4072, lastBelowClient: true, lastBelowViewport: true };
    response = await renderExpanded(expandedRows(cappedRows), null, cappedCss);
    check(await cappedMetrics(), expectedCappedMetrics, 'Rendered synthetic DOM reproduces measured capped editor scroll and content geometry');
    check((await expansionShape()).nodeCount, 188, 'Capped expansion retains the complete known 188-node topology');
    check((await expansionShape()).rowValues, cappedRows, 'All 33 capped rows remain present even below the client rectangle and viewport');
    check(response.state.assistants[0], { key: 'fenced-fixture', text: cappedText, source_kind: 'fenced_plaintext', collapsed: false }, 'Measured capped expansion returns every complete direct row without treating viewport clipping as missing data');
    check(JSON.parse(response.state.assistants[0].text.split('\n').slice(0, -1).join('\n')), { request_id: requestId, state: 'BLOCKED', message: cappedMessage, robin: cappedRobin, artifacts: Array.from({ length: 19 }, (_, index) => 'C:\\fixture\\artifact-' + String(index + 1).padStart(2, '0') + '.txt') }, 'Capped transport roundtrips exact Unicode, escaping, strings and all array entries');

    await renderExpansionAction(fencedRows(cappedRows) + span('<p><br></p>'), null, cappedTransitionCss);
    check((await page.evaluate(snapshot)).assistants[0], { key: 'fenced-fixture', text: cappedText, source_kind: 'fenced_collapsed', collapsed: true }, 'A capped-transition fixture starts in the known folded state');
    const cappedOperation = expandExpression('fenced-fixture', cappedText, requestId);
    check(await page.evaluate(cappedOperation), true, 'One production More click can transition into the measured capped expansion');
    check(await expansionCounts(), { more: 1, copy: 0, menu: 0, goto: 0, inputFocus: 0, keys: ['fenced-fixture'] }, 'The capped transition performs no extra UI operation');
    check(await cappedMetrics(), expectedCappedMetrics, 'The actual More handler produces the complete capped scroll geometry');
    check((await page.evaluate(snapshot)).assistants[0], { key: 'fenced-fixture', text: cappedText, source_kind: 'fenced_plaintext', collapsed: false }, 'After one capped expansion all original response characters remain identical');
    await assert.rejects(() => page.evaluate(cappedOperation), error => error.message.includes('expand unavailable'), 'Recognized capped expansion cannot receive a second More click');
    checks++;
    check((await expansionCounts()).more, 1, 'Rejecting a second capped expansion leaves the click count unchanged');

    for (const [label, setup, css] of [
      ['maximum height 3049', null, '.code-editor{max-height:3049px}'],
      ['maximum height 3051', null, '.code-editor{max-height:3051px}'],
      ['visible overflow', null, '.code-editor{overflow:visible}'],
      ['hidden overflow', null, '.code-editor{overflow:hidden}'],
      ['scroll overflow', null, '.code-editor{overflow:scroll}'],
      ['horizontal overflow hidden', null, '.code-editor{overflow-x:hidden}'],
      ['vertical scroll offset', () => { document.querySelector('.code-editor').scrollTop = 1; }],
      ['horizontal overflow', null, '.code-editor{grid-template-columns:38px 700px}'],
      ['horizontal scroll offset', () => { document.querySelector('.code-editor').scrollLeft = 1; }, '.code-editor{grid-template-columns:38px 700px}'],
      ['scaled rectangle', null, '.code-editor{transform:scale(.99);transform-origin:top left}'],
      ['content rectangle shorter than its final row', () => { const editor = document.querySelector('.code-editor'); Object.defineProperty(editor, 'scrollHeight', { value: editor.clientHeight + 1, configurable: true }); }],
      ['no scroll content beyond client', () => { const editor = document.querySelector('.code-editor'); Object.defineProperty(editor, 'scrollHeight', { value: editor.clientHeight, configurable: true }); }],
      ['zero client height', () => Object.defineProperty(document.querySelector('.code-editor'), 'clientHeight', { value: 0, configurable: true })],
      ['zero client width', () => Object.defineProperty(document.querySelector('.code-editor'), 'clientWidth', { value: 0, configurable: true })],
      ['row beyond scroll content', null, '[data-line-index="32"]{position:fixed;top:5000px}'],
      ['row left of client content', null, '[data-line-index="6"]{position:relative;left:-40px}'],
      ['detached middle row', () => document.querySelector('[data-line-index="16"]').remove()],
      ['missing middle pair', () => { const row = document.querySelector('[data-line-index="16"]'); row.previousSibling.remove(); row.remove(); }],
      ['missing middle index', () => document.querySelector('[data-line-index="16"]').removeAttribute('data-line-index')],
      ['duplicate middle index', () => document.querySelector('[data-line-index="16"]').setAttribute('data-line-index', '15')],
      ['noncanonical middle index', () => document.querySelector('[data-line-index="16"]').setAttribute('data-line-index', '016')],
      ['missing middle gutter', () => document.querySelector('[data-line-index="16"]').previousSibling.remove()],
      ['unknown middle attribute', () => document.querySelector('[data-line-index="16"]').setAttribute('title', 'unrecognized')],
      ['wrapped middle value', () => { const row = document.querySelector('[data-line-index="16"]'); const wrapper = document.createElement('span'); wrapper.textContent = row.textContent; row.replaceChildren(wrapper); }],
      ['unknown middle text node', () => document.querySelector('[data-line-index="16"]').appendChild(document.createTextNode(''))],
      ['unknown extra editor node', () => document.querySelector('.code-editor').appendChild(document.createComment('unknown'))],
      ['unknown extra response node', () => document.querySelector('.fenced-reply').appendChild(document.createElement('span'))],
      ['wrong expanded label', () => document.querySelector('.more-button').setAttribute('aria-label', 'その他の行を表示する')],
      ['unrecognized holder layout', null, '.more-holder{display:block}']
    ]) {
      response = await renderExpanded(expandedRows(cappedRows), setup, cappedCss + (css || ''));
      check(response.state.assistants[0].source_kind, 'rendered', 'Reject an incomplete or unmeasured capped state: ' + label);
    }

    // The 2026-09-06 two-fence observation (d1d3bb...) contains 139 nodes:
    // one shared wrapper alternating code-block divs and one exact LF text node.
    // Payloads below are synthetic. Saved live evidence is never a fixture input.
    const partRows = (data, index, total) => [
      'AGENT_PART_V1 ' + requestId + ' ' + index + ' ' + total,
      'AGENT_DATA ' + data,
      'AGENT_PART_END_V1 ' + requestId + ' ' + index + ' ' + total,
      ...(index === total ? [marker] : [])
    ];
    const multipartReply = (frames, key = 'parts-fixture') => {
      const first = fencedRows(frames[0], key);
      const offset = first.indexOf('<div class="fenced-inner">');
      return first.slice(0, offset) + frames.map(rows => {
        const reply = fencedRows(rows);
        return reply.slice(reply.indexOf('<div class="fenced-inner">'), -12);
      }).join('\n') + '</div></div>';
    };
    const splitAt = fencedJson.indexOf('\\') + 1;
    const twoParts = [partRows(fencedJson.slice(0, splitAt), 1, 2), partRows(fencedJson.slice(splitAt), 2, 2)];
    const expectedParts = (frames, collapsed = false) => ({ key: 'parts-fixture', text: '', source_kind: 'fenced_parts', collapsed, frames: frames.map(rows => rows.join('\n')) });
    response = await renderFenced(multipartReply(twoParts));
    check(response.state.assistants, [expectedParts(twoParts)], 'Capture both exact frames in one owned assistant without joining their payloads');
    const multipartShape = await page.locator('.fenced-reply').evaluate(root => {
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_ALL);
      let nodes = 1; while (walker.nextNode()) nodes++;
      return { nodes, wrappers: [...root.firstChild.childNodes].map(node => node.nodeType === 3 ? ['text', node.nodeValue] : ['element', node.tagName, node.childNodes.length]), rows: [...root.querySelectorAll('.code-editor')].map(editor => editor.childNodes.length / 2) };
    });
    check(multipartShape, { nodes: 139, wrappers: [['element', 'DIV', 1], ['text', '\n'], ['element', 'DIV', 1]], rows: [3, 4] }, 'Reproduce all measured multipart parent nodes and direct row counts');
    check(response.state.assistants[0].frames.map(frame => frame.split('\n')[1].slice(11)).join(''), fencedJson, 'Raw fragments may split a JSON escape and rejoin with no inserted separator');
    check(response.state.assistants[0].frames[0].endsWith(' 1 2'), true, 'The nonfinal frame retains its own footer without synthesizing an end marker');
    for (const count of [1, 3, 256]) {
      const frames = Array.from({ length: count }, (_, index) => partRows('日本語' + index, index + 1, count));
      response = await renderFenced(multipartReply(frames));
      check(response.state.assistants, [expectedParts(frames)], 'Capture every owned bounded part for count ' + count);
    }
    const tooManyParts = Array.from({ length: 257 }, (_, index) => partRows('x', index + 1, 257));
    response = await renderFenced(multipartReply(tooManyParts));
    check(response.state.assistants[0].source_kind, 'rendered', 'Reject more than 256 DOM blocks before parsing their contents');
    response = await renderFenced(multipartReply(twoParts), () => {
      const wrapper = document.querySelector('.fenced-wrapper');
      wrapper.replaceChildren(wrapper.lastChild, wrapper.childNodes[1], wrapper.firstChild);
    });
    check(response.state.assistants[0].source_kind, 'rendered', 'The actual DOM order must leave the final marker in the last block; never sort parts');
    const nbspParts = twoParts.map(rows => [...rows, '\u00a0']);
    response = await renderFenced(multipartReply(nbspParts));
    check(response.state.assistants, [expectedParts(twoParts)], 'Omit exactly one measured structural terminal NBSP row in each frame');
    const payloadNbspParts = [partRows(' \u00a0日本語  \u00a0', 1, 2), partRows('\u00a0 末尾 \u00a0 ', 2, 2)];
    response = await renderFenced(multipartReply(payloadNbspParts.map(rows => [...rows, '\u00a0'])));
    check(response.state.assistants, [expectedParts(payloadNbspParts)], 'Preserve every DATA payload space and NBSP while dropping only separate structural tails');

    for (const length of [4096, 4097, 4685, 8192]) {
      const value = '  日本語 "引用" C:\\raw %FileContents%\r\n\r\n  ';
      const base = JSON.stringify({ request_id: requestId, state: 'ACT', message: value, robin: 'ReadText followed by AiCall', artifacts: [] });
      const payload = JSON.stringify({ request_id: requestId, state: 'ACT', message: value + 'a'.repeat(length - base.length), robin: 'ReadText followed by AiCall', artifacts: [] });
      const frames = [partRows(payload, 1, 1)];
      response = await renderFolded(multipartReply(frames));
      check(payload.length, length, 'Boundary fixture is complete valid JSON at ' + length + ' UTF16 units');
      check(response.state.assistants, [expectedParts(frames, true)], 'Capture the entire single folded ACT-shaped payload at ' + length + ' UTF16 units');
      check(JSON.parse(response.state.assistants[0].frames[0].split('\n')[1].slice(11)).message, value + 'a'.repeat(length - base.length), 'Actual DOM preserves decoded value exactly at ' + length + ' UTF16 units');
    }

    const foldedParts = [partRows('文'.repeat(8192), 1, 2), partRows('字'.repeat(8192), 2, 2)];
    response = await renderFolded(multipartReply(foldedParts));
    check(response.state.assistants, [expectedParts(foldedParts, true)], 'Complete bounded folded frames expose all direct rows with their collapsed state recorded');
    response = await renderFolded(multipartReply(foldedParts.map(rows => [...rows, '\u00a0'])));
    check(response.state.assistants, [expectedParts(foldedParts, true)], 'Folded frame completeness includes each observed trailing NBSP row');
    await assert.rejects(() => page.evaluate(expandExpression('parts-fixture', foldedParts[1].join('\n'), requestId)), error => error.message.includes('expand unavailable'), 'Multipart frames never authorize the legacy More operation');
    checks++;

    for (const [label, setup, css] of [
      ['separator missing', () => document.querySelector('.fenced-wrapper').childNodes[1].remove()],
      ['separator is two LF', () => { document.querySelector('.fenced-wrapper').childNodes[1].nodeValue = '\n\n'; }],
      ['separator is ordinary space', () => { document.querySelector('.fenced-wrapper').childNodes[1].nodeValue = ' '; }],
      ['separator is CRLF', () => { document.querySelector('.fenced-wrapper').childNodes[1].nodeValue = '\r\n'; }],
      ['separator is NBSP', () => { document.querySelector('.fenced-wrapper').childNodes[1].nodeValue = '\u00a0'; }],
      ['separator comment', () => document.querySelector('.fenced-wrapper').childNodes[1].replaceWith(document.createComment('unknown'))],
      ['separator element', () => { const span = document.createElement('span'); span.textContent = '\n'; document.querySelector('.fenced-wrapper').childNodes[1].replaceWith(span); }],
      ['interleaved explanation', () => { document.querySelector('.fenced-wrapper').childNodes[1].nodeValue += 'explanation'; }],
      ['root unowned hidden text', () => { const span = document.createElement('span'); span.hidden = true; span.textContent = 'unknown'; document.querySelector('.fenced-reply').appendChild(span); }],
      ['wrapper leading LF', () => document.querySelector('.fenced-wrapper').prepend(document.createTextNode('\n'))],
      ['wrapper trailing LF', () => document.querySelector('.fenced-wrapper').append(document.createTextNode('\n'))],
      ['second block unknown attribute', () => document.querySelectorAll('.fenced-inner')[1].setAttribute('title', 'unknown')],
      ['second block extra child', () => document.querySelectorAll('.fenced-inner')[1].appendChild(document.createComment('unknown'))],
      ['second block unknown language', () => { document.querySelectorAll('.badge-text')[1].firstChild.nodeValue = 'JavaScript'; }],
      ['second block missing footer pair', () => { const row = document.querySelectorAll('.code-editor')[1].querySelector('[data-line-index="2"]'); row.previousSibling.remove(); row.remove(); }],
      ['second block missing marker pair', () => { const row = document.querySelectorAll('.code-editor')[1].querySelector('[data-line-index="3"]'); row.previousSibling.remove(); row.remove(); }],
      ['second block wrong index', () => document.querySelectorAll('.code-editor')[1].querySelector('[data-line-index="1"]').setAttribute('data-line-index', '0')],
      ['second block wrong gutter', () => { document.querySelectorAll('.code-editor')[1].firstChild.firstChild.nodeValue = '2'; }],
      ['second block wrapped data', () => { const row = document.querySelectorAll('.code-editor')[1].querySelector('[data-line-index="1"]'); const span = document.createElement('span'); span.textContent = row.textContent; row.replaceChildren(span); }],
      ['second block split text', () => document.querySelectorAll('.code-editor')[1].querySelector('[data-line-index="1"]').firstChild.splitText(12)],
      ['second block hidden line', null, '.fenced-inner:last-child .code-line{visibility:hidden!important}'],
      ['second block transparent', null, '.fenced-inner:last-child{opacity:0!important}'],
      ['second block content visibility auto', null, '.fenced-inner:last-child{content-visibility:auto!important}'],
      ['second block hidden More but clipped', null, '.fenced-inner:last-child .code-editor{height:20px}'],
      ['second block horizontal overflow', null, '.fenced-inner:last-child .code-line{min-width:1000px}'],
      ['second block transformed', null, '.fenced-inner:last-child .code-editor{transform:scale(.9)}']
    ]) {
      response = await renderFenced(multipartReply(twoParts), setup, css || '');
      check(response.state.assistants[0].source_kind, 'rendered', 'Reject incomplete or unowned multipart DOM: ' + label);
    }
    for (const [label, frames] of [
      ['nonframed block', [twoParts[0], [fencedJson, marker]]],
      ['empty DATA', [partRows('', 1, 1)]],
      ['oversized DATA', [partRows('x'.repeat(8193), 1, 1)]],
      ['missing DATA prefix', [twoParts[0], twoParts[1].map((row, i) => i === 1 ? row.slice(11) : row)]],
      ['missing footer', [twoParts[0], twoParts[1].filter((row, i) => i !== 2)]],
      ['unknown fifth row', [twoParts[0], [...twoParts[1], 'extra']]],
      ['two terminal NBSP rows', [twoParts[0], [...twoParts[1], '\u00a0', '\u00a0']]],
      ['ordinary trailing space row', [twoParts[0], [...twoParts[1], ' ']]],
      ['unknown marker line', [twoParts[0], twoParts[1].map((row, i) => i === 3 ? 'not marker' : row)]]
    ]) {
      response = await renderFenced(multipartReply(frames));
      check(response.state.assistants[0].source_kind, 'rendered', 'Reject incomplete multipart carrier rows before protocol parsing: ' + label);
    }
    for (const [label, setup, css] of [
      ['scrolled content', () => { document.querySelectorAll('.code-editor')[1].scrollTop = 30; }],
      ['detached footer', () => document.querySelectorAll('.code-editor')[1].querySelector('[data-line-index="2"]').remove()],
      ['last row outside content', null, '.fenced-inner:last-child [data-line-index="3"]{position:fixed;top:100000px}'],
      ['DATA too long', () => { document.querySelectorAll('.code-editor')[1].querySelector('[data-line-index="1"]').firstChild.nodeValue += 'x'; }],
      ['unknown label', () => document.querySelectorAll('.more-button')[1].setAttribute('aria-label', 'More')]
    ]) {
      response = await renderFolded(multipartReply(foldedParts), setup, css || '');
      check(response.state.assistants[0].source_kind, 'rendered', 'Complete-folded exemption remains bounded: ' + label);
    }
    // Planner V2 keeps actual code rows separate from strict JSON metadata.
    // Empty Robin rows use an explicit nonce marker because the live renderer
    // represented a requested empty row as an indistinguishable U+00A0 node.
    const plannerRows = (body, meta = { request_id: requestId, state: 'ACT', message: '日本語の計画', artifacts: [] }) => [
      ['AGENT_META_V2 ' + requestId, ...JSON.stringify(meta, null, 2).split('\n'), 'AGENT_META_END_V2 ' + requestId],
      ['AGENT_ROBIN_V2 ' + requestId, ...body, 'AGENT_ROBIN_END_V2 ' + requestId, marker]
    ];
    const expectedPlanner = (frames, collapsed = false) => ({ key: 'parts-fixture', text: '', frames: frames.map(rows => rows.join('\n')), source_kind: 'fenced_planner_v2', collapsed });
    const plannerBody = ['  File.Read "日本語" C:\\raw %FileContents%  ', 'AGENT_EMPTY_V2 ' + requestId, 'IF result = AGENT_AICALL_FAILED', '  \u00a0 ', 'END'];
    const plannerFrames = plannerRows(plannerBody);
    const expectedSinglePlanner = (frames, collapsed = false) => ({ ...expectedPlanner(frames, collapsed), source_kind: 'fenced_planner_v2_single' });
    const renderSinglePlanner = rows => renderFenced(multipartReply([rows]), null, '.code-editor{max-height:none}');
    response = await renderSinglePlanner(plannerFrames.flat());
    check(response.state.assistants, [expectedSinglePlanner(plannerFrames)], 'A single physical fence preserves the two explicit V2 sections exactly');
    check((await page.evaluate(snapshot)).assistants, response.state.assistants, 'Single-fence V2 readback retains identity and both logical boundaries');
    for (const state of ['DONE', 'ASK_USER', 'BLOCKED']) {
      const frames = plannerRows([], { request_id: requestId, state, message: '観測済みの状態', artifacts: [] });
      response = await renderSinglePlanner(frames.flat());
      check(response.state.assistants, [expectedSinglePlanner(frames)], 'Single fence preserves zero Robin body rows for ' + state);
    }
    response = await renderSinglePlanner([...plannerFrames.flat(), '\u00a0']);
    check(response.state.assistants, [expectedSinglePlanner(plannerFrames)], 'Single fence accepts only the measured final renderer tail');
    const fittedDoneFrames = [
      ['AGENT_META_V2 ' + requestId, '{', '  "request_id":"' + requestId + '",', '  "state":"DONE",', '  "message":"' + 'M'.repeat(73) + '",', '  "artifacts":[' + JSON.stringify('C:\\fixture\\' + 'x'.repeat(145) + '.txt') + ']', '}', 'AGENT_META_END_V2 ' + requestId],
      ['AGENT_ROBIN_V2 ' + requestId, 'AGENT_ROBIN_END_V2 ' + requestId, marker]
    ];
    const fittedDoneCss = '#fixture .fenced-reply{width:706px}.code-editor{grid-template-columns:38px minmax(0,1fr);grid-template-rows:20px 20px 20px 20px 40px 80px 20px 20px 20px 20px 20px;padding:12px 0 8px;box-sizing:content-box;align-content:start}.code-line,.gutter{line-height:20px;font-family:monospace;font-size:14px}';
    response = await renderFolded(multipartReply([fittedDoneFrames.flat()]), null, fittedDoneCss);
    const fittedMetrics = await page.evaluate(() => { const e = document.querySelector('.code-editor'), r = e.getBoundingClientRect(); return { rows: e.querySelectorAll('[data-line-index]').length, height: r.height, client: e.clientHeight, scroll: e.scrollHeight, maxHeight: getComputedStyle(e).maxHeight, allRowsInside: [...e.children].every(n => n.getBoundingClientRect().bottom <= r.bottom) }; });
    check(fittedMetrics, { rows: 11, height: 320, client: 320, scroll: 320, maxHeight: '300px', allRowsInside: true }, 'Reproduce the measured short DONE with visible More but no hidden rows');
    check(response.state.assistants, [expectedSinglePlanner(fittedDoneFrames, true)], 'A complete collapsed-control state retains every short DONE row without clicking More');
    check((await page.evaluate(snapshot)).assistants, response.state.assistants, 'Short complete folded state is stable on reread');
    for (const [label, css] of [['hidden overflow', '.code-editor{overflow:hidden}'], ['scaled editor', '.code-editor{transform:scale(.9)}'], ['hidden final row', '.code-line[data-line-index="10"]{visibility:hidden}']]) {
      response = await renderFolded(multipartReply([fittedDoneFrames.flat()]), null, fittedDoneCss + css);
      check(response.state.assistants[0].source_kind, 'rendered', 'Short fitted DONE still rejects unsupported geometry: ' + label);
    }
    for (const [label, rows] of [
      ['one backtick separator', [...plannerFrames[0], '`', ...plannerFrames[1]]],
      ['two backtick separator', [...plannerFrames[0], '``', ...plannerFrames[1]]],
      ['fence delimiter separator', [...plannerFrames[0], '```', ...plannerFrames[1]]],
      ['missing metadata end', [...plannerFrames[0].slice(0, -1), ...plannerFrames[1]]],
      ['duplicate metadata end', [...plannerFrames[0], plannerFrames[0].at(-1), ...plannerFrames[1]]],
      ['mismatched section ID', [...plannerFrames[0], ...plannerFrames[1].map(row => row.replace(requestId, 'different-id'))]],
      ['missing final marker', plannerFrames.flat().slice(0, -1)],
      ['extra final row', [...plannerFrames.flat(), 'extra']],
      ['extra final delimiter', [...plannerFrames.flat(), '``']],
      ['two renderer tails', [...plannerFrames.flat(), '\u00a0', '\u00a0']]
    ]) {
      response = await renderSinglePlanner(rows);
      check(response.state.assistants[0].source_kind, 'rendered', 'Single fence refuses malformed framing without repair: ' + label);
    }
    response = await renderFenced(multipartReply(plannerFrames));
    check(response.state.assistants, [expectedPlanner(plannerFrames)], 'V2 preserves complete metadata and every literal code/sentinel/space character');
    check((await page.evaluate(snapshot)).assistants, response.state.assistants, 'Repeated complete V2 snapshots are ordinally identical');
    for (const state of ['DONE', 'ASK_USER', 'BLOCKED']) {
      const frames = plannerRows([], { request_id: requestId, state, message: '観測済みの状態', artifacts: [] });
      response = await renderFenced(multipartReply(frames));
      check(response.state.assistants, [expectedPlanner(frames)], 'Non-ACT has exactly three marker rows and zero body rows: ' + state);
    }
    response = await renderFenced(multipartReply(plannerFrames.map(rows => [...rows, '\u00a0'])));
    check(response.state.assistants, [expectedPlanner(plannerFrames)], 'V2 strips only the measured separate renderer tail after each terminal marker');
    const nbspBody = plannerRows(['Read input', '\u00a0', 'Write output']);
    response = await renderFenced(multipartReply(nbspBody));
    check(response.state.assistants, [expectedPlanner(nbspBody)], 'The measured U+00A0 body row is retained and never silently decoded as empty');
    const longPlanner = plannerRows(Array.from({ length: 25 }, (_, i) => '  File.' + i + ' "引用" C:\\path %FileContents% ' + '日本語'.repeat(90)));
    const foldedPlannerCss = '.fenced-inner:last-child .more-holder{display:flex}.fenced-inner:last-child .more-button{display:flex;height:32px}.fenced-inner:last-child .code-editor{overflow:auto;max-height:300px}';
    response = await renderFenced(multipartReply(longPlanner), null, foldedPlannerCss);
    check(longPlanner[1].join('\n').length > 7000, true, 'Long Robin fixture exceeds the previously failing JSON payload size');
    check(response.state.assistants, [expectedPlanner(longPlanner, true)], 'Short metadata and folded long Robin both retain complete geometry and all rows');
    await assert.rejects(() => page.evaluate(expandExpression('parts-fixture', longPlanner[1].join('\n'), requestId)), error => error.message.includes('expand unavailable'), 'V2 full-row reading never authorizes a legacy More click');
    checks++;
    const longMeta = plannerRows(longPlanner[1].slice(1, -2), { request_id: requestId, state: 'ACT', message: '説明'.repeat(9000), artifacts: [] });
    response = await renderFolded(multipartReply(longMeta));
    check(response.state.assistants, [expectedPlanner(longMeta, true)], 'Metadata physical rows are not silently narrowed to the diagnostic 16384-character limit');
    const maximumRows = plannerRows(Array.from({ length: 250 }, () => 'AGENT_EMPTY_V2 ' + requestId));
    response = await renderFenced(multipartReply(maximumRows), null, foldedPlannerCss);
    check(response.state.assistants, [expectedPlanner(maximumRows, true)], 'Capture all 250 wire body rows without inferring missing lines');
    const boundedMetaValue = JSON.stringify({ request_id: requestId, state: 'ACT', message: '', artifacts: [] });
    const encodedMessageLength = 1048576 - boundedMetaValue.length;
    const encodedMessage = '\\u3042'.repeat(Math.floor(encodedMessageLength / 6)) + 'a'.repeat(encodedMessageLength % 6);
    const boundedMetaText = boundedMetaValue.replace('"message":""', '"message":"' + encodedMessage + '"');
    const boundedBody = ['SET X TO ' + 'a'.repeat(64000 - 249 - 9), ...Array.from({ length: 249 }, () => 'AGENT_EMPTY_V2 ' + requestId)];
    const combinedBound = [['AGENT_META_V2 ' + requestId, boundedMetaText, 'AGENT_META_END_V2 ' + requestId], plannerRows(boundedBody)[1]];
    response = await renderFolded(multipartReply(combinedBound));
    check(combinedBound.map(rows => rows.join('\n').length).reduce((a, b) => a + b) > 1114000, true, 'Individually legal metadata and encoded-empty overhead exceed the removed aggregate shortcut');
    check(response.state.assistants[0].source_kind, 'fenced_planner_v2', 'Preserve the complete combined boundary as a structured carrier');
    check(response.state.assistants[0].frames.map((frame, i) => frame === expectedPlanner(combinedBound, true).frames[i]), [true, true], 'Preserve full bounded metadata and 250 encoded body rows together without narrowing the final parser contract');
    check(JSON.stringify({ ...JSON.parse(boundedMetaText), robin: [boundedBody[0], ...Array(249).fill('')].join('\n') }).length < 1048576, true, 'The combined wire boundary still fits the decoded final JSON contract');
    response = await renderFolded(multipartReply([combinedBound.flat()]));
    check(response.state.assistants, [expectedSinglePlanner(combinedBound, true)], 'Single fence retains the full metadata and 250 encoded body rows at the combined bound');
    for (const [label, frames] of [
      ['third fence', [...plannerFrames, plannerFrames[1]]],
      ['reversed fences', [...plannerFrames].reverse()],
      ['missing Robin end', [plannerFrames[0], plannerFrames[1].filter((_, i, rows) => i !== rows.length - 2)]],
      ['missing final marker', [plannerFrames[0], plannerFrames[1].slice(0, -1)]],
      ['extra terminal row', [plannerFrames[0], [...plannerFrames[1], 'extra']]],
      ['two renderer tails', [plannerFrames[0], [...plannerFrames[1], '\u00a0', '\u00a0']]],
      ['ordinary trailing space', [plannerFrames[0], [...plannerFrames[1], ' ']]],
      ['251 body rows', plannerRows(Array.from({ length: 251 }, () => 'AGENT_EMPTY_V2 ' + requestId))],
      ['unmeasured true empty row', plannerRows(['Read input', '', 'Write output'])]
    ]) {
      response = await renderFenced(multipartReply(frames));
      check(response.state.assistants[0].source_kind, 'rendered', 'V2 refuses incomplete/unknown carrier shape: ' + label);
    }
    for (const [label, setup, css] of [
      ['separator explanation', () => { document.querySelector('.fenced-wrapper').childNodes[1].nodeValue += 'explanation'; }],
      ['unknown outside node', () => document.querySelector('.fenced-reply').appendChild(document.createComment('unknown'))],
      ['missing indexed row', () => { const row = document.querySelectorAll('.code-editor')[1].querySelector('[data-line-index="2"]'); row.previousSibling.remove(); row.remove(); }],
      ['changed row index', () => document.querySelectorAll('.code-editor')[1].querySelector('[data-line-index="2"]').setAttribute('data-line-index', '1')],
      ['nested body text', () => { const row = document.querySelectorAll('.code-editor')[1].querySelector('[data-line-index="2"]'); const inner = document.createElement('span'); inner.textContent = row.textContent; row.replaceChildren(inner); }],
      ['split body text', () => document.querySelectorAll('.code-editor')[1].querySelector('[data-line-index="2"]').firstChild.splitText(3)],
      ['BR instead of blank', () => document.querySelectorAll('.code-editor')[1].querySelector('[data-line-index="2"]').replaceChildren(document.createElement('br'))],
      ['hidden row', null, '.fenced-inner:last-child [data-line-index="2"]{visibility:hidden!important}'],
      ['transparent ancestor', null, '.fenced-wrapper{opacity:.5!important}'],
      ['content visibility', null, '.fenced-inner:last-child{content-visibility:auto!important}'],
      ['clipped hidden-control body', null, '.fenced-inner:last-child .code-editor{height:20px}'],
      ['horizontal overflow', null, '.fenced-inner:last-child .code-line{min-width:1000px}'],
      ['transformed editor', null, '.fenced-inner:last-child .code-editor{transform:scale(.9)}']
    ]) {
      response = await renderFenced(multipartReply(plannerFrames), setup, css || '');
      check(response.state.assistants[0].source_kind, 'rendered', 'V2 retains full DOM ownership and geometry checks: ' + label);
    }
    for (const [label, frames] of [
      ['wrong nonce', plannerFrames.map(rows => rows.map(row => row.replaceAll(requestId, 'wrong-nonce')))],
      ['duplicate JSON key', [['AGENT_META_V2 ' + requestId, '{"request_id":"' + requestId + '","state":"ACT","state":"DONE"}', 'AGENT_META_END_V2 ' + requestId], plannerFrames[1]]],
      ['wrong empty marker nonce', plannerRows(['Read input', 'AGENT_EMPTY_V2 wrong-nonce', 'Write output'])]
    ]) {
      response = await renderFenced(multipartReply(frames));
      check(response.state.assistants, [expectedPlanner(frames)], 'DOM keeps parser-owned invalid content exact without repair: ' + label);
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
