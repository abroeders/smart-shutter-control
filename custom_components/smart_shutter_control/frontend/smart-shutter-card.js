var ft=globalThis,gt=ft.ShadowRoot&&(ft.ShadyCSS===void 0||ft.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,Et=Symbol(),ee=new WeakMap,Q=class{constructor(t,e,s){if(this._$cssResult$=!0,s!==Et)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e}get styleSheet(){let t=this.o,e=this.t;if(gt&&t===void 0){let s=e!==void 0&&e.length===1;s&&(t=ee.get(e)),t===void 0&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),s&&ee.set(e,t))}return t}toString(){return this.cssText}},ne=n=>new Q(typeof n=="string"?n:n+"",void 0,Et),L=(n,...t)=>{let e=n.length===1?n[0]:t.reduce((s,i,o)=>s+(r=>{if(r._$cssResult$===!0)return r.cssText;if(typeof r=="number")return r;throw Error("Value passed to 'css' function must be a 'css' function result: "+r+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(i)+n[o+1],n[0]);return new Q(e,n,Et)},se=(n,t)=>{if(gt)n.adoptedStyleSheets=t.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet);else for(let e of t){let s=document.createElement("style"),i=ft.litNonce;i!==void 0&&s.setAttribute("nonce",i),s.textContent=e.cssText,n.appendChild(s)}},kt=gt?n=>n:n=>n instanceof CSSStyleSheet?(t=>{let e="";for(let s of t.cssRules)e+=s.cssText;return ne(e)})(n):n;var{is:Ge,defineProperty:Be,getOwnPropertyDescriptor:Fe,getOwnPropertyNames:je,getOwnPropertySymbols:We,getPrototypeOf:Ye}=Object,_t=globalThis,ie=_t.trustedTypes,qe=ie?ie.emptyScript:"",Ke=_t.reactiveElementPolyfillSupport,tt=(n,t)=>n,Ct={toAttribute(n,t){switch(t){case Boolean:n=n?qe:null;break;case Object:case Array:n=n==null?n:JSON.stringify(n)}return n},fromAttribute(n,t){let e=n;switch(t){case Boolean:e=n!==null;break;case Number:e=n===null?null:Number(n);break;case Object:case Array:try{e=JSON.parse(n)}catch{e=null}}return e}},re=(n,t)=>!Ge(n,t),oe={attribute:!0,type:String,converter:Ct,reflect:!1,useDefault:!1,hasChanged:re};Symbol.metadata??=Symbol("metadata"),_t.litPropertyMetadata??=new WeakMap;var E=class extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??=[]).push(t)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,e=oe){if(e.state&&(e.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(t)&&((e=Object.create(e)).wrapped=!0),this.elementProperties.set(t,e),!e.noAccessor){let s=Symbol(),i=this.getPropertyDescriptor(t,s,e);i!==void 0&&Be(this.prototype,t,i)}}static getPropertyDescriptor(t,e,s){let{get:i,set:o}=Fe(this.prototype,t)??{get(){return this[e]},set(r){this[e]=r}};return{get:i,set(r){let l=i?.call(this);o?.call(this,r),this.requestUpdate(t,l,s)},configurable:!0,enumerable:!0}}static getPropertyOptions(t){return this.elementProperties.get(t)??oe}static _$Ei(){if(this.hasOwnProperty(tt("elementProperties")))return;let t=Ye(this);t.finalize(),t.l!==void 0&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties)}static finalize(){if(this.hasOwnProperty(tt("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(tt("properties"))){let e=this.properties,s=[...je(e),...We(e)];for(let i of s)this.createProperty(i,e[i])}let t=this[Symbol.metadata];if(t!==null){let e=litPropertyMetadata.get(t);if(e!==void 0)for(let[s,i]of e)this.elementProperties.set(s,i)}this._$Eh=new Map;for(let[e,s]of this.elementProperties){let i=this._$Eu(e,s);i!==void 0&&this._$Eh.set(i,e)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(t){let e=[];if(Array.isArray(t)){let s=new Set(t.flat(1/0).reverse());for(let i of s)e.unshift(kt(i))}else t!==void 0&&e.push(kt(t));return e}static _$Eu(t,e){let s=e.attribute;return s===!1?void 0:typeof s=="string"?s:typeof t=="string"?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(t=>this.enableUpdating=t),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(t=>t(this))}addController(t){(this._$EO??=new Set).add(t),this.renderRoot!==void 0&&this.isConnected&&t.hostConnected?.()}removeController(t){this._$EO?.delete(t)}_$E_(){let t=new Map,e=this.constructor.elementProperties;for(let s of e.keys())this.hasOwnProperty(s)&&(t.set(s,this[s]),delete this[s]);t.size>0&&(this._$Ep=t)}createRenderRoot(){let t=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return se(t,this.constructor.elementStyles),t}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(t=>t.hostConnected?.())}enableUpdating(t){}disconnectedCallback(){this._$EO?.forEach(t=>t.hostDisconnected?.())}attributeChangedCallback(t,e,s){this._$AK(t,s)}_$ET(t,e){let s=this.constructor.elementProperties.get(t),i=this.constructor._$Eu(t,s);if(i!==void 0&&s.reflect===!0){let o=(s.converter?.toAttribute!==void 0?s.converter:Ct).toAttribute(e,s.type);this._$Em=t,o==null?this.removeAttribute(i):this.setAttribute(i,o),this._$Em=null}}_$AK(t,e){let s=this.constructor,i=s._$Eh.get(t);if(i!==void 0&&this._$Em!==i){let o=s.getPropertyOptions(i),r=typeof o.converter=="function"?{fromAttribute:o.converter}:o.converter?.fromAttribute!==void 0?o.converter:Ct;this._$Em=i;let l=r.fromAttribute(e,o.type);this[i]=l??this._$Ej?.get(i)??l,this._$Em=null}}requestUpdate(t,e,s,i=!1,o){if(t!==void 0){let r=this.constructor;if(i===!1&&(o=this[t]),s??=r.getPropertyOptions(t),!((s.hasChanged??re)(o,e)||s.useDefault&&s.reflect&&o===this._$Ej?.get(t)&&!this.hasAttribute(r._$Eu(t,s))))return;this.C(t,e,s)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(t,e,{useDefault:s,reflect:i,wrapped:o},r){s&&!(this._$Ej??=new Map).has(t)&&(this._$Ej.set(t,r??e??this[t]),o!==!0||r!==void 0)||(this._$AL.has(t)||(this.hasUpdated||s||(e=void 0),this._$AL.set(t,e)),i===!0&&this._$Em!==t&&(this._$Eq??=new Set).add(t))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(e){Promise.reject(e)}let t=this.scheduleUpdate();return t!=null&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[i,o]of this._$Ep)this[i]=o;this._$Ep=void 0}let s=this.constructor.elementProperties;if(s.size>0)for(let[i,o]of s){let{wrapped:r}=o,l=this[i];r!==!0||this._$AL.has(i)||l===void 0||this.C(i,void 0,o,l)}}let t=!1,e=this._$AL;try{t=this.shouldUpdate(e),t?(this.willUpdate(e),this._$EO?.forEach(s=>s.hostUpdate?.()),this.update(e)):this._$EM()}catch(s){throw t=!1,this._$EM(),s}t&&this._$AE(e)}willUpdate(t){}_$AE(t){this._$EO?.forEach(e=>e.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(t)),this.updated(t)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return!0}update(t){this._$Eq&&=this._$Eq.forEach(e=>this._$ET(e,this[e])),this._$EM()}updated(t){}firstUpdated(t){}};E.elementStyles=[],E.shadowRootOptions={mode:"open"},E[tt("elementProperties")]=new Map,E[tt("finalized")]=new Map,Ke?.({ReactiveElement:E}),(_t.reactiveElementVersions??=[]).push("2.1.2");var Dt=globalThis,ae=n=>n,$t=Dt.trustedTypes,le=$t?$t.createPolicy("lit-html",{createHTML:n=>n}):void 0,me="$lit$",C=`lit$${Math.random().toFixed(9).slice(2)}$`,fe="?"+C,Ze=`<${fe}>`,N=document,nt=()=>N.createComment(""),st=n=>n===null||typeof n!="object"&&typeof n!="function",Ht=Array.isArray,Xe=n=>Ht(n)||typeof n?.[Symbol.iterator]=="function",Rt=`[ 	
\f\r]`,et=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,ce=/-->/g,ue=/>/g,P=RegExp(`>|${Rt}(?:([^\\s"'>=/]+)(${Rt}*=${Rt}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),he=/'/g,de=/"/g,ge=/^(?:script|style|textarea|title)$/i,Ut=n=>(t,...e)=>({_$litType$:n,strings:t,values:e}),$=Ut(1),p=Ut(2),Gn=Ut(3),D=Symbol.for("lit-noChange"),_=Symbol.for("lit-nothing"),pe=new WeakMap,O=N.createTreeWalker(N,129);function _e(n,t){if(!Ht(n)||!n.hasOwnProperty("raw"))throw Error("invalid template strings array");return le!==void 0?le.createHTML(t):t}var Je=(n,t)=>{let e=n.length-1,s=[],i,o=t===2?"<svg>":t===3?"<math>":"",r=et;for(let l=0;l<e;l++){let a=n[l],c,u,h=-1,m=0;for(;m<a.length&&(r.lastIndex=m,u=r.exec(a),u!==null);)m=r.lastIndex,r===et?u[1]==="!--"?r=ce:u[1]!==void 0?r=ue:u[2]!==void 0?(ge.test(u[2])&&(i=RegExp("</"+u[2],"g")),r=P):u[3]!==void 0&&(r=P):r===P?u[0]===">"?(r=i??et,h=-1):u[1]===void 0?h=-2:(h=r.lastIndex-u[2].length,c=u[1],r=u[3]===void 0?P:u[3]==='"'?de:he):r===de||r===he?r=P:r===ce||r===ue?r=et:(r=P,i=void 0);let f=r===P&&n[l+1].startsWith("/>")?" ":"";o+=r===et?a+Ze:h>=0?(s.push(c),a.slice(0,h)+me+a.slice(h)+C+f):a+C+(h===-2?l:f)}return[_e(n,o+(n[e]||"<?>")+(t===2?"</svg>":t===3?"</math>":"")),s]},it=class n{constructor({strings:t,_$litType$:e},s){let i;this.parts=[];let o=0,r=0,l=t.length-1,a=this.parts,[c,u]=Je(t,e);if(this.el=n.createElement(c,s),O.currentNode=this.el.content,e===2||e===3){let h=this.el.content.firstChild;h.replaceWith(...h.childNodes)}for(;(i=O.nextNode())!==null&&a.length<l;){if(i.nodeType===1){if(i.hasAttributes())for(let h of i.getAttributeNames())if(h.endsWith(me)){let m=u[r++],f=i.getAttribute(h).split(C),x=/([.?@])?(.*)/.exec(m);a.push({type:1,index:o,name:x[2],strings:f,ctor:x[1]==="."?Lt:x[1]==="?"?Pt:x[1]==="@"?Ot:F}),i.removeAttribute(h)}else h.startsWith(C)&&(a.push({type:6,index:o}),i.removeAttribute(h));if(ge.test(i.tagName)){let h=i.textContent.split(C),m=h.length-1;if(m>0){i.textContent=$t?$t.emptyScript:"";for(let f=0;f<m;f++)i.append(h[f],nt()),O.nextNode(),a.push({type:2,index:++o});i.append(h[m],nt())}}}else if(i.nodeType===8)if(i.data===fe)a.push({type:2,index:o});else{let h=-1;for(;(h=i.data.indexOf(C,h+1))!==-1;)a.push({type:7,index:o}),h+=C.length-1}o++}}static createElement(t,e){let s=N.createElement("template");return s.innerHTML=t,s}};function B(n,t,e=n,s){if(t===D)return t;let i=s!==void 0?e._$Co?.[s]:e._$Cl,o=st(t)?void 0:t._$litDirective$;return i?.constructor!==o&&(i?._$AO?.(!1),o===void 0?i=void 0:(i=new o(n),i._$AT(n,e,s)),s!==void 0?(e._$Co??=[])[s]=i:e._$Cl=i),i!==void 0&&(t=B(n,i._$AS(n,t.values),i,s)),t}var Tt=class{constructor(t,e){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=e}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){let{el:{content:e},parts:s}=this._$AD,i=(t?.creationScope??N).importNode(e,!0);O.currentNode=i;let o=O.nextNode(),r=0,l=0,a=s[0];for(;a!==void 0;){if(r===a.index){let c;a.type===2?c=new ot(o,o.nextSibling,this,t):a.type===1?c=new a.ctor(o,a.name,a.strings,this,t):a.type===6&&(c=new Nt(o,this,t)),this._$AV.push(c),a=s[++l]}r!==a?.index&&(o=O.nextNode(),r++)}return O.currentNode=N,i}p(t){let e=0;for(let s of this._$AV)s!==void 0&&(s.strings!==void 0?(s._$AI(t,s,e),e+=s.strings.length-2):s._$AI(t[e])),e++}},ot=class n{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(t,e,s,i){this.type=2,this._$AH=_,this._$AN=void 0,this._$AA=t,this._$AB=e,this._$AM=s,this.options=i,this._$Cv=i?.isConnected??!0}get parentNode(){let t=this._$AA.parentNode,e=this._$AM;return e!==void 0&&t?.nodeType===11&&(t=e.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,e=this){t=B(this,t,e),st(t)?t===_||t==null||t===""?(this._$AH!==_&&this._$AR(),this._$AH=_):t!==this._$AH&&t!==D&&this._(t):t._$litType$!==void 0?this.$(t):t.nodeType!==void 0?this.T(t):Xe(t)?this.k(t):this._(t)}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t))}_(t){this._$AH!==_&&st(this._$AH)?this._$AA.nextSibling.data=t:this.T(N.createTextNode(t)),this._$AH=t}$(t){let{values:e,_$litType$:s}=t,i=typeof s=="number"?this._$AC(t):(s.el===void 0&&(s.el=it.createElement(_e(s.h,s.h[0]),this.options)),s);if(this._$AH?._$AD===i)this._$AH.p(e);else{let o=new Tt(i,this),r=o.u(this.options);o.p(e),this.T(r),this._$AH=o}}_$AC(t){let e=pe.get(t.strings);return e===void 0&&pe.set(t.strings,e=new it(t)),e}k(t){Ht(this._$AH)||(this._$AH=[],this._$AR());let e=this._$AH,s,i=0;for(let o of t)i===e.length?e.push(s=new n(this.O(nt()),this.O(nt()),this,this.options)):s=e[i],s._$AI(o),i++;i<e.length&&(this._$AR(s&&s._$AB.nextSibling,i),e.length=i)}_$AR(t=this._$AA.nextSibling,e){for(this._$AP?.(!1,!0,e);t!==this._$AB;){let s=ae(t).nextSibling;ae(t).remove(),t=s}}setConnected(t){this._$AM===void 0&&(this._$Cv=t,this._$AP?.(t))}},F=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,e,s,i,o){this.type=1,this._$AH=_,this._$AN=void 0,this.element=t,this.name=e,this._$AM=i,this.options=o,s.length>2||s[0]!==""||s[1]!==""?(this._$AH=Array(s.length-1).fill(new String),this.strings=s):this._$AH=_}_$AI(t,e=this,s,i){let o=this.strings,r=!1;if(o===void 0)t=B(this,t,e,0),r=!st(t)||t!==this._$AH&&t!==D,r&&(this._$AH=t);else{let l=t,a,c;for(t=o[0],a=0;a<o.length-1;a++)c=B(this,l[s+a],e,a),c===D&&(c=this._$AH[a]),r||=!st(c)||c!==this._$AH[a],c===_?t=_:t!==_&&(t+=(c??"")+o[a+1]),this._$AH[a]=c}r&&!i&&this.j(t)}j(t){t===_?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"")}},Lt=class extends F{constructor(){super(...arguments),this.type=3}j(t){this.element[this.name]=t===_?void 0:t}},Pt=class extends F{constructor(){super(...arguments),this.type=4}j(t){this.element.toggleAttribute(this.name,!!t&&t!==_)}},Ot=class extends F{constructor(t,e,s,i,o){super(t,e,s,i,o),this.type=5}_$AI(t,e=this){if((t=B(this,t,e,0)??_)===D)return;let s=this._$AH,i=t===_&&s!==_||t.capture!==s.capture||t.once!==s.once||t.passive!==s.passive,o=t!==_&&(s===_||i);i&&this.element.removeEventListener(this.name,this,s),o&&this.element.addEventListener(this.name,this,t),this._$AH=t}handleEvent(t){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,t):this._$AH.handleEvent(t)}},Nt=class{constructor(t,e,s){this.element=t,this.type=6,this._$AN=void 0,this._$AM=e,this.options=s}get _$AU(){return this._$AM._$AU}_$AI(t){B(this,t)}};var Qe=Dt.litHtmlPolyfillSupport;Qe?.(it,ot),(Dt.litHtmlVersions??=[]).push("3.3.3");var $e=(n,t,e)=>{let s=e?.renderBefore??t,i=s._$litPart$;if(i===void 0){let o=e?.renderBefore??null;s._$litPart$=i=new ot(t.insertBefore(nt(),o),o,void 0,e??{})}return i._$AI(n),i};var zt=globalThis,S=class extends E{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let t=super.createRenderRoot();return this.renderOptions.renderBefore??=t.firstChild,t}update(t){let e=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=$e(e,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return D}};S._$litElement$=!0,S.finalized=!0,zt.litElementHydrateSupport?.({LitElement:S});var tn=zt.litElementPolyfillSupport;tn?.({LitElement:S});(zt.litElementVersions??=[]).push("4.2.2");var rt="smart_shutter_control";function H(n,t){let e={};for(let s of Object.values(n.entities??{}))s.platform===rt&&s.device_id===t&&s.translation_key&&(e[s.translation_key]=s.entity_id);return e}function j(n,t){return"shutter"in H(n,t)}function yt(n,t){let e=n.devices?.[t];return e?.name_by_user||e?.name||t}function It(n){let t=new Set;for(let e of Object.values(n.entities??{}))e.platform===rt&&e.device_id&&t.add(e.device_id);return[...t].sort((e,s)=>Number(j(n,e))-Number(j(n,s))||yt(n,e).localeCompare(yt(n,s)))}function ye(n,t){return It(n).filter(e=>n.devices?.[e]?.via_device_id===t&&j(n,e))}function we(n,t){return n.devices?.[t]?.via_device_id??void 0}var ve={open:"open",closed:"closed",slit:"slit",partly_open:"partly open",automatic:"Automatic",manual_pause:"Manual",off:"Off",storm_chip:"Storm: only open/closed",frost_chip:"Frost: no moves",sleep_in:"Sleep in",sleep_in_all:"Sleep in (all)",next:"Next",after:"then",until:"until",next_phase:"the next phase",resume:"Resume",sun_left:"Sun has left the window",open_cover:"Open",stop_cover:"Stop",close_cover:"Close",all_shutters:"All shutters",no_device:"Choose a shutter or a base controller of Smart Shutter Control.",not_found:"Device not found",max:"max",position:"Position",device_id:"Device",language:"Language",language_auto:"Integration setting",reason_idle:"No action",reason_off:"Automatic control off",reason_paused:"Automatic control paused",reason_manual:"Manual",reason_calibrating:"Calibrating",reason_sun:"Sun on the window",reason_schedule:"Schedule",reason_sleep_in:"Sleeping in",reason_storm:"Storm",reason_frost:"Frost",reason_heat_limit:"Too warm",reason_cold_limit:"Too cold",reason_winter:"Winter",reason_glare:"Bright sun on the window",reason_lockout:"Door open",reason_ventilation:"Window tilted",why:"Why?",rule_storm:"Storm",rule_frost:"Frost",rule_temperature_limits:"Temperature limits",rule_manual:"Manual control",rule_sleep_in:"Sleep-in",rule_heat:"Heat protection",rule_glare:"Glare protection",rule_winter:"Winter",rule_schedule:"Schedule",rule_contacts:"Window and door contacts",decision_nothing:"nothing",decision_to:"to {position} %",decision_at_most:"at most {position} %",decision_final:"to {position} %, wins",decision_hold:"keeps it where it is",decision_at_least:"at least {position} %",decision_at_least_slit:"at least the slit",decision_minutes:"{duration} min",decision_seconds:"{duration} sec",why_off:"off",why_night:"sun down",why_below_horizon:"below horizon ({elevation}\xB0 < {limit}\xB0)",why_above_overhang:"sun too high ({elevation}\xB0 > {limit}\xB0)",why_not_facing:"sun not in front of the window ({incidence}\xB0 \u2265 {limit}\xB0)",why_not_sunny:"not sunny",why_too_cold:"not warm ({outdoor} < {limit})",why_too_cold_room:"not warm ({outdoor} < {limit}; room {room} < {room_limit})",why_too_cold_forecast:"not warm ({outdoor} < {limit}; forecast {forecast} < {forecast_limit})",why_too_cold_room_forecast:"not warm ({outdoor} < {limit}; room {room} < {room_limit}; forecast {forecast} < {forecast_limit})",why_waiting:"starts in {duration}",why_leaving:"ends in {duration}",why_bright:"sun factor {factor} % \u2265 {limit} %",why_not_bright:"sun factor {factor} % < {limit} %",why_not_day:"not in the day phase",why_phase:"{phase}",why_calm:"calm",why_no_frost:"no frost",why_within_limits:"within the limits ({outdoor})",why_no_pause:"no pause",why_not_cold:"not that cold ({outdoor} > {limit})",why_opened:"open",why_opened_hold:"closed less than a minute ago",why_tilted:"tilted",why_tilted_hold:"closed less than a minute ago",why_contacts_closed:"closed",phase_night:"night",phase_slit:"slit",phase_day:"day",phase_dusk:"dusk"},en={open:"open",closed:"dicht",slit:"spleetstand",partly_open:"deels open",automatic:"Automatisch",manual_pause:"Handbediening",off:"Uit",storm_chip:"Storm: alleen open/dicht",frost_chip:"Vorst: geen bewegingen",sleep_in:"Uitslapen",sleep_in_all:"Uitslapen (alle)",next:"Volgende",after:"daarna",until:"tot",next_phase:"de volgende fase",resume:"Hervatten",sun_left:"Zon is weg van het raam",open_cover:"Open",stop_cover:"Stop",close_cover:"Dicht",all_shutters:"Alle rolluiken",no_device:"Kies een rolluik of een basiscontroller van Smart Shutter Control.",not_found:"Apparaat niet gevonden",max:"max",position:"Stand",device_id:"Apparaat",language:"Taal",language_auto:"Instelling van de integratie",reason_idle:"Geen actie",reason_off:"Automaat uit",reason_paused:"Automatische sturing gepauzeerd",reason_manual:"Handbediening",reason_calibrating:"Kalibreren",reason_sun:"Zon op het raam",reason_schedule:"Schema",reason_sleep_in:"Uitslapen",reason_storm:"Storm",reason_frost:"Vorst",reason_heat_limit:"Te warm",reason_cold_limit:"Te koud",reason_winter:"Winter",reason_glare:"Felle zon op het raam",reason_lockout:"Deur open",reason_ventilation:"Raam gekanteld",why:"Waarom?",rule_storm:"Storm",rule_frost:"Vorst",rule_temperature_limits:"Temperatuurgrenzen",rule_manual:"Handbediening",rule_sleep_in:"Uitslapen",rule_heat:"Hittewering",rule_glare:"Verblinding",rule_winter:"Winter",rule_schedule:"Schema",rule_contacts:"Raam- en deurcontacten",decision_nothing:"niets",decision_to:"naar {position} %",decision_at_most:"hooguit {position} %",decision_final:"naar {position} %, gaat voor",decision_hold:"laat hem staan",decision_at_least:"minstens {position} %",decision_at_least_slit:"minstens de spleet",decision_minutes:"{duration} min",decision_seconds:"{duration} sec",why_off:"uit",why_night:"zon onder",why_below_horizon:"onder de horizon ({elevation}\xB0 < {limit}\xB0)",why_above_overhang:"zon te hoog ({elevation}\xB0 > {limit}\xB0)",why_not_facing:"zon niet voor het raam ({incidence}\xB0 \u2265 {limit}\xB0)",why_not_sunny:"niet zonnig",why_too_cold:"niet warm ({outdoor} < {limit})",why_too_cold_room:"niet warm ({outdoor} < {limit}; kamer {room} < {room_limit})",why_too_cold_forecast:"niet warm ({outdoor} < {limit}; verwachting {forecast} < {forecast_limit})",why_too_cold_room_forecast:"niet warm ({outdoor} < {limit}; kamer {room} < {room_limit}; verwachting {forecast} < {forecast_limit})",why_waiting:"start over {duration}",why_leaving:"stopt over {duration}",why_bright:"zonfactor {factor} % \u2265 {limit} %",why_not_bright:"zonfactor {factor} % < {limit} %",why_not_day:"niet in de dagfase",why_phase:"{phase}",why_calm:"rustig",why_no_frost:"geen vorst",why_within_limits:"binnen de grenzen ({outdoor})",why_no_pause:"geen pauze",why_not_cold:"niet zo koud ({outdoor} > {limit})",why_opened:"open",why_opened_hold:"minder dan een minuut dicht",why_tilted:"gekanteld",why_tilted_hold:"minder dan een minuut dicht",why_contacts_closed:"dicht",phase_night:"nacht",phase_slit:"spleet",phase_day:"dag",phase_dusk:"schemer"};function at(n){let t=n?.toLowerCase().startsWith("nl")?en:ve;return e=>t[e]??ve[e]??e}var be=["en","nl"];var nn=Date.UTC(2e3,0,1,12,0,0),sn=29.530588853,on=Date.UTC(2e3,0,6,18,14,0),k=Math.PI/180,lt=n=>(n%360+360)%360;function xe(n){return((n.getTime()-on)/864e5/sn%1+1)%1}function Ae(n,t,e){let s=(n.getTime()-nn)/864e5,i=lt(218.316+13.176396*s),o=lt(134.963+13.064993*s),r=lt(93.272+13.22935*s),l=(i+6.289*Math.sin(o*k))*k,a=5.128*Math.sin(r*k)*k,c=23.4397*k,u=Math.sin(c),h=Math.cos(c),m=Math.sin(a),f=Math.cos(a),x=f*Math.cos(l),z=f*Math.sin(l)*h-m*u,Z=f*Math.sin(l)*u+m*h,Qt=Math.atan2(z,x),X=Math.asin(Z),v=t*k,R=lt(280.16+360.9856235*s+e)*k-Qt,pt=Math.asin(Math.sin(v)*Math.sin(X)+Math.cos(v)*Math.cos(X)*Math.cos(R)),J=Math.atan2(Math.sin(R),Math.cos(R)*Math.sin(v)-Math.tan(X)*Math.cos(v));return{azimuth:lt(J/k+180),elevation:pt/k}}var rn=Date.UTC(2e3,0,1,12,0,0),U=Math.PI/180,wt=n=>(n%360+360)%360;function Se(n,t,e){let s=(n.getTime()-rn)/864e5,i=wt(357.529+.98560028*s)*U,r=(wt(280.459+.98564736*s)+1.915*Math.sin(i)+.02*Math.sin(2*i))*U,l=(23.439-36e-8*s)*U,a=Math.atan2(Math.cos(l)*Math.sin(r),Math.cos(r)),c=Math.asin(Math.sin(l)*Math.sin(r)),u=t*U,m=wt(280.16+360.9856235*s+e)*U-a,f=Math.asin(Math.sin(u)*Math.sin(c)+Math.cos(u)*Math.cos(c)*Math.cos(m)),x=Math.atan2(Math.sin(m),Math.cos(m)*Math.sin(u)-Math.tan(c)*Math.cos(u));return{azimuth:wt(x/U+180),elevation:f/U}}var Me=.72,an=.16,W=70,ln=["rainy","lightning-rainy"],cn=["rainy","pouring","snowy","snowy-rainy","lightning","lightning-rainy","hail","exceptional"],un={sunny:.05,"clear-night":.05,partlycloudy:.4,windy:.3,"windy-variant":.5,cloudy:.9,fog:.9},Ce=.8,Ee=.9,hn=6;function dn(n){return n===null?"day":n<-6?"night":n<0?"twilight":"day"}function ke(n,t,e){if(n===null||t===null||t<0)return null;let s=Vt(n,e);if(Math.abs(s)>W)return null;let i=.5+s/(2*W);return{x:Math.min(.94,Math.max(.06,i)),y:Re(t)}}function Vt(n,t){return t===null?0:(n-t+540)%360-180}function Re(n){return Me-Math.min(n,60)/60*(Me-an)}function pn(n,t,e){let s=t!==null?t/100:cn.includes(n??"")?1:un[n??""]??.3,i=e===null?s:(s+3*(1-e))/4;return Math.round(Math.max(0,Math.min(1,i))*100)/100}function mn(n,t){if(n===null)return t<.1?null:{opacity:t,offset:0};if(n>=Ee)return null;let e=Math.max(0,n)/Ee;return{opacity:Math.round(.9*(1-e)*100)/100,offset:Math.round(e*2.5*100)/100}}function fn(n,t,e,s){let i=new Date(n);i.setHours(0,0,0,0);let o=[],r=[];for(let l=0;l<=1440;l+=10){let a=Se(new Date(i.getTime()+l*6e4),t,e),c=Vt(a.azimuth,s);a.elevation>=0&&Math.abs(c)<=W?r.push({x:.5+c/(2*W),y:Re(a.elevation)}):r.length&&(o.push(r),r=[])}return r.length&&o.push(r),o.filter(l=>l.length>1)}function gn(n,t,e,s){if(n===null||t===null||t<-6)return null;let i=Vt(n,e),o=Math.max(0,Math.abs(i)-W)/80;if(o>=1)return null;let r=1-Math.min(Math.max(t,0),40)/40,l=Math.round(.7*r*(1-o)*(1-.7*s)*100)/100;return l<.05?null:{x:Math.max(-.3,Math.min(1.3,.5+i/(2*W))),strength:l}}function _n(n){let t=n>>>0;return()=>(t=Math.imul(t,1664525)+1013904223>>>0,t/4294967296)}function $n(n){let t=n===null?18:Math.round((n%360+360)%360/10)%36,e=_n(7919*(t+1)),s=[0,0,0,0].map(()=>Math.round((e()*.12-.07)*1e3)/1e3),i=2+Math.floor(e()*2),o=Array.from({length:i},(r,l)=>({x:Math.round((l+.2+e()*.6)/i*100)/100,height:Math.round((.12+e()*.11)*100)/100}));return{hill:s,trees:o}}function yn(n,t){let e=["winter","spring","summer","autumn"],s=Math.floor((n.getMonth()+1)%12/3);return e[t<0?(s+2)%4:s]}function wn(n,t,e){let s=Math.max(n??0,(t??0)*.7),i=s<10?0:s<40?1+(s-10)/10:s<60?4+(s-40)/5:8+Math.min(4,(s-60)/10);return e&&(i=Math.max(i,10)+3),Math.round(i*10)/10}function vn(n,t,e){let s=e>=Ce;return n==="night"?s?["#1b1f2a","#2e3440"]:["#0d1442","#283593"]:n==="twilight"?s?["#4a4f63","#7a6f80"]:["#3949ab","#ff8a65"]:s?["#78909c","#b0bec5"]:e>=.55?["#6f9fc8","#cfd8dc"]:t!==null&&t<12?["#64b5f6","#ffe0b2"]:["#42a5f5","#bbdefb"]}function Gt(n){let t=n.weather??"",e=dn(n.sunElevation),s=e==="day"?n.sunFactor:null,i=pn(n.weather,n.cloudCoverage,s),o=i>=Ce,r=t==="pouring"?"pouring":t==="snowy-rainy"?"sleet":t==="snowy"?"snow":ln.includes(t)?"rain":"none",l=e==="day"?ke(n.sunAzimuth,n.sunElevation,n.windowAzimuth):null,a=null;if(e!=="day"&&!o){let f=xe(n.now),x=Ae(n.now,n.latitude,n.longitude),z=ke(x.azimuth,x.elevation,n.windowAzimuth),Z=f>.03&&f<.97;z&&Z&&(a={...z,phase:f})}let c=1-i,u=o?0:(e==="night"?1:e==="twilight"?Math.max(0,Math.min(1,-(n.sunElevation??0)/6)):0)*Math.min(1,c*1.5),h=wn(n.wind,n.gust,n.storm),m=e==="night"?.65:e==="twilight"?.35:o?.15:0;return{light:e,sky:vn(e,n.sunElevation,i),stars:u,sun:l,glow:l?Math.round(.25*(s??c)*100)/100:0,veil:l?mn(s,i):null,path:e==="night"?[]:fn(n.now,n.latitude,n.longitude,n.windowAzimuth),moon:a,cover:i,cloudCount:o?0:Math.round(i*hn),overcast:o,sideLight:e==="night"?null:gn(n.sunAzimuth,n.sunElevation,n.windowAzimuth,i),landscape:$n(n.windowAzimuth),precipitation:r,fog:t==="fog",lightning:t==="lightning"||t==="lightning-rainy",season:yn(n.now,n.latitude),snowGround:r==="snow"||r==="sleet",sway:h,slant:Math.min(30,h*2.5),dim:m}}var b=n=>n==null||n===""||Number.isNaN(Number(n))?null:Number(n),bn=n=>{if(!n||typeof n!="object")return!1;let t=n;return typeof t.rule=="string"&&["target","cap","final","floor","none"].includes(String(t.result))&&(t.values===void 0||typeof t.values=="object"&&t.values!==null&&!Array.isArray(t.values))};function Ft(n,t){let e=H(n,t),s=f=>e[f]?n.states[e[f]]:void 0,i=we(n,t),o=i?H(n,i):{},r=f=>f?n.states[f]?.state==="on":!1,l=s("shutter"),a=s("reason"),c=s("next_action"),u=[];if(c&&!["unknown","unavailable"].includes(c.state)&&c.attributes.phase){u.push({at:c.state,phase:c.attributes.phase,position:c.attributes.position});for(let f of c.attributes.following??[])u.push({at:f.at,phase:f.phase,position:f.position})}let h=s("manual_pause"),m=l?.state;return{deviceId:t,name:yt(n,t),entities:e,position:b(l?.attributes.current_position),moving:m==="opening"||m==="closing"?m:null,closed:m==="closed",stand:s("stand")?.state??null,reason:a?.state??null,decision:Array.isArray(a?.attributes.decision)?a.attributes.decision.filter(bn):[],target:b(a?.attributes.target_position),max:b(a?.attributes.max_position)??100,phase:s("phase")?.state??null,automatic:s("automatic")?.state!=="off",sleepIn:r(e.sleep_in),paused:r(e.manual_pause),pausedUntil:h?.attributes.until??null,next:u,storm:r(o.storm),frost:r(o.frost),language:a?.attributes.language??null,outside:xn(n,o,e)}}function xn(n,t,e,s=new Date){let i=c=>c?n.states[c]?.attributes??{}:{},o=i(t.sun_factor),r=t.storm?n.states[t.storm]:void 0,l=i(e.sun_on_window),a=b(l.sun_factor)??b(t.sun_factor?n.states[t.sun_factor]?.state:void 0);return{now:s,latitude:n.config?.latitude??52,longitude:n.config?.longitude??5,sunAzimuth:b(o.sun_azimuth),sunElevation:b(o.sun_elevation),windowAzimuth:b(l.window_azimuth),weather:o.weather??null,cloudCoverage:b(o.cloud_coverage),sunFactor:a===null?null:Math.max(0,Math.min(1,a/100)),wind:b(r?.attributes.wind),gust:b(r?.attributes.gust),storm:r?.state==="on"}}function jt(n,t,e){return t||e?.language||n.locale?.language||n.language||"en"}function Te(n,t,e){let s=new Date(n);if(Number.isNaN(s.getTime()))return"";try{return new Intl.DateTimeFormat(e,{hour:"2-digit",minute:"2-digit",hour12:!1,timeZone:t.config?.time_zone}).format(s)}catch{return new Intl.DateTimeFormat(e,{hour:"2-digit",minute:"2-digit",hour12:!1}).format(s)}}var An=new Set(["heat","glare"]);function Le(n){return!!n.entities.sun_left&&n.reason!==null&&An.has(n.reason)}function vt(n,t){return n===null?"\u2013":n==="slit"?t("slit"):n<=0?t("closed"):n>=100?t("open"):`${n}\xA0%`}function bt(n,t){let e=b(n);if(e===null)return String(n??"");try{return new Intl.NumberFormat(t,{maximumFractionDigits:1}).format(e)}catch{return String(e)}}function Bt(n,t,e,s){return n.replace(/\{(\w+)\}/g,(i,o)=>{let r=t[o];return r==null?"\u2013":o==="phase"?s(`phase_${r}`):o==="duration"?String(r):bt(r,e)})}function Sn(n,t,e){let s=b(n);if(s===null)return"";let i=s>=60,o=bt(Math.ceil(i?s/60:s),t);return Bt(e(i?"decision_minutes":"decision_seconds"),{duration:o},t,e)}var Mn=new Set(["too_cold","within_limits","not_cold"]),En=["outdoor","limit","room","room_limit","forecast","forecast_limit"];function kn(n,t,e){let s=b(n);return s===null?"\u2013":`${bt(t==="\xB0F"?s*9/5+32:s,e)} ${t==="\xB0F"?"\xB0F":"\xB0C"}`}var Cn={cap:"decision_at_most",final:"decision_final",floor:"decision_at_least"};function Pe(n,t,e="en",s="\xB0C"){return n.map(i=>{let o=i.values??{},r={...o};if((i.why==="waiting"||i.why==="leaving")&&(r.duration=Sn(o.seconds,e,t)),i.why&&Mn.has(i.why))for(let m of En)o[m]!==void 0&&o[m]!==null&&(r[m]=kn(o[m],s,e));let l=`why_${i.why}`;i.why==="too_cold"&&(o.room!==void 0&&o.room_limit!==void 0&&(l+="_room"),o.forecast!==void 0&&o.forecast_limit!==void 0&&(l+="_forecast"));let a=i.why?Bt(t(l),r,e,t):"",c=i.position===void 0?null:i.position,u=c===null?t(i.result==="final"?"decision_hold":i.result==="floor"?"decision_at_least_slit":"decision_nothing"):Bt(t(Cn[i.result]??"decision_to"),{position:bt(c,e)},e,t),h=i.result==="none"?a||t("decision_nothing"):[u,a?`(${a})`:""].filter(Boolean).join(" ");return{rule:t(`rule_${i.rule}`),text:h,applied:i.applied===!0}})}function Wt(n,t,e){let s=n.stand&&!["unknown","unavailable"].includes(n.stand)?t(n.stand):"",i=n.reason?t(`reason_${n.reason}`):"",o="";if(n.paused){let c=n.pausedUntil==="next phase"||!n.pausedUntil?t("next_phase"):e(n.pausedUntil);o=`${t("until")} ${c}`}else n.target!==null&&(o=[n.position!==null&&Math.abs(n.target-n.position)>1?`\u2192 ${vt(n.target,t)}`:"",n.phase?t(`phase_${n.phase}`):""].filter(Boolean).join(" \xB7 "));let r=c=>[e(c.at),c.phase==="dusk"?t("phase_dusk"):"",vt(c.position,t)].filter(Boolean).join(" "),[l,a]=n.next;return{stand:s,reason:i,detail:o,next:l?`${t("next")}: ${r(l)}`:null,after:a?`${t("after")} ${r(a)}`:null,chip:!n.automatic||n.reason==="paused"?"off":n.paused?"manual_pause":"automatic"}}var ct="smart-shutter-card",Yt="smart-shutter-card-editor",Rn=360,Tn={up:"M13,20H11V8L5.5,13.5L4.08,12.08L12,4.16L19.92,12.08L18.5,13.5L13,8V20Z",stop:"M18,18H6V6H18V18Z",down:"M11,4H13V16L18.5,10.5L19.92,11.92L12,19.84L4.08,11.92L5.5,10.5L11,16V4Z"},Y=class extends S{constructor(){super(...arguments);this._narrow=!1;this._decisionOpen=!1}static getConfigElement(){return document.createElement(Yt)}static getStubConfig(e){return{type:`custom:${ct}`,device_id:It(e)[0]}}setConfig(e){if(!e)throw new Error("Invalid configuration");this._config={...e}}getCardSize(){return 6}getGridOptions(){return{columns:!!(this.hass&&this._config?.device_id&&!j(this.hass,this._config.device_id))?"full":12,min_columns:6,rows:"auto"}}connectedCallback(){super.connectedCallback(),typeof ResizeObserver<"u"&&(this.observer=new ResizeObserver(e=>{let s=e[0]?.contentRect.width??0;s&&(this._narrow=s<Rn)}),this.observer.observe(this))}disconnectedCallback(){super.disconnectedCallback(),this.observer?.disconnect()}call(e,s,i,o={}){!this.hass||!i||this.hass.callService(e,s,{entity_id:i,...o}).catch(()=>{})}toggle(e,s){this.call(e?.split(".")[0]??"switch",s?"turn_off":"turn_on",e)}moreInfo(e){e&&this.dispatchEvent(new CustomEvent("hass-more-info",{detail:{entityId:e},bubbles:!0,composed:!0}))}render(){let e=this.hass,s=this._config?.device_id;if(!e||!this._config)return _;let i=at(jt(e,this._config.language));return s?!e.devices?.[s]&&!Object.keys(H(e,s)).length?$`<ha-card><div class="message">${i("not_found")}: ${s}</div></ha-card>`:j(e,s)?this.renderShutter(e,s):this.renderOverview(e,s):$`<ha-card><div class="message">${i("no_device")}</div></ha-card>`}texts(e,s){let i=jt(e,this._config?.language,s);return{t:at(i),time:o=>Te(o,e,i),lang:i}}buttons(e,s,i=!1){let o=e.entities.shutter,r=(l,a,c)=>$`<button class="round ${i?"small":""}" title=${c} aria-label=${c} @click=${u=>{u.stopPropagation(),this.call("cover",a,o)}}>
        <svg viewBox="0 0 24 24"><path d=${Tn[l]}></path></svg>
      </button>`;return $`${r("up","open_cover",s("open_cover"))}${r("stop","stop_cover",s("stop_cover"))}${r("down","close_cover",s("close_cover"))}`}switch(e,s,i,o){return s?$`<button class="switch ${o}" role="switch" aria-checked=${i?"true":"false"} @click=${()=>this.toggle(s,i)}>
      <span class="track ${i?"on":""}"><span class="knob"></span></span>${e}
    </button>`:_}warnings(e,s,i){return $`${e?$`<span class="chip warn storm">⚠ ${i("storm_chip")}</span>`:_}${s?$`<span class="chip warn frost">❄ ${i("frost_chip")}</span>`:_}`}renderShutter(e,s){let i=Ft(e,s),{t:o,time:r,lang:l}=this.texts(e,i),a=Wt(i,o,r),c=Pe(i.decision,o,l,e.config?.unit_system?.temperature),u=!!e.themes?.darkMode;return $`<ha-card class=${this._narrow?"narrow":""}>
      <div class="head">
        <div class="name">${i.name}</div>
        <div class="chips"><span class="chip ${a.chip}">${o(a.chip)}</span>${this.warnings(i.storm,i.frost,o)}</div>
      </div>
      <div class="body">
        <ssc-drawing
          ?dark=${u}
          .position=${i.position}
          .max=${i.max}
          .moving=${i.moving}
          .gaps=${!i.closed}
          .scene=${Gt(i.outside)}
          .animated=${!0}
          .storm=${i.storm}
          .interactive=${!!i.entities.shutter}
          .label=${`${i.name}: ${o("position")}`}
          .maxLabel=${o("max")}
          @set-position=${h=>this.call("cover","set_cover_position",i.entities.shutter,{position:h.detail.position})}
        ></ssc-drawing>
        <div class="buttons">${this.buttons(i,o)}</div>
        <div class="status">
          <div class="big">${i.position===null?"\u2013":`${i.position}\xA0%`}</div>
          <div class="sub">${a.stand}</div>
          <div class="line reason">${a.reason}</div>
          <div class="sub">${a.detail}</div>
          ${a.next?$`<div class="line next">${a.next}</div>`:_}
          ${a.after?$`<div class="sub then">${a.after}</div>`:_}
          ${c.length?$`<div class="why">
                <button class="why-toggle" type="button" aria-expanded=${this._decisionOpen?"true":"false"} aria-controls="decision-list" @click=${()=>this._decisionOpen=!this._decisionOpen}>
                  ${o("why")}
                </button>
                <div id="decision-list" class="decision-list" ?hidden=${!this._decisionOpen}>
                  ${c.map(h=>$`<div class="decision-line ${h.applied?"applied":""}">${h.rule}: ${h.text}</div>`)}
                </div>
              </div>`:_}
        </div>
      </div>
      <div class="switches">
        ${this.switch(o("automatic"),i.entities.automatic,i.automatic,"automatic")}
        ${this.switch(o("sleep_in"),i.entities.sleep_in,i.sleepIn,"sleep-in")}
        ${Le(i)?$`<button class="text sun-left" @click=${()=>this.call("button","press",i.entities.sun_left)}>${o("sun_left")}</button>`:_}
        ${i.paused&&i.entities.resume?$`<button class="text resume" @click=${()=>this.call("button","press",i.entities.resume)}>${o("resume")}</button>`:_}
      </div>
    </ha-card>`}renderOverview(e,s){let i=ye(e,s).map(u=>Ft(e,u)),{t:o,time:r}=this.texts(e,i[0]??null),l=H(e,s),a=u=>l[u]?e.states[l[u]]?.state==="on":!1,c=!!e.themes?.darkMode;return $`<ha-card class="overview">
      <div class="head">
        <div class="name">${o("all_shutters")}</div>
        <div class="chips">${this.warnings(a("storm"),a("frost"),o)}</div>
      </div>
      <div class="grid">
        ${i.map(u=>{let h=Wt(u,o,r),m=[u.position===null?"\u2013":vt(u.position,o),h.reason].filter(Boolean).join(" \xB7 ");return $`<div class="tile" @click=${()=>this.moreInfo(u.entities.shutter)}>
            <ssc-drawing compact ?dark=${c} .position=${u.position} .max=${u.max} .moving=${u.moving} .gaps=${!u.closed} .scene=${Gt(u.outside)}></ssc-drawing>
            <div class="tile-text">
              <div class="tile-name">${u.name}</div>
              <div class="sub ${h.chip==="manual_pause"?"manual":""}">${m}${h.chip==="manual_pause"?` \xB7 ${h.detail}`:""}</div>
              <div class="tile-buttons">${this.buttons(u,o,!0)}</div>
            </div>
          </div>`})}
      </div>
      <div class="switches">${this.switch(o("sleep_in_all"),l.sleep_in_all,a("sleep_in_all"),"sleep-in-all")}</div>
    </ha-card>`}};Y.properties={hass:{attribute:!1},_config:{state:!0},_narrow:{state:!0},_decisionOpen:{state:!0}},Y.styles=L`
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
    .switch:focus-visible,
    .why-toggle:focus-visible {
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
    .why {
      margin-top: 8px;
    }
    .why-toggle {
      border: none;
      background: none;
      color: var(--secondary-text-color);
      font-size: 0.9em;
      padding: 0;
    }
    .decision-list {
      margin-top: 4px;
      color: var(--secondary-text-color);
      font-size: 0.9em;
    }
    .decision-line.applied {
      font-weight: 700;
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
  `;var qt=(n,t,e)=>Math.min(e,Math.max(t,n));function ut(n,t){return t.top+(1-qt(n,0,100)/100)*(t.bottom-t.top)}function Oe(n,t){return Math.round(qt((t.bottom-n)/(t.bottom-t.top),0,1)*100)}function Kt(n,t){let e=qt(Math.round(n),0,100);return t?e>=50?100:0:e}function Ne(n){let t=n>>>0;return()=>(t=Math.imul(t,1664525)+1013904223>>>0,t/4294967296)}var De=L`
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
`;function Ln(n,t,e,s){if(s<.03||s>.97)return"";if(s>.97-1e-4||Math.abs(s-.5)<1e-4)return p`<circle class="moon-disc" cx=${n} cy=${t} r=${e} fill="#fff8e1"></circle>`;let i=s<.5,o=e*Math.abs(Math.cos(2*Math.PI*s)),r=i?1:0,l=i?1:0,a=`M ${n} ${t-e} A ${e} ${e} 0 0 ${r} ${n} ${t+e} A ${o} ${e} 0 0 ${l} ${n} ${t-e} Z`;return p`<path class="moon-disc" d=${a} fill="#fff8e1"></path>`}function Zt(n,t,e,s,i,o=.95){return p`<g class=${i} opacity=${o}>
    <ellipse cx=${n-8*e} cy=${t} rx=${10*e} ry=${5*e} fill=${s}></ellipse>
    <ellipse cx=${n+2*e} cy=${t-4*e} rx=${12*e} ry=${8*e} fill=${s}></ellipse>
    <ellipse cx=${n+14*e} cy=${t} rx=${11*e} ry=${5*e} fill=${s}></ellipse>
  </g>`}var Pn=[{x:.18,y:.18},{x:.68,y:.28},{x:.45,y:.12},{x:.86,y:.15},{x:.3,y:.34},{x:.06,y:.3}];function He(n,t,e){let s="ssc-view-sky",i="ssc-view-side",o="ssc-view-precip",r=t.y+.72*t.h,l=d=>({x:t.x+d.x*t.w,y:t.y+d.y*t.h}),a=Ne(20261124),c=[];for(let d=0;d<30;d++){let g=t.x+a()*t.w,y=t.y+a()*t.h*.55,A=.6+a()*.8,w=e&&d%7===0,T=`${d%5*.35}s`;c.push(p`<circle class=${w?"star twinkle":"star"} cx=${g} cy=${y} r=${A} fill="#fff" style=${w?`animation-delay:${T};opacity:${n.stars}`:`opacity:${n.stars}`}></circle>`)}let u=n.snowGround?"#eceff1":n.season==="spring"?"#8bc34a":n.season==="summer"?"#7cb342":n.season==="autumn"?"#9e9d24":"#a1887f",[h,m,f,x]=n.landscape.hill.map(d=>r+d*t.h),z=`M ${t.x} ${r} C ${t.x+.22*t.w} ${h}, ${t.x+.42*t.w} ${m}, ${t.x+.58*t.w} ${f} S ${t.x+.82*t.w} ${x}, ${t.x+t.w} ${r-.02*t.h} L ${t.x+t.w} ${t.y+t.h} L ${t.x} ${t.y+t.h} Z`,Z=d=>r+(d<.5?n.landscape.hill[0]:n.landscape.hill[2])*t.h*.5+.01*t.h,X=n.landscape.trees.map(d=>({fx:d.x,base:Z(d.x),height:d.height*t.h})).map(d=>{let g=t.x+d.fx*t.w,y=d.base-d.height,A=Math.max(2.5,t.w*.018),w=Math.max(5,d.height*.23),T=e&&n.sway>0?" sway":"",I=!e&&n.sway>0?` rotate(${n.sway/2} ${g} ${d.base})`:"",V=`transform-origin:${g}px ${d.base}px;--sway:${n.sway}deg;--sway-speed:${n.sway>8?"1.2s":"2.5s"}`,G;if(n.season==="winter"){let Mt=[-1,-.35,.35,1].map(mt=>p`<line class="branch" x1=${g} y1=${d.base-d.height*.58} x2=${g+mt*w*1.15} y2=${d.base-d.height*(.68+Math.abs(mt)*.15)} stroke="#6d4c41" stroke-width="1.2"></line>`);G=p`<g class="winter">${Mt}${n.snowGround?p`<line x1=${g-w} y1=${y+w*.45} x2=${g-w*.35} y2=${y+w*.25} stroke="#eceff1" stroke-width="1.8"></line>`:""}</g>`}else{let Mt=n.season==="spring"?["#9ccc65","#9ccc65","#9ccc65","#9ccc65"]:n.season==="summer"?["#388e3c","#43a047","#388e3c","#43a047"]:["#ef6c00","#d84315","#f9a825","#ef6c00"],mt=[[g-w*.45,y+w*.45],[g+w*.45,y+w*.45],[g,y],[g,y+w*.72]];G=p`<g class="foliage">${mt.map(([ze,Ie],Ve)=>p`<circle class="crown" cx=${ze} cy=${Ie} r=${w} fill=${Mt[Ve]}></circle>`)}${n.season==="spring"?p`<circle cx=${g-w*.9} cy=${y+w*.1} r="1.3" fill="#f8bbd0"></circle><circle cx=${g+w*.8} cy=${y+w*.7} r="1.3" fill="#f8bbd0"></circle>`:""}</g>`}return p`<g class=${`tree${T}`} style=${V} transform=${I||void 0}>
      <rect x=${g-A/2} y=${d.base-d.height*.58} width=${A} height=${d.height*.58} rx="1" fill="#6d4c41"></rect>
      ${G}
    </g>`}),v=Ne(481516),dt=n.precipitation==="pouring"?45:25,R=[];if(n.precipitation==="rain"||n.precipitation==="pouring")for(let d=0;d<dt;d++){let g=t.x+v()*t.w,y=t.y+v()*t.h,A=4+v()*3,w=n.slant*.12,T=e?"fall":"",I=`${.7+v()*.4}s`,V=`-${v()*1.1}s`;R.push(p`<line class=${T} x1=${g} y1=${y} x2=${g+w} y2=${y+A} stroke="#90caf9" stroke-width="1" style=${e?`--fall-from:-${t.h}px;--fall-to:${t.h}px;--fall-speed:${I};animation-delay:${V}`:""}></line>`)}else if(n.precipitation==="snow"||n.precipitation==="sleet"){let d=n.precipitation==="sleet"?12:dt;for(let g=0;g<dt;g++){let y=t.x+v()*t.w,A=t.y+v()*t.h,w=1.2+v()*1,T=n.precipitation==="sleet"&&g>=d,I=e?"fall":"",V=`${4+v()*3}s`,G=`-${v()*6}s`;R.push(T?p`<line class=${I} x1=${y} y1=${A} x2=${y+n.slant*.12} y2=${A+5} stroke="#90caf9" stroke-width="1" style=${e?`--fall-from:-${t.h}px;--fall-to:${t.h}px;--fall-speed:${V};animation-delay:${G}`:""}></line>`:p`<circle class=${I} cx=${y} cy=${A} r=${w} fill="#fff" style=${e?`--fall-from:-${t.h}px;--fall-to:${t.h}px;--fall-speed:${V};animation-delay:${G}`:""}></circle>`)}}let pt=e?"cloud drift":"cloud",J=Pn.slice(0,n.cloudCount).map(d=>Zt(t.x+d.x*t.w,t.y+d.y*t.h,1,n.cover>=.55?"#eceff1":"#fff",pt));if(n.overcast){let d=["#90a4ae","#78909c"];for(let g=0;g<4;g++){let y=t.x+(.08+g*.28)*t.w,A=t.y+(.12+g%2*.06)*t.h;J.push(Zt(y,A,1.3,d[g%2],pt))}}let M=n.sun?l(n.sun):null,At=.08*t.w,St=At/12,te=n.path.map(d=>d.map(g=>{let y=l(g);return`${y.x.toFixed(1)},${y.y.toFixed(1)}`}).join(" "));return p`
    <defs>
      <linearGradient id=${s} x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color=${n.sky[0]}></stop>
        <stop offset="1" stop-color=${n.sky[1]}></stop>
      </linearGradient>
      ${n.sideLight?p`<radialGradient id=${i} gradientUnits="userSpaceOnUse" cx=${t.x+n.sideLight.x*t.w} cy=${r} r=${.75*t.w}>
        <stop offset="0" stop-color="#ffe0b2" stop-opacity=${n.sideLight.strength}></stop>
        <stop offset="1" stop-color="#ffe0b2" stop-opacity="0"></stop>
      </radialGradient>`:""}
      <clipPath id=${o}><rect x=${t.x} y=${t.y} width=${t.w} height=${t.h}></rect></clipPath>
    </defs>
    <g class="sky"><rect x=${t.x} y=${t.y} width=${t.w} height=${t.h} fill=${`url(#${s})`}></rect>
      ${n.sideLight?p`<rect class="side-light" x=${t.x} y=${t.y} width=${t.w} height=${t.h} fill=${`url(#${i})`}></rect>`:""}</g>
    ${te.length?p`<g class="sun-path" clip-path=${`url(#${o})`}>${te.map(d=>p`<polyline points=${d} fill="none" stroke="#fff8e1" stroke-opacity="0.55" stroke-width="1" stroke-dasharray="1.5 3" stroke-linecap="round"></polyline>`)}</g>`:""}
    ${n.stars>0&&!n.overcast?p`<g class="stars" opacity=${n.stars}>${c}</g>`:""}
    ${n.moon?p`<g class="moon">
      <circle cx=${t.x+n.moon.x*t.w} cy=${t.y+n.moon.y*t.h} r=${.095*t.w} fill="#fff8e1" opacity="0.15"></circle>
      ${Ln(t.x+n.moon.x*t.w,t.y+n.moon.y*t.h,.07*t.w,n.moon.phase)}
    </g>`:""}
    ${M?p`<g class="sun">
      ${n.glow>0?p`<circle class="sun-glow" cx=${M.x} cy=${M.y} r=${.13*t.w} fill="#ffd54f" opacity=${n.glow}></circle>`:""}
      <circle class="sun-disc" cx=${M.x} cy=${M.y} r=${At} fill="#ffd54f" opacity=${n.veil?(1-.45*n.veil.opacity).toFixed(2):1}></circle>
    </g>`:""}
    ${J.length?p`<g class="clouds">${J}</g>`:""}
    ${M&&n.veil?p`<g class="veil">${Zt(M.x+n.veil.offset*At-3.5*St,M.y+2*St,St,"#b0bec5","veil-cloud",n.veil.opacity)}</g>`:""}
    <g class="land" style=${n.dim>0?`filter: brightness(${(1-n.dim).toFixed(2)})`:""}>
      <path class="hill" d=${z} fill=${u}></path>
      ${X}
    </g>
    ${n.precipitation!=="none"?p`<g class="precip" clip-path=${`url(#${o})`}>${R}</g>`:""}
    ${n.fog?p`<g class="fog">
      <ellipse cx=${t.x+.2*t.w} cy=${t.y+.82*t.h} rx=${.25*t.w} ry=${.05*t.h} fill="#fff" opacity="0.5"></ellipse>
      <ellipse cx=${t.x+.58*t.w} cy=${t.y+.88*t.h} rx=${.32*t.w} ry=${.06*t.h} fill="#fff" opacity="0.5"></ellipse>
      <ellipse cx=${t.x+.9*t.w} cy=${t.y+.78*t.h} rx=${.2*t.w} ry=${.04*t.h} fill="#fff" opacity="0.5"></ellipse>
    </g>`:""}
    ${n.lightning&&e?p`<g class="lightning"><polyline class="flash" points=${`${t.x+.72*t.w},${t.y+.08*t.h} ${t.x+.68*t.w},${t.y+.25*t.h} ${t.x+.74*t.w},${t.y+.22*t.h} ${t.x+.69*t.w},${t.y+.42*t.h}`} fill="none" stroke="#ffd54f" stroke-width="2"></polyline></g>`:""}
  `}var Ue="ssc-drawing",Xt=262,q={top:40,bottom:241},On={x:64,y:40,w:156,h:206},Nn=4,Dn={handleEvent:n=>n.preventDefault(),passive:!1},K=class extends S{constructor(){super(...arguments);this.position=null;this.max=100;this.moving=null;this.gaps=!1;this.scene=null;this.animated=!1;this.storm=!1;this.compact=!1;this.interactive=!1;this.label="";this.maxLabel="max";this._drag=null;this.startY=null;this.moved=!1}viewY(e){let s=this.renderRoot.querySelector("svg")?.getBoundingClientRect();return!s||!s.height?null:(e.clientY-s.top)/s.height*Xt}onDown(e){!this.interactive||this.compact||(e.currentTarget.setPointerCapture?.(e.pointerId),this.startY=e.clientY,this.moved=!1,e.preventDefault())}onMove(e){if(this.startY===null||!this.moved&&Math.abs(e.clientY-this.startY)<Nn)return;this.moved=!0;let s=this.viewY(e);s!==null&&(this._drag=Kt(Oe(s,q),this.storm))}onUp(e){this.startY!==null&&(this.onMove(e),this.startY=null,this.moved&&this.send(),this._drag=null)}onCancel(){this.startY=null,this._drag=null}onKey(e){if(!this.interactive)return;let s=this._drag??this.position??0,i={ArrowUp:s+5,ArrowDown:s-5,PageUp:s+25,PageDown:s-25,Home:100,End:0};e.key in i?(this._drag=this.storm?i[e.key]>s?100:0:Kt(i[e.key],!1),e.preventDefault()):e.key==="Enter"&&this._drag!==null?(this.send(),this._drag=null,e.preventDefault()):e.key==="Escape"&&(this._drag=null)}send(){this._drag!==null&&this.dispatchEvent(new CustomEvent("set-position",{detail:{position:this._drag},bubbles:!0,composed:!0}))}render(){let e=this.position??0,i=ut(e,q)-q.bottom,o=this.interactive&&!this.compact,r=ut(this.max,q),l=this.compact?`46 0 192 ${Xt}`:`-16 0 256 ${Xt}`;return $`<svg
      class=${this.interactive?"interactive":""}
      viewBox=${l}
      role=${this.interactive?"slider":"img"}
      tabindex=${this.interactive?"0":"-1"}
      aria-label=${this.label}
      aria-valuemin="0"
      aria-valuemax="100"
      aria-valuenow=${this._drag??e}
      aria-valuetext=${`${this._drag??e}\xA0%`}
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
      ${this.scene?p`<g class="view" clip-path="url(#glass-clip)">${He(this.scene,On,this.animated&&!this.compact)}</g>`:""}
      <rect x="58" y="40" width="6" height="206" fill="var(--ssc-slat-2)"></rect>
      <rect x="220" y="40" width="6" height="206" fill="var(--ssc-slat-2)"></rect>
      <g clip-path="url(#opening)">
        <g class="curtain" style=${`transform: translateY(${i}px)`}>
          <rect class="slats ${this.gaps?"open":"closed"}" x="64" y="-170" width="156" height="406" fill=${this.gaps?"url(#slats-open)":"url(#slats)"}></rect>
          <rect class="bar" x="60" y="236" width="164" height="10" rx="3" fill="var(--ssc-bar)"></rect>
          ${o?p`<g
                class="grip"
                @pointerdown=${this.onDown}
                @pointermove=${this.onMove}
                @pointerup=${this.onUp}
                @pointercancel=${this.onCancel}
                @touchstart=${Dn}
              >
                <rect x="112" y="220" width="60" height="40" fill="transparent"></rect>
                <rect x="124" y="230" width="36" height="22" rx="11" fill="var(--ssc-accent)" stroke="#fff" stroke-width="2"></rect>
                <line x1="134" y1="238" x2="150" y2="238" stroke="#fff" stroke-width="2"></line>
                <line x1="134" y1="244" x2="150" y2="244" stroke="#fff" stroke-width="2"></line>
              </g>`:""}
        </g>
      </g>
      <rect x="46" y="6" width="192" height="34" rx="6" fill="var(--ssc-box)" stroke="var(--ssc-frame)" stroke-width="3"></rect>
      ${this.moving?p`<path class="moving" d=${this.moving==="opening"?"M142 15 l8 10 h-16 z":"M142 31 l8 -10 h-16 z"} fill="var(--ssc-accent)"></path>`:""}
      ${this.max<100?p`<line class="max" x1=${this.compact?46:28} x2=${this.compact?58:46} y1=${r} y2=${r} stroke="var(--ssc-max)" stroke-width="3"></line>
             ${this.compact?"":p`<text x="46" y=${r+15} font-size="11" text-anchor="end" fill="var(--ssc-max)">${this.maxLabel} ${this.max} %</text>`}`:""}
      ${this._drag!==null?p`<g class="target">
            <rect x="60" y=${ut(this._drag,q)-5} width="164" height="10" rx="3" fill="var(--ssc-accent)" opacity="0.45"></rect>
            <text x="142" y=${ut(this._drag,q)-10} font-size="16" font-weight="700" text-anchor="middle" fill="var(--ssc-accent)">${this._drag} %</text>
          </g>`:""}
    </svg>`}};K.properties={position:{type:Number},max:{type:Number},moving:{type:String},gaps:{type:Boolean},scene:{attribute:!1},animated:{type:Boolean},storm:{type:Boolean},compact:{type:Boolean},interactive:{type:Boolean},label:{type:String},maxLabel:{type:String},_drag:{state:!0}},K.styles=[De,L`
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
    .grip {
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
  `];function Hn(n){return[{name:"device_id",selector:{device:{integration:rt}}},{name:"language",selector:{select:{mode:"dropdown",options:[{value:"auto",label:n("language_auto")},...be.map(t=>({value:t,label:t==="nl"?"Nederlands":"English"}))]}}}]}var ht=class extends S{setConfig(t){this._config=t}changed(t){let e={...t.detail.value};(!e.language||e.language==="auto")&&delete e.language,this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:e},bubbles:!0,composed:!0}))}render(){if(!this.hass||!this._config)return $``;let t=at(this._config.language||this.hass.locale?.language);return $`<ha-form
      .hass=${this.hass}
      .data=${{...this._config,language:this._config.language||"auto"}}
      .schema=${Hn(t)}
      .computeLabel=${e=>t(e.name)}
      @value-changed=${this.changed}
    ></ha-form>`}};ht.properties={hass:{attribute:!1},_config:{state:!0}};function Jt(n,t){customElements.get(n)||customElements.define(n,t)}Jt(Ue,K);Jt(Yt,ht);Jt(ct,Y);var xt=window;xt.customCards=xt.customCards??[];xt.customCards.some(n=>n.type===ct)||xt.customCards.push({type:ct,name:"Smart Shutter",description:"A shutter you can drag to a position, with buttons and its status; or all shutters of a base controller.",preview:!0,documentationURL:"https://github.com/abroeders/smart-shutter-control/blob/main/docs/card.md"});
/*! Bundled license information:

@lit/reactive-element/css-tag.js:
  (**
   * @license
   * Copyright 2019 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/reactive-element.js:
lit-html/lit-html.js:
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
