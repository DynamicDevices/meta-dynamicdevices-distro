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
const pointer = (type,x,y,id=1,target={closest:()=>null},pointerType='mouse') => listeners.get(type)({type,pointerId:id,clientX:x,clientY:y,pointerType,target});
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

run('clear()');
const control = {closest:()=>({})};
const surface = {closest:()=>null};
pointer('pointerdown',400,400,21);
pointer('pointermove',500,450,21,control);
assert.equal(run('pointers.size'),1,'tracked drag continues over navigation');
pointer('pointerup',500,450,21,control);
assert.equal(run('pointers.size'),0,'release over navigation clears tracked pointer');
pointer('pointerdown',400,400,22);
pointer('pointercancel',500,450,22,control);
assert.equal(run('pointers.size'),0,'cancel over navigation clears tracked pointer');
run('clear()');
function native(type, target, contacts) {
    listeners.get(type)({type,target,touches:contacts,changedTouches:contacts,preventDefault(){}});
}
const buttonTouch = {identifier:31,clientX:50,clientY:50,target:control};
native('touchstart',control,[buttonTouch]);
assert.equal(run('touches.size'),0,'button-only touch is not a test contact');
assert.equal(run('nativeSeen'),false,'button-only touch must not disable pointer fallback');
const testTouch = {identifier:32,clientX:500,clientY:400,target:surface};
native('touchstart',surface,[testTouch]);
native('touchstart',control,[testTouch,buttonTouch]);
assert.equal(run('touches.size'),1,'control contact cannot join an existing gesture');
assert.equal(run('touches.has(32)'),true,'existing surface contact is retained');
native('touchend',surface,[]);
assert.equal(run('touches.size'),0,'last surface release clears contacts');
console.log('PASS: control-touch filtering, existing-contact retention, pointer move/release/cancel over navigation');

// Browser animation frames are queued: a whole contact can happen before one draw.
const frames = [];
sandbox.requestAnimationFrame = callback => frames.push(callback);
run('clear()');
pointer('pointerdown',400,400,41);
pointer('pointerdown',500,400,42);
pointer('pointerup',400,400,41);
pointer('pointerup',500,400,42);
assert.equal(run('pointers.size'),0);
assert.equal(run('maximum'),2,'pointer peak survives down/up before rendering');
assert.equal(frames.length,1,'contact updates coalesce into one frame');
while (frames.length) frames.shift()();
assert.equal(run('maximum'),2);
run('clear()');
native('touchstart',surface,[testTouch, {...testTouch,identifier:33}]);
native('touchend',surface,[]);
assert.equal(run('touches.size'),0);
assert.equal(run('maximum'),2,'native peak survives start/end before rendering');
assert.equal(frames.length,1);
while (frames.length) frames.shift()();
assert.equal(run('maximum'),2);
console.log('PASS: native and pointer contact peaks survive queued animation frames');

run('clear()');
pointer('pointerdown',100,100,50,surface,'mouse');
pointer('pointerup',100,100,50,surface,'mouse');
const mouseHistory = run('history.length');
pointer('pointerdown',500,400,51,surface,'touch');
pointer('pointermove',510,410,51,surface,'touch');
assert.equal(run('history.length'),mouseHistory+2);
native('touchstart',surface,[{...testTouch,clientX:500,clientY:400}]);
assert.equal(run('history.length'),mouseHistory+1,'first native contact replaces compatibility trail only');
assert.equal(run('history.filter(point => point.down).length'),2,'one real mouse and one native initial mark');
native('touchmove',surface,[{...testTouch,clientX:510,clientY:410}]);
pointer('pointermove',510,410,51,surface,'touch');
assert.equal(run('history.length'),mouseHistory+2,'corresponding native/pointer moves add one mark');
native('touchend',surface,[]);
pointer('pointerup',510,410,51,surface,'touch');
while (frames.length) frames.shift()();
assert.equal(run('history.some(point => point.compatibilityId !== undefined)'),false);
console.log('PASS: Chromium compatibility pointer/native input does not duplicate trails or erase mouse history');
