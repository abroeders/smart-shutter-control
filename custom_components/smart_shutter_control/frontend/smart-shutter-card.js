var rt=globalThis,ot=rt.ShadowRoot&&(rt.ShadyCSS===void 0||rt.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,dt=Symbol(),Lt=new WeakMap,Y=class{constructor(t,e,n){if(this._$cssResult$=!0,n!==dt)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e}get styleSheet(){let t=this.o,e=this.t;if(ot&&t===void 0){let n=e!==void 0&&e.length===1;n&&(t=Lt.get(e)),t===void 0&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),n&&Lt.set(e,t))}return t}toString(){return this.cssText}},Ut=s=>new Y(typeof s=="string"?s:s+"",void 0,dt),T=(s,...t)=>{let e=s.length===1?s[0]:t.reduce((n,i,r)=>n+(o=>{if(o._$cssResult$===!0)return o.cssText;if(typeof o=="number")return o;throw Error("Value passed to 'css' function must be a 'css' function result: "+o+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(i)+s[r+1],s[0]);return new Y(e,s,dt)},Dt=(s,t)=>{if(ot)s.adoptedStyleSheets=t.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet);else for(let e of t){let n=document.createElement("style"),i=rt.litNonce;i!==void 0&&n.setAttribute("nonce",i),n.textContent=e.cssText,s.appendChild(n)}},ft=ot?s=>s:s=>s instanceof CSSStyleSheet?(t=>{let e="";for(let n of t.cssRules)e+=n.cssText;return Ut(e)})(s):s;var{is:ye,defineProperty:ve,getOwnPropertyDescriptor:_e,getOwnPropertyNames:we,getOwnPropertySymbols:xe,getPrototypeOf:be}=Object,at=globalThis,zt=at.trustedTypes,Ae=zt?zt.emptyScript:"",Se=at.reactiveElementPolyfillSupport,W=(s,t)=>s,gt={toAttribute(s,t){switch(t){case Boolean:s=s?Ae:null;break;case Object:case Array:s=s==null?s:JSON.stringify(s)}return s},fromAttribute(s,t){let e=s;switch(t){case Boolean:e=s!==null;break;case Number:e=s===null?null:Number(s);break;case Object:case Array:try{e=JSON.parse(s)}catch{e=null}}return e}},Bt=(s,t)=>!ye(s,t),It={attribute:!0,type:String,converter:gt,reflect:!1,useDefault:!1,hasChanged:Bt};Symbol.metadata??=Symbol("metadata"),at.litPropertyMetadata??=new WeakMap;var S=class extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??=[]).push(t)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,e=It){if(e.state&&(e.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(t)&&((e=Object.create(e)).wrapped=!0),this.elementProperties.set(t,e),!e.noAccessor){let n=Symbol(),i=this.getPropertyDescriptor(t,n,e);i!==void 0&&ve(this.prototype,t,i)}}static getPropertyDescriptor(t,e,n){let{get:i,set:r}=_e(this.prototype,t)??{get(){return this[e]},set(o){this[e]=o}};return{get:i,set(o){let l=i?.call(this);r?.call(this,o),this.requestUpdate(t,l,n)},configurable:!0,enumerable:!0}}static getPropertyOptions(t){return this.elementProperties.get(t)??It}static _$Ei(){if(this.hasOwnProperty(W("elementProperties")))return;let t=be(this);t.finalize(),t.l!==void 0&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties)}static finalize(){if(this.hasOwnProperty(W("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(W("properties"))){let e=this.properties,n=[...we(e),...xe(e)];for(let i of n)this.createProperty(i,e[i])}let t=this[Symbol.metadata];if(t!==null){let e=litPropertyMetadata.get(t);if(e!==void 0)for(let[n,i]of e)this.elementProperties.set(n,i)}this._$Eh=new Map;for(let[e,n]of this.elementProperties){let i=this._$Eu(e,n);i!==void 0&&this._$Eh.set(i,e)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(t){let e=[];if(Array.isArray(t)){let n=new Set(t.flat(1/0).reverse());for(let i of n)e.unshift(ft(i))}else t!==void 0&&e.push(ft(t));return e}static _$Eu(t,e){let n=e.attribute;return n===!1?void 0:typeof n=="string"?n:typeof t=="string"?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(t=>this.enableUpdating=t),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(t=>t(this))}addController(t){(this._$EO??=new Set).add(t),this.renderRoot!==void 0&&this.isConnected&&t.hostConnected?.()}removeController(t){this._$EO?.delete(t)}_$E_(){let t=new Map,e=this.constructor.elementProperties;for(let n of e.keys())this.hasOwnProperty(n)&&(t.set(n,this[n]),delete this[n]);t.size>0&&(this._$Ep=t)}createRenderRoot(){let t=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return Dt(t,this.constructor.elementStyles),t}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(t=>t.hostConnected?.())}enableUpdating(t){}disconnectedCallback(){this._$EO?.forEach(t=>t.hostDisconnected?.())}attributeChangedCallback(t,e,n){this._$AK(t,n)}_$ET(t,e){let n=this.constructor.elementProperties.get(t),i=this.constructor._$Eu(t,n);if(i!==void 0&&n.reflect===!0){let r=(n.converter?.toAttribute!==void 0?n.converter:gt).toAttribute(e,n.type);this._$Em=t,r==null?this.removeAttribute(i):this.setAttribute(i,r),this._$Em=null}}_$AK(t,e){let n=this.constructor,i=n._$Eh.get(t);if(i!==void 0&&this._$Em!==i){let r=n.getPropertyOptions(i),o=typeof r.converter=="function"?{fromAttribute:r.converter}:r.converter?.fromAttribute!==void 0?r.converter:gt;this._$Em=i;let l=o.fromAttribute(e,r.type);this[i]=l??this._$Ej?.get(i)??l,this._$Em=null}}requestUpdate(t,e,n,i=!1,r){if(t!==void 0){let o=this.constructor;if(i===!1&&(r=this[t]),n??=o.getPropertyOptions(t),!((n.hasChanged??Bt)(r,e)||n.useDefault&&n.reflect&&r===this._$Ej?.get(t)&&!this.hasAttribute(o._$Eu(t,n))))return;this.C(t,e,n)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(t,e,{useDefault:n,reflect:i,wrapped:r},o){n&&!(this._$Ej??=new Map).has(t)&&(this._$Ej.set(t,o??e??this[t]),r!==!0||o!==void 0)||(this._$AL.has(t)||(this.hasUpdated||n||(e=void 0),this._$AL.set(t,e)),i===!0&&this._$Em!==t&&(this._$Eq??=new Set).add(t))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(e){Promise.reject(e)}let t=this.scheduleUpdate();return t!=null&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[i,r]of this._$Ep)this[i]=r;this._$Ep=void 0}let n=this.constructor.elementProperties;if(n.size>0)for(let[i,r]of n){let{wrapped:o}=r,l=this[i];o!==!0||this._$AL.has(i)||l===void 0||this.C(i,void 0,r,l)}}let t=!1,e=this._$AL;try{t=this.shouldUpdate(e),t?(this.willUpdate(e),this._$EO?.forEach(n=>n.hostUpdate?.()),this.update(e)):this._$EM()}catch(n){throw t=!1,this._$EM(),n}t&&this._$AE(e)}willUpdate(t){}_$AE(t){this._$EO?.forEach(e=>e.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(t)),this.updated(t)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return!0}update(t){this._$Eq&&=this._$Eq.forEach(e=>this._$ET(e,this[e])),this._$EM()}updated(t){}firstUpdated(t){}};S.elementStyles=[],S.shadowRootOptions={mode:"open"},S[W("elementProperties")]=new Map,S[W("finalized")]=new Map,Se?.({ReactiveElement:S}),(at.reactiveElementVersions??=[]).push("2.1.2");var xt=globalThis,Gt=s=>s,lt=xt.trustedTypes,Vt=lt?lt.createPolicy("lit-html",{createHTML:s=>s}):void 0,Kt="$lit$",M=`lit$${Math.random().toFixed(9).slice(2)}$`,Zt="?"+M,Ee=`<${Zt}>`,H=document,q=()=>H.createComment(""),K=s=>s===null||typeof s!="object"&&typeof s!="function",bt=Array.isArray,Ce=s=>bt(s)||typeof s?.[Symbol.iterator]=="function",mt=`[ 	
\f\r]`,F=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,jt=/-->/g,Yt=/>/g,N=RegExp(`>|${mt}(?:([^\\s"'>=/]+)(${mt}*=${mt}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),Wt=/'/g,Ft=/"/g,Xt=/^(?:script|style|textarea|title)$/i,At=s=>(t,...e)=>({_$litType$:s,strings:t,values:e}),w=At(1),g=At(2),ts=At(3),L=Symbol.for("lit-noChange"),y=Symbol.for("lit-nothing"),qt=new WeakMap,O=H.createTreeWalker(H,129);function Jt(s,t){if(!bt(s)||!s.hasOwnProperty("raw"))throw Error("invalid template strings array");return Vt!==void 0?Vt.createHTML(t):t}var ke=(s,t)=>{let e=s.length-1,n=[],i,r=t===2?"<svg>":t===3?"<math>":"",o=F;for(let l=0;l<e;l++){let a=s[l],c,h,u=-1,d=0;for(;d<a.length&&(o.lastIndex=d,h=o.exec(a),h!==null);)d=o.lastIndex,o===F?h[1]==="!--"?o=jt:h[1]!==void 0?o=Yt:h[2]!==void 0?(Xt.test(h[2])&&(i=RegExp("</"+h[2],"g")),o=N):h[3]!==void 0&&(o=N):o===N?h[0]===">"?(o=i??F,u=-1):h[1]===void 0?u=-2:(u=o.lastIndex-h[2].length,c=h[1],o=h[3]===void 0?N:h[3]==='"'?Ft:Wt):o===Ft||o===Wt?o=N:o===jt||o===Yt?o=F:(o=N,i=void 0);let m=o===N&&s[l+1].startsWith("/>")?" ":"";r+=o===F?a+Ee:u>=0?(n.push(c),a.slice(0,u)+Kt+a.slice(u)+M+m):a+M+(u===-2?l:m)}return[Jt(s,r+(s[e]||"<?>")+(t===2?"</svg>":t===3?"</math>":"")),n]},Z=class s{constructor({strings:t,_$litType$:e},n){let i;this.parts=[];let r=0,o=0,l=t.length-1,a=this.parts,[c,h]=ke(t,e);if(this.el=s.createElement(c,n),O.currentNode=this.el.content,e===2||e===3){let u=this.el.content.firstChild;u.replaceWith(...u.childNodes)}for(;(i=O.nextNode())!==null&&a.length<l;){if(i.nodeType===1){if(i.hasAttributes())for(let u of i.getAttributeNames())if(u.endsWith(Kt)){let d=h[o++],m=i.getAttribute(u).split(M),x=/([.?@])?(.*)/.exec(d);a.push({type:1,index:r,name:x[2],strings:m,ctor:x[1]==="."?yt:x[1]==="?"?vt:x[1]==="@"?_t:z}),i.removeAttribute(u)}else u.startsWith(M)&&(a.push({type:6,index:r}),i.removeAttribute(u));if(Xt.test(i.tagName)){let u=i.textContent.split(M),d=u.length-1;if(d>0){i.textContent=lt?lt.emptyScript:"";for(let m=0;m<d;m++)i.append(u[m],q()),O.nextNode(),a.push({type:2,index:++r});i.append(u[d],q())}}}else if(i.nodeType===8)if(i.data===Zt)a.push({type:2,index:r});else{let u=-1;for(;(u=i.data.indexOf(M,u+1))!==-1;)a.push({type:7,index:r}),u+=M.length-1}r++}}static createElement(t,e){let n=H.createElement("template");return n.innerHTML=t,n}};function D(s,t,e=s,n){if(t===L)return t;let i=n!==void 0?e._$Co?.[n]:e._$Cl,r=K(t)?void 0:t._$litDirective$;return i?.constructor!==r&&(i?._$AO?.(!1),r===void 0?i=void 0:(i=new r(s),i._$AT(s,e,n)),n!==void 0?(e._$Co??=[])[n]=i:e._$Cl=i),i!==void 0&&(t=D(s,i._$AS(s,t.values),i,n)),t}var $t=class{constructor(t,e){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=e}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){let{el:{content:e},parts:n}=this._$AD,i=(t?.creationScope??H).importNode(e,!0);O.currentNode=i;let r=O.nextNode(),o=0,l=0,a=n[0];for(;a!==void 0;){if(o===a.index){let c;a.type===2?c=new X(r,r.nextSibling,this,t):a.type===1?c=new a.ctor(r,a.name,a.strings,this,t):a.type===6&&(c=new wt(r,this,t)),this._$AV.push(c),a=n[++l]}o!==a?.index&&(r=O.nextNode(),o++)}return O.currentNode=H,i}p(t){let e=0;for(let n of this._$AV)n!==void 0&&(n.strings!==void 0?(n._$AI(t,n,e),e+=n.strings.length-2):n._$AI(t[e])),e++}},X=class s{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(t,e,n,i){this.type=2,this._$AH=y,this._$AN=void 0,this._$AA=t,this._$AB=e,this._$AM=n,this.options=i,this._$Cv=i?.isConnected??!0}get parentNode(){let t=this._$AA.parentNode,e=this._$AM;return e!==void 0&&t?.nodeType===11&&(t=e.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,e=this){t=D(this,t,e),K(t)?t===y||t==null||t===""?(this._$AH!==y&&this._$AR(),this._$AH=y):t!==this._$AH&&t!==L&&this._(t):t._$litType$!==void 0?this.$(t):t.nodeType!==void 0?this.T(t):Ce(t)?this.k(t):this._(t)}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t))}_(t){this._$AH!==y&&K(this._$AH)?this._$AA.nextSibling.data=t:this.T(H.createTextNode(t)),this._$AH=t}$(t){let{values:e,_$litType$:n}=t,i=typeof n=="number"?this._$AC(t):(n.el===void 0&&(n.el=Z.createElement(Jt(n.h,n.h[0]),this.options)),n);if(this._$AH?._$AD===i)this._$AH.p(e);else{let r=new $t(i,this),o=r.u(this.options);r.p(e),this.T(o),this._$AH=r}}_$AC(t){let e=qt.get(t.strings);return e===void 0&&qt.set(t.strings,e=new Z(t)),e}k(t){bt(this._$AH)||(this._$AH=[],this._$AR());let e=this._$AH,n,i=0;for(let r of t)i===e.length?e.push(n=new s(this.O(q()),this.O(q()),this,this.options)):n=e[i],n._$AI(r),i++;i<e.length&&(this._$AR(n&&n._$AB.nextSibling,i),e.length=i)}_$AR(t=this._$AA.nextSibling,e){for(this._$AP?.(!1,!0,e);t!==this._$AB;){let n=Gt(t).nextSibling;Gt(t).remove(),t=n}}setConnected(t){this._$AM===void 0&&(this._$Cv=t,this._$AP?.(t))}},z=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,e,n,i,r){this.type=1,this._$AH=y,this._$AN=void 0,this.element=t,this.name=e,this._$AM=i,this.options=r,n.length>2||n[0]!==""||n[1]!==""?(this._$AH=Array(n.length-1).fill(new String),this.strings=n):this._$AH=y}_$AI(t,e=this,n,i){let r=this.strings,o=!1;if(r===void 0)t=D(this,t,e,0),o=!K(t)||t!==this._$AH&&t!==L,o&&(this._$AH=t);else{let l=t,a,c;for(t=r[0],a=0;a<r.length-1;a++)c=D(this,l[n+a],e,a),c===L&&(c=this._$AH[a]),o||=!K(c)||c!==this._$AH[a],c===y?t=y:t!==y&&(t+=(c??"")+r[a+1]),this._$AH[a]=c}o&&!i&&this.j(t)}j(t){t===y?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"")}},yt=class extends z{constructor(){super(...arguments),this.type=3}j(t){this.element[this.name]=t===y?void 0:t}},vt=class extends z{constructor(){super(...arguments),this.type=4}j(t){this.element.toggleAttribute(this.name,!!t&&t!==y)}},_t=class extends z{constructor(t,e,n,i,r){super(t,e,n,i,r),this.type=5}_$AI(t,e=this){if((t=D(this,t,e,0)??y)===L)return;let n=this._$AH,i=t===y&&n!==y||t.capture!==n.capture||t.once!==n.once||t.passive!==n.passive,r=t!==y&&(n===y||i);i&&this.element.removeEventListener(this.name,this,n),r&&this.element.addEventListener(this.name,this,t),this._$AH=t}handleEvent(t){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,t):this._$AH.handleEvent(t)}},wt=class{constructor(t,e,n){this.element=t,this.type=6,this._$AN=void 0,this._$AM=e,this.options=n}get _$AU(){return this._$AM._$AU}_$AI(t){D(this,t)}};var Me=xt.litHtmlPolyfillSupport;Me?.(Z,X),(xt.litHtmlVersions??=[]).push("3.3.3");var Qt=(s,t,e)=>{let n=e?.renderBefore??t,i=n._$litPart$;if(i===void 0){let r=e?.renderBefore??null;n._$litPart$=i=new X(t.insertBefore(q(),r),r,void 0,e??{})}return i._$AI(s),i};var St=globalThis,b=class extends S{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let t=super.createRenderRoot();return this.renderOptions.renderBefore??=t.firstChild,t}update(t){let e=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=Qt(e,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return L}};b._$litElement$=!0,b.finalized=!0,St.litElementHydrateSupport?.({LitElement:b});var Pe=St.litElementPolyfillSupport;Pe?.({LitElement:b});(St.litElementVersions??=[]).push("4.2.2");var J="smart_shutter_control";function U(s,t){let e={};for(let n of Object.values(s.entities??{}))n.platform===J&&n.device_id===t&&n.translation_key&&(e[n.translation_key]=n.entity_id);return e}function I(s,t){return"shutter"in U(s,t)}function ct(s,t){let e=s.devices?.[t];return e?.name_by_user||e?.name||t}function Et(s){let t=new Set;for(let e of Object.values(s.entities??{}))e.platform===J&&e.device_id&&t.add(e.device_id);return[...t].sort((e,n)=>Number(I(s,e))-Number(I(s,n))||ct(s,e).localeCompare(ct(s,n)))}function te(s,t){return Et(s).filter(e=>s.devices?.[e]?.via_device_id===t&&I(s,e))}function ee(s,t){return s.devices?.[t]?.via_device_id??void 0}var se={open:"open",closed:"closed",slit:"slit",partly_open:"partly open",automatic:"Automatic",manual_pause:"Manual",off:"Off",storm_chip:"Storm: only open/closed",frost_chip:"Frost: no moves",sleep_in:"Sleep in",sleep_in_all:"Sleep in (all)",next:"Next",then:"then",until:"until",next_phase:"the next phase",resume:"Resume",open_cover:"Open",stop_cover:"Stop",close_cover:"Close",all_shutters:"All shutters",no_device:"Choose a shutter or a base controller of Smart Shutter Control.",not_found:"Device not found",max:"max",position:"Position",device_id:"Device",language:"Language",language_auto:"Integration setting",reason_idle:"No action",reason_off:"Automatic control off",reason_manual:"Manual",reason_calibrating:"Calibrating",reason_sun:"Sun on the window",reason_schedule:"Schedule",reason_sleep_in:"Sleeping in",reason_storm:"Storm",reason_frost:"Frost",reason_heat_limit:"Too warm",reason_cold_limit:"Too cold",reason_winter:"Winter",phase_night:"night",phase_slit:"slit",phase_day:"day",phase_dusk:"dusk"},Re={open:"open",closed:"dicht",slit:"spleetstand",partly_open:"deels open",automatic:"Automatisch",manual_pause:"Handbediening",off:"Uit",storm_chip:"Storm: alleen open/dicht",frost_chip:"Vorst: geen bewegingen",sleep_in:"Uitslapen",sleep_in_all:"Uitslapen (alle)",next:"Volgende",then:"daarna",until:"tot",next_phase:"de volgende fase",resume:"Hervatten",open_cover:"Open",stop_cover:"Stop",close_cover:"Dicht",all_shutters:"Alle rolluiken",no_device:"Kies een rolluik of een basiscontroller van Smart Shutter Control.",not_found:"Apparaat niet gevonden",max:"max",position:"Stand",device_id:"Apparaat",language:"Taal",language_auto:"Instelling van de integratie",reason_idle:"Geen actie",reason_off:"Automaat uit",reason_manual:"Handbediening",reason_calibrating:"Kalibreren",reason_sun:"Zon op het raam",reason_schedule:"Schema",reason_sleep_in:"Uitslapen",reason_storm:"Storm",reason_frost:"Vorst",reason_heat_limit:"Te warm",reason_cold_limit:"Te koud",reason_winter:"Winter",phase_night:"nacht",phase_slit:"spleet",phase_day:"dag",phase_dusk:"schemer"};function Q(s){let t=s?.toLowerCase().startsWith("nl")?Re:se;return e=>t[e]??se[e]??e}var ne=["en","nl"];var Te=Date.UTC(2e3,0,1,12,0,0),Ne=29.530588853,Oe=Date.UTC(2e3,0,6,18,14,0),E=Math.PI/180,tt=s=>(s%360+360)%360;function ie(s){return((s.getTime()-Oe)/864e5/Ne%1+1)%1}function re(s,t,e){let n=(s.getTime()-Te)/864e5,i=tt(218.316+13.176396*n),r=tt(134.963+13.064993*n),o=tt(93.272+13.22935*n),l=(i+6.289*Math.sin(r*E))*E,a=5.128*Math.sin(o*E)*E,c=23.4397*E,h=Math.sin(c),u=Math.cos(c),d=Math.sin(a),m=Math.cos(a),x=m*Math.cos(l),j=m*Math.sin(l)*u-d*h,f=m*Math.sin(l)*h+d*u,p=Math.atan2(j,x),$=Math.asin(f),v=t*E,A=tt(280.16+360.9856235*n+e)*E-p,C=Math.asin(Math.sin(v)*Math.sin($)+Math.cos(v)*Math.cos($)*Math.cos(A)),k=Math.atan2(Math.sin(A),Math.cos(A)*Math.sin(v)-Math.tan($)*Math.cos(v));return{azimuth:tt(k/E+180),elevation:C/E}}var oe=.72,He=.16,ae=70,Le=["rainy","lightning-rainy"],Ue=["cloudy","rainy","pouring","snowy","snowy-rainy","lightning","lightning-rainy","hail","fog","exceptional"],De=["partlycloudy","windy-variant"];function ze(s){return s===null?"day":s<-6?"night":s<0?"twilight":"day"}function le(s,t,e){if(s===null||t===null||t<0)return null;let n=e===null?0:(s-e+540)%360-180;if(Math.abs(n)>ae)return null;let i=.5+n/(2*ae),r=oe-Math.min(t,60)/60*(oe-He);return{x:Math.min(.94,Math.max(.06,i)),y:r}}function Ie(s,t){let e=["winter","spring","summer","autumn"],n=Math.floor((s.getMonth()+1)%12/3);return e[t<0?(n+2)%4:n]}function Be(s,t,e){let n=Math.max(s??0,(t??0)*.7),i=n<10?0:n<40?1+(n-10)/10:n<60?4+(n-40)/5:8+Math.min(4,(n-60)/10);return e&&(i=Math.max(i,10)+3),Math.round(i*10)/10}function Ge(s,t,e){return s==="night"?e?["#1b1f2a","#2e3440"]:["#0d1442","#283593"]:s==="twilight"?e?["#4a4f63","#7a6f80"]:["#3949ab","#ff8a65"]:e?["#78909c","#b0bec5"]:t!==null&&t<12?["#64b5f6","#ffe0b2"]:["#42a5f5","#bbdefb"]}function Ct(s){let t=s.weather??"",e=ze(s.sunElevation),n=Ue.includes(t),i=n?"overcast":De.includes(t)?"few":"none",r=t==="pouring"?"pouring":t==="snowy-rainy"?"sleet":t==="snowy"?"snow":Le.includes(t)?"rain":"none",o=e==="day"&&!n?le(s.sunAzimuth,s.sunElevation,s.windowAzimuth):null,l=null;if(e!=="day"&&!n){let u=ie(s.now),d=re(s.now,s.latitude,s.longitude),m=le(d.azimuth,d.elevation,s.windowAzimuth),x=u>.03&&u<.97;m&&x&&(l={...m,phase:u})}let a=n?0:e==="night"?1:e==="twilight"?Math.max(0,Math.min(1,-(s.sunElevation??0)/6)):0,c=Be(s.wind,s.gust,s.storm),h=e==="night"?.65:e==="twilight"?.35:n?.15:0;return{light:e,sky:Ge(e,s.sunElevation,n),stars:a,sun:o,moon:l,clouds:i,precipitation:r,fog:t==="fog",lightning:t==="lightning"||t==="lightning-rainy",season:Ie(s.now,s.latitude),snowGround:r==="snow"||r==="sleet",sway:c,slant:Math.min(30,c*2.5),dim:h}}var P=s=>s==null||s===""||isNaN(Number(s))?null:Number(s);function kt(s,t){let e=U(s,t),n=m=>e[m]?s.states[e[m]]:void 0,i=ee(s,t),r=i?U(s,i):{},o=m=>m?s.states[m]?.state==="on":!1,l=n("shutter"),a=n("reason"),c=n("next_action"),h=[];if(c&&!["unknown","unavailable"].includes(c.state)&&c.attributes.phase){h.push({at:c.state,phase:c.attributes.phase,position:c.attributes.position});for(let m of c.attributes.following??[])h.push({at:m.at,phase:m.phase,position:m.position})}let u=n("manual_pause"),d=l?.state;return{deviceId:t,name:ct(s,t),entities:e,position:P(l?.attributes.current_position),moving:d==="opening"||d==="closing"?d:null,closed:d==="closed",stand:n("stand")?.state??null,reason:a?.state??null,target:P(a?.attributes.target_position),max:P(a?.attributes.max_position)??100,phase:n("phase")?.state??null,automatic:n("automatic")?.state!=="off",sleepIn:o(e.sleep_in),paused:o(e.manual_pause),pausedUntil:u?.attributes.until??null,next:h,storm:o(r.storm),frost:o(r.frost),language:a?.attributes.language??null,outside:Ve(s,r,e)}}function Ve(s,t,e,n=new Date){let i=l=>l?s.states[l]?.attributes??{}:{},r=i(t.sun_factor),o=t.storm?s.states[t.storm]:void 0;return{now:n,latitude:s.config?.latitude??52,longitude:s.config?.longitude??5,sunAzimuth:P(r.sun_azimuth),sunElevation:P(r.sun_elevation),windowAzimuth:P(i(e.sun_on_window).window_azimuth),weather:r.weather??null,wind:P(o?.attributes.wind),gust:P(o?.attributes.gust),storm:o?.state==="on"}}function Mt(s,t,e){return t||e?.language||s.locale?.language||s.language||"en"}function ce(s,t,e){let n=new Date(s);if(isNaN(n.getTime()))return"";try{return new Intl.DateTimeFormat(e,{hour:"2-digit",minute:"2-digit",hour12:!1,timeZone:t.config?.time_zone}).format(n)}catch{return new Intl.DateTimeFormat(e,{hour:"2-digit",minute:"2-digit",hour12:!1}).format(n)}}function ht(s,t){return s===null?"\u2013":s==="slit"?t("slit"):s<=0?t("closed"):s>=100?t("open"):`${s}\xA0%`}function Pt(s,t,e){let n=s.stand&&!["unknown","unavailable"].includes(s.stand)?t(s.stand):"",i=s.reason?t(`reason_${s.reason}`):"",r="";if(s.paused){let c=s.pausedUntil==="next phase"||!s.pausedUntil?t("next_phase"):e(s.pausedUntil);r=`${t("until")} ${c}`}else s.target!==null&&(r=[s.position!==null&&Math.abs(s.target-s.position)>1?`\u2192 ${ht(s.target,t)}`:"",s.phase?t(`phase_${s.phase}`):""].filter(Boolean).join(" \xB7 "));let o=c=>[e(c.at),c.phase==="dusk"?t("phase_dusk"):"",ht(c.position,t)].filter(Boolean).join(" "),[l,a]=s.next;return{stand:n,reason:i,detail:r,next:l?`${t("next")}: ${o(l)}`:null,then:a?`${t("then")} ${o(a)}`:null,chip:s.automatic?s.paused?"manual_pause":"automatic":"off"}}var et="smart-shutter-card",Rt="smart-shutter-card-editor",je=360,Ye={up:"M13,20H11V8L5.5,13.5L4.08,12.08L12,4.16L19.92,12.08L18.5,13.5L13,8V20Z",stop:"M18,18H6V6H18V18Z",down:"M11,4H13V16L18.5,10.5L19.92,11.92L12,19.84L4.08,11.92L5.5,10.5L11,16V4Z"},B=class extends b{constructor(){super(...arguments);this._narrow=!1}static getConfigElement(){return document.createElement(Rt)}static getStubConfig(e){return{type:`custom:${et}`,device_id:Et(e)[0]}}setConfig(e){if(!e)throw new Error("Invalid configuration");this._config={...e}}getCardSize(){return 6}getGridOptions(){return{columns:!!(this.hass&&this._config?.device_id&&!I(this.hass,this._config.device_id))?"full":12,min_columns:6,rows:"auto"}}connectedCallback(){super.connectedCallback(),typeof ResizeObserver<"u"&&(this.observer=new ResizeObserver(e=>{let n=e[0]?.contentRect.width??0;n&&(this._narrow=n<je)}),this.observer.observe(this))}disconnectedCallback(){super.disconnectedCallback(),this.observer?.disconnect()}call(e,n,i,r={}){!this.hass||!i||this.hass.callService(e,n,{entity_id:i,...r})}toggle(e,n){this.call(e?.split(".")[0]??"switch",n?"turn_off":"turn_on",e)}moreInfo(e){e&&this.dispatchEvent(new CustomEvent("hass-more-info",{detail:{entityId:e},bubbles:!0,composed:!0}))}render(){let e=this.hass,n=this._config?.device_id;if(!e||!this._config)return y;let i=Q(Mt(e,this._config.language));return n?!e.devices?.[n]&&!Object.keys(U(e,n)).length?w`<ha-card><div class="message">${i("not_found")}: ${n}</div></ha-card>`:I(e,n)?this.renderShutter(e,n):this.renderOverview(e,n):w`<ha-card><div class="message">${i("no_device")}</div></ha-card>`}texts(e,n){let i=Mt(e,this._config?.language,n);return{t:Q(i),time:r=>ce(r,e,i),lang:i}}buttons(e,n,i=!1){let r=e.entities.shutter,o=(l,a,c)=>w`<button class="round ${i?"small":""}" title=${c} aria-label=${c} @click=${h=>{h.stopPropagation(),this.call("cover",a,r)}}>
        <svg viewBox="0 0 24 24"><path d=${Ye[l]}></path></svg>
      </button>`;return w`${o("up","open_cover",n("open_cover"))}${o("stop","stop_cover",n("stop_cover"))}${o("down","close_cover",n("close_cover"))}`}switch(e,n,i,r){return n?w`<button class="switch ${r}" role="switch" aria-checked=${i?"true":"false"} @click=${()=>this.toggle(n,i)}>
      <span class="track ${i?"on":""}"><span class="knob"></span></span>${e}
    </button>`:y}warnings(e,n,i){return w`${e?w`<span class="chip warn storm">⚠ ${i("storm_chip")}</span>`:y}${n?w`<span class="chip warn frost">❄ ${i("frost_chip")}</span>`:y}`}renderShutter(e,n){let i=kt(e,n),{t:r,time:o}=this.texts(e,i),l=Pt(i,r,o),a=!!e.themes?.darkMode;return w`<ha-card class=${this._narrow?"narrow":""}>
      <div class="head">
        <div class="name">${i.name}</div>
        <div class="chips"><span class="chip ${l.chip}">${r(l.chip)}</span>${this.warnings(i.storm,i.frost,r)}</div>
      </div>
      <div class="body">
        <ssc-drawing
          ?dark=${a}
          .position=${i.position}
          .max=${i.max}
          .moving=${i.moving}
          .gaps=${!i.closed}
          .scene=${Ct(i.outside)}
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
          <div class="sub">${l.stand}</div>
          <div class="line reason">${l.reason}</div>
          <div class="sub">${l.detail}</div>
          ${l.next?w`<div class="line next">${l.next}</div>`:y}
          ${l.then?w`<div class="sub then">${l.then}</div>`:y}
        </div>
      </div>
      <div class="switches">
        ${this.switch(r("automatic"),i.entities.automatic,i.automatic,"automatic")}
        ${this.switch(r("sleep_in"),i.entities.sleep_in,i.sleepIn,"sleep-in")}
        ${i.paused&&i.entities.resume?w`<button class="text resume" @click=${()=>this.call("button","press",i.entities.resume)}>${r("resume")}</button>`:y}
      </div>
    </ha-card>`}renderOverview(e,n){let i=te(e,n).map(h=>kt(e,h)),{t:r,time:o}=this.texts(e,i[0]??null),l=U(e,n),a=h=>l[h]?e.states[l[h]]?.state==="on":!1,c=!!e.themes?.darkMode;return w`<ha-card class="overview">
      <div class="head">
        <div class="name">${r("all_shutters")}</div>
        <div class="chips">${this.warnings(a("storm"),a("frost"),r)}</div>
      </div>
      <div class="grid">
        ${i.map(h=>{let u=Pt(h,r,o),d=[h.position===null?"\u2013":ht(h.position,r),u.reason].filter(Boolean).join(" \xB7 ");return w`<div class="tile" @click=${()=>this.moreInfo(h.entities.shutter)}>
            <ssc-drawing compact ?dark=${c} .position=${h.position} .max=${h.max} .moving=${h.moving} .gaps=${!h.closed} .scene=${Ct(h.outside)}></ssc-drawing>
            <div class="tile-text">
              <div class="tile-name">${h.name}</div>
              <div class="sub ${u.chip==="manual_pause"?"manual":""}">${d}${u.chip==="manual_pause"?` \xB7 ${u.detail}`:""}</div>
              <div class="tile-buttons">${this.buttons(h,r,!0)}</div>
            </div>
          </div>`})}
      </div>
      <div class="switches">${this.switch(r("sleep_in_all"),l.sleep_in_all,a("sleep_in_all"),"sleep-in-all")}</div>
    </ha-card>`}};B.properties={hass:{attribute:!1},_config:{state:!0},_narrow:{state:!0}},B.styles=T`
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
  `;var Tt=(s,t,e)=>Math.min(e,Math.max(t,s));function st(s,t){return t.top+(1-Tt(s,0,100)/100)*(t.bottom-t.top)}function he(s,t){return Math.round(Tt((t.bottom-s)/(t.bottom-t.top),0,1)*100)}function Nt(s,t){let e=Tt(Math.round(s),0,100);return t?e>=50?100:0:e}function ue(s){let t=s>>>0;return()=>(t=Math.imul(t,1664525)+1013904223>>>0,t/4294967296)}var pe=T`
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
`;function We(s,t,e,n){if(n<.03||n>.97)return"";if(n>.97-1e-4||Math.abs(n-.5)<1e-4)return g`<circle class="moon-disc" cx=${s} cy=${t} r=${e} fill="#fff8e1"></circle>`;let i=n<.5,r=e*Math.abs(Math.cos(2*Math.PI*n)),o=i?1:0,l=i?1:0,a=`M ${s} ${t-e} A ${e} ${e} 0 0 ${o} ${s} ${t+e} A ${r} ${e} 0 0 ${l} ${s} ${t-e} Z`;return g`<path class="moon-disc" d=${a} fill="#fff8e1"></path>`}function de(s,t,e){let n="ssc-view-sky",i="ssc-view-precip",r=t.y+.72*t.h,o=ue(20261124),l=[];for(let f=0;f<30;f++){let p=t.x+o()*t.w,$=t.y+o()*t.h*.55,v=.6+o()*.8,_=e&&f%7===0,A=`${f%5*.35}s`;l.push(g`<circle class=${_?"star twinkle":"star"} cx=${p} cy=${$} r=${v} fill="#fff" style=${_?`animation-delay:${A};opacity:${s.stars}`:`opacity:${s.stars}`}></circle>`)}let a=s.snowGround?"#eceff1":s.season==="spring"?"#8bc34a":s.season==="summer"?"#7cb342":s.season==="autumn"?"#9e9d24":"#a1887f",c=`M ${t.x} ${r} C ${t.x+.22*t.w} ${r-.08*t.h}, ${t.x+.42*t.w} ${r+.03*t.h}, ${t.x+.58*t.w} ${r-.05*t.h} S ${t.x+.82*t.w} ${r+.02*t.h}, ${t.x+t.w} ${r-.02*t.h} L ${t.x+t.w} ${t.y+t.h} L ${t.x} ${t.y+t.h} Z`,u=[{fx:.25,base:r+.01*t.h,height:.19*t.h},{fx:.72,base:r+.015*t.h,height:.22*t.h},{fx:.5,base:r-.025*t.h,height:.13*t.h}].map(f=>{let p=t.x+f.fx*t.w,$=f.base-f.height,v=Math.max(2.5,t.w*.018),_=Math.max(5,f.height*.23),A=e&&s.sway>0?" sway":"",C=!e&&s.sway>0?` rotate(${s.sway/2} ${p} ${f.base})`:"",k=`transform-origin:${p}px ${f.base}px;--sway:${s.sway}deg;--sway-speed:${s.sway>8?"1.2s":"2.5s"}`,R;if(s.season==="winter"){let pt=[-1,-.35,.35,1].map(it=>g`<line class="branch" x1=${p} y1=${f.base-f.height*.58} x2=${p+it*_*1.15} y2=${f.base-f.height*(.68+Math.abs(it)*.15)} stroke="#6d4c41" stroke-width="1.2"></line>`);R=g`<g class="winter">${pt}${s.snowGround?g`<line x1=${p-_} y1=${$+_*.45} x2=${p-_*.35} y2=${$+_*.25} stroke="#eceff1" stroke-width="1.8"></line>`:""}</g>`}else{let pt=s.season==="spring"?["#9ccc65","#9ccc65","#9ccc65","#9ccc65"]:s.season==="summer"?["#388e3c","#43a047","#388e3c","#43a047"]:["#ef6c00","#d84315","#f9a825","#ef6c00"],it=[[p-_*.45,$+_*.45],[p+_*.45,$+_*.45],[p,$],[p,$+_*.72]];R=g`<g class="foliage">${it.map(([ge,me],$e)=>g`<circle class="crown" cx=${ge} cy=${me} r=${_} fill=${pt[$e]}></circle>`)}${s.season==="spring"?g`<circle cx=${p-_*.9} cy=${$+_*.1} r="1.3" fill="#f8bbd0"></circle><circle cx=${p+_*.8} cy=${$+_*.7} r="1.3" fill="#f8bbd0"></circle>`:""}</g>`}return g`<g class=${`tree${A}`} style=${k} transform=${C||void 0}>
      <rect x=${p-v/2} y=${f.base-f.height*.58} width=${v} height=${f.height*.58} rx="1" fill="#6d4c41"></rect>
      ${R}
    </g>`}),d=ue(481516),m=s.precipitation==="pouring"?45:25,x=[];if(s.precipitation==="rain"||s.precipitation==="pouring")for(let f=0;f<m;f++){let p=t.x+d()*t.w,$=t.y+d()*t.h,v=4+d()*3,_=s.slant*.12,A=e?"fall":"",C=`${.7+d()*.4}s`,k=`-${d()*1.1}s`;x.push(g`<line class=${A} x1=${p} y1=${$} x2=${p+_} y2=${$+v} stroke="#90caf9" stroke-width="1" style=${e?`--fall-from:-${t.h}px;--fall-to:${t.h}px;--fall-speed:${C};animation-delay:${k}`:""}></line>`)}else if(s.precipitation==="snow"||s.precipitation==="sleet"){let f=s.precipitation==="sleet"?12:m;for(let p=0;p<m;p++){let $=t.x+d()*t.w,v=t.y+d()*t.h,_=1.2+d()*1,A=s.precipitation==="sleet"&&p>=f,C=e?"fall":"",k=`${4+d()*3}s`,R=`-${d()*6}s`;x.push(A?g`<line class=${C} x1=${$} y1=${v} x2=${$+s.slant*.12} y2=${v+5} stroke="#90caf9" stroke-width="1" style=${e?`--fall-from:-${t.h}px;--fall-to:${t.h}px;--fall-speed:${k};animation-delay:${R}`:""}></line>`:g`<circle class=${C} cx=${$} cy=${v} r=${_} fill="#fff" style=${e?`--fall-from:-${t.h}px;--fall-to:${t.h}px;--fall-speed:${k};animation-delay:${R}`:""}></circle>`)}}let j=[];if(s.clouds==="few"){let f=[{x:.18,y:.18},{x:.68,y:.28}];for(let p of f){let $=t.x+p.x*t.w,v=t.y+p.y*t.h;j.push(g`<g class=${e?"cloud drift":"cloud"} opacity="0.95">
        <ellipse cx=${$-8} cy=${v} rx="10" ry="5" fill="#fff"></ellipse>
        <ellipse cx=${$+2} cy=${v-4} rx="12" ry="8" fill="#fff"></ellipse>
        <ellipse cx=${$+14} cy=${v} rx="11" ry="5" fill="#fff"></ellipse>
      </g>`)}}else if(s.clouds==="overcast"){let f=["#90a4ae","#78909c"];for(let p=0;p<4;p++){let $=t.x+(.08+p*.28)*t.w,v=t.y+(.12+p%2*.06)*t.h;j.push(g`<g class=${e?"cloud drift":"cloud"} opacity="0.95">
        <ellipse cx=${$-10} cy=${v} rx="13" ry="7" fill=${f[p%2]}></ellipse>
        <ellipse cx=${$+2} cy=${v-5} rx="16" ry="11" fill=${f[p%2]}></ellipse>
        <ellipse cx=${$+16} cy=${v} rx="14" ry="7" fill=${f[p%2]}></ellipse>
      </g>`)}}return g`
    <defs>
      <linearGradient id=${n} x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color=${s.sky[0]}></stop>
        <stop offset="1" stop-color=${s.sky[1]}></stop>
      </linearGradient>
      <clipPath id=${i}><rect x=${t.x} y=${t.y} width=${t.w} height=${t.h}></rect></clipPath>
    </defs>
    <g class="sky"><rect x=${t.x} y=${t.y} width=${t.w} height=${t.h} fill=${`url(#${n})`}></rect></g>
    ${s.stars>0&&s.clouds!=="overcast"?g`<g class="stars" opacity=${s.stars}>${l}</g>`:""}
    ${s.moon?g`<g class="moon">
      <circle cx=${t.x+s.moon.x*t.w} cy=${t.y+s.moon.y*t.h} r=${.095*t.w} fill="#fff8e1" opacity="0.15"></circle>
      ${We(t.x+s.moon.x*t.w,t.y+s.moon.y*t.h,.07*t.w,s.moon.phase)}
    </g>`:""}
    ${s.sun?g`<g class="sun">
      <circle cx=${t.x+s.sun.x*t.w} cy=${t.y+s.sun.y*t.h} r=${.13*t.w} fill="#ffd54f" opacity="0.25"></circle>
      <circle class="sun-disc" cx=${t.x+s.sun.x*t.w} cy=${t.y+s.sun.y*t.h} r=${.08*t.w} fill="#ffd54f"></circle>
    </g>`:""}
    ${s.clouds!=="none"?g`<g class="clouds">${j}</g>`:""}
    <g class="land" style=${s.dim>0?`filter: brightness(${(1-s.dim).toFixed(2)})`:""}>
      <path class="hill" d=${c} fill=${a}></path>
      ${u}
    </g>
    ${s.precipitation!=="none"?g`<g class="precip" clip-path=${`url(#${i})`}>${x}</g>`:""}
    ${s.fog?g`<g class="fog">
      <ellipse cx=${t.x+.2*t.w} cy=${t.y+.82*t.h} rx=${.25*t.w} ry=${.05*t.h} fill="#fff" opacity="0.5"></ellipse>
      <ellipse cx=${t.x+.58*t.w} cy=${t.y+.88*t.h} rx=${.32*t.w} ry=${.06*t.h} fill="#fff" opacity="0.5"></ellipse>
      <ellipse cx=${t.x+.9*t.w} cy=${t.y+.78*t.h} rx=${.2*t.w} ry=${.04*t.h} fill="#fff" opacity="0.5"></ellipse>
    </g>`:""}
    ${s.lightning&&e?g`<g class="lightning"><polyline class="flash" points=${`${t.x+.72*t.w},${t.y+.08*t.h} ${t.x+.68*t.w},${t.y+.25*t.h} ${t.x+.74*t.w},${t.y+.22*t.h} ${t.x+.69*t.w},${t.y+.42*t.h}`} fill="none" stroke="#ffd54f" stroke-width="2"></polyline></g>`:""}
  `}var fe="ssc-drawing",Ot=262,G={top:40,bottom:241},Fe={x:64,y:40,w:156,h:206},qe=4,V=class extends b{constructor(){super(...arguments);this.position=null;this.max=100;this.moving=null;this.gaps=!1;this.scene=null;this.animated=!1;this.storm=!1;this.compact=!1;this.interactive=!1;this.label="";this.maxLabel="max";this._drag=null;this.startY=null;this.moved=!1}viewY(e){let n=this.renderRoot.querySelector("svg")?.getBoundingClientRect();return!n||!n.height?null:(e.clientY-n.top)/n.height*Ot}onDown(e){this.interactive&&(e.currentTarget.setPointerCapture?.(e.pointerId),this.startY=e.clientY,this.moved=!1,e.preventDefault())}onMove(e){if(this.startY===null||!this.moved&&Math.abs(e.clientY-this.startY)<qe)return;this.moved=!0;let n=this.viewY(e);n!==null&&(this._drag=Nt(he(n,G),this.storm))}onUp(e){this.startY!==null&&(this.onMove(e),this.startY=null,this.moved&&this.send(),this._drag=null)}onCancel(){this.startY=null,this._drag=null}onKey(e){if(!this.interactive)return;let n=this._drag??this.position??0,i={ArrowUp:n+5,ArrowDown:n-5,PageUp:n+25,PageDown:n-25,Home:100,End:0};e.key in i?(this._drag=this.storm?i[e.key]>n?100:0:Nt(i[e.key],!1),e.preventDefault()):e.key==="Enter"&&this._drag!==null?(this.send(),this._drag=null,e.preventDefault()):e.key==="Escape"&&(this._drag=null)}send(){this._drag!==null&&this.dispatchEvent(new CustomEvent("set-position",{detail:{position:this._drag},bubbles:!0,composed:!0}))}render(){let e=this.position??0,i=st(e,G)-G.bottom,r=this.interactive&&!this.compact,o=st(this.max,G),l=this.compact?`46 0 192 ${Ot}`:`-16 0 256 ${Ot}`;return w`<svg
      class=${this.interactive?"interactive":""}
      viewBox=${l}
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
      ${this.scene?g`<g class="view" clip-path="url(#glass-clip)">${de(this.scene,Fe,this.animated&&!this.compact)}</g>`:""}
      <rect x="58" y="40" width="6" height="206" fill="var(--ssc-slat-2)"></rect>
      <rect x="220" y="40" width="6" height="206" fill="var(--ssc-slat-2)"></rect>
      <g clip-path="url(#opening)">
        <g class="curtain" style=${`transform: translateY(${i}px)`}>
          <rect class="slats ${this.gaps?"open":"closed"}" x="64" y="-170" width="156" height="406" fill=${this.gaps?"url(#slats-open)":"url(#slats)"}></rect>
          <rect class="bar" x="60" y="236" width="164" height="10" rx="3" fill="var(--ssc-bar)"></rect>
          ${r?g`<rect x="124" y="230" width="36" height="22" rx="11" fill="var(--ssc-accent)" stroke="#fff" stroke-width="2"></rect>
                 <line x1="134" y1="238" x2="150" y2="238" stroke="#fff" stroke-width="2"></line>
                 <line x1="134" y1="244" x2="150" y2="244" stroke="#fff" stroke-width="2"></line>`:""}
        </g>
      </g>
      <rect x="46" y="6" width="192" height="34" rx="6" fill="var(--ssc-box)" stroke="var(--ssc-frame)" stroke-width="3"></rect>
      ${this.moving?g`<path class="moving" d=${this.moving==="opening"?"M142 15 l8 10 h-16 z":"M142 31 l8 -10 h-16 z"} fill="var(--ssc-accent)"></path>`:""}
      ${this.max<100?g`<line class="max" x1=${this.compact?46:28} x2=${this.compact?58:46} y1=${o} y2=${o} stroke="var(--ssc-max)" stroke-width="3"></line>
             ${this.compact?"":g`<text x="46" y=${o+15} font-size="11" text-anchor="end" fill="var(--ssc-max)">${this.maxLabel} ${this.max} %</text>`}`:""}
      ${this._drag!==null?g`<g class="target">
            <rect x="60" y=${st(this._drag,G)-5} width="164" height="10" rx="3" fill="var(--ssc-accent)" opacity="0.45"></rect>
            <text x="142" y=${st(this._drag,G)-10} font-size="16" font-weight="700" text-anchor="middle" fill="var(--ssc-accent)">${this._drag} %</text>
          </g>`:""}
    </svg>`}};V.properties={position:{type:Number},max:{type:Number},moving:{type:String},gaps:{type:Boolean},scene:{attribute:!1},animated:{type:Boolean},storm:{type:Boolean},compact:{type:Boolean},interactive:{type:Boolean},label:{type:String},maxLabel:{type:String},_drag:{state:!0}},V.styles=[pe,T`
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
  `];function Ke(s){return[{name:"device_id",selector:{device:{integration:J}}},{name:"language",selector:{select:{mode:"dropdown",options:[{value:"auto",label:s("language_auto")},...ne.map(t=>({value:t,label:t==="nl"?"Nederlands":"English"}))]}}}]}var nt=class extends b{setConfig(t){this._config=t}changed(t){let e={...t.detail.value};(!e.language||e.language==="auto")&&delete e.language,this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:e},bubbles:!0,composed:!0}))}render(){if(!this.hass||!this._config)return w``;let t=Q(this._config.language||this.hass.locale?.language);return w`<ha-form
      .hass=${this.hass}
      .data=${{...this._config,language:this._config.language||"auto"}}
      .schema=${Ke(t)}
      .computeLabel=${e=>t(e.name)}
      @value-changed=${this.changed}
    ></ha-form>`}};nt.properties={hass:{attribute:!1},_config:{state:!0}};function Ht(s,t){customElements.get(s)||customElements.define(s,t)}Ht(fe,V);Ht(Rt,nt);Ht(et,B);var ut=window;ut.customCards=ut.customCards??[];ut.customCards.some(s=>s.type===et)||ut.customCards.push({type:et,name:"Smart Shutter",description:"A shutter you can drag to a position, with buttons and its status; or all shutters of a base controller.",preview:!0,documentationURL:"https://github.com/abroeders/smart-shutter-control/blob/main/docs/card.md"});
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
