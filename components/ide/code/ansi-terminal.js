/* CodyNick terminal renderer 0.3.0: SGR colors only; output is never HTML. */
(function (root) {
  'use strict';
  class AnsiParser {
    constructor() { this.reset(); }
    reset() { this.pending = ''; this.color = null; this.bold = false; this.osc = false; }
    feed(chunk, emit) {
      let data = this.pending + chunk; this.pending = '';
      let i = 0, text = '';
      const flush = () => { if (text) emit(text, this.color, this.bold); text = ''; };
      while (i < data.length) {
        if (this.osc) {
          if (data[i] === '\x07') { this.osc = false; i++; }
          else if (data[i] === '\x1b' && i + 1 === data.length) { this.pending = '\x1b'; break; }
          else if (data.slice(i, i + 2) === '\x1b\\') { this.osc = false; i += 2; }
          else i++;
          continue;
        }
        if (data[i] !== '\x1b') {
          if (data[i] === '\n' || data[i] === '\t' || data.charCodeAt(i) >= 32) text += data[i];
          i++; continue;
        }
        flush();
        if (i + 1 === data.length) { this.pending = data.slice(i); break; }
        if (data[i + 1] === ']') { this.osc = true; i += 2; continue; }
        if (data[i + 1] !== '[') { i += 2; continue; }
        let end = i + 2;
        while (end < data.length && !(/[\x40-\x7e]/.test(data[end]))) end++;
        if (end === data.length) { this.pending = data.slice(i).slice(0, 128); break; }
        if (data[end] === 'm') {
          const args = data.slice(i + 2, end).split(';').map(v => Number(v || 0));
          for (let n = 0; n < args.length; n++) {
            const code = args[n];
            if (code === 0) { this.color = null; this.bold = false; }
            else if (code === 1) this.bold = true;
            else if (code === 22) this.bold = false;
            else if (code === 39) this.color = null;
            else if ((code >= 30 && code <= 37) || (code >= 90 && code <= 97)) this.color = code;
            else if (code === 38 || code === 48) n += args[n + 1] === 2 ? 4 : args[n + 1] === 5 ? 2 : args.length;
          }
        }
        i = end + 1;
      }
      flush();
    }
  }
  class AnsiTerminal {
    constructor(element) { this.element = element; this.parser = new AnsiParser(); this.length = 0; this.reset(); }
    reset() { this.parser.reset(); this.length = 0; this.element.replaceChildren(); }
    append(chunk) {
      this.parser.feed(chunk, (text, color, bold) => {
        const node = document.createElement('span');
        node.className = (color === null ? '' : 'ansi-' + color) + (bold ? ' ansi-bold' : '');
        node.textContent = text;
        this.element.appendChild(node); this.length += text.length;
      });
      while (this.length > 262144 && this.element.firstChild) {
        const node = this.element.firstChild, excess = this.length - 262144;
        if (node.textContent.length <= excess) { this.length -= node.textContent.length; node.remove(); }
        else { node.textContent = node.textContent.slice(excess); this.length -= excess; }
      }
    }
  }
  root.CodyNickAnsi = { AnsiParser, AnsiTerminal };
  if (typeof module !== 'undefined') module.exports = root.CodyNickAnsi;
})(typeof globalThis !== 'undefined' ? globalThis : window);
