const $ = s => document.querySelector(s);
let selected = 'cat';
const reducedMotion=matchMedia('(prefers-reduced-motion: reduce)').matches;
const petNames = {cat:'Mochi',dog:'Biscuit',bunny:'Clover',fox:'Maple',dino:'Fern',tiger:'Tiggy',parrot:'Pip'};
const petTitles = {cat:'kitty',dog:'puppy',bunny:'bunny',fox:'fox',dino:'dino',tiger:'tiger',parrot:'parrot'};
const clean = (value, fallback) => value.replace(/[^a-z0-9 -]/gi,'').trim().slice(0,12) || fallback;
function updateNames(){
  const owner=clean($('#owner-name').value,'Friend'),pet=clean($('#pet-name').value,'Mochi');
  $('#name-speech').textContent=`Hi ${owner}! I’m ${pet}. ♡`;
  $('#name-tag').textContent=`${pet.toUpperCase()} ♥ ${owner.toUpperCase()}`;
  $('#phone-owner').textContent=`Hi, ${owner}`;
  $('#phone-description').textContent=`${pet} is happy to see you.`;
  $('#phone-pet-label').textContent=`${pet.toUpperCase()} · LEVEL 1`;
  $('#hero-speech').textContent=`Hi ${owner}! You’re my person. ♡`;
  $('#hero-pet').setAttribute('aria-label',`Pet ${pet}`);
  $('#hero-pet img').alt=`${pet}, your pixel ${petTitles[selected]}`;
  for(const image of [$('#name-pet'),$('#hero-pet img'),$('.phone-room img')]){
    image.src=`assets/pets/${selected}-0${reducedMotion?'.png':'-idle.gif'}`;
    image.alt=`${pet}, your pixel ${petTitles[selected]}`;
  }
  $('#hero-care-hint').textContent=`Click ${pet} to say hello!`;

}
document.querySelectorAll('[data-species]').forEach(button=>button.addEventListener('click',()=>{
  const useDefaultName=!$('#pet-name').value.trim()||$('#pet-name').value===petNames[selected];
  selected=button.dataset.species;
  document.querySelectorAll('[data-species]').forEach(b=>{b.classList.toggle('selected',b===button);b.setAttribute('aria-pressed',String(b===button))});
  if(useDefaultName)$('#pet-name').value=petNames[selected];
  $('#selection-note').textContent=`${clean($('#pet-name').value,petNames[selected])} the ${petTitles[selected]} is ready to meet you. Preview only; unlock pets with earned coins in the app.`;
  updateNames();
}));
['#owner-name','#pet-name'].forEach(s=>$(s).addEventListener('input',updateNames));
$('#preview-form').addEventListener('submit',e=>{e.preventDefault();updateNames();$('#name-speech').textContent+=' Your free Plus room is ready—open it below.';});
let greetings=0;
$('#hero-pet').addEventListener('click',()=>{const owner=clean($('#owner-name').value,'Friend');$('#hero-speech').textContent=['Purr… best break of the day. ♡','A little snack? Pretty please?','You make my little world happy.',`Hi ${owner}! You’re my person. ♡`][greetings++%4]});
updateNames();
fetch('downloads/release.json').then(r=>r.ok?r.json():null).then(r=>{if(r)$('#download-size').textContent=`${r.sizeMB} MB installer · no Python needed`}).catch(()=>{});
if(reducedMotion) document.querySelectorAll('img[src$=".gif"]').forEach(img=>img.src=img.src.replace(/-(idle|dance|wave)\.gif$/,'.png'));
