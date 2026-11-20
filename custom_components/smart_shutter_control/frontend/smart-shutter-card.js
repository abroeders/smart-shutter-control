var Y=globalThis,W=Y.ShadowRoot&&(Y.ShadyCSS===void 0||Y.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,X=Symbol(),xt=new WeakMap,N=class{constructor(t,e,s){if(this._$cssResult$=!0,s!==X)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e}get styleSheet(){let t=this.o,e=this.t;if(W&&t===void 0){let s=e!==void 0&&e.length===1;s&&(t=xt.get(e)),t===void 0&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),s&&xt.set(e,t))}return t}toString(){return this.cssText}},yt=i=>new N(typeof i=="string"?i:i+"",void 0,X),P=(i,...t)=>{let e=i.length===1?i[0]:t.reduce((s,n,r)=>s+(o=>{if(o._$cssResult$===!0)return o.cssText;if(typeof o=="number")return o;throw Error("Value passed to 'css' function must be a 'css' function result: "+o+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(n)+i[r+1],i[0]);return new N(e,i,X)},wt=(i,t)=>{if(W)i.adoptedStyleSheets=t.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet);else for(let e of t){let s=document.createElement("style"),n=Y.litNonce;n!==void 0&&s.setAttribute("nonce",n),s.textContent=e.cssText,i.appendChild(s)}},Q=W?i=>i:i=>i instanceof CSSStyleSheet?(t=>{let e="";for(let s of t.cssRules)e+=s.cssText;return yt(e)})(i):i;var{is:Wt,defineProperty:Ft,getOwnPropertyDescriptor:Kt,getOwnPropertyNames:qt,getOwnPropertySymbols:Zt,getPrototypeOf:Jt}=Object,F=globalThis,At=F.trustedTypes,Xt=At?At.emptyScript:"",Qt=F.reactiveElementPolyfillSupport,T=(i,t)=>i,tt={toAttribute(i,t){switch(t){case Boolean:i=i?Xt:null;break;case Object:case Array:i=i==null?i:JSON.stringify(i)}return i},fromAttribute(i,t){let e=i;switch(t){case Boolean:e=i!==null;break;case Number:e=i===null?null:Number(i);break;case Object:case Array:try{e=JSON.parse(i)}catch{e=null}}return e}},St=(i,t)=>!Wt(i,t),Et={attribute:!0,type:String,converter:tt,reflect:!1,useDefault:!1,hasChanged:St};Symbol.metadata??=Symbol("metadata"),F.litPropertyMetadata??=new WeakMap;var _=class extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??=[]).push(t)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,e=Et){if(e.state&&(e.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(t)&&((e=Object.create(e)).wrapped=!0),this.elementProperties.set(t,e),!e.noAccessor){let s=Symbol(),n=this.getPropertyDescriptor(t,s,e);n!==void 0&&Ft(this.prototype,t,n)}}static getPropertyDescriptor(t,e,s){let{get:n,set:r}=Kt(this.prototype,t)??{get(){return this[e]},set(o){this[e]=o}};return{get:n,set(o){let l=n?.call(this);r?.call(this,o),this.requestUpdate(t,l,s)},configurable:!0,enumerable:!0}}static getPropertyOptions(t){return this.elementProperties.get(t)??Et}static _$Ei(){if(this.hasOwnProperty(T("elementProperties")))return;let t=Jt(this);t.finalize(),t.l!==void 0&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties)}static finalize(){if(this.hasOwnProperty(T("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(T("properties"))){let e=this.properties,s=[...qt(e),...Zt(e)];for(let n of s)this.createProperty(n,e[n])}let t=this[Symbol.metadata];if(t!==null){let e=litPropertyMetadata.get(t);if(e!==void 0)for(let[s,n]of e)this.elementProperties.set(s,n)}this._$Eh=new Map;for(let[e,s]of this.elementProperties){let n=this._$Eu(e,s);n!==void 0&&this._$Eh.set(n,e)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(t){let e=[];if(Array.isArray(t)){let s=new Set(t.flat(1/0).reverse());for(let n of s)e.unshift(Q(n))}else t!==void 0&&e.push(Q(t));return e}static _$Eu(t,e){let s=e.attribute;return s===!1?void 0:typeof s=="string"?s:typeof t=="string"?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(t=>this.enableUpdating=t),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(t=>t(this))}addController(t){(this._$EO??=new Set).add(t),this.renderRoot!==void 0&&this.isConnected&&t.hostConnected?.()}removeController(t){this._$EO?.delete(t)}_$E_(){let t=new Map,e=this.constructor.elementProperties;for(let s of e.keys())this.hasOwnProperty(s)&&(t.set(s,this[s]),delete this[s]);t.size>0&&(this._$Ep=t)}createRenderRoot(){let t=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return wt(t,this.constructor.elementStyles),t}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(t=>t.hostConnected?.())}enableUpdating(t){}disconnectedCallback(){this._$EO?.forEach(t=>t.hostDisconnected?.())}attributeChangedCallback(t,e,s){this._$AK(t,s)}_$ET(t,e){let s=this.constructor.elementProperties.get(t),n=this.constructor._$Eu(t,s);if(n!==void 0&&s.reflect===!0){let r=(s.converter?.toAttribute!==void 0?s.converter:tt).toAttribute(e,s.type);this._$Em=t,r==null?this.removeAttribute(n):this.setAttribute(n,r),this._$Em=null}}_$AK(t,e){let s=this.constructor,n=s._$Eh.get(t);if(n!==void 0&&this._$Em!==n){let r=s.getPropertyOptions(n),o=typeof r.converter=="function"?{fromAttribute:r.converter}:r.converter?.fromAttribute!==void 0?r.converter:tt;this._$Em=n;let l=o.fromAttribute(e,r.type);this[n]=l??this._$Ej?.get(n)??l,this._$Em=null}}requestUpdate(t,e,s,n=!1,r){if(t!==void 0){let o=this.constructor;if(n===!1&&(r=this[t]),s??=o.getPropertyOptions(t),!((s.hasChanged??St)(r,e)||s.useDefault&&s.reflect&&r===this._$Ej?.get(t)&&!this.hasAttribute(o._$Eu(t,s))))return;this.C(t,e,s)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(t,e,{useDefault:s,reflect:n,wrapped:r},o){s&&!(this._$Ej??=new Map).has(t)&&(this._$Ej.set(t,o??e??this[t]),r!==!0||o!==void 0)||(this._$AL.has(t)||(this.hasUpdated||s||(e=void 0),this._$AL.set(t,e)),n===!0&&this._$Em!==t&&(this._$Eq??=new Set).add(t))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(e){Promise.reject(e)}let t=this.scheduleUpdate();return t!=null&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[n,r]of this._$Ep)this[n]=r;this._$Ep=void 0}let s=this.constructor.elementProperties;if(s.size>0)for(let[n,r]of s){let{wrapped:o}=r,l=this[n];o!==!0||this._$AL.has(n)||l===void 0||this.C(n,void 0,r,l)}}let t=!1,e=this._$AL;try{t=this.shouldUpdate(e),t?(this.willUpdate(e),this._$EO?.forEach(s=>s.hostUpdate?.()),this.update(e)):this._$EM()}catch(s){throw t=!1,this._$EM(),s}t&&this._$AE(e)}willUpdate(t){}_$AE(t){this._$EO?.forEach(e=>e.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(t)),this.updated(t)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return!0}update(t){this._$Eq&&=this._$Eq.forEach(e=>this._$ET(e,this[e])),this._$EM()}updated(t){}firstUpdated(t){}};_.elementStyles=[],_.shadowRootOptions={mode:"open"},_[T("elementProperties")]=new Map,_[T("finalized")]=new Map,Qt?.({ReactiveElement:_}),(F.reactiveElementVersions??=[]).push("2.1.2");var at=globalThis,Ct=i=>i,K=at.trustedTypes,kt=K?K.createPolicy("lit-html",{createHTML:i=>i}):void 0,Ot="$lit$",v=`lit$${Math.random().toFixed(9).slice(2)}$`,Rt="?"+v,te=`<${Rt}>`,x=document,R=()=>x.createComment(""),U=i=>i===null||typeof i!="object"&&typeof i!="function",lt=Array.isArray,ee=i=>lt(i)||typeof i?.[Symbol.iterator]=="function",et=`[ 	
\f\r]`,O=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,Mt=/-->/g,Ht=/>/g,$=RegExp(`>|${et}(?:([^\\s"'>=/]+)(${et}*=${et}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),Nt=/'/g,Pt=/"/g,Ut=/^(?:script|style|textarea|title)$/i,ct=i=>(t,...e)=>({_$litType$:i,strings:t,values:e}),u=ct(1),S=ct(2),ge=ct(3),y=Symbol.for("lit-noChange"),p=Symbol.for("lit-nothing"),Tt=new WeakMap,b=x.createTreeWalker(x,129);function Lt(i,t){if(!lt(i)||!i.hasOwnProperty("raw"))throw Error("invalid template strings array");return kt!==void 0?kt.createHTML(t):t}var se=(i,t)=>{let e=i.length-1,s=[],n,r=t===2?"<svg>":t===3?"<math>":"",o=O;for(let l=0;l<e;l++){let a=i[l],c,h,d=-1,m=0;for(;m<a.length&&(o.lastIndex=m,h=o.exec(a),h!==null);)m=o.lastIndex,o===O?h[1]==="!--"?o=Mt:h[1]!==void 0?o=Ht:h[2]!==void 0?(Ut.test(h[2])&&(n=RegExp("</"+h[2],"g")),o=$):h[3]!==void 0&&(o=$):o===$?h[0]===">"?(o=n??O,d=-1):h[1]===void 0?d=-2:(d=o.lastIndex-h[2].length,c=h[1],o=h[3]===void 0?$:h[3]==='"'?Pt:Nt):o===Pt||o===Nt?o=$:o===Mt||o===Ht?o=O:(o=$,n=void 0);let g=o===$&&i[l+1].startsWith("/>")?" ":"";r+=o===O?a+te:d>=0?(s.push(c),a.slice(0,d)+Ot+a.slice(d)+v+g):a+v+(d===-2?l:g)}return[Lt(i,r+(i[e]||"<?>")+(t===2?"</svg>":t===3?"</math>":"")),s]},L=class i{constructor({strings:t,_$litType$:e},s){let n;this.parts=[];let r=0,o=0,l=t.length-1,a=this.parts,[c,h]=se(t,e);if(this.el=i.createElement(c,s),b.currentNode=this.el.content,e===2||e===3){let d=this.el.content.firstChild;d.replaceWith(...d.childNodes)}for(;(n=b.nextNode())!==null&&a.length<l;){if(n.nodeType===1){if(n.hasAttributes())for(let d of n.getAttributeNames())if(d.endsWith(Ot)){let m=h[o++],g=n.getAttribute(d).split(v),V=/([.?@])?(.*)/.exec(m);a.push({type:1,index:r,name:V[2],strings:g,ctor:V[1]==="."?it:V[1]==="?"?nt:V[1]==="@"?rt:E}),n.removeAttribute(d)}else d.startsWith(v)&&(a.push({type:6,index:r}),n.removeAttribute(d));if(Ut.test(n.tagName)){let d=n.textContent.split(v),m=d.length-1;if(m>0){n.textContent=K?K.emptyScript:"";for(let g=0;g<m;g++)n.append(d[g],R()),b.nextNode(),a.push({type:2,index:++r});n.append(d[m],R())}}}else if(n.nodeType===8)if(n.data===Rt)a.push({type:2,index:r});else{let d=-1;for(;(d=n.data.indexOf(v,d+1))!==-1;)a.push({type:7,index:r}),d+=v.length-1}r++}}static createElement(t,e){let s=x.createElement("template");return s.innerHTML=t,s}};function A(i,t,e=i,s){if(t===y)return t;let n=s!==void 0?e._$Co?.[s]:e._$Cl,r=U(t)?void 0:t._$litDirective$;return n?.constructor!==r&&(n?._$AO?.(!1),r===void 0?n=void 0:(n=new r(i),n._$AT(i,e,s)),s!==void 0?(e._$Co??=[])[s]=n:e._$Cl=n),n!==void 0&&(t=A(i,n._$AS(i,t.values),n,s)),t}var st=class{constructor(t,e){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=e}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){let{el:{content:e},parts:s}=this._$AD,n=(t?.creationScope??x).importNode(e,!0);b.currentNode=n;let r=b.nextNode(),o=0,l=0,a=s[0];for(;a!==void 0;){if(o===a.index){let c;a.type===2?c=new D(r,r.nextSibling,this,t):a.type===1?c=new a.ctor(r,a.name,a.strings,this,t):a.type===6&&(c=new ot(r,this,t)),this._$AV.push(c),a=s[++l]}o!==a?.index&&(r=b.nextNode(),o++)}return b.currentNode=x,n}p(t){let e=0;for(let s of this._$AV)s!==void 0&&(s.strings!==void 0?(s._$AI(t,s,e),e+=s.strings.length-2):s._$AI(t[e])),e++}},D=class i{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(t,e,s,n){this.type=2,this._$AH=p,this._$AN=void 0,this._$AA=t,this._$AB=e,this._$AM=s,this.options=n,this._$Cv=n?.isConnected??!0}get parentNode(){let t=this._$AA.parentNode,e=this._$AM;return e!==void 0&&t?.nodeType===11&&(t=e.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,e=this){t=A(this,t,e),U(t)?t===p||t==null||t===""?(this._$AH!==p&&this._$AR(),this._$AH=p):t!==this._$AH&&t!==y&&this._(t):t._$litType$!==void 0?this.$(t):t.nodeType!==void 0?this.T(t):ee(t)?this.k(t):this._(t)}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t))}_(t){this._$AH!==p&&U(this._$AH)?this._$AA.nextSibling.data=t:this.T(x.createTextNode(t)),this._$AH=t}$(t){let{values:e,_$litType$:s}=t,n=typeof s=="number"?this._$AC(t):(s.el===void 0&&(s.el=L.createElement(Lt(s.h,s.h[0]),this.options)),s);if(this._$AH?._$AD===n)this._$AH.p(e);else{let r=new st(n,this),o=r.u(this.options);r.p(e),this.T(o),this._$AH=r}}_$AC(t){let e=Tt.get(t.strings);return e===void 0&&Tt.set(t.strings,e=new L(t)),e}k(t){lt(this._$AH)||(this._$AH=[],this._$AR());let e=this._$AH,s,n=0;for(let r of t)n===e.length?e.push(s=new i(this.O(R()),this.O(R()),this,this.options)):s=e[n],s._$AI(r),n++;n<e.length&&(this._$AR(s&&s._$AB.nextSibling,n),e.length=n)}_$AR(t=this._$AA.nextSibling,e){for(this._$AP?.(!1,!0,e);t!==this._$AB;){let s=Ct(t).nextSibling;Ct(t).remove(),t=s}}setConnected(t){this._$AM===void 0&&(this._$Cv=t,this._$AP?.(t))}},E=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,e,s,n,r){this.type=1,this._$AH=p,this._$AN=void 0,this.element=t,this.name=e,this._$AM=n,this.options=r,s.length>2||s[0]!==""||s[1]!==""?(this._$AH=Array(s.length-1).fill(new String),this.strings=s):this._$AH=p}_$AI(t,e=this,s,n){let r=this.strings,o=!1;if(r===void 0)t=A(this,t,e,0),o=!U(t)||t!==this._$AH&&t!==y,o&&(this._$AH=t);else{let l=t,a,c;for(t=r[0],a=0;a<r.length-1;a++)c=A(this,l[s+a],e,a),c===y&&(c=this._$AH[a]),o||=!U(c)||c!==this._$AH[a],c===p?t=p:t!==p&&(t+=(c??"")+r[a+1]),this._$AH[a]=c}o&&!n&&this.j(t)}j(t){t===p?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"")}},it=class extends E{constructor(){super(...arguments),this.type=3}j(t){this.element[this.name]=t===p?void 0:t}},nt=class extends E{constructor(){super(...arguments),this.type=4}j(t){this.element.toggleAttribute(this.name,!!t&&t!==p)}},rt=class extends E{constructor(t,e,s,n,r){super(t,e,s,n,r),this.type=5}_$AI(t,e=this){if((t=A(this,t,e,0)??p)===y)return;let s=this._$AH,n=t===p&&s!==p||t.capture!==s.capture||t.once!==s.once||t.passive!==s.passive,r=t!==p&&(s===p||n);n&&this.element.removeEventListener(this.name,this,s),r&&this.element.addEventListener(this.name,this,t),this._$AH=t}handleEvent(t){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,t):this._$AH.handleEvent(t)}},ot=class{constructor(t,e,s){this.element=t,this.type=6,this._$AN=void 0,this._$AM=e,this.options=s}get _$AU(){return this._$AM._$AU}_$AI(t){A(this,t)}};var ie=at.litHtmlPolyfillSupport;ie?.(L,D),(at.litHtmlVersions??=[]).push("3.3.3");var Dt=(i,t,e)=>{let s=e?.renderBefore??t,n=s._$litPart$;if(n===void 0){let r=e?.renderBefore??null;s._$litPart$=n=new D(t.insertBefore(R(),r),r,void 0,e??{})}return n._$AI(i),n};var ht=globalThis,f=class extends _{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let t=super.createRenderRoot();return this.renderOptions.renderBefore??=t.firstChild,t}update(t){let e=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=Dt(e,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return y}};f._$litElement$=!0,f.finalized=!0,ht.litElementHydrateSupport?.({LitElement:f});var ne=ht.litElementPolyfillSupport;ne?.({LitElement:f});(ht.litElementVersions??=[]).push("4.2.2");var z="smart_shutter_control";function w(i,t){let e={};for(let s of Object.values(i.entities??{}))s.platform===z&&s.device_id===t&&s.translation_key&&(e[s.translation_key]=s.entity_id);return e}function C(i,t){return"shutter"in w(i,t)}function q(i,t){let e=i.devices?.[t];return e?.name_by_user||e?.name||t}function dt(i){let t=new Set;for(let e of Object.values(i.entities??{}))e.platform===z&&e.device_id&&t.add(e.device_id);return[...t].sort((e,s)=>Number(C(i,e))-Number(C(i,s))||q(i,e).localeCompare(q(i,s)))}function zt(i,t){return dt(i).filter(e=>i.devices?.[e]?.via_device_id===t&&C(i,e))}function Bt(i,t){return i.devices?.[t]?.via_device_id??void 0}var It={open:"open",closed:"closed",slit:"slit",partly_open:"partly open",automatic:"Automatic",manual_pause:"Manual",off:"Off",storm_chip:"Storm: only open/closed",frost_chip:"Frost: no moves",sleep_in:"Sleep in",sleep_in_all:"Sleep in (all)",next:"Next",then:"then",until:"until",next_phase:"the next phase",resume:"Resume",open_cover:"Open",stop_cover:"Stop",close_cover:"Close",all_shutters:"All shutters",no_device:"Choose a shutter or a base controller of Smart Shutter Control.",not_found:"Device not found",max:"max",position:"Position",device_id:"Device",language:"Language",language_auto:"Integration setting",reason_idle:"No action",reason_off:"Automatic control off",reason_manual:"Manual",reason_calibrating:"Calibrating",reason_sun:"Sun on the window",reason_schedule:"Schedule",reason_sleep_in:"Sleeping in",reason_storm:"Storm",reason_frost:"Frost",reason_heat_limit:"Too warm",reason_cold_limit:"Too cold",reason_winter:"Winter",phase_night:"night",phase_slit:"slit",phase_day:"day",phase_dusk:"dusk"},re={open:"open",closed:"dicht",slit:"spleetstand",partly_open:"deels open",automatic:"Automatisch",manual_pause:"Handbediening",off:"Uit",storm_chip:"Storm: alleen open/dicht",frost_chip:"Vorst: geen bewegingen",sleep_in:"Uitslapen",sleep_in_all:"Uitslapen (alle)",next:"Volgende",then:"daarna",until:"tot",next_phase:"de volgende fase",resume:"Hervatten",open_cover:"Open",stop_cover:"Stop",close_cover:"Dicht",all_shutters:"Alle rolluiken",no_device:"Kies een rolluik of een basiscontroller van Smart Shutter Control.",not_found:"Apparaat niet gevonden",max:"max",position:"Stand",device_id:"Apparaat",language:"Taal",language_auto:"Instelling van de integratie",reason_idle:"Geen actie",reason_off:"Automaat uit",reason_manual:"Handbediening",reason_calibrating:"Kalibreren",reason_sun:"Zon op het raam",reason_schedule:"Schema",reason_sleep_in:"Uitslapen",reason_storm:"Storm",reason_frost:"Vorst",reason_heat_limit:"Te warm",reason_cold_limit:"Te koud",reason_winter:"Winter",phase_night:"nacht",phase_slit:"spleet",phase_day:"dag",phase_dusk:"schemer"};function B(i){let t=i?.toLowerCase().startsWith("nl")?re:It;return e=>t[e]??It[e]??e}var jt=["en","nl"];var pt=i=>i==null||i===""||isNaN(Number(i))?null:Number(i);function ut(i,t){let e=w(i,t),s=g=>e[g]?i.states[e[g]]:void 0,n=Bt(i,t),r=n?w(i,n):{},o=g=>g?i.states[g]?.state==="on":!1,l=s("shutter"),a=s("reason"),c=s("next_action"),h=[];if(c&&!["unknown","unavailable"].includes(c.state)&&c.attributes.phase){h.push({at:c.state,phase:c.attributes.phase,position:c.attributes.position});for(let g of c.attributes.following??[])h.push({at:g.at,phase:g.phase,position:g.position})}let d=s("manual_pause"),m=l?.state;return{deviceId:t,name:q(i,t),entities:e,position:pt(l?.attributes.current_position),moving:m==="opening"||m==="closing"?m:null,closed:m==="closed",stand:s("stand")?.state??null,reason:a?.state??null,target:pt(a?.attributes.target_position),max:pt(a?.attributes.max_position)??100,phase:s("phase")?.state??null,automatic:s("automatic")?.state!=="off",sleepIn:o(e.sleep_in),paused:o(e.manual_pause),pausedUntil:d?.attributes.until??null,next:h,storm:o(r.storm),frost:o(r.frost),language:a?.attributes.language??null}}function gt(i,t,e){return t||e?.language||i.locale?.language||i.language||"en"}function Gt(i,t,e){let s=new Date(i);if(isNaN(s.getTime()))return"";try{return new Intl.DateTimeFormat(e,{hour:"2-digit",minute:"2-digit",hour12:!1,timeZone:t.config?.time_zone}).format(s)}catch{return new Intl.DateTimeFormat(e,{hour:"2-digit",minute:"2-digit",hour12:!1}).format(s)}}function Z(i,t){return i===null?"\u2013":i==="slit"?t("slit"):i<=0?t("closed"):i>=100?t("open"):`${i}\xA0%`}function mt(i,t,e){let s=i.stand&&!["unknown","unavailable"].includes(i.stand)?t(i.stand):"",n=i.reason?t(`reason_${i.reason}`):"",r="";if(i.paused){let c=i.pausedUntil==="next phase"||!i.pausedUntil?t("next_phase"):e(i.pausedUntil);r=`${t("until")} ${c}`}else i.target!==null&&(r=[i.position!==null&&Math.abs(i.target-i.position)>1?`\u2192 ${Z(i.target,t)}`:"",i.phase?t(`phase_${i.phase}`):""].filter(Boolean).join(" \xB7 "));let o=c=>[e(c.at),c.phase==="dusk"?t("phase_dusk"):"",Z(c.position,t)].filter(Boolean).join(" "),[l,a]=i.next;return{stand:s,reason:n,detail:r,next:l?`${t("next")}: ${o(l)}`:null,then:a?`${t("then")} ${o(a)}`:null,chip:i.automatic?i.paused?"manual_pause":"automatic":"off"}}var I="smart-shutter-card",ft="smart-shutter-card-editor",oe=360,ae={up:"M13,20H11V8L5.5,13.5L4.08,12.08L12,4.16L19.92,12.08L18.5,13.5L13,8V20Z",stop:"M18,18H6V6H18V18Z",down:"M11,4H13V16L18.5,10.5L19.92,11.92L12,19.84L4.08,11.92L5.5,10.5L11,16V4Z"},k=class extends f{constructor(){super(...arguments);this._narrow=!1}static getConfigElement(){return document.createElement(ft)}static getStubConfig(e){return{type:`custom:${I}`,device_id:dt(e)[0]}}setConfig(e){if(!e)throw new Error("Invalid configuration");this._config={...e}}getCardSize(){return 6}getGridOptions(){return{columns:!!(this.hass&&this._config?.device_id&&!C(this.hass,this._config.device_id))?"full":12,min_columns:6,rows:"auto"}}connectedCallback(){super.connectedCallback(),typeof ResizeObserver<"u"&&(this.observer=new ResizeObserver(e=>{let s=e[0]?.contentRect.width??0;s&&(this._narrow=s<oe)}),this.observer.observe(this))}disconnectedCallback(){super.disconnectedCallback(),this.observer?.disconnect()}call(e,s,n,r={}){!this.hass||!n||this.hass.callService(e,s,{entity_id:n,...r})}toggle(e,s){this.call(e?.split(".")[0]??"switch",s?"turn_off":"turn_on",e)}moreInfo(e){e&&this.dispatchEvent(new CustomEvent("hass-more-info",{detail:{entityId:e},bubbles:!0,composed:!0}))}render(){let e=this.hass,s=this._config?.device_id;if(!e||!this._config)return p;let n=B(gt(e,this._config.language));return s?!e.devices?.[s]&&!Object.keys(w(e,s)).length?u`<ha-card><div class="message">${n("not_found")}: ${s}</div></ha-card>`:C(e,s)?this.renderShutter(e,s):this.renderOverview(e,s):u`<ha-card><div class="message">${n("no_device")}</div></ha-card>`}texts(e,s){let n=gt(e,this._config?.language,s);return{t:B(n),time:r=>Gt(r,e,n),lang:n}}buttons(e,s,n=!1){let r=e.entities.shutter,o=(l,a,c)=>u`<button class="round ${n?"small":""}" title=${c} aria-label=${c} @click=${h=>{h.stopPropagation(),this.call("cover",a,r)}}>
        <svg viewBox="0 0 24 24"><path d=${ae[l]}></path></svg>
      </button>`;return u`${o("up","open_cover",s("open_cover"))}${o("stop","stop_cover",s("stop_cover"))}${o("down","close_cover",s("close_cover"))}`}switch(e,s,n,r){return s?u`<button class="switch ${r}" role="switch" aria-checked=${n?"true":"false"} @click=${()=>this.toggle(s,n)}>
      <span class="track ${n?"on":""}"><span class="knob"></span></span>${e}
    </button>`:p}warnings(e,s,n){return u`${e?u`<span class="chip warn storm">⚠ ${n("storm_chip")}</span>`:p}${s?u`<span class="chip warn frost">❄ ${n("frost_chip")}</span>`:p}`}renderShutter(e,s){let n=ut(e,s),{t:r,time:o}=this.texts(e,n),l=mt(n,r,o),a=!!e.themes?.darkMode;return u`<ha-card class=${this._narrow?"narrow":""}>
      <div class="head">
        <div class="name">${n.name}</div>
        <div class="chips"><span class="chip ${l.chip}">${r(l.chip)}</span>${this.warnings(n.storm,n.frost,r)}</div>
      </div>
      <div class="body">
        <ssc-drawing
          ?dark=${a}
          .position=${n.position}
          .max=${n.max}
          .moving=${n.moving}
          .gaps=${!n.closed}
          .storm=${n.storm}
          .interactive=${!!n.entities.shutter}
          .label=${`${n.name}: ${r("position")}`}
          .maxLabel=${r("max")}
          @set-position=${c=>this.call("cover","set_cover_position",n.entities.shutter,{position:c.detail.position})}
        ></ssc-drawing>
        <div class="buttons">${this.buttons(n,r)}</div>
        <div class="status">
          <div class="big">${n.position===null?"\u2013":`${n.position}\xA0%`}</div>
          <div class="sub">${l.stand}</div>
          <div class="line reason">${l.reason}</div>
          <div class="sub">${l.detail}</div>
          ${l.next?u`<div class="line next">${l.next}</div>`:p}
          ${l.then?u`<div class="sub then">${l.then}</div>`:p}
        </div>
      </div>
      <div class="switches">
        ${this.switch(r("automatic"),n.entities.automatic,n.automatic,"automatic")}
        ${this.switch(r("sleep_in"),n.entities.sleep_in,n.sleepIn,"sleep-in")}
        ${n.paused&&n.entities.resume?u`<button class="text resume" @click=${()=>this.call("button","press",n.entities.resume)}>${r("resume")}</button>`:p}
      </div>
    </ha-card>`}renderOverview(e,s){let n=zt(e,s).map(h=>ut(e,h)),{t:r,time:o}=this.texts(e,n[0]??null),l=w(e,s),a=h=>l[h]?e.states[l[h]]?.state==="on":!1,c=!!e.themes?.darkMode;return u`<ha-card class="overview">
      <div class="head">
        <div class="name">${r("all_shutters")}</div>
        <div class="chips">${this.warnings(a("storm"),a("frost"),r)}</div>
      </div>
      <div class="grid">
        ${n.map(h=>{let d=mt(h,r,o),m=[h.position===null?"\u2013":Z(h.position,r),d.reason].filter(Boolean).join(" \xB7 ");return u`<div class="tile" @click=${()=>this.moreInfo(h.entities.shutter)}>
            <ssc-drawing compact ?dark=${c} .position=${h.position} .max=${h.max} .moving=${h.moving} .gaps=${!h.closed}></ssc-drawing>
            <div class="tile-text">
              <div class="tile-name">${h.name}</div>
              <div class="sub ${d.chip==="manual_pause"?"manual":""}">${m}${d.chip==="manual_pause"?` \xB7 ${d.detail}`:""}</div>
              <div class="tile-buttons">${this.buttons(h,r,!0)}</div>
            </div>
          </div>`})}
      </div>
      <div class="switches">${this.switch(r("sleep_in_all"),l.sleep_in_all,a("sleep_in_all"),"sleep-in-all")}</div>
    </ha-card>`}};k.properties={hass:{attribute:!1},_config:{state:!0},_narrow:{state:!0}},k.styles=P`
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
  `;var _t=(i,t,e)=>Math.min(e,Math.max(t,i));function j(i,t){return t.top+(1-_t(i,0,100)/100)*(t.bottom-t.top)}function Vt(i,t){return Math.round(_t((t.bottom-i)/(t.bottom-t.top),0,1)*100)}function vt(i,t){let e=_t(Math.round(i),0,100);return t?e>=50?100:0:e}var Yt="ssc-drawing",$t=262,M={top:40,bottom:241},le=4,H=class extends f{constructor(){super(...arguments);this.position=null;this.max=100;this.moving=null;this.gaps=!1;this.storm=!1;this.compact=!1;this.interactive=!1;this.label="";this.maxLabel="max";this._drag=null;this.startY=null;this.moved=!1}viewY(e){let s=this.renderRoot.querySelector("svg")?.getBoundingClientRect();return!s||!s.height?null:(e.clientY-s.top)/s.height*$t}onDown(e){this.interactive&&(e.currentTarget.setPointerCapture?.(e.pointerId),this.startY=e.clientY,this.moved=!1,e.preventDefault())}onMove(e){if(this.startY===null||!this.moved&&Math.abs(e.clientY-this.startY)<le)return;this.moved=!0;let s=this.viewY(e);s!==null&&(this._drag=vt(Vt(s,M),this.storm))}onUp(e){this.startY!==null&&(this.onMove(e),this.startY=null,this.moved&&this.send(),this._drag=null)}onCancel(){this.startY=null,this._drag=null}onKey(e){if(!this.interactive)return;let s=this._drag??this.position??0,n={ArrowUp:s+5,ArrowDown:s-5,PageUp:s+25,PageDown:s-25,Home:100,End:0};e.key in n?(this._drag=this.storm?n[e.key]>s?100:0:vt(n[e.key],!1),e.preventDefault()):e.key==="Enter"&&this._drag!==null?(this.send(),this._drag=null,e.preventDefault()):e.key==="Escape"&&(this._drag=null)}send(){this._drag!==null&&this.dispatchEvent(new CustomEvent("set-position",{detail:{position:this._drag},bubbles:!0,composed:!0}))}render(){let e=this.position??0,n=j(e,M)-M.bottom,r=this.interactive&&!this.compact,o=j(this.max,M),l=this.compact?`46 0 192 ${$t}`:`-16 0 256 ${$t}`;return u`<svg
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
        <clipPath id="opening"><rect x="58" y="40" width="168" height="208"></rect></clipPath>
      </defs>
      <rect class="frame" x="52" y="24" width="180" height="230" rx="6" fill="none" stroke="var(--ssc-frame)" stroke-width="4"></rect>
      <rect x="64" y="40" width="156" height="206" fill="url(#glass)"></rect>
      <rect x="58" y="40" width="6" height="206" fill="var(--ssc-slat-2)"></rect>
      <rect x="220" y="40" width="6" height="206" fill="var(--ssc-slat-2)"></rect>
      <g clip-path="url(#opening)">
        <g class="curtain" style=${`transform: translateY(${n}px)`}>
          <rect class="slats ${this.gaps?"open":"closed"}" x="64" y="-170" width="156" height="406" fill=${this.gaps?"url(#slats-open)":"url(#slats)"}></rect>
          <rect class="bar" x="60" y="236" width="164" height="10" rx="3" fill="var(--ssc-bar)"></rect>
          ${r?S`<rect x="124" y="230" width="36" height="22" rx="11" fill="var(--ssc-accent)" stroke="#fff" stroke-width="2"></rect>
                 <line x1="134" y1="238" x2="150" y2="238" stroke="#fff" stroke-width="2"></line>
                 <line x1="134" y1="244" x2="150" y2="244" stroke="#fff" stroke-width="2"></line>`:""}
        </g>
      </g>
      <rect x="46" y="6" width="192" height="34" rx="6" fill="var(--ssc-box)" stroke="var(--ssc-frame)" stroke-width="3"></rect>
      ${this.moving?S`<path class="moving" d=${this.moving==="opening"?"M142 15 l8 10 h-16 z":"M142 31 l8 -10 h-16 z"} fill="var(--ssc-accent)"></path>`:""}
      ${this.max<100?S`<line class="max" x1=${this.compact?46:28} x2=${this.compact?58:46} y1=${o} y2=${o} stroke="var(--ssc-max)" stroke-width="3"></line>
             ${this.compact?"":S`<text x="46" y=${o+15} font-size="11" text-anchor="end" fill="var(--ssc-max)">${this.maxLabel} ${this.max} %</text>`}`:""}
      ${this._drag!==null?S`<g class="target">
            <rect x="60" y=${j(this._drag,M)-5} width="164" height="10" rx="3" fill="var(--ssc-accent)" opacity="0.45"></rect>
            <text x="142" y=${j(this._drag,M)-10} font-size="16" font-weight="700" text-anchor="middle" fill="var(--ssc-accent)">${this._drag} %</text>
          </g>`:""}
    </svg>`}};H.properties={position:{type:Number},max:{type:Number},moving:{type:String},gaps:{type:Boolean},storm:{type:Boolean},compact:{type:Boolean},interactive:{type:Boolean},label:{type:String},maxLabel:{type:String},_drag:{state:!0}},H.styles=P`
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
  `;function ce(i){return[{name:"device_id",selector:{device:{integration:z}}},{name:"language",selector:{select:{mode:"dropdown",options:[{value:"auto",label:i("language_auto")},...jt.map(t=>({value:t,label:t==="nl"?"Nederlands":"English"}))]}}}]}var G=class extends f{setConfig(t){this._config=t}changed(t){let e={...t.detail.value};(!e.language||e.language==="auto")&&delete e.language,this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:e},bubbles:!0,composed:!0}))}render(){if(!this.hass||!this._config)return u``;let t=B(this._config.language||this.hass.locale?.language);return u`<ha-form
      .hass=${this.hass}
      .data=${{...this._config,language:this._config.language||"auto"}}
      .schema=${ce(t)}
      .computeLabel=${e=>t(e.name)}
      @value-changed=${this.changed}
    ></ha-form>`}};G.properties={hass:{attribute:!1},_config:{state:!0}};function bt(i,t){customElements.get(i)||customElements.define(i,t)}bt(Yt,H);bt(ft,G);bt(I,k);var J=window;J.customCards=J.customCards??[];J.customCards.some(i=>i.type===I)||J.customCards.push({type:I,name:"Smart Shutter",description:"A shutter you can drag to a position, with buttons and its status; or all shutters of a base controller.",preview:!0,documentationURL:"https://github.com/abroeders/smart-shutter-control/blob/main/docs/card.md"});
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
