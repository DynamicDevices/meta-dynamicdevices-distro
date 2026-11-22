const fs = require('fs');
const vm = require('vm');
const assert = require('node:assert/strict');
let draws = 0;
const context2d = new Proxy({}, {get: () => () => { draws++; }});
const elements = new Map();
const listeners = new Map();
function element(id) {
  if (!elements.has(id)) elements.set(id, {style:{}, textContent:'',className:'',
    appendChild(){},addEventListener(){},querySelector(){return element('svg');},
    getContext(){return context2d;}});
  return elements.get(id);
}
const sandbox = {console, URLSearchParams, location:{search:'?mode=gestures'},
  innerWidth:1920, innerHeight:1200, devicePixelRatio:1,
  matchMedia:()=>({matches:false}),addEventListener(){},
  performance:{now:()=>1000},setTimeout:()=>1,clearTimeout(){},requestAnimationFrame:callback=>callback(),
  document:{body:{appendChild(){}},querySelector:element,createElement:()=>element(Math.random()),
    addEventListener(type,callback){listeners.set(type,callback);}}};
vm.createContext(sandbox);
const html = fs.readFileSync(process.argv[2] || __dirname+'/jaguar-touch-test/index.html','utf8');
vm.runInContext(html.match(/<script>([\s\S]*?)<\/script>/)[1],sandbox);
const run = code => vm.runInContext(code,sandbox);
assert.equal(element('#screen').style.display,'none');
draws=0;run('render()');assert.equal(draws,0,'Empty gesture view must not redraw canvas');
const pointer = (type,x,y,id=1,target={closest:()=>null}) => listeners.get(type)({type,pointerId:id,clientX:x,clientY:y,pointerType:'mouse',target});
pointer('pointerdown',400,400);pointer('pointermove',500,450);
assert.equal(run('view.x'),100);assert.equal(run('view.y'),50);
assert.equal(element('#screen').style.display,'none');
assert.equal(run('contactMarkers.size'),1,'Live markers must exist without fullscreen canvas');
assert.equal(run('pointers.size'),1);
assert.equal(element('#gesture-art').className,'paused','Decorative motion pauses during contact');
pointer('pointerdown',700,450,2);pointer('pointermove',900,450,2);
assert.equal(run('view.scale'),2,'Two-pointer pinch must still zoom');
pointer('pointerup',500,450);pointer('pointerup',900,450,2);
assert.equal(run('pointers.size'),0);
assert.equal(element('#screen').style.display,'none');
assert.equal(element('#gesture-art').className,'','Decorative motion resumes after release');
assert.notEqual(element('#gesture-art').style.transform,'');
pointer('pointerdown',5,5,3,{closest:()=>({})});
assert.equal(run('pointers.size'),0,'Button presses must not become contacts');
run('trailVisibility.gestures=true;render()');
assert.equal(element('#screen').style.display,'block','Visible trails retain canvas');
run('clear();setMode("contacts")');
assert.equal(element('#screen').style.display,'block','Contact calibration view retains canvas');
assert.equal(element('#gesture-art').style.display,'none');
run('setMode("gestures");trailVisibility.gestures=false;motionPaused=true;render()');
assert.equal(element('#gesture-art').className,'paused');
assert.equal(element('#screen').style.display,'none');
run(`onTouch({type:'touchstart', target:{closest:()=>null}, preventDefault(){},
    touches:[{identifier:7,clientX:500,clientY:400}],changedTouches:[{identifier:7,clientX:500,clientY:400}]});
    onTouch({type:'touchmove', target:{closest:()=>null}, preventDefault(){},
    touches:[{identifier:7,clientX:600,clientY:450}],changedTouches:[{identifier:7,clientX:600,clientY:450}]});`);
assert.equal(run('view.x'),100); assert.equal(run('view.y'),50);
run(`onTouch({type:'touchcancel', target:{closest:()=>null}, preventDefault(){},
    touches:[],changedTouches:[{identifier:7,clientX:600,clientY:450}]});`);
assert.equal(run('touches.size'),0);
assert.equal(element('#screen').style.display,'none');
console.log('PASS: empty-view redraw, pointer fallback, native-touch pan/cancel, pinch, release, buttons, trails, modes, animation control');
