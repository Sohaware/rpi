const assert = require('node:assert/strict');
const {AnsiParser, AnsiTerminal} = require('../components/ide/code/ansi-terminal.js');
let out = [], parser = new AnsiParser();
const emit = (text,color,bold) => out.push({text,color,bold});
parser.feed('\x1b[9', emit); parser.feed('2mGreen', emit); parser.feed(' still green\x1b[0m plain',emit);
assert.deepEqual(out.map(x=>x.color), [92,92,null]);
assert.equal(out.map(x=>x.text).join(''), 'Green still green plain');
parser.reset(); out=[]; parser.feed('<img src=x onerror=alert(1)>\x1b[2Jsafe\x1b]8;;https://evil\x07text\x1b]8;;\x1b\\',emit);
assert.equal(out.map(x=>x.text).join(''),'<img src=x onerror=alert(1)>safetext');
parser.reset(); out=[]; parser.feed('\x1b[38;2;92;0;0mno unsupported color',emit); assert.equal(out[0].color,null);
parser.reset(); out=[]; parser.feed('\x1b[1;31mred',emit); parser.reset(); parser.feed('normal',emit); assert.equal(out[1].color,null); assert.equal(out[1].bold,false);
class Node {
  constructor(){this.children=[];this.textContent='';}
  appendChild(child){child.parent=this;this.children.push(child);}
  replaceChildren(){this.children=[];}
  get firstChild(){return this.children[0];}
  remove(){this.parent.children.shift();}
  set innerHTML(value){throw Error('Unsafe HTML insertion');}
}
global.document={createElement:()=>new Node()};
const element=new Node(), terminal=new AnsiTerminal(element);
terminal.append('\x1b[92m<img src=x>');
assert.equal(element.children[0].textContent,'<img src=x>'); assert.equal(element.children[0].className,'ansi-92');
terminal.append('x'.repeat(300000)); assert.equal(terminal.length,262144);
terminal.reset(); terminal.append('plain'); assert.equal(element.children[0].className,'');
console.log('ANSI chunking, reset, escaping, controls, and bounded output passed.');
