#!/usr/bin/env node
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {spawnSync} from 'node:child_process';

const page = new URL('../recipes-graphics/jaguar-touch-test/jaguar-touch-test/index.html', import.meta.url);
const script = fs.readFileSync(page, 'utf8').match(/<script>([\s\S]*?)<\/script>/)[1];
const drawCalls = [];
const context2d = new Proxy({}, {get: (_target,name) => (...args) => {drawCalls.push({name,args});}});
const elements = new Map();
function element(id) {
    if (!elements.has(id)) elements.set(id, {
        style:{}, textContent:'', appendChild(){}, addEventListener(){},
        querySelector(){ return element('svg'); },
        getContext(){ return context2d; }
    });
    return elements.get(id);
}
const context = vm.createContext({
    document:{body:{appendChild(){}},querySelector:element,createElement:() => ({style:{}}),addEventListener(){}},
    addEventListener(){}, innerWidth:1920, innerHeight:1200, devicePixelRatio:1,
    performance:{now:()=>1000}, setTimeout:()=>1, clearTimeout(){},
    requestAnimationFrame:callback=>callback(),
    URLSearchParams, location:{search:''},
});
vm.runInContext(script, context);
const run = source => vm.runInContext(source, context);
function touch(type, identifiers, changed = identifiers) {
    context.event = {type, target:{closest:()=>null}, preventDefault(){},
        touches:identifiers.map(identifier=>({identifier,clientX:100+identifier,clientY:200+identifier})),
        changedTouches:changed.map(identifier=>({identifier,clientX:120+identifier,clientY:220+identifier})),
    };
    run('onTouch(event)');
}
touch('touchstart',[10]);
assert.equal(run('touches.size'),1);
assert.equal(run('history.length'),1,'one finger must make a visible mark');
touch('touchmove',[10]);
assert.equal(run('history.length'),2,'one finger must leave a trail');
touch('touchstart',[10,20],[20]);
assert.equal(run('touches.size'),2);
assert.equal(run('new Set(Array.from(touches.values(),p=>p.slot)).size'),2);
touch('touchstart',[30,20,10],[30]);
assert.equal(run('touches.size'),3);
assert.equal(run('new Set(Array.from(touches.values(),p=>p.slot)).size'),3,'contact reorder must not duplicate labels');
touch('touchstart',[10,20,30,40,50,60,70,80,90,100]);
assert.equal(run('touches.size'),10);
assert.equal(run('new Set(Array.from(touches.values(),p=>p.slot)).size'),10);
assert.equal(run('maximum'),10);
touch('touchend',[10],[20,30,40,50,60,70,80,90,100]);
assert.equal(run('touches.size'),1);
touch('touchcancel',[],[10]);
assert.equal(run('touches.size'),0);
run('clear()');
touch('touchmove',[77]);
assert.equal(run('touches.size'),1,'complete TouchEvent set must recover without pointerdown');
assert.equal(run('history.length'),1);
run('clear()');
context.event={type:'pointerdown',pointerId:3,pointerType:'touch',clientX:100,clientY:200};
run('onPointer(event)');
assert.equal(run('pointers.size'),1);
assert.equal(run('history.length'),1,'pointer-only fallback must show one contact');
assert.equal(elements.get('#count').textContent,'1 contact · peak 1');
console.log('PASS: one-finger trails, 2/3/10 contacts, contact reorder, lift/cancel, native recovery, pointer fallback');

function gestureEvent(type, coordinates) {
    context.event = {type,target:{closest:()=>null},preventDefault(){},
        touches:coordinates.map(([identifier,clientX,clientY])=>({identifier,clientX,clientY})),
        changedTouches:coordinates.map(([identifier,clientX,clientY])=>({identifier,clientX,clientY}))};
    run('onTouch(event)');
}
run("setMode('gestures')");
gestureEvent('touchstart',[[1,800,600]]);
gestureEvent('touchmove',[[1,900,650]]);
assert.equal(run('view.x'),100,'single-finger horizontal pan');
assert.equal(run('view.y'),50,'single-finger vertical pan');
gestureEvent('touchstart',[[1,900,650],[2,1100,650]]);
gestureEvent('touchmove',[[1,800,650],[2,1200,650]]);
assert.equal(run('view.scale'),2,'two-finger spread must double scale');
assert.equal(run('view.x'),160,'zoom must retain image anchor under pinch midpoint');
gestureEvent('touchmove',[[1,850,680],[2,1250,680]]);
assert.equal(run('view.x'),210,'two-finger translation');
assert.equal(run('view.y'),80);
gestureEvent('touchmove',[[1,1000,680],[2,1100,680]]);
assert.equal(run('view.scale'),.5,'pinch must zoom out');
gestureEvent('touchend',[[1,1000,680]]);
const beforeX = run('view.x');
gestureEvent('touchmove',[[1,1010,680]]);
assert.equal(run('view.x'),beforeX+10,'lifting one finger must continue drag without a jump');
gestureEvent('touchstart',[[1,1010,680],[2,1110,680],[3,1300,800]]);
gestureEvent('touchmove',[[3,1400,900],[2,1110,680],[1,1010,680]]);
assert.equal(run('view.scale'),.5,'third finger and contact reorder must not corrupt pinch');
gestureEvent('touchmove',[[1,0,680],[2,10000,680]]);
assert.equal(run('view.scale'),8,'upper zoom bound');
gestureEvent('touchmove',[[1,10,680],[2,10.01,680]]);
assert.equal(run('view.scale'),.25,'lower zoom bound');
run('resetView()');
assert.equal(run('view.scale'),1);
assert.equal(run('view.x'),0);
run("setMode('contacts')");
gestureEvent('touchstart',[[1,100,100]]);
gestureEvent('touchmove',[[1,300,300]]);
assert.equal(run('view.x'),0,'contact mode must not pan');
assert.ok(elements.get('#instructions').textContent.includes('ONE finger'));
run("setMode('gestures')");
assert.equal(elements.get('#gesture-art').style.display,'grid');
assert.ok(elements.get('#gesture-art').style.transform.includes('scale(1)'));
assert.ok(elements.get('#instructions').textContent.includes('Pause animation'));
elements.get('#motion').onclick();
assert.equal(elements.get('#gesture-art').className,'paused');
assert.equal(elements.get('#motion').textContent,'Play animation');
elements.get('#motion').onclick();
assert.equal(elements.get('#gesture-art').className,'');
run("setMode('contacts')");
assert.equal(elements.get('#gesture-art').style.display,'none');
console.log('PASS: single/two-finger pan, anchored pinch, liftoff transition, third finger, zoom bounds, reset, on-page instructions');

run("setMode('gestures')");
assert.equal(run('trailVisibility.gestures'),false,'gesture mode starts with trails hidden');
assert.equal(elements.get('#trails').textContent,'Show trails');
gestureEvent('touchstart',[[1,800,600]]);
gestureEvent('touchmove',[[1,900,650]]);
const gestureX = run('view.x');
drawCalls.length=0;
run('render()');
assert.equal(drawCalls.filter(call=>call.name==='arc').length,0,'hidden trails use DOM contact markers without canvas drawing');
assert.equal(run('contactMarkers.size > 0'),true,'live contact markers remain visible');
elements.get('#trails').onclick();
assert.equal(elements.get('#trails').textContent,'Hide trails');
assert.equal(elements.get('#trails').ariaPressed,'true');
assert.equal(run('view.x'),gestureX,'toggling trails must not reset gesture');
assert.equal(run('touches.size'),1,'toggling trails must retain active contacts');
drawCalls.length=0;
run('render()');
assert.equal(drawCalls.filter(call=>call.name==='arc').length,3,'shown history must include two recorded marks and the live contact');
run("setMode('contacts')");
assert.equal(run('trailVisibility.contacts'),true,'contact mode starts with trails visible');
elements.get('#trails').onclick();
assert.equal(run('trailVisibility.contacts'),false);
run("setMode('gestures')");
assert.equal(run('trailVisibility.gestures'),true,'each mode retains its own toggle preference');
run('clear()');
assert.equal(run('history.length'),0);
assert.equal(run('trailVisibility.gestures'),true,'clear must not change visibility preference');
console.log('PASS: per-mode trail defaults, actual hidden/visible drawing, live contacts retained, gestures unchanged, independent preferences');

// Catch lost payloads and accidental return to demo-only touch policy ownership.
const root = new URL('../', import.meta.url);
const read = path => fs.readFileSync(new URL(path, root), 'utf8');
const display = read('recipes-samples/images/lmp-feature-display-multimedia.inc');
const kiosk = read('recipes-samples/images/lmp-feature-kiosk-browser.inc');
assert.match(display,/CORE_IMAGE_BASE_INSTALL:append:imx8mm-jaguar-screen = " jaguar-screen-touch"/);
assert.match(kiosk,/CORE_IMAGE_BASE_INSTALL:append:imx8mm-jaguar-screen = " jaguar-touch-test"/);
for (const name of ['jaguar-screen-touch','jaguar-touch-test']) {
    const recipe = read(`recipes-graphics/${name}/${name}_1.0.bb`);
    for (const match of recipe.matchAll(/file:\/\/([^\s";]+)/g)) {
        if (match[1].includes('${')) continue;
        assert.ok(fs.existsSync(new URL(`recipes-graphics/${name}/${name}/${match[1]}`,root)), `missing ${match[1]}`);
    }
    assert.match(recipe,/COMPATIBLE_MACHINE = "\^imx8mm-jaguar-screen\$"/);
}
assert.match(read('recipes-graphics/jaguar-screen-touch/jaguar-screen-touch/99-jaguar-screen-touch.rules'),/LIBINPUT_CALIBRATION_MATRIX}="1 0 0 0 1 0"/);
const flutter = read('recipes-graphics/screen-flutter-demo/screen-flutter-demo_1.0.bb');
assert.match(flutter,/jaguar-screen-touch/);
assert.doesNotMatch(flutter,/file:\/\/99-jaguar-screen-touch.rules/);
console.log('PASS: Jaguar image hooks, recipe payloads, shared identity policy, Flutter dependency');

assert.match(read('recipes-graphics/jaguar-touch-test/jaguar-touch-test_1.0.bb'),
    /RDEPENDS:\$\{PN\} = "packagegroup-dd-kiosk-browser"/);
assert.match(read('recipes-core/packagegroups/packagegroup-dd-kiosk-browser.bb'),
    /RDEPENDS:\$\{PN\} = "\$\{DD_KIOSK_BROWSER_RUNTIME\}"/);
const launcher = read('recipes-graphics/jaguar-touch-test/jaguar-touch-test/jaguar-touch-test')
    .replace('exec /usr/bin/dd-kiosk-browser', 'printf \'%s\\n%s\\n\' "$DD_KIOSK_GLES2_COMPAT" "$DD_KIOSK_URL"');
for (const override of [undefined,'0','1']) {
    const env = {PATH:process.env.PATH};
    if (override !== undefined) env.DD_KIOSK_GLES2_COMPAT = override;
    const result = spawnSync('sh',['-c',launcher,'jaguar-touch-test','--gestures'],{env,encoding:'utf8'});
    assert.equal(result.status,0,result.stderr);
    assert.deepEqual(result.stdout.trim().split('\n'),[
        override ?? '1','file:///usr/share/jaguar-touch-test/index.html?mode=gestures']);
}
console.log('PASS: selected browser provider dependency, direct-launch GLES2 default and explicit overrides');
