// Exercises the generated report without network access or a browser service.
// DOM checks verify behaviour, not visual layout in a native browser.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {JSDOM,VirtualConsole}=require('jsdom');
const html=fs.readFileSync(path.join(__dirname,'../reports/dashboard.html'),'utf8');
const errors=[];const vc=new VirtualConsole();vc.on('jsdomError',e=>errors.push(e.message));
const dom=new JSDOM(html,{runScripts:'dangerously',url:'https://offline-report.invalid/',virtualConsole:vc});
const w=dom.window,d=w.document,$=id=>d.getElementById(id);
const change=(id,value)=>{$(id).value=value;$(id).dispatchEvent(new w.Event('change'))};
const data=JSON.parse($('dataset').textContent);
assert.equal(d.querySelectorAll('#map path').length,61);
assert.equal(d.querySelectorAll('#cards .number').length,3);
assert.equal($('selected-value').textContent,'55.2%');
assert.equal($('area-title').textContent,'Liverpool 024');
change('metric','aged_65_share');change('area','E02001347');
assert.equal($('selected-value').textContent,'15.0%');
assert.equal($('selected-counts').textContent,'1,205 of 8,039 · all usual residents');
assert.match($('map-subtitle').textContent,/Residents aged 65/);
assert.equal(d.querySelector('#map path.selected').dataset.code,'E02001347');
change('metric','employed_share');
assert.equal($('selected-value').textContent,'56.4%');
assert.match($('selected-counts').textContent,/3,643 of 6,463/);
d.querySelector('#map path[data-code="E02001348"]').dispatchEvent(new w.KeyboardEvent('keydown',{key:'Enter',bubbles:true}));
assert.equal($('area').value,'E02001348');
$('tab-comparison').click();assert.equal($('overview').hidden,true);assert.equal($('comparison').hidden,false);
assert.equal(d.querySelectorAll('#tablebody tr').length,61);
change('sort','asc');
let first=d.querySelector('#tablebody tr button').textContent;
assert.equal(first,'Liverpool 031');
$('search').value='Liverpool 001';$('search').dispatchEvent(new w.Event('input'));
assert.equal(d.querySelectorAll('#tablebody tr').length,1);
assert.match($('table-status').textContent,/1 of 61/);
// Capture generated CSV without initiating navigation or a download.
let captured=null,filename='';w.Blob=class {constructor(parts,options){captured=parts.join('');this.type=options.type}};
w.URL.createObjectURL=()=> 'blob:local-test';w.URL.revokeObjectURL=()=>{};
w.HTMLAnchorElement.prototype.click=function(){filename=this.download};
$('download').click();
assert.equal(filename,'liverpool-employed_share.csv');
assert.equal(captured.split('\r\n').length,2);assert.match(captured,/"3643","6463"/);
assert.match(captured,/"2021-03-21"/);
d.querySelector('#tablebody button').click();
assert.equal($('overview').hidden,false);assert.equal($('area').value,'E02001347');
$('search').value='no-such-area';$('search').dispatchEvent(new w.Event('input'));
assert.equal(d.querySelectorAll('#tablebody tr').length,0);assert.match($('table-status').textContent,/0 of 61/);
// Validate every UI indicator for every area against the exported SQL values.
for(const metric of Object.keys(data.definitions)){
 change('metric',metric);
 for(const row of data.neighbourhoods){change('area',row.area_code);assert.equal($('selected-value').textContent,(100*row[metric]).toFixed(1)+'%')}
}
assert.deepEqual(errors,[]);
dom.window.close();
console.log('Report DOM checks passed: 183 area/indicator combinations; map keyboard selection; navigation; sorting; search; empty results; CSV counts and date.');
