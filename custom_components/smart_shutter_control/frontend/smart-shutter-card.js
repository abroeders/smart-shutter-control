var ft=globalThis,gt=ft.ShadowRoot&&(ft.ShadyCSS===void 0||ft.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,Mt=Symbol(),Qt=new WeakMap,Q=class{constructor(t,e,n){if(this._$cssResult$=!0,n!==Mt)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e}get styleSheet(){let t=this.o,e=this.t;if(gt&&t===void 0){let n=e!==void 0&&e.length===1;n&&(t=Qt.get(e)),t===void 0&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),n&&Qt.set(e,t))}return t}toString(){return this.cssText}},te=s=>new Q(typeof s=="string"?s:s+"",void 0,Mt),T=(s,...t)=>{let e=s.length===1?s[0]:t.reduce((n,i,r)=>n+(o=>{if(o._$cssResult$===!0)return o.cssText;if(typeof o=="number")return o;throw Error("Value passed to 'css' function must be a 'css' function result: "+o+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(i)+s[r+1],s[0]);return new Q(e,s,Mt)},ee=(s,t)=>{if(gt)s.adoptedStyleSheets=t.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet);else for(let e of t){let n=document.createElement("style"),i=ft.litNonce;i!==void 0&&n.setAttribute("nonce",i),n.textContent=e.cssText,s.appendChild(n)}},Et=gt?s=>s:s=>s instanceof CSSStyleSheet?(t=>{let e="";for(let n of t.cssRules)e+=n.cssText;return te(e)})(s):s;var{is:De,defineProperty:ze,getOwnPropertyDescriptor:Ie,getOwnPropertyNames:Ve,getOwnPropertySymbols:Ge,getPrototypeOf:Be}=Object,$t=globalThis,se=$t.trustedTypes,Fe=se?se.emptyScript:"",je=$t.reactiveElementPolyfillSupport,tt=(s,t)=>s,Ct={toAttribute(s,t){switch(t){case Boolean:s=s?Fe:null;break;case Object:case Array:s=s==null?s:JSON.stringify(s)}return s},fromAttribute(s,t){let e=s;switch(t){case Boolean:e=s!==null;break;case Number:e=s===null?null:Number(s);break;case Object:case Array:try{e=JSON.parse(s)}catch{e=null}}return e}},ie=(s,t)=>!De(s,t),ne={attribute:!0,type:String,converter:Ct,reflect:!1,useDefault:!1,hasChanged:ie};Symbol.metadata??=Symbol("metadata"),$t.litPropertyMetadata??=new WeakMap;var E=class extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??=[]).push(t)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,e=ne){if(e.state&&(e.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(t)&&((e=Object.create(e)).wrapped=!0),this.elementProperties.set(t,e),!e.noAccessor){let n=Symbol(),i=this.getPropertyDescriptor(t,n,e);i!==void 0&&ze(this.prototype,t,i)}}static getPropertyDescriptor(t,e,n){let{get:i,set:r}=Ie(this.prototype,t)??{get(){return this[e]},set(o){this[e]=o}};return{get:i,set(o){let a=i?.call(this);r?.call(this,o),this.requestUpdate(t,a,n)},configurable:!0,enumerable:!0}}static getPropertyOptions(t){return this.elementProperties.get(t)??ne}static _$Ei(){if(this.hasOwnProperty(tt("elementProperties")))return;let t=Be(this);t.finalize(),t.l!==void 0&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties)}static finalize(){if(this.hasOwnProperty(tt("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(tt("properties"))){let e=this.properties,n=[...Ve(e),...Ge(e)];for(let i of n)this.createProperty(i,e[i])}let t=this[Symbol.metadata];if(t!==null){let e=litPropertyMetadata.get(t);if(e!==void 0)for(let[n,i]of e)this.elementProperties.set(n,i)}this._$Eh=new Map;for(let[e,n]of this.elementProperties){let i=this._$Eu(e,n);i!==void 0&&this._$Eh.set(i,e)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(t){let e=[];if(Array.isArray(t)){let n=new Set(t.flat(1/0).reverse());for(let i of n)e.unshift(Et(i))}else t!==void 0&&e.push(Et(t));return e}static _$Eu(t,e){let n=e.attribute;return n===!1?void 0:typeof n=="string"?n:typeof t=="string"?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(t=>this.enableUpdating=t),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(t=>t(this))}addController(t){(this._$EO??=new Set).add(t),this.renderRoot!==void 0&&this.isConnected&&t.hostConnected?.()}removeController(t){this._$EO?.delete(t)}_$E_(){let t=new Map,e=this.constructor.elementProperties;for(let n of e.keys())this.hasOwnProperty(n)&&(t.set(n,this[n]),delete this[n]);t.size>0&&(this._$Ep=t)}createRenderRoot(){let t=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return ee(t,this.constructor.elementStyles),t}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(t=>t.hostConnected?.())}enableUpdating(t){}disconnectedCallback(){this._$EO?.forEach(t=>t.hostDisconnected?.())}attributeChangedCallback(t,e,n){this._$AK(t,n)}_$ET(t,e){let n=this.constructor.elementProperties.get(t),i=this.constructor._$Eu(t,n);if(i!==void 0&&n.reflect===!0){let r=(n.converter?.toAttribute!==void 0?n.converter:Ct).toAttribute(e,n.type);this._$Em=t,r==null?this.removeAttribute(i):this.setAttribute(i,r),this._$Em=null}}_$AK(t,e){let n=this.constructor,i=n._$Eh.get(t);if(i!==void 0&&this._$Em!==i){let r=n.getPropertyOptions(i),o=typeof r.converter=="function"?{fromAttribute:r.converter}:r.converter?.fromAttribute!==void 0?r.converter:Ct;this._$Em=i;let a=o.fromAttribute(e,r.type);this[i]=a??this._$Ej?.get(i)??a,this._$Em=null}}requestUpdate(t,e,n,i=!1,r){if(t!==void 0){let o=this.constructor;if(i===!1&&(r=this[t]),n??=o.getPropertyOptions(t),!((n.hasChanged??ie)(r,e)||n.useDefault&&n.reflect&&r===this._$Ej?.get(t)&&!this.hasAttribute(o._$Eu(t,n))))return;this.C(t,e,n)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(t,e,{useDefault:n,reflect:i,wrapped:r},o){n&&!(this._$Ej??=new Map).has(t)&&(this._$Ej.set(t,o??e??this[t]),r!==!0||o!==void 0)||(this._$AL.has(t)||(this.hasUpdated||n||(e=void 0),this._$AL.set(t,e)),i===!0&&this._$Em!==t&&(this._$Eq??=new Set).add(t))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(e){Promise.reject(e)}let t=this.scheduleUpdate();return t!=null&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[i,r]of this._$Ep)this[i]=r;this._$Ep=void 0}let n=this.constructor.elementProperties;if(n.size>0)for(let[i,r]of n){let{wrapped:o}=r,a=this[i];o!==!0||this._$AL.has(i)||a===void 0||this.C(i,void 0,r,a)}}let t=!1,e=this._$AL;try{t=this.shouldUpdate(e),t?(this.willUpdate(e),this._$EO?.forEach(n=>n.hostUpdate?.()),this.update(e)):this._$EM()}catch(n){throw t=!1,this._$EM(),n}t&&this._$AE(e)}willUpdate(t){}_$AE(t){this._$EO?.forEach(e=>e.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(t)),this.updated(t)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return!0}update(t){this._$Eq&&=this._$Eq.forEach(e=>this._$ET(e,this[e])),this._$EM()}updated(t){}firstUpdated(t){}};E.elementStyles=[],E.shadowRootOptions={mode:"open"},E[tt("elementProperties")]=new Map,E[tt("finalized")]=new Map,je?.({ReactiveElement:E}),($t.reactiveElementVersions??=[]).push("2.1.2");var Ht=globalThis,re=s=>s,yt=Ht.trustedTypes,oe=yt?yt.createPolicy("lit-html",{createHTML:s=>s}):void 0,pe="$lit$",k=`lit$${Math.random().toFixed(9).slice(2)}$`,de="?"+k,Ye=`<${de}>`,H=document,st=()=>H.createComment(""),nt=s=>s===null||typeof s!="object"&&typeof s!="function",Nt=Array.isArray,We=s=>Nt(s)||typeof s?.[Symbol.iterator]=="function",kt=`[ 	
\f\r]`,et=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,ae=/-->/g,le=/>/g,L=RegExp(`>|${kt}(?:([^\\s"'>=/]+)(${kt}*=${kt}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),ce=/'/g,he=/"/g,me=/^(?:script|style|textarea|title)$/i,Ut=s=>(t,...e)=>({_$litType$:s,strings:t,values:e}),_=Ut(1),d=Ut(2),ks=Ut(3),N=Symbol.for("lit-noChange"),$=Symbol.for("lit-nothing"),ue=new WeakMap,O=H.createTreeWalker(H,129);function fe(s,t){if(!Nt(s)||!s.hasOwnProperty("raw"))throw Error("invalid template strings array");return oe!==void 0?oe.createHTML(t):t}var qe=(s,t)=>{let e=s.length-1,n=[],i,r=t===2?"<svg>":t===3?"<math>":"",o=et;for(let a=0;a<e;a++){let l=s[a],c,h,p=-1,g=0;for(;g<l.length&&(o.lastIndex=g,h=o.exec(l),h!==null);)g=o.lastIndex,o===et?h[1]==="!--"?o=ae:h[1]!==void 0?o=le:h[2]!==void 0?(me.test(h[2])&&(i=RegExp("</"+h[2],"g")),o=L):h[3]!==void 0&&(o=L):o===L?h[0]===">"?(o=i??et,p=-1):h[1]===void 0?p=-2:(p=o.lastIndex-h[2].length,c=h[1],o=h[3]===void 0?L:h[3]==='"'?he:ce):o===he||o===ce?o=L:o===ae||o===le?o=et:(o=L,i=void 0);let m=o===L&&s[a+1].startsWith("/>")?" ":"";r+=o===et?l+Ye:p>=0?(n.push(c),l.slice(0,p)+pe+l.slice(p)+k+m):l+k+(p===-2?a:m)}return[fe(s,r+(s[e]||"<?>")+(t===2?"</svg>":t===3?"</math>":"")),n]},it=class s{constructor({strings:t,_$litType$:e},n){let i;this.parts=[];let r=0,o=0,a=t.length-1,l=this.parts,[c,h]=qe(t,e);if(this.el=s.createElement(c,n),O.currentNode=this.el.content,e===2||e===3){let p=this.el.content.firstChild;p.replaceWith(...p.childNodes)}for(;(i=O.nextNode())!==null&&l.length<a;){if(i.nodeType===1){if(i.hasAttributes())for(let p of i.getAttributeNames())if(p.endsWith(pe)){let g=h[o++],m=i.getAttribute(p).split(k),x=/([.?@])?(.*)/.exec(g);l.push({type:1,index:r,name:x[2],strings:m,ctor:x[1]==="."?Rt:x[1]==="?"?Tt:x[1]==="@"?Lt:F}),i.removeAttribute(p)}else p.startsWith(k)&&(l.push({type:6,index:r}),i.removeAttribute(p));if(me.test(i.tagName)){let p=i.textContent.split(k),g=p.length-1;if(g>0){i.textContent=yt?yt.emptyScript:"";for(let m=0;m<g;m++)i.append(p[m],st()),O.nextNode(),l.push({type:2,index:++r});i.append(p[g],st())}}}else if(i.nodeType===8)if(i.data===de)l.push({type:2,index:r});else{let p=-1;for(;(p=i.data.indexOf(k,p+1))!==-1;)l.push({type:7,index:r}),p+=k.length-1}r++}}static createElement(t,e){let n=H.createElement("template");return n.innerHTML=t,n}};function B(s,t,e=s,n){if(t===N)return t;let i=n!==void 0?e._$Co?.[n]:e._$Cl,r=nt(t)?void 0:t._$litDirective$;return i?.constructor!==r&&(i?._$AO?.(!1),r===void 0?i=void 0:(i=new r(s),i._$AT(s,e,n)),n!==void 0?(e._$Co??=[])[n]=i:e._$Cl=i),i!==void 0&&(t=B(s,i._$AS(s,t.values),i,n)),t}var Pt=class{constructor(t,e){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=e}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){let{el:{content:e},parts:n}=this._$AD,i=(t?.creationScope??H).importNode(e,!0);O.currentNode=i;let r=O.nextNode(),o=0,a=0,l=n[0];for(;l!==void 0;){if(o===l.index){let c;l.type===2?c=new rt(r,r.nextSibling,this,t):l.type===1?c=new l.ctor(r,l.name,l.strings,this,t):l.type===6&&(c=new Ot(r,this,t)),this._$AV.push(c),l=n[++a]}o!==l?.index&&(r=O.nextNode(),o++)}return O.currentNode=H,i}p(t){let e=0;for(let n of this._$AV)n!==void 0&&(n.strings!==void 0?(n._$AI(t,n,e),e+=n.strings.length-2):n._$AI(t[e])),e++}},rt=class s{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(t,e,n,i){this.type=2,this._$AH=$,this._$AN=void 0,this._$AA=t,this._$AB=e,this._$AM=n,this.options=i,this._$Cv=i?.isConnected??!0}get parentNode(){let t=this._$AA.parentNode,e=this._$AM;return e!==void 0&&t?.nodeType===11&&(t=e.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,e=this){t=B(this,t,e),nt(t)?t===$||t==null||t===""?(this._$AH!==$&&this._$AR(),this._$AH=$):t!==this._$AH&&t!==N&&this._(t):t._$litType$!==void 0?this.$(t):t.nodeType!==void 0?this.T(t):We(t)?this.k(t):this._(t)}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t))}_(t){this._$AH!==$&&nt(this._$AH)?this._$AA.nextSibling.data=t:this.T(H.createTextNode(t)),this._$AH=t}$(t){let{values:e,_$litType$:n}=t,i=typeof n=="number"?this._$AC(t):(n.el===void 0&&(n.el=it.createElement(fe(n.h,n.h[0]),this.options)),n);if(this._$AH?._$AD===i)this._$AH.p(e);else{let r=new Pt(i,this),o=r.u(this.options);r.p(e),this.T(o),this._$AH=r}}_$AC(t){let e=ue.get(t.strings);return e===void 0&&ue.set(t.strings,e=new it(t)),e}k(t){Nt(this._$AH)||(this._$AH=[],this._$AR());let e=this._$AH,n,i=0;for(let r of t)i===e.length?e.push(n=new s(this.O(st()),this.O(st()),this,this.options)):n=e[i],n._$AI(r),i++;i<e.length&&(this._$AR(n&&n._$AB.nextSibling,i),e.length=i)}_$AR(t=this._$AA.nextSibling,e){for(this._$AP?.(!1,!0,e);t!==this._$AB;){let n=re(t).nextSibling;re(t).remove(),t=n}}setConnected(t){this._$AM===void 0&&(this._$Cv=t,this._$AP?.(t))}},F=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,e,n,i,r){this.type=1,this._$AH=$,this._$AN=void 0,this.element=t,this.name=e,this._$AM=i,this.options=r,n.length>2||n[0]!==""||n[1]!==""?(this._$AH=Array(n.length-1).fill(new String),this.strings=n):this._$AH=$}_$AI(t,e=this,n,i){let r=this.strings,o=!1;if(r===void 0)t=B(this,t,e,0),o=!nt(t)||t!==this._$AH&&t!==N,o&&(this._$AH=t);else{let a=t,l,c;for(t=r[0],l=0;l<r.length-1;l++)c=B(this,a[n+l],e,l),c===N&&(c=this._$AH[l]),o||=!nt(c)||c!==this._$AH[l],c===$?t=$:t!==$&&(t+=(c??"")+r[l+1]),this._$AH[l]=c}o&&!i&&this.j(t)}j(t){t===$?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"")}},Rt=class extends F{constructor(){super(...arguments),this.type=3}j(t){this.element[this.name]=t===$?void 0:t}},Tt=class extends F{constructor(){super(...arguments),this.type=4}j(t){this.element.toggleAttribute(this.name,!!t&&t!==$)}},Lt=class extends F{constructor(t,e,n,i,r){super(t,e,n,i,r),this.type=5}_$AI(t,e=this){if((t=B(this,t,e,0)??$)===N)return;let n=this._$AH,i=t===$&&n!==$||t.capture!==n.capture||t.once!==n.once||t.passive!==n.passive,r=t!==$&&(n===$||i);i&&this.element.removeEventListener(this.name,this,n),r&&this.element.addEventListener(this.name,this,t),this._$AH=t}handleEvent(t){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,t):this._$AH.handleEvent(t)}},Ot=class{constructor(t,e,n){this.element=t,this.type=6,this._$AN=void 0,this._$AM=e,this.options=n}get _$AU(){return this._$AM._$AU}_$AI(t){B(this,t)}};var Ke=Ht.litHtmlPolyfillSupport;Ke?.(it,rt),(Ht.litHtmlVersions??=[]).push("3.3.3");var ge=(s,t,e)=>{let n=e?.renderBefore??t,i=n._$litPart$;if(i===void 0){let r=e?.renderBefore??null;n._$litPart$=i=new rt(t.insertBefore(st(),r),r,void 0,e??{})}return i._$AI(s),i};var Dt=globalThis,A=class extends E{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let t=super.createRenderRoot();return this.renderOptions.renderBefore??=t.firstChild,t}update(t){let e=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=ge(e,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return N}};A._$litElement$=!0,A.finalized=!0,Dt.litElementHydrateSupport?.({LitElement:A});var Ze=Dt.litElementPolyfillSupport;Ze?.({LitElement:A});(Dt.litElementVersions??=[]).push("4.2.2");var ot="smart_shutter_control";function U(s,t){let e={};for(let n of Object.values(s.entities??{}))n.platform===ot&&n.device_id===t&&n.translation_key&&(e[n.translation_key]=n.entity_id);return e}function j(s,t){return"shutter"in U(s,t)}function vt(s,t){let e=s.devices?.[t];return e?.name_by_user||e?.name||t}function zt(s){let t=new Set;for(let e of Object.values(s.entities??{}))e.platform===ot&&e.device_id&&t.add(e.device_id);return[...t].sort((e,n)=>Number(j(s,e))-Number(j(s,n))||vt(s,e).localeCompare(vt(s,n)))}function $e(s,t){return zt(s).filter(e=>s.devices?.[e]?.via_device_id===t&&j(s,e))}function ye(s,t){return s.devices?.[t]?.via_device_id??void 0}var ve={open:"open",closed:"closed",slit:"slit",partly_open:"partly open",automatic:"Automatic",manual_pause:"Manual",off:"Off",storm_chip:"Storm: only open/closed",frost_chip:"Frost: no moves",sleep_in:"Sleep in",sleep_in_all:"Sleep in (all)",next:"Next",then:"then",until:"until",next_phase:"the next phase",resume:"Resume",open_cover:"Open",stop_cover:"Stop",close_cover:"Close",all_shutters:"All shutters",no_device:"Choose a shutter or a base controller of Smart Shutter Control.",not_found:"Device not found",max:"max",position:"Position",device_id:"Device",language:"Language",language_auto:"Integration setting",reason_idle:"No action",reason_off:"Automatic control off",reason_manual:"Manual",reason_calibrating:"Calibrating",reason_sun:"Sun on the window",reason_schedule:"Schedule",reason_sleep_in:"Sleeping in",reason_storm:"Storm",reason_frost:"Frost",reason_heat_limit:"Too warm",reason_cold_limit:"Too cold",reason_winter:"Winter",phase_night:"night",phase_slit:"slit",phase_day:"day",phase_dusk:"dusk"},Xe={open:"open",closed:"dicht",slit:"spleetstand",partly_open:"deels open",automatic:"Automatisch",manual_pause:"Handbediening",off:"Uit",storm_chip:"Storm: alleen open/dicht",frost_chip:"Vorst: geen bewegingen",sleep_in:"Uitslapen",sleep_in_all:"Uitslapen (alle)",next:"Volgende",then:"daarna",until:"tot",next_phase:"de volgende fase",resume:"Hervatten",open_cover:"Open",stop_cover:"Stop",close_cover:"Dicht",all_shutters:"Alle rolluiken",no_device:"Kies een rolluik of een basiscontroller van Smart Shutter Control.",not_found:"Apparaat niet gevonden",max:"max",position:"Stand",device_id:"Apparaat",language:"Taal",language_auto:"Instelling van de integratie",reason_idle:"Geen actie",reason_off:"Automaat uit",reason_manual:"Handbediening",reason_calibrating:"Kalibreren",reason_sun:"Zon op het raam",reason_schedule:"Schema",reason_sleep_in:"Uitslapen",reason_storm:"Storm",reason_frost:"Vorst",reason_heat_limit:"Te warm",reason_cold_limit:"Te koud",reason_winter:"Winter",phase_night:"nacht",phase_slit:"spleet",phase_day:"dag",phase_dusk:"schemer"};function at(s){let t=s?.toLowerCase().startsWith("nl")?Xe:ve;return e=>t[e]??ve[e]??e}var _e=["en","nl"];var Je=Date.UTC(2e3,0,1,12,0,0),Qe=29.530588853,ts=Date.UTC(2e3,0,6,18,14,0),C=Math.PI/180,lt=s=>(s%360+360)%360;function we(s){return((s.getTime()-ts)/864e5/Qe%1+1)%1}function xe(s,t,e){let n=(s.getTime()-Je)/864e5,i=lt(218.316+13.176396*n),r=lt(134.963+13.064993*n),o=lt(93.272+13.22935*n),a=(i+6.289*Math.sin(r*C))*C,l=5.128*Math.sin(o*C)*C,c=23.4397*C,h=Math.sin(c),p=Math.cos(c),g=Math.sin(l),m=Math.cos(l),x=m*Math.cos(a),z=m*Math.sin(a)*p-g*h,Z=m*Math.sin(a)*h+g*p,Xt=Math.atan2(z,x),X=Math.asin(Z),w=t*C,P=lt(280.16+360.9856235*n+e)*C-Xt,dt=Math.asin(Math.sin(w)*Math.sin(X)+Math.cos(w)*Math.cos(X)*Math.cos(P)),J=Math.atan2(Math.sin(P),Math.cos(P)*Math.sin(w)-Math.tan(X)*Math.cos(w));return{azimuth:lt(J/C+180),elevation:dt/C}}var es=Date.UTC(2e3,0,1,12,0,0),D=Math.PI/180,_t=s=>(s%360+360)%360;function be(s,t,e){let n=(s.getTime()-es)/864e5,i=_t(357.529+.98560028*n)*D,o=(_t(280.459+.98564736*n)+1.915*Math.sin(i)+.02*Math.sin(2*i))*D,a=(23.439-36e-8*n)*D,l=Math.atan2(Math.cos(a)*Math.sin(o),Math.cos(o)),c=Math.asin(Math.sin(a)*Math.sin(o)),h=t*D,g=_t(280.16+360.9856235*n+e)*D-l,m=Math.asin(Math.sin(h)*Math.sin(c)+Math.cos(h)*Math.cos(c)*Math.cos(g)),x=Math.atan2(Math.sin(g),Math.cos(g)*Math.sin(h)-Math.tan(c)*Math.cos(h));return{azimuth:_t(x/D+180),elevation:m/D}}var Ae=.72,ss=.16,Y=70,ns=["rainy","lightning-rainy"],is=["rainy","pouring","snowy","snowy-rainy","lightning","lightning-rainy","hail","exceptional"],rs={sunny:.05,"clear-night":.05,partlycloudy:.4,windy:.3,"windy-variant":.5,cloudy:.9,fog:.9},Ee=.8,Se=.9,os=6;function as(s){return s===null?"day":s<-6?"night":s<0?"twilight":"day"}function Me(s,t,e){if(s===null||t===null||t<0)return null;let n=It(s,e);if(Math.abs(n)>Y)return null;let i=.5+n/(2*Y);return{x:Math.min(.94,Math.max(.06,i)),y:Ce(t)}}function It(s,t){return t===null?0:(s-t+540)%360-180}function Ce(s){return Ae-Math.min(s,60)/60*(Ae-ss)}function ls(s,t,e){let n=t!==null?t/100:is.includes(s??"")?1:rs[s??""]??.3,i=e===null?n:(n+3*(1-e))/4;return Math.round(Math.max(0,Math.min(1,i))*100)/100}function cs(s,t){if(s===null)return t<.1?null:{opacity:t,offset:0};if(s>=Se)return null;let e=Math.max(0,s)/Se;return{opacity:Math.round(.9*(1-e)*100)/100,offset:Math.round(e*2.5*100)/100}}function hs(s,t,e,n){let i=new Date(s);i.setHours(0,0,0,0);let r=[],o=[];for(let a=0;a<=24*60;a+=10){let l=be(new Date(i.getTime()+a*6e4),t,e),c=It(l.azimuth,n);l.elevation>=0&&Math.abs(c)<=Y?o.push({x:.5+c/(2*Y),y:Ce(l.elevation)}):o.length&&(r.push(o),o=[])}return o.length&&r.push(o),r.filter(a=>a.length>1)}function us(s,t,e,n){if(s===null||t===null||t<-6)return null;let i=It(s,e),r=Math.max(0,Math.abs(i)-Y)/80;if(r>=1)return null;let o=1-Math.min(Math.max(t,0),40)/40,a=Math.round(.7*o*(1-r)*(1-.7*n)*100)/100;return a<.05?null:{x:Math.max(-.3,Math.min(1.3,.5+i/(2*Y))),strength:a}}function ps(s){let t=s>>>0;return()=>(t=Math.imul(t,1664525)+1013904223>>>0,t/4294967296)}function ds(s){let t=s===null?18:Math.round((s%360+360)%360/10)%36,e=ps(7919*(t+1)),n=[0,0,0,0].map(()=>Math.round((e()*.12-.07)*1e3)/1e3),i=2+Math.floor(e()*2),r=Array.from({length:i},(o,a)=>({x:Math.round((a+.2+e()*.6)/i*100)/100,height:Math.round((.12+e()*.11)*100)/100}));return{hill:n,trees:r}}function ms(s,t){let e=["winter","spring","summer","autumn"],n=Math.floor((s.getMonth()+1)%12/3);return e[t<0?(n+2)%4:n]}function fs(s,t,e){let n=Math.max(s??0,(t??0)*.7),i=n<10?0:n<40?1+(n-10)/10:n<60?4+(n-40)/5:8+Math.min(4,(n-60)/10);return e&&(i=Math.max(i,10)+3),Math.round(i*10)/10}function gs(s,t,e){let n=e>=Ee;return s==="night"?n?["#1b1f2a","#2e3440"]:["#0d1442","#283593"]:s==="twilight"?n?["#4a4f63","#7a6f80"]:["#3949ab","#ff8a65"]:n?["#78909c","#b0bec5"]:e>=.55?["#6f9fc8","#cfd8dc"]:t!==null&&t<12?["#64b5f6","#ffe0b2"]:["#42a5f5","#bbdefb"]}function Vt(s){let t=s.weather??"",e=as(s.sunElevation),n=e==="day"?s.sunFactor:null,i=ls(s.weather,s.cloudCoverage,n),r=i>=Ee,o=t==="pouring"?"pouring":t==="snowy-rainy"?"sleet":t==="snowy"?"snow":ns.includes(t)?"rain":"none",a=e==="day"?Me(s.sunAzimuth,s.sunElevation,s.windowAzimuth):null,l=null;if(e!=="day"&&!r){let m=we(s.now),x=xe(s.now,s.latitude,s.longitude),z=Me(x.azimuth,x.elevation,s.windowAzimuth),Z=m>.03&&m<.97;z&&Z&&(l={...z,phase:m})}let c=1-i,h=r?0:(e==="night"?1:e==="twilight"?Math.max(0,Math.min(1,-(s.sunElevation??0)/6)):0)*Math.min(1,c*1.5),p=fs(s.wind,s.gust,s.storm),g=e==="night"?.65:e==="twilight"?.35:r?.15:0;return{light:e,sky:gs(e,s.sunElevation,i),stars:h,sun:a,glow:a?Math.round(.25*(n??c)*100)/100:0,veil:a?cs(n,i):null,path:e==="night"?[]:hs(s.now,s.latitude,s.longitude,s.windowAzimuth),moon:l,cover:i,cloudCount:r?0:Math.round(i*os),overcast:r,sideLight:e==="night"?null:us(s.sunAzimuth,s.sunElevation,s.windowAzimuth,i),landscape:ds(s.windowAzimuth),precipitation:o,fog:t==="fog",lightning:t==="lightning"||t==="lightning-rainy",season:ms(s.now,s.latitude),snowGround:o==="snow"||o==="sleet",sway:p,slant:Math.min(30,p*2.5),dim:g}}var S=s=>s==null||s===""||isNaN(Number(s))?null:Number(s);function Gt(s,t){let e=U(s,t),n=m=>e[m]?s.states[e[m]]:void 0,i=ye(s,t),r=i?U(s,i):{},o=m=>m?s.states[m]?.state==="on":!1,a=n("shutter"),l=n("reason"),c=n("next_action"),h=[];if(c&&!["unknown","unavailable"].includes(c.state)&&c.attributes.phase){h.push({at:c.state,phase:c.attributes.phase,position:c.attributes.position});for(let m of c.attributes.following??[])h.push({at:m.at,phase:m.phase,position:m.position})}let p=n("manual_pause"),g=a?.state;return{deviceId:t,name:vt(s,t),entities:e,position:S(a?.attributes.current_position),moving:g==="opening"||g==="closing"?g:null,closed:g==="closed",stand:n("stand")?.state??null,reason:l?.state??null,target:S(l?.attributes.target_position),max:S(l?.attributes.max_position)??100,phase:n("phase")?.state??null,automatic:n("automatic")?.state!=="off",sleepIn:o(e.sleep_in),paused:o(e.manual_pause),pausedUntil:p?.attributes.until??null,next:h,storm:o(r.storm),frost:o(r.frost),language:l?.attributes.language??null,outside:$s(s,r,e)}}function $s(s,t,e,n=new Date){let i=c=>c?s.states[c]?.attributes??{}:{},r=i(t.sun_factor),o=t.storm?s.states[t.storm]:void 0,a=i(e.sun_on_window),l=S(a.sun_factor)??S(t.sun_factor?s.states[t.sun_factor]?.state:void 0);return{now:n,latitude:s.config?.latitude??52,longitude:s.config?.longitude??5,sunAzimuth:S(r.sun_azimuth),sunElevation:S(r.sun_elevation),windowAzimuth:S(a.window_azimuth),weather:r.weather??null,cloudCoverage:S(r.cloud_coverage),sunFactor:l===null?null:Math.max(0,Math.min(1,l/100)),wind:S(o?.attributes.wind),gust:S(o?.attributes.gust),storm:o?.state==="on"}}function Bt(s,t,e){return t||e?.language||s.locale?.language||s.language||"en"}function ke(s,t,e){let n=new Date(s);if(isNaN(n.getTime()))return"";try{return new Intl.DateTimeFormat(e,{hour:"2-digit",minute:"2-digit",hour12:!1,timeZone:t.config?.time_zone}).format(n)}catch{return new Intl.DateTimeFormat(e,{hour:"2-digit",minute:"2-digit",hour12:!1}).format(n)}}function wt(s,t){return s===null?"\u2013":s==="slit"?t("slit"):s<=0?t("closed"):s>=100?t("open"):`${s}\xA0%`}function Ft(s,t,e){let n=s.stand&&!["unknown","unavailable"].includes(s.stand)?t(s.stand):"",i=s.reason?t(`reason_${s.reason}`):"",r="";if(s.paused){let c=s.pausedUntil==="next phase"||!s.pausedUntil?t("next_phase"):e(s.pausedUntil);r=`${t("until")} ${c}`}else s.target!==null&&(r=[s.position!==null&&Math.abs(s.target-s.position)>1?`\u2192 ${wt(s.target,t)}`:"",s.phase?t(`phase_${s.phase}`):""].filter(Boolean).join(" \xB7 "));let o=c=>[e(c.at),c.phase==="dusk"?t("phase_dusk"):"",wt(c.position,t)].filter(Boolean).join(" "),[a,l]=s.next;return{stand:n,reason:i,detail:r,next:a?`${t("next")}: ${o(a)}`:null,then:l?`${t("then")} ${o(l)}`:null,chip:s.automatic?s.paused?"manual_pause":"automatic":"off"}}var ct="smart-shutter-card",jt="smart-shutter-card-editor",ys=360,vs={up:"M13,20H11V8L5.5,13.5L4.08,12.08L12,4.16L19.92,12.08L18.5,13.5L13,8V20Z",stop:"M18,18H6V6H18V18Z",down:"M11,4H13V16L18.5,10.5L19.92,11.92L12,19.84L4.08,11.92L5.5,10.5L11,16V4Z"},W=class extends A{constructor(){super(...arguments);this._narrow=!1}static getConfigElement(){return document.createElement(jt)}static getStubConfig(e){return{type:`custom:${ct}`,device_id:zt(e)[0]}}setConfig(e){if(!e)throw new Error("Invalid configuration");this._config={...e}}getCardSize(){return 6}getGridOptions(){return{columns:!!(this.hass&&this._config?.device_id&&!j(this.hass,this._config.device_id))?"full":12,min_columns:6,rows:"auto"}}connectedCallback(){super.connectedCallback(),typeof ResizeObserver<"u"&&(this.observer=new ResizeObserver(e=>{let n=e[0]?.contentRect.width??0;n&&(this._narrow=n<ys)}),this.observer.observe(this))}disconnectedCallback(){super.disconnectedCallback(),this.observer?.disconnect()}call(e,n,i,r={}){!this.hass||!i||this.hass.callService(e,n,{entity_id:i,...r})}toggle(e,n){this.call(e?.split(".")[0]??"switch",n?"turn_off":"turn_on",e)}moreInfo(e){e&&this.dispatchEvent(new CustomEvent("hass-more-info",{detail:{entityId:e},bubbles:!0,composed:!0}))}render(){let e=this.hass,n=this._config?.device_id;if(!e||!this._config)return $;let i=at(Bt(e,this._config.language));return n?!e.devices?.[n]&&!Object.keys(U(e,n)).length?_`<ha-card><div class="message">${i("not_found")}: ${n}</div></ha-card>`:j(e,n)?this.renderShutter(e,n):this.renderOverview(e,n):_`<ha-card><div class="message">${i("no_device")}</div></ha-card>`}texts(e,n){let i=Bt(e,this._config?.language,n);return{t:at(i),time:r=>ke(r,e,i),lang:i}}buttons(e,n,i=!1){let r=e.entities.shutter,o=(a,l,c)=>_`<button class="round ${i?"small":""}" title=${c} aria-label=${c} @click=${h=>{h.stopPropagation(),this.call("cover",l,r)}}>
        <svg viewBox="0 0 24 24"><path d=${vs[a]}></path></svg>
      </button>`;return _`${o("up","open_cover",n("open_cover"))}${o("stop","stop_cover",n("stop_cover"))}${o("down","close_cover",n("close_cover"))}`}switch(e,n,i,r){return n?_`<button class="switch ${r}" role="switch" aria-checked=${i?"true":"false"} @click=${()=>this.toggle(n,i)}>
      <span class="track ${i?"on":""}"><span class="knob"></span></span>${e}
    </button>`:$}warnings(e,n,i){return _`${e?_`<span class="chip warn storm">⚠ ${i("storm_chip")}</span>`:$}${n?_`<span class="chip warn frost">❄ ${i("frost_chip")}</span>`:$}`}renderShutter(e,n){let i=Gt(e,n),{t:r,time:o}=this.texts(e,i),a=Ft(i,r,o),l=!!e.themes?.darkMode;return _`<ha-card class=${this._narrow?"narrow":""}>
      <div class="head">
        <div class="name">${i.name}</div>
        <div class="chips"><span class="chip ${a.chip}">${r(a.chip)}</span>${this.warnings(i.storm,i.frost,r)}</div>
      </div>
      <div class="body">
        <ssc-drawing
          ?dark=${l}
          .position=${i.position}
          .max=${i.max}
          .moving=${i.moving}
          .gaps=${!i.closed}
          .scene=${Vt(i.outside)}
          .animated=${!0}
          .storm=${i.storm}
          .interactive=${!!i.entities.shutter}
          .label=${`${i.name}: ${r("position")}`}
          .maxLabel=${r("max")}
          @set-position=${c=>this.call("cover","set_cover_position",i.entities.shutter,{position:c.detail.position})}
        ></ssc-drawing>
        <div class="buttons">${this.buttons(i,r)}</div>
        <div class="status">
          <div class="big">${i.position===null?"\u2013":`${i.position}\xA0%`}</div>
          <div class="sub">${a.stand}</div>
          <div class="line reason">${a.reason}</div>
          <div class="sub">${a.detail}</div>
          ${a.next?_`<div class="line next">${a.next}</div>`:$}
          ${a.then?_`<div class="sub then">${a.then}</div>`:$}
        </div>
      </div>
      <div class="switches">
        ${this.switch(r("automatic"),i.entities.automatic,i.automatic,"automatic")}
        ${this.switch(r("sleep_in"),i.entities.sleep_in,i.sleepIn,"sleep-in")}
        ${i.paused&&i.entities.resume?_`<button class="text resume" @click=${()=>this.call("button","press",i.entities.resume)}>${r("resume")}</button>`:$}
      </div>
    </ha-card>`}renderOverview(e,n){let i=$e(e,n).map(h=>Gt(e,h)),{t:r,time:o}=this.texts(e,i[0]??null),a=U(e,n),l=h=>a[h]?e.states[a[h]]?.state==="on":!1,c=!!e.themes?.darkMode;return _`<ha-card class="overview">
      <div class="head">
        <div class="name">${r("all_shutters")}</div>
        <div class="chips">${this.warnings(l("storm"),l("frost"),r)}</div>
      </div>
      <div class="grid">
        ${i.map(h=>{let p=Ft(h,r,o),g=[h.position===null?"\u2013":wt(h.position,r),p.reason].filter(Boolean).join(" \xB7 ");return _`<div class="tile" @click=${()=>this.moreInfo(h.entities.shutter)}>
            <ssc-drawing compact ?dark=${c} .position=${h.position} .max=${h.max} .moving=${h.moving} .gaps=${!h.closed} .scene=${Vt(h.outside)}></ssc-drawing>
            <div class="tile-text">
              <div class="tile-name">${h.name}</div>
              <div class="sub ${p.chip==="manual_pause"?"manual":""}">${g}${p.chip==="manual_pause"?` \xB7 ${p.detail}`:""}</div>
              <div class="tile-buttons">${this.buttons(h,r,!0)}</div>
            </div>
          </div>`})}
      </div>
      <div class="switches">${this.switch(r("sleep_in_all"),a.sleep_in_all,l("sleep_in_all"),"sleep-in-all")}</div>
    </ha-card>`}};W.properties={hass:{attribute:!1},_config:{state:!0},_narrow:{state:!0}},W.styles=T`
    :host {
      display: block;
    }
    ha-card {
      padding: 16px;
      box-sizing: border-box;
      color: var(--primary-text-color);
    }
    .message {
      color: var(--secondary-text-color);
    }
    .head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      flex-wrap: wrap;
      margin-bottom: 12px;
    }
    .name {
      font-size: 1.15em;
      font-weight: 600;
    }
    .chips {
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
    }
    .chip {
      border-radius: 12px;
      padding: 2px 10px;
      font-size: 0.85em;
      background: color-mix(in srgb, var(--success-color, #43a047) 15%, transparent);
      color: var(--success-color, #2e7d32);
    }
    .chip.manual_pause,
    .chip.warn {
      background: color-mix(in srgb, var(--warning-color, #ef6c00) 15%, transparent);
      color: var(--warning-color, #e65100);
    }
    .chip.off {
      background: var(--secondary-background-color, #eee);
      color: var(--secondary-text-color);
    }
    .body {
      display: grid;
      grid-template-columns: minmax(140px, 240px) auto 1fr;
      gap: 12px;
      align-items: center;
    }
    .narrow .body {
      grid-template-columns: 1fr auto;
    }
    .narrow .status {
      grid-column: 1 / -1;
    }
    .buttons {
      display: flex;
      flex-direction: column;
      gap: 14px;
    }
    button {
      font: inherit;
      color: inherit;
      cursor: pointer;
    }
    .round {
      width: 44px;
      height: 44px;
      border-radius: 50%;
      border: none;
      background: var(--secondary-background-color, #eceff1);
      display: grid;
      place-items: center;
      padding: 0;
    }
    .round.small {
      width: 32px;
      height: 32px;
    }
    .round svg {
      width: 22px;
      height: 22px;
      fill: var(--primary-text-color);
    }
    .round.small svg {
      width: 18px;
      height: 18px;
    }
    .round:focus-visible,
    .switch:focus-visible {
      outline: 2px solid var(--primary-color);
    }
    .status .big {
      font-size: 2em;
      font-weight: 700;
      color: var(--primary-color);
      line-height: 1.1;
    }
    .status .line {
      margin-top: 12px;
    }
    .sub {
      color: var(--secondary-text-color);
      font-size: 0.9em;
    }
    .sub.manual {
      color: var(--warning-color, #e65100);
    }
    .switches {
      display: flex;
      flex-wrap: wrap;
      gap: 8px 20px;
      margin-top: 14px;
      align-items: center;
    }
    .switch {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      border: none;
      background: none;
      padding: 0;
    }
    .track {
      width: 34px;
      height: 18px;
      border-radius: 9px;
      background: var(--disabled-color, #bdbdbd);
      position: relative;
      transition: background 0.2s;
    }
    .track.on {
      background: var(--switch-checked-color, var(--primary-color));
    }
    .knob {
      position: absolute;
      top: 2px;
      left: 2px;
      width: 14px;
      height: 14px;
      border-radius: 50%;
      background: #fff;
      transition: left 0.2s;
    }
    .track.on .knob {
      left: 18px;
    }
    .text {
      border: 1px solid var(--primary-color);
      border-radius: 16px;
      background: none;
      color: var(--primary-color);
      padding: 4px 12px;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
      gap: 12px;
    }
    .tile {
      display: grid;
      grid-template-columns: 72px 1fr;
      gap: 10px;
      align-items: center;
      cursor: pointer;
    }
    .tile-name {
      font-weight: 600;
    }
    .tile-buttons {
      display: flex;
      gap: 6px;
      margin-top: 6px;
    }
  `;var Yt=(s,t,e)=>Math.min(e,Math.max(t,s));function ht(s,t){return t.top+(1-Yt(s,0,100)/100)*(t.bottom-t.top)}function Pe(s,t){return Math.round(Yt((t.bottom-s)/(t.bottom-t.top),0,1)*100)}function Wt(s,t){let e=Yt(Math.round(s),0,100);return t?e>=50?100:0:e}function Re(s){let t=s>>>0;return()=>(t=Math.imul(t,1664525)+1013904223>>>0,t/4294967296)}var Te=T`
  .twinkle { transform-box: view-box; transform-origin: center; animation: ssc-twinkle 4s ease-in-out infinite alternate; }
  .drift { transform-box: view-box; animation: ssc-drift 36s ease-in-out infinite alternate; }
  .sway { transform-box: view-box; animation: ssc-sway var(--sway-speed, 2.5s) ease-in-out infinite alternate; }
  .fall { animation: ssc-fall var(--fall-speed, 3s) linear infinite; }
  .flash { animation: ssc-flash 6s linear infinite; }
  @keyframes ssc-twinkle {
    0%, 70% { opacity: 0.45; }
    100% { opacity: 1; }
  }
  @keyframes ssc-drift {
    from { transform: translateX(-6px); }
    to { transform: translateX(6px); }
  }
  @keyframes ssc-sway {
    from { transform: rotate(calc(var(--sway) * -1)); }
    to { transform: rotate(var(--sway)); }
  }
  @keyframes ssc-fall {
    from { transform: translateY(var(--fall-from, -206px)); }
    to { transform: translateY(var(--fall-to, 206px)); }
  }
  @keyframes ssc-flash {
    0%, 92%, 100% { opacity: 0; }
    93%, 95% { opacity: 1; }
    94%, 96% { opacity: 0.15; }
  }
  @media (prefers-reduced-motion: reduce) {
    .twinkle, .drift, .sway, .fall, .flash { animation: none !important; }
  }
`;function _s(s,t,e,n){if(n<.03||n>.97)return"";if(n>.97-1e-4||Math.abs(n-.5)<1e-4)return d`<circle class="moon-disc" cx=${s} cy=${t} r=${e} fill="#fff8e1"></circle>`;let i=n<.5,r=e*Math.abs(Math.cos(2*Math.PI*n)),o=i?1:0,a=i?1:0,l=`M ${s} ${t-e} A ${e} ${e} 0 0 ${o} ${s} ${t+e} A ${r} ${e} 0 0 ${a} ${s} ${t-e} Z`;return d`<path class="moon-disc" d=${l} fill="#fff8e1"></path>`}function qt(s,t,e,n,i,r=.95){return d`<g class=${i} opacity=${r}>
    <ellipse cx=${s-8*e} cy=${t} rx=${10*e} ry=${5*e} fill=${n}></ellipse>
    <ellipse cx=${s+2*e} cy=${t-4*e} rx=${12*e} ry=${8*e} fill=${n}></ellipse>
    <ellipse cx=${s+14*e} cy=${t} rx=${11*e} ry=${5*e} fill=${n}></ellipse>
  </g>`}var ws=[{x:.18,y:.18},{x:.68,y:.28},{x:.45,y:.12},{x:.86,y:.15},{x:.3,y:.34},{x:.06,y:.3}];function Le(s,t,e){let n="ssc-view-sky",i="ssc-view-side",r="ssc-view-precip",o=t.y+.72*t.h,a=u=>({x:t.x+u.x*t.w,y:t.y+u.y*t.h}),l=Re(20261124),c=[];for(let u=0;u<30;u++){let f=t.x+l()*t.w,y=t.y+l()*t.h*.55,b=.6+l()*.8,v=e&&u%7===0,R=`${u%5*.35}s`;c.push(d`<circle class=${v?"star twinkle":"star"} cx=${f} cy=${y} r=${b} fill="#fff" style=${v?`animation-delay:${R};opacity:${s.stars}`:`opacity:${s.stars}`}></circle>`)}let h=s.snowGround?"#eceff1":s.season==="spring"?"#8bc34a":s.season==="summer"?"#7cb342":s.season==="autumn"?"#9e9d24":"#a1887f",[p,g,m,x]=s.landscape.hill.map(u=>o+u*t.h),z=`M ${t.x} ${o} C ${t.x+.22*t.w} ${p}, ${t.x+.42*t.w} ${g}, ${t.x+.58*t.w} ${m} S ${t.x+.82*t.w} ${x}, ${t.x+t.w} ${o-.02*t.h} L ${t.x+t.w} ${t.y+t.h} L ${t.x} ${t.y+t.h} Z`,Z=u=>o+(u<.5?s.landscape.hill[0]:s.landscape.hill[2])*t.h*.5+.01*t.h,X=s.landscape.trees.map(u=>({fx:u.x,base:Z(u.x),height:u.height*t.h})).map(u=>{let f=t.x+u.fx*t.w,y=u.base-u.height,b=Math.max(2.5,t.w*.018),v=Math.max(5,u.height*.23),R=e&&s.sway>0?" sway":"",I=!e&&s.sway>0?` rotate(${s.sway/2} ${f} ${u.base})`:"",V=`transform-origin:${f}px ${u.base}px;--sway:${s.sway}deg;--sway-speed:${s.sway>8?"1.2s":"2.5s"}`,G;if(s.season==="winter"){let St=[-1,-.35,.35,1].map(mt=>d`<line class="branch" x1=${f} y1=${u.base-u.height*.58} x2=${f+mt*v*1.15} y2=${u.base-u.height*(.68+Math.abs(mt)*.15)} stroke="#6d4c41" stroke-width="1.2"></line>`);G=d`<g class="winter">${St}${s.snowGround?d`<line x1=${f-v} y1=${y+v*.45} x2=${f-v*.35} y2=${y+v*.25} stroke="#eceff1" stroke-width="1.8"></line>`:""}</g>`}else{let St=s.season==="spring"?["#9ccc65","#9ccc65","#9ccc65","#9ccc65"]:s.season==="summer"?["#388e3c","#43a047","#388e3c","#43a047"]:["#ef6c00","#d84315","#f9a825","#ef6c00"],mt=[[f-v*.45,y+v*.45],[f+v*.45,y+v*.45],[f,y],[f,y+v*.72]];G=d`<g class="foliage">${mt.map(([He,Ne],Ue)=>d`<circle class="crown" cx=${He} cy=${Ne} r=${v} fill=${St[Ue]}></circle>`)}${s.season==="spring"?d`<circle cx=${f-v*.9} cy=${y+v*.1} r="1.3" fill="#f8bbd0"></circle><circle cx=${f+v*.8} cy=${y+v*.7} r="1.3" fill="#f8bbd0"></circle>`:""}</g>`}return d`<g class=${`tree${R}`} style=${V} transform=${I||void 0}>
      <rect x=${f-b/2} y=${u.base-u.height*.58} width=${b} height=${u.height*.58} rx="1" fill="#6d4c41"></rect>
      ${G}
    </g>`}),w=Re(481516),pt=s.precipitation==="pouring"?45:25,P=[];if(s.precipitation==="rain"||s.precipitation==="pouring")for(let u=0;u<pt;u++){let f=t.x+w()*t.w,y=t.y+w()*t.h,b=4+w()*3,v=s.slant*.12,R=e?"fall":"",I=`${.7+w()*.4}s`,V=`-${w()*1.1}s`;P.push(d`<line class=${R} x1=${f} y1=${y} x2=${f+v} y2=${y+b} stroke="#90caf9" stroke-width="1" style=${e?`--fall-from:-${t.h}px;--fall-to:${t.h}px;--fall-speed:${I};animation-delay:${V}`:""}></line>`)}else if(s.precipitation==="snow"||s.precipitation==="sleet"){let u=s.precipitation==="sleet"?12:pt;for(let f=0;f<pt;f++){let y=t.x+w()*t.w,b=t.y+w()*t.h,v=1.2+w()*1,R=s.precipitation==="sleet"&&f>=u,I=e?"fall":"",V=`${4+w()*3}s`,G=`-${w()*6}s`;P.push(R?d`<line class=${I} x1=${y} y1=${b} x2=${y+s.slant*.12} y2=${b+5} stroke="#90caf9" stroke-width="1" style=${e?`--fall-from:-${t.h}px;--fall-to:${t.h}px;--fall-speed:${V};animation-delay:${G}`:""}></line>`:d`<circle class=${I} cx=${y} cy=${b} r=${v} fill="#fff" style=${e?`--fall-from:-${t.h}px;--fall-to:${t.h}px;--fall-speed:${V};animation-delay:${G}`:""}></circle>`)}}let dt=e?"cloud drift":"cloud",J=ws.slice(0,s.cloudCount).map(u=>qt(t.x+u.x*t.w,t.y+u.y*t.h,1,s.cover>=.55?"#eceff1":"#fff",dt));if(s.overcast){let u=["#90a4ae","#78909c"];for(let f=0;f<4;f++){let y=t.x+(.08+f*.28)*t.w,b=t.y+(.12+f%2*.06)*t.h;J.push(qt(y,b,1.3,u[f%2],dt))}}let M=s.sun?a(s.sun):null,bt=.08*t.w,At=bt/12,Jt=s.path.map(u=>u.map(f=>{let y=a(f);return`${y.x.toFixed(1)},${y.y.toFixed(1)}`}).join(" "));return d`
    <defs>
      <linearGradient id=${n} x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color=${s.sky[0]}></stop>
        <stop offset="1" stop-color=${s.sky[1]}></stop>
      </linearGradient>
      ${s.sideLight?d`<radialGradient id=${i} gradientUnits="userSpaceOnUse" cx=${t.x+s.sideLight.x*t.w} cy=${o} r=${.75*t.w}>
        <stop offset="0" stop-color="#ffe0b2" stop-opacity=${s.sideLight.strength}></stop>
        <stop offset="1" stop-color="#ffe0b2" stop-opacity="0"></stop>
      </radialGradient>`:""}
      <clipPath id=${r}><rect x=${t.x} y=${t.y} width=${t.w} height=${t.h}></rect></clipPath>
    </defs>
    <g class="sky"><rect x=${t.x} y=${t.y} width=${t.w} height=${t.h} fill=${`url(#${n})`}></rect>
      ${s.sideLight?d`<rect class="side-light" x=${t.x} y=${t.y} width=${t.w} height=${t.h} fill=${`url(#${i})`}></rect>`:""}</g>
    ${Jt.length?d`<g class="sun-path" clip-path=${`url(#${r})`}>${Jt.map(u=>d`<polyline points=${u} fill="none" stroke="#fff8e1" stroke-opacity="0.55" stroke-width="1" stroke-dasharray="1.5 3" stroke-linecap="round"></polyline>`)}</g>`:""}
    ${s.stars>0&&!s.overcast?d`<g class="stars" opacity=${s.stars}>${c}</g>`:""}
    ${s.moon?d`<g class="moon">
      <circle cx=${t.x+s.moon.x*t.w} cy=${t.y+s.moon.y*t.h} r=${.095*t.w} fill="#fff8e1" opacity="0.15"></circle>
      ${_s(t.x+s.moon.x*t.w,t.y+s.moon.y*t.h,.07*t.w,s.moon.phase)}
    </g>`:""}
    ${M?d`<g class="sun">
      ${s.glow>0?d`<circle class="sun-glow" cx=${M.x} cy=${M.y} r=${.13*t.w} fill="#ffd54f" opacity=${s.glow}></circle>`:""}
      <circle class="sun-disc" cx=${M.x} cy=${M.y} r=${bt} fill="#ffd54f" opacity=${s.veil?(1-.45*s.veil.opacity).toFixed(2):1}></circle>
    </g>`:""}
    ${J.length?d`<g class="clouds">${J}</g>`:""}
    ${M&&s.veil?d`<g class="veil">${qt(M.x+s.veil.offset*bt-3.5*At,M.y+2*At,At,"#b0bec5","veil-cloud",s.veil.opacity)}</g>`:""}
    <g class="land" style=${s.dim>0?`filter: brightness(${(1-s.dim).toFixed(2)})`:""}>
      <path class="hill" d=${z} fill=${h}></path>
      ${X}
    </g>
    ${s.precipitation!=="none"?d`<g class="precip" clip-path=${`url(#${r})`}>${P}</g>`:""}
    ${s.fog?d`<g class="fog">
      <ellipse cx=${t.x+.2*t.w} cy=${t.y+.82*t.h} rx=${.25*t.w} ry=${.05*t.h} fill="#fff" opacity="0.5"></ellipse>
      <ellipse cx=${t.x+.58*t.w} cy=${t.y+.88*t.h} rx=${.32*t.w} ry=${.06*t.h} fill="#fff" opacity="0.5"></ellipse>
      <ellipse cx=${t.x+.9*t.w} cy=${t.y+.78*t.h} rx=${.2*t.w} ry=${.04*t.h} fill="#fff" opacity="0.5"></ellipse>
    </g>`:""}
    ${s.lightning&&e?d`<g class="lightning"><polyline class="flash" points=${`${t.x+.72*t.w},${t.y+.08*t.h} ${t.x+.68*t.w},${t.y+.25*t.h} ${t.x+.74*t.w},${t.y+.22*t.h} ${t.x+.69*t.w},${t.y+.42*t.h}`} fill="none" stroke="#ffd54f" stroke-width="2"></polyline></g>`:""}
  `}var Oe="ssc-drawing",Kt=262,q={top:40,bottom:241},xs={x:64,y:40,w:156,h:206},bs=4,K=class extends A{constructor(){super(...arguments);this.position=null;this.max=100;this.moving=null;this.gaps=!1;this.scene=null;this.animated=!1;this.storm=!1;this.compact=!1;this.interactive=!1;this.label="";this.maxLabel="max";this._drag=null;this.startY=null;this.moved=!1}viewY(e){let n=this.renderRoot.querySelector("svg")?.getBoundingClientRect();return!n||!n.height?null:(e.clientY-n.top)/n.height*Kt}onDown(e){this.interactive&&(e.currentTarget.setPointerCapture?.(e.pointerId),this.startY=e.clientY,this.moved=!1,e.preventDefault())}onMove(e){if(this.startY===null||!this.moved&&Math.abs(e.clientY-this.startY)<bs)return;this.moved=!0;let n=this.viewY(e);n!==null&&(this._drag=Wt(Pe(n,q),this.storm))}onUp(e){this.startY!==null&&(this.onMove(e),this.startY=null,this.moved&&this.send(),this._drag=null)}onCancel(){this.startY=null,this._drag=null}onKey(e){if(!this.interactive)return;let n=this._drag??this.position??0,i={ArrowUp:n+5,ArrowDown:n-5,PageUp:n+25,PageDown:n-25,Home:100,End:0};e.key in i?(this._drag=this.storm?i[e.key]>n?100:0:Wt(i[e.key],!1),e.preventDefault()):e.key==="Enter"&&this._drag!==null?(this.send(),this._drag=null,e.preventDefault()):e.key==="Escape"&&(this._drag=null)}send(){this._drag!==null&&this.dispatchEvent(new CustomEvent("set-position",{detail:{position:this._drag},bubbles:!0,composed:!0}))}render(){let e=this.position??0,i=ht(e,q)-q.bottom,r=this.interactive&&!this.compact,o=ht(this.max,q),a=this.compact?`46 0 192 ${Kt}`:`-16 0 256 ${Kt}`;return _`<svg
      class=${this.interactive?"interactive":""}
      viewBox=${a}
      role=${this.interactive?"slider":"img"}
      tabindex=${this.interactive?"0":"-1"}
      aria-label=${this.label}
      aria-valuemin="0"
      aria-valuemax="100"
      aria-valuenow=${this._drag??e}
      aria-valuetext=${`${this._drag??e}\xA0%`}
      @pointerdown=${this.onDown}
      @pointermove=${this.onMove}
      @pointerup=${this.onUp}
      @pointercancel=${this.onCancel}
      @keydown=${this.onKey}
    >
      <defs>
        <linearGradient id="glass" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="var(--ssc-glass-1)"></stop><stop offset="1" stop-color="var(--ssc-glass-2)"></stop>
        </linearGradient>
        <linearGradient id="slat" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="var(--ssc-slat-1)"></stop><stop offset="1" stop-color="var(--ssc-slat-2)"></stop>
        </linearGradient>
        <pattern id="slats" width="10" height="13" patternUnits="userSpaceOnUse" y="-3">
          <rect width="10" height="13" fill="url(#slat)"></rect><line x1="0" y1="12" x2="10" y2="12" stroke="var(--ssc-slat-line)" stroke-width="1.5"></line>
        </pattern>
        <!-- open slats: between two slats a row of separate slots with bridges; the slots are transparent,
             so the window (and what is outside) shows through -->
        <pattern id="slats-open" width="12" height="13" patternUnits="userSpaceOnUse" x="2" y="-3">
          <rect width="12" height="10.5" fill="url(#slat)"></rect>
          <rect y="10.5" width="3" height="2.5" fill="var(--ssc-slat-line)"></rect>
        </pattern>
        <clipPath id="glass-clip"><rect x="64" y="40" width="156" height="206"></rect></clipPath>
        <clipPath id="opening"><rect x="58" y="40" width="168" height="208"></rect></clipPath>
      </defs>
      <rect class="frame" x="52" y="24" width="180" height="230" rx="6" fill="none" stroke="var(--ssc-frame)" stroke-width="4"></rect>
      <rect x="64" y="40" width="156" height="206" fill="url(#glass)"></rect>
      ${this.scene?d`<g class="view" clip-path="url(#glass-clip)">${Le(this.scene,xs,this.animated&&!this.compact)}</g>`:""}
      <rect x="58" y="40" width="6" height="206" fill="var(--ssc-slat-2)"></rect>
      <rect x="220" y="40" width="6" height="206" fill="var(--ssc-slat-2)"></rect>
      <g clip-path="url(#opening)">
        <g class="curtain" style=${`transform: translateY(${i}px)`}>
          <rect class="slats ${this.gaps?"open":"closed"}" x="64" y="-170" width="156" height="406" fill=${this.gaps?"url(#slats-open)":"url(#slats)"}></rect>
          <rect class="bar" x="60" y="236" width="164" height="10" rx="3" fill="var(--ssc-bar)"></rect>
          ${r?d`<rect x="124" y="230" width="36" height="22" rx="11" fill="var(--ssc-accent)" stroke="#fff" stroke-width="2"></rect>
                 <line x1="134" y1="238" x2="150" y2="238" stroke="#fff" stroke-width="2"></line>
                 <line x1="134" y1="244" x2="150" y2="244" stroke="#fff" stroke-width="2"></line>`:""}
        </g>
      </g>
      <rect x="46" y="6" width="192" height="34" rx="6" fill="var(--ssc-box)" stroke="var(--ssc-frame)" stroke-width="3"></rect>
      ${this.moving?d`<path class="moving" d=${this.moving==="opening"?"M142 15 l8 10 h-16 z":"M142 31 l8 -10 h-16 z"} fill="var(--ssc-accent)"></path>`:""}
      ${this.max<100?d`<line class="max" x1=${this.compact?46:28} x2=${this.compact?58:46} y1=${o} y2=${o} stroke="var(--ssc-max)" stroke-width="3"></line>
             ${this.compact?"":d`<text x="46" y=${o+15} font-size="11" text-anchor="end" fill="var(--ssc-max)">${this.maxLabel} ${this.max} %</text>`}`:""}
      ${this._drag!==null?d`<g class="target">
            <rect x="60" y=${ht(this._drag,q)-5} width="164" height="10" rx="3" fill="var(--ssc-accent)" opacity="0.45"></rect>
            <text x="142" y=${ht(this._drag,q)-10} font-size="16" font-weight="700" text-anchor="middle" fill="var(--ssc-accent)">${this._drag} %</text>
          </g>`:""}
    </svg>`}};K.properties={position:{type:Number},max:{type:Number},moving:{type:String},gaps:{type:Boolean},scene:{attribute:!1},animated:{type:Boolean},storm:{type:Boolean},compact:{type:Boolean},interactive:{type:Boolean},label:{type:String},maxLabel:{type:String},_drag:{state:!0}},K.styles=[Te,T`
    :host {
      display: block;
      --ssc-frame: var(--secondary-text-color, #90a4ae);
      --ssc-box: var(--secondary-background-color, #eceff1);
      --ssc-glass-1: #e3f2fd;
      --ssc-glass-2: #90caf9;
      --ssc-slat-1: #eceff1;
      --ssc-slat-2: #b0bec5;
      --ssc-slat-line: #90a4ae;
      --ssc-bar: #546e7a;
      --ssc-accent: var(--primary-color, #1e88e5);
      --ssc-max: var(--warning-color, #ef6c00);
    }
    :host([dark]) {
      --ssc-glass-1: #1a3550;
      --ssc-glass-2: #2b5a85;
      --ssc-slat-1: #607d8b;
      --ssc-slat-2: #455a64;
      --ssc-slat-line: #37474f;
      --ssc-bar: #b0bec5;
    }
    svg {
      display: block;
      width: 100%;
      height: auto;
      outline: none;
    }
    svg.interactive {
      cursor: ns-resize;
      touch-action: none;
    }
    svg:focus-visible .frame {
      stroke: var(--ssc-accent);
    }
    .curtain {
      transition: transform 0.6s ease;
    }
    @media (prefers-reduced-motion: reduce) {
      .curtain {
        transition: none;
      }
    }
    text {
      font-family: var(--paper-font-body1_-_font-family, inherit);
    }
  `];function As(s){return[{name:"device_id",selector:{device:{integration:ot}}},{name:"language",selector:{select:{mode:"dropdown",options:[{value:"auto",label:s("language_auto")},..._e.map(t=>({value:t,label:t==="nl"?"Nederlands":"English"}))]}}}]}var ut=class extends A{setConfig(t){this._config=t}changed(t){let e={...t.detail.value};(!e.language||e.language==="auto")&&delete e.language,this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:e},bubbles:!0,composed:!0}))}render(){if(!this.hass||!this._config)return _``;let t=at(this._config.language||this.hass.locale?.language);return _`<ha-form
      .hass=${this.hass}
      .data=${{...this._config,language:this._config.language||"auto"}}
      .schema=${As(t)}
      .computeLabel=${e=>t(e.name)}
      @value-changed=${this.changed}
    ></ha-form>`}};ut.properties={hass:{attribute:!1},_config:{state:!0}};function Zt(s,t){customElements.get(s)||customElements.define(s,t)}Zt(Oe,K);Zt(jt,ut);Zt(ct,W);var xt=window;xt.customCards=xt.customCards??[];xt.customCards.some(s=>s.type===ct)||xt.customCards.push({type:ct,name:"Smart Shutter",description:"A shutter you can drag to a position, with buttons and its status; or all shutters of a base controller.",preview:!0,documentationURL:"https://github.com/abroeders/smart-shutter-control/blob/main/docs/card.md"});
/*! Bundled license information:

@lit/reactive-element/css-tag.js:
  (**
   * @license
   * Copyright 2019 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/reactive-element.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-html/lit-html.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-element/lit-element.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-html/is-server.js:
  (**
   * @license
   * Copyright 2022 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)
*/
