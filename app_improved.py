from __future__ import annotations

import base64
import gzip
import json
import math
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterator

import streamlit as st

st.set_page_config(
    page_title="PowerShell Master Toolkit",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "powershell_toolkit_v2.db"
RISK_LEVELS = ("None", "Low", "Medium", "High")
USAGE_TYPES = ("User", "Admin", "User/Admin")
PAGE_SIZES = (12, 24, 48, 96)
_FACTORY_PAYLOAD = "ABzY8U3pY$0{_LmZF3t*wkGyha@#!vQB9Bp_##RjiXD=mBu*0|E<sB7-r=~T2o%T~6{^rx1xjd*9J>+zWIKG<_J-dg92<7nUfbUs{^C#mG5ZJXpWt&&W)||T3RNid?B3XE3YC?a=c&w-=bSt*U%wm0)2SDY)9+rfKYjf!7{h-%+w8lMm-!EIvVebnH(aEdKV<_ynZyY+9{Jxvi!8`OA0OYuGj=w(WrHLh`DyB>_;fVIp1ynQXKnF2`zss9Nk&cEJwF}c4}R#6GS+?*Bx%Mvd+fb8^|vp^+t3Jmnaz_~oYE+7f@qBIwjX`(X~DeNjK)d)bRK4M8qfoF{}?}{EDT`QV`>wmpRmRIIHH-)Q}2QLyiNUN_hdW`BK$duGaq62?z?Z>OhD1C4@KXfLgT7vd>pO@;}2iozi#zUTR)z^{`#k>mp%UZ)vN1x9*v)U|MSkr;clmYy4~6O_RWRZ^+}(FzW2!i)|5|l6i4ZN>L)2nALGwaL%{ay0VW>b&az<YD@Z*<sCv-P7HhL-52IkpJ_gZ#_vfpbpLkgiJ@7ZTb}qd%JB{P)c6I|@EMe?<i*);4JWtZ?eh|$w{vi~2sCgQ|j93VLuzTo42Z_&$-6w$G7@%R}Af1KYqQa^wg6E(fJh+%|v0wH(6&wW*v7F)rkcho8bTsm#3}>QKd+mE+o5;aFLujhg`a4GRXNjN9lc)iOhxI7L^?4I#UdVpW-Xy-d2Gp-UTz**E4fM*-ZwvMWJ^c`*!F}lS?Klj6_49qgHx!Om*aJQsJTB5;<b}M4qFsgrq?wncEQr|KQ*)akWx!t91UjV6SZ$LPp?g#h-5!iVu(ILIgN1$)hOCzaPc~N?($5V3fED!=jQxbY2|{1=pMy^<iQt1-jtk+#hr6A(wcyU%8vx^+$27T=Xy7<$F!Q;m@Qu@k_`ayQKY_I-3_D~u{&Yr=snA}-(s}aR7ud)5e)RO}=Da_+yL-;s*Zv4t69E1uh8@e==O=8><lp$+GVC_Z;>04FMy1D-IK=NY!pZ16_cH!mne^jzNQdnSoG~Tp3+O(3b$2J4-Q8iks`T>_Qa+7L46vksxO`BB^wLx7<vO$v5`W@nqsJ<A%eF*&G0FUW2H%s-#2akvWu8vC?5r`_oxPgO+6PVtLd*G=Sr{jLDGADlSv<>Sn>Mlu=8IN>;2+r#U(OrJ$2<NP-;!Lu0K<%b_2J0%(@)T~4uBjVPAi&FT?kH-z@M;m1RE@3lQ0;40$LPUY6`$V1;C;tS@#QKlI75}a4Iuz+$viPH+}*WhiR~R1cc5&PD3^alCQZOc-Nm`8afhve;mxGE5Nw+L8gHzh$*qpLH5W1)dxRQG3hqLWN^_dgydoj-R~a=EDRK=qjctvf=Muv-Ppuu60G$Bpg9orIEq4gO_}x*6c0LSE2sd<smisU%EG=>Amn0Gx6d2~pNT<&=m`WuoVkYE$+C&RAzi7nhH(3Pl8J_M&_VeO6_`FwgRA?$AU=kuYXJ9tKE3yotH~L#1Q7PUFK1yq`ZS#R{`f~$AVj()L<7fnUNZg+43+^;PM!k)vkoE7{|7G9!SZY>d30(D&S&!^fe*_D@n>L!gV2i<_-6RyX!5{zVHbO&3?;tNqi?O0vqyjQiSY)EUSc!Rld{F=cm6($kbO0zw5AX{^fUG@cz84$ShS{+R(3o(^j}QIUfVyupR^CWmq+cF-tl4EJMz2x-tp*Y|8QhL0XigXTOn=C^pTcWnDZdG7z|wR0D60S(F3t9vFTD^dQl&yQ!m8d$9z?+0BQfYbAQn7cH5Jqmj~^G&SbCs@(4hhOb+kwyGMKDN!QjQQ4|H0SdKH3<18V{=dd0$Dgre{(zkwu#sME-$lyF!FyQRKBAqbY^Ck(kV7u`=o6R$l*~H8I-JQp58k#Fb^!^AcH5?XR<b|Lp8U~hkH~mW{dQZJ4fFp~k`_gS=!*S`&;H*qp9EA%Nnwk>p00x+Va>6d6NxX{BLR(a1xZy$PwSw!=qwRt3eY#C;TLb4RPeGE+LHp%qCWEEO>2RaNYJO5~q}y9Zd<P9=0Rl8T4OGra&)VV{JaP*q=hIoXfX~Z&xDO1DiSL10k_GE)W8KbLhBW-V49|asB+k<Ud?G()dzd9b^uStI!@t4-_Se%3_@ft3y&!5Cr2gF;#AC@9-3Q@M{(@2W)$L;|tgbbMO;Rl8Gj=hZ0dKRnJ+AVzV0saOwt!5VuXFL%88?8N3!VSEEx(b*1Q7z3ia~8#nw(AmbFL&?m4i`J{Co$~hDCV^o0HK_EH^;&=4T*bW-BbwN=uie`H_!XU~Cpo=V>)Vb2%b41<ljpRgd+9C>YNjHX2$Sk3l%Lwf6iSQqLq}XmS3Sz{e#EGGXSzW0ZI)Xz%#?L=LH#tn%NRFOa&DV?2ek4n(?sJoZELL{J1~+0Zls_PuC6fsHl?6?~gI*(P~fH<%ijT#Vt|2qtiBN~wB^ZyM*q8UK|`rp>LT-93|wzW1}waq>y$9xw*G7_hTAngkDXyk3aaBO#cL=n32P!qBB^T?}@6?}xj+cV`1O2JtEgQ(M{c#&D9Om5%q-l(23E!rp{)Sb;D#cIJWf?j&h~ZN^dRw!Ohe^{E5+c1d8ZVR$gYo*DJh;L@PGw_kytYmo2gOP!3zFpJblPy%bzOLJ?}F!cQy>;A~p77;(e42u(Vj7`E|lo^D+hhgdKLK81dgNJB6ixZrWFhT@-NTdCr0_`^-dBawP6%>J-|7-xK_m)CGK5n1!zG3yU;~n}x*5-`;z!G6$qr#ajx=Vccir#$?2AL_Sp_IV?nKoXthgInu&^@uB=1ELSr4-&&h;2(oMYgqvIDQEIol!hxZR+UYVBaaA1`{?D&shKx_RKfLxEuK58P13Qv=05!w)BX~B{DUVOjJ;gs(_MUAL0qS24zLv%o#ofI@)9T*<Hs`0&n5Re2mSD^LO#AeZOeK12*$Op=tV=UsRw7S;u7@f12yJ25B5V`R!hm(wA%--_uq`u{mK&W(m-+E(SVnxM4Z7fP=R2-DY?1xDuNJDLLhQb0v-LF9y>FVsgR~d}%I^CH2eY4c4JdE=~YVrSWCeGxLPo5tcjA6szD(*hA`01*Q!8`8gac_aOGbk+GC2E@KcK1ZUr-f8g%j#w(G`m%sCW(Sxhc5v*q+&6;<Hd}g?T;lrmmv^O6I#{IrJjnR^b<^q{@uTlsh+KPRogLqz5{P<g|pv&b|`GWz{6)-%`0Sj!z%gJG@P2f^R93%6&<aH-pYH|Q0o)~Hy;xh*ff`}V{xBK2mkrs?=Whs*t*~rD<{8Avr{)mV7PtMk7A)Rg|7Q!#u3>eB#5U;2|wn?H*rmw!Acwy?W<-yVKEn!FtsBd)1<`#K6Rm8nskiz!#9mI<#8m;_Z?PCB+YikANvg7<#$y<(K(T@~hYmIs|+g7|)l4}h4v<5*HsqZ{0K!8737l3QO?em^XDd%l!e)g4gSCIl?b+aK^O+N;20=!6@7+O1st)Sa{CKEF<(wWjkp_G_Oy6kB<yy!WUGy1veEm-l^KB~(0IaQ!az~k|1stCl_t^NY%*<zpk#cR6yw>~Q>Y3K<<1kaTIbz>du$PDj}EJ?4{eJP)g2EdDIybZoCoNK!v<p96d3{)HdP)tByL&oE0KQi^Vrz8HWLwy^gq8AB<If|2HKC>kz8jp9u#^U4F+SKSJ2=D(g576;KrTw@v?H_|EjU8lv=D!zGh!277hwzC*<|j#Pvh0s)2b-p^vRH_6@6b=4^kbWQbVlh}7{Jow&&A2i+TxEl-ZTgoAdfyBZ0%@Gtc@+NKXI^>TEc4%`-FHF5+7)$*mNsNbv~aHi0^MnaZ$Y<N)RB`egfO-Bn-Tiwa&9g(#?UD8$hsUEul2Dw&|~forBhvrQv$fgRh|DfMz}$qrZec)moh3Wc-(TnsGbAgqS`~Uc;<Y53{o{o{uM?m;5HUb$00g0JqN09{gX&!VMOHG6$ShA#T3~THVU3*Y&_M>UqhGwLOC%kX74R+y+)V^=31a<x%G`Znd#DVc~1MNvcS8+`8zZA?Ni1A~*%cAl`${1JsRVW7}hnTPhVgYy!EZvZ>2lw|h|a8(j;F%Z&tF(1?~8ACC6Gx<`>rP1<T)p9-WE>L9In+qQz5D$*EiAv~xvkd#f^6Q{+42A!APozBtmP6sv?thMwL>mDBN$p62$e7@6R?U|{JK?gHnQlxNZ<WCKQC33JO`PXv127X?6PN)!6k=lBE5tgDL7ODz_d$D>e3FKX^DS3}UUqe?oG#Kcnoo*HROzNDcpz3}O#-RD;cl=J>lQ4l1N2WvDwLkI$5JXQGFv0C1d|3L+?Sdq<g?nfL!rMHu_0gNei_(do2ygqQcZl68@*0`HN&CmUJ{VZ@a_;QFM+TyQ$G)=G*S&A7&AxWN!O1gWdHf3gqxJ6HtLgMrnzpvKpRKUeceZw}xvwW(FaFS)rY-i(5xPQ?Q4CjTCMRpPjv7obQ(EH*(45Ct76m_Cp1fzf{O;ruuVsu?)O#Gw_%Z!-K+oaS9>p{NLg6RYF8UD2>lnJ}frFikI9mp%<TgOjW-Z&*^*mzmiD)c7hITJsMIIzW+;9X69hu?SaDE^8nZAg+hX-O6eILwTx0aN*e)#_9A6YQ577et^7Yu9v-8}HKt*@=CC=4S16@%A;**E5l2MYsXF-Mmomgcijt$t6$BiDm$7{X_Vo<npX7X7R2_Q1N5?FXYIPUA_&_Kyy2A7VW4t|pTJqgO=CpTn5}R3}t*xBV|8Kimc$8piRb?acS4={8Inr?)*#y%Bdfmbdwu7qZLGhkk31Lii_H%J@X=6Io0!g$`#cEJX$0FSij_+KKhTc$tP-w=!m2v=Z|{R|iYPQezbEzN4s=%d4}K%ag&NcXD%rUJs)4yF1>`-CgHsXHWhMJEcDF?w;R$S1pnSlvgn&GG`QN=VwJCT0P!=VBIFK!s`YXiiMQJaetb&`J$r#)oA{aIgoXMN`u|qt$`t*CORCkAWi3{l*=EFDud{_5aMQM-jO%SG=_IzT~rstN`4W%n`>#!_*<Y_4NJT)CRvToFt@juP)>k~1@M;HN@>%Al6UYKIauPiF?y6f8=2cd8#Q?1Vcq>5`8?*W!jjF~u7tIi4Tvu8?nY~Dd^vu)h(<cf`J)Z2*}N}%*&bC!m)qyA`0*jl&IP=)_3o#$+gEpYL+A+onaUU^?-0YlxRttPqUXTvK8Zj1Q9ha3axz-<3o+DB{sNaVPOk1f1%(k#=j7$kMnw(|NpkU15qwd1eTqq+%(GZ-wsnsniQV&^=u;Qh-OBJeZVX804-cpbiEC-)z*Z*3-v88HZ{2D599PGO)Ez0%ponU^n~l;@63jBzLRUoizz>Nx<xYzVE=(>k{@>0K{52d5c0QaATWoin(lw|{ZVsU}=oW0*LY4f~XKQI#!p22@BpBbYi027I^CQxzBKEQ}Vge*z5xzEuls7VMFgHm6>n6#8^0aScs25zx#(03~tkKo@f#ot#49G3nALSZ)&+P&NlDqF5SfDR6OjG=8ns=N&;<AV57y)?`gSI14I_q9@Ybyq4!k*jZHcxWjb&1GwGQ63YMS)(G@o2=Y(<VrDYO?c>pcnv5$<zyX#&I?+XGCt<0=NZ?2<R#Ol=C8F;WV=J6DNOQTV&%syO{TC9z^{o{{1`%$0-XkRJ<bpOU8ZKRLr{dlrAp4pxfiKk3rPwY!#?o;?h~lZ><`t6^(=boI=<%qgwgT4vngc^rg|hzvkh^wUMjgP4klr^tn|h7k$Kh?5P)o_wg5&o4ggFX?Vl6s4C~Zg^V0PN~S23VXXDkHgFtt4r=VQnHS`G=Q9c#+4>vsrG$@*d`a5F>3a0F%k5zZ14SA8g(6z`n>w_Ar#xZFJZi+Is>}2OwGaH5G#&EEl!yxs(3|;5wm`}AvX7GI)tj4-C)ejr$x{VS^K5Tz?TC@!X&xz~z=X~h0fx$8IJx|!@(kDTk~5Ad0=J=A@t|{5bE6J%oeX014Cs5vChXiM=-mv9gFOeKh@0nk7X?On*bh_Q%Q){vxAJI@UE8k;Yr2R=;d~75M{(3vC=i3Hc)X}{(2){EA06-e;Ir#ar`#DHqqj!Vv39vahEJnnJwz-3*m}ewEc=)8U|m-+jq2mNtKidOR>{hh^Jsdbo)XIkaT#6slLiW`MtpU#7<Z}oG*WKAfteJ>c1kssH|CzR<M{}^L_a?IiO;@%|ML!ayAFd-aHv1$y+4OT9i1NGsTha*ShBYN3+sF{?tHW+&YK=7S7&0fmimFIPiSV1?|2Tn)rD&56DT0P0h*?MrsX6UntZrDKsCp<0}NsyGSIXT(;~o+zLwaDzf6TYUi*U=&V7e;0C?nc!-Ozw6o(<d3^2teF>$BgVy&%sWSQz^wx8?#>|9>=yg8$54mIv{GGe<a{1(NZErRHX6?S0w<RZS*5h!;~eopY@3p9&G{8Tc<lj*0L_oH)A)lx<ef;5BEFitdbyVc3<T@3p?x{|%4FmTm76`$?$%NVwcOe&hs+80xdbl#<RmakZWwgEL0q2(hPzNxtU^Ct~dbdBWwnk3UrRy~UG6(_+xblBtcE-wUFIx_Q5(3q7&aBPBayie%Yf>9Y5jxLe`swf=PL_wxOs0W02%ZY{95OQEb#fW5?^7MSzuI{FO@B649%5X2(MX-MYPs8A_CI&yii84<#drWoeVO7w}uX@Bd@lW8ELg?K298BHt%<<e}@nk|Ha2iTLk}d0j)u(IKi{TaUoJ6~aJF+avB_MI;KneKHUa3Z_$4_JWjqOfcX|GVT6Wq|{;wji6ZWv(y>v+L{T9exe67u)dNPMvti9eXkUnLXNGzX=eItr+`_uvEoax7};8flCJDC$}rYWd#xSQw)_RiL?|A6aJG5?V!8*IwW~L@|21D6~$;m>g&9NMts|-{&FE{AfF8$X{`(M)G4c;N~x@)02B5Q-dLHO@*S*Dcy+`q-I-6QS_c$ET$)$5sQy3<7g>iAk#mf>p~)?=WrW<pZ<Q}jXoi_XoG5ZOKA!I%0LM?hbgnK7-EdAzT~ZhfY?LpLOcV3EyKunwj2z!3{25=!I>C(d*FGtb$5q@^}Q&Vz?a_nG7VAfAT!yw;#;5Fj{`@FW26L)Hi;OsiE!8H)WMWnr!GMFs&eIMW&T@fHp8B&<DK!nVJWMbH*gB85l@L=WL^Bw^!bwHM$>HF>?}u}ZhiFL#Bi=S(UW>Pw%}Gr7jP{tH-&gd-YDMPk$;i+l@?tO^aSzq-Cf=_=)Ens+M9>Wo3n8pQ%FnVM`IuJ$QVo;pH+r=#VXxjm!*ko2Q$D#!~65xL(AdQ_9$7*vf<Nc`##9h?P(f_umRU+(7%FE`g*8P1ov|urC9~tRb#v2Ke9QTxBQMJbzZWh%kY+(*T5R+2X#Q_f@}YR((a^z45O4MNf1pRrWsmlVN!|K#JnwmK8iepmVLX{R3%ZM?=3*+@y8CKr&B}tr33Kvnl45L=aiRAHFRUwAen*G6MUK8CvG{m@6m~YY0EJUl@+6f{gc95^CN=jjhUFJPgp{WU7Djt=}|pOX^KM<%>>0o#7f!4rj|mAxOiuz$yz@6t;l^*pG}{hshLXeM`KuAuzum#p{x|J`{B2r?_s0OXFswW0&xuo&q`3>DM$<y&U&sjT`5|N)6L*K4U#xQp+uv;hI~tswsigGQF5l^R@K-%`KuPrrY2x1$~hx_GGq{+!!HZX@VuLJEjA|t+)N*#qfRZ+Sw_#k3+_Rq_A+-m%18N>ac<_wqquA`@jc9^WM-R`j~$`7HI;*I4H;S*L*HOs1d+{54R`P#DCC3gq2LVshvCgR{8vP;oWb#*#2|@ebn%3LqqM@aFn}BkvrW)O3NW?U?h^+QzY33O9<yCwisx^C?tQ$v?y=o52+B@PnV*BZ^gUe~2u)sIzBf09c02VrCncd}L*er#Ps9CgHl?!=uU&U1jw=^@LmB`^)Ca{MyuUFroAB}#(D)H{e(-CvwNXQw<(DpJr<mL1p-Sp=Xoh#ar$hRmoiKh_ne?6~`lnlI90*=9zODGRxvTI|x3+-!CP@6xcw2ZqcZH;T<EM#i;R@uHTYv0NJhW&o8_zA<_Z#imS`6=O4#Q1F2XyIw@0<SRN8N*ZhW;NIw|~de`#@x!sci!Mk(JyJ&}k&@;Zy&Yxo;)nJ&iF-c^ro+Ueu!$08*5n)V~qHRGp#!M3JzAp@vEgsgOjOEY3v{ja$O_Q3kXktCEHm-S>ldSOo9G5ZC9<ItSuvHDy|>Is&lhNO*o2GVrl=*&`H{)ScU0eX1B%q;?}x&&aDnJ+GvisfA7#ytv%%arX@}ApDiRxnXT|)O0NjdD~o)+FUegp0noIx)mzM1(p+K%UOvHzi?IVQRSODL^>ix+1^E*Q%*5u3f7e;(R<#c;kD7Rb!}9P$&fp6t$~Sr(^@vp^&*!We`ubmqAR&@9J!!mlZuG~R^W3`1s|F%^CUEyk;3-Y7|wv%S!My=NA~Em0mc)ntrXfsM{D_J$f#1$b3u8CW9$B?faG{qK(S($(Fk@srcg(fNUq{PSWI;hwMSK`m0me6g554Tr8F<QbNb;7H|B$LY+VAmKPD#W5re{^gxq@S={F-ozmP(qR^V>cUsYKf{N5Hsy9%_)M9b()(kRpXv2_(xg<{Nu>xK2nUB0I#YM>wa9(C|=jnolk_h|BgUsfSks)5c8TaDD7qIW684if)~0{vCaWEqlW|1RaN(k@m>wrd@gZCQ)86l~kl4U1|ZrFmc=!Onedzcok{?{8q!b~<$k)Xn526iPdFF^Lt-(wk#Voo*c}PvD@BD{x<GmzEJ30VBdHJlxb^1{C2a4T;1^fH?7z1)E}02$kghIwVuNXY!FQp|=;MBjujSnHi9>J5xt4FLdSUCcf%HEfO&ve>IJdqgfGs6PWX(l0(3t4S#P&TuJi7<Idqa8+GV=iBW4#r}raoQL<0@bLh|i;^4LPaFaW=mW*_IaWgC-4j&g&CZdyMl&!&p=-o{a^r8+y*MqYXdah@qVOmTOybPNzbZ2?Pho#@C@^zRunV@1d_GfsL8)-qw$DQLk<jSi9>Gx1V`}@!<bvT#if0_Jn>}M`d*Y}qv8(pq1t4V-@xd_NcL7_^^rK08WDPPIdj#ZV$_m^KH*VPTqB!^wFj0~k~D5_Gmk=PjtI*+@R1SLu)B1y&ies;wbwZ7jocRJ%`u3}8WPWIrf9WAl5RV2?q?c-wrY)b|g0vc(a)ZJYuuwntTV%+lXRm>{MUg!J@QKEL1Uj{l2BD{6`EPWz-x?B+A=5c2PzqjAVC}m^7P%_Q8otEbx+p1!=8J&4H{LrXAm4-sM#uiH18!rec%UR3~H)iNU5S^2f(0&tynV-D#(nm^&#{Tg2GJbeZDN(siv-RV}`1Omu{ey3;-S@uGYbm4LOtRizF!j$8AFaIGeOLx|(W+(5mZhP{ymg?8E<W$Qv0<^hUsvVK?|V;128&Hc=ncgtfap9~Y9(}G@R}VT9qjE<Aafk0uO+kGJ>1*db1B^7IrX;0!t}=wQ{lbVSH4A{cy5sc@W+1WEi{BGNrfUuGS3XpxI3N|x3Po}TggTRRtVEoM}NuABOZUIU@(f}6&>?TLzT^N6)tjy=u?C_zVIFP@BYQVrnt6|m-v*WM8oZ{&QW&4^F36l45wK4O_QuJ!!ARKmcO<mpS8Gm8sDwoG<&Vfq>c7j3Xl^Qp&}<m0ig0}<2~8gbKHUm*nh8h`zvVyC*%XimH|%+eEnHoL5Z8SbKFk)V(#M3d;28Hf^@b(S2Fq2H4KMr3l1(J|EP_hf@Gc!gNKOR2CyX6?J_N?d0}$$p(LUtr(rWOC4gbK7KS|T#c&_z8?Zm4*pD{;FKtn3E1RlR;$8pL3#qPDQ3T06O1JY`HbKPr=^}2it8*^3`e#4|=XC1#Yf(?%ryB9t)ImFi(I5|yo5iM|-<nAf)^wuZ-}}K4JOczD)FN1zgz{Afe*{rrRuAE=5Cgfy9YM;Jk^yf&@L<Oab+sdHfy)Q3+`W}VKgx%_4585hIIIN#kDAD@_C=xSiK8kV$jh>sO!T93Uda%8+?U`Yx<?Zgmk#8QSMyBy)e?HdEX3ZQVFBQ>L_-_n5l6K!6KDJ?(1vc%(8C{;3*laLlg!P<bTdz)r6UH2GZ-tj_>5<nvuZZ4+qYJE1RaGJ^-de<mL+HU?B;xU!>-<6{=-&X6yB87#mJGs3_clUlQpbGCzqFOaDDaW;_`fmz91*3m*>6Ou6WXoE|^j%SLW*_ZucCQGG*{^-voXeUg)G_>??e%i7gTzyn$}vQfVn6&dQbZb}vZysl3g1mXvAo-<>jzSTinXA2D<8sj~q|=4CDLFaxvTA3AsncJKYq7Itm*8otGa;p^U@g%1P}dB128$l_5PQeh@V`QP6^ehKT7x28UvLUvxSB@i9T<Q1x`1E!bcir%^j+Q~xTsMXflbKD`V!c?+fc1pf{wGrj7oy=w$qIs`vnNo#<L%i7x^}tq+CB1Fh1gJ-7x(o<)X)C;0vH?72Vv3j)Ooy|cuq_gG6s=C-fLL{bT2d6xGOzpNITly7v>zqex%qTVvm2n%T|<mG4YEtD3R0kf<c~kZ;e4uy4;17|iAT1V`h{@GI*%wM1%BxJ*<(CbegN5b1VXcIJ>jVr{k)+wzua=NWQb}mMRfMpks_AU&;oNsNu}k}_7WtFV{Mzbu#@v)_wb0dZ&QCfM3+?xNN7vjh^+4;0FF)H9nqh3_N4?cMzF7jr;#?Tip{{o14Wu@KKTnC()`bK5bMeBD0nY1%I!cu`HK~6&wz7TW%~Tf47hEcRRek|LM$(Eq|#)UH=4=U9fE2V)Ob)UVD3%OS5{nTXqeR#`G@lq?e<IDRB4SrD_M8kKU8G<HXSMOc0t{DD6+Y-@F{zb57^9|0w6eAgI(R8oUu!cpf%P?_4HP`Te*lf5GknCq$|S8v|M3)XJ6i)Y@cCXeZV$}r?c$TfApS$ILQfB>%hQ7M`k@}#joK6ui&z*VmAF%P}WlexFq?8TW2rhhrp`4S<Q4V1|j45!BO{6GoE(~jOTy&`u=qbLt|S%p1($cS$sA?{!fR0-l6<8->iBC3C0r%dvX{*EOTaBF&nZ85VhtljZoG3BMs)`HDDgjNj93y!wo`x@Y_L+MK|#Ja5?QTpSF@}34ddcK}r#o%@^>?`ik1Hf65cMS@);Yd-~n5bzrWgZS*6@l&`3EiNg`2oXwk5${z@<FdP>b_r&oj(clI)aCdJ_`gv583jq-?m1Dr&U2ruJ8vLJX-Rtf5^C?zzO|1*k7^_<gKNNuFDe!P`r}8O^<!%C!&RV7onAlUtyt_d-FeF+_V<=4-@J1)sD|xlcBCj7(AI?$d@xoKgvqi+2tKzA%X0(`KJ(SCXY-)54>BiD-xBg1G$a68C;qC_oSUTD%Yv$}R2**753L3o<asPd9^cX~#ntZWbO2awb>1@A`vlEPi+`f67Pw%;-q6{+-kIV?o<@iP03Y&<6x&D_~unF$ct!Yumi`;V@8!wmne4g#^jknf7Ov#KV5Mk{wTUPhk+5sKE=PgngVC!2k#10%&jt|9U#FlT1?<H-4-^foka<$bxSVLf=8qvtA4F3))NCT?2>dc{XBNCfKs(RlR{vC&AI&wb=CJXAE+#*~WqkNST8t+mamhlD_)ZrTJTKHcJdrRuNXfBpyT_pkvCE4qF)UuqzX;tRotj;2L7|n({-V+K2%~^QYx(lUJ0l!zvA}m*ns9YzLrpS2L$Jm<&Y!}#<>t1ps-lFuqfw+HGq-^+kn+-2|+w38U=d-4TtAM0#b&}|_^P)|Z9?1C6^n_k_-^t*W>?Ml2+tLm|JjqYXLb<|_Zyb50?TS>QF)2)mmnGlKjZD|Nx2y&Y_3FgtEq=1TPnm(+^bbAtqUqX&F88Bg=7r0=a)uc5=%viVF5uvPc+9MN<@jVu18#s{cCCBOvgJ=AyRupg8}D+lh>YnMHze3&3Q@i|*fU_IAmd~=ahuqYKg{TGXbt|5rk(EoKSQf-ItaZWy1~?KT*ldg|H4j^oid}>_jr*d)|~+;CU@7?nkf+S1-P#5R}`RK+R|k)Y7OGU>JXzbogQPTk-6wFTUW(J*A`FZCou1o6A!mt;VPpkQ2j}LBI~8v0SJz&Lm(trYC*yA77oG&z9tkatHwXYpZrzW2>ZA>!L{*uQ5_$tL^!vhcv!d<t@{8^)*UI`ADf6x0xFNIQz@+2P9lX3yCRL(e!Cixjc>ZU)@@|jXXIBgP6E{hUWGu~FcsLGqu^?Vm8y6}EGVfarmEEFwr&hdw>O5}aIz%>H&o#!=Lj%-JW2}A5qJG?j@(R{j3S%M5gVo(1CVM6n&=Okk4(oKQ_i<qP^pI_`#!VXLMX^s5--)+8QG3aH6;v23)2a<J{#!N5Knmul^hEG!D?e5$zN);))pe82LH$yg-dy3$);Ga9Hw6K$ro@n<%^v<La9eWDH@llK5j*MJ(ts^T)zB)(pDIFaLcJD3+_7PbD9S?a-%zyESa>f7}}{JhSDR+lqfH+t8}ws_yFBhrao0MA<OgIQ?fh%Y3gN<e}47q8vPBPJ<~h*{^y-s{B&kLgpT{ZmjWAV3s2%pKY9SQr9GTaw|3xvb~|rRx4T>4a;M<8r%vE=UK{-COyHnCUr!yvh^Wj13CGA24Bz0erf!6a9B1StcopkMX2y@DeY-?W<UNy0T$Tex=*-PEq0UiF@;PZ-x~!@jwuA#eK=29qF0IR!BSwnTE%dy{z$hElZ=(N69}PZ)>7mi>yjag5f+h^LpwFMAy=f=cd3S_0=mLYk;0bIv084c8Y-?)=`{7qU4o6tcjv@wAY}yw+mU1DWsr{r=Lr&!e#9+de0Cp~tEGa<z={}CbKR+wOBmd#g>wtEVUPRY%=s#=enon!XJm%1zDe^!Sd9R=|;4ZmM!eN-rlc+&PYe4d4%{_I#%<;%Rcu9Z~dGRFxw0@;>5QERS780@yKYC(MUg4eDIe%Pfca@Xh-K!_^(PJE5lCCZze&N5PAOtG`-co*$uRUw^|KaBkC)cg*)^zbRSxVtg5{fJlnA>z_XqJWkNev?MjT%^@=T#w4j>5H^+2ke?nvIT9r{*FNWw2y0u2l|;!ZL@V9PnTW{X7MDM~WrbM0zlJ>2ZxY$wVojyF1Dnt*@bLJK<|zDUemPhUDBt6|LqgsfNr9^V6|0%yc<4v}OLW2%<J&L#PbTuRok$!+-H68RcreT38!a4{;?psJYCP|9i^@jd^*{GhIm=@e4Gke|#nCkFB-HOyA3HcfYpXNv*MFtK=4Tt~=OXo)AGRrskyA<!M<bM?271S9F%v0Fk!T?NeE#NJs@pUITBt^vrF15d=-HuBlqSc{d_&0A^gbd<y)}Zqvm~I6gJM0_fHebJ08aBdl0FD)nI01QdlZ-0xCIDvBiVC;YIDuizWQ%oVCk9fI`h`;it9U<7i}b97B^!ZZ%7t1aRGz&)%5&(d5TPkN>)it0%8xOOci5cZdJikC9&rK^q>G|=~g5QO}hmt=S<EtOAHy$K+Hd^OM95eF4tb_M|UxNPW*?ZJcJ%Xs>FzoFOF_3-2dN1Mi2_C&|LTL*KIkA!Qd_lsN&a)8eruh>_uc-;`c!}HcR?Nb;C8XMU0v_JtP7lXN+8oq#hJ`xQTWyH(y-u6MXZLEnMSeJCA7~V!ac%Ua4n;Kw8&j3ToM$9#AIz;lm_|9v`^Q_#SI*;r<TF+#BVBNo!(#nmeKx%>IG$%B-Q`wuA_t8c}X;o`#@x|PaY*@x1^aJ2TSe#r|NIokR5Gh@>NdER4*<uf@E4fnC<&BGTiOCz6%4<xybAb+PU%S*M^{5W1;@ZVYsknBjOz5@$H@bH@u&&Qm9(1%`H3QCLVAoIT<x03>%E6X$f$OZ58l8!0lv%b=cJ^}Hm5$2W4cW5}tlPFyP}GZOnu2lfeA3gbS^1Z5UEH*X^BMX!wd7T6>Ru20(wSSGT(MaCrSpTF#M*ZC1M50&1#dO(olO{o3a}0m)$W{EK(lU4mWGLSRac5hKSu<<2>Mc7-70|eIUK^|y+q=fBDZk*w|1~}5F9D<05i{U8Rmu(&hqNASGTW0V4h62duOl5@f1!O{A(0X?aNLIRq>@a6|gD?RQz%t=FI2Y0IvEXG&hRl<<N<e&m%viQQ%W~s6!m)`9{2{Xro`?^hD5$DX4kes|v?;=MlNoA8vrdbh_(+Ba@|8gGc<4zf=a2JJ5Sv=4NKL*$6EAbz$LZb3H`lJ31ihL()GT%SFCf0*ldPBdF98ba~>n%nN;?96fuv$Hv|w-CCg@Y5Szejk*1DZ;RLaRs-QlEY(#hy|;oZRryT2RxR45LF93|3zGd1$(vH7I<>^yT)aN#J^)U;kjB<EtmNwm0VoBAL#W$ORA5}H(}lDAdhX8P$OR{;Lr2`k#-xKzE$NyBzaAZL()t$KcZVlE-elP#U*6A6{ugBa_C@+OjPJb=Bu_7lAK>30d5<YdS7x9JiqDMRnVCrDY$N3X0GnD;Isb5=c%U&iu+nRCV3cQXL>4$9Mo6K9LkIH4`=P^he}YBG@-9TWC_6ZBzKM9LgHA00oVybg(vM|g=!S6@t0Ccs+dZ+;VBI9a!vl)1qOgqGk5*+cM_|2T3G)cuz<Osoxi9M;doq;5m6YwImp@$!mV>jsj>dDY;13VwN`7Zy7z-tH*Y`}NckFdDlGAZo7xT$(hOKn>YO@s-t>i4y5-@X4QW?iO_?4LxDHdXhQ=vzP0`?{j!ER?w!6Qc#g^%&pYE1uq2_FW~7gEH?!FE=HK@taN8$r019w2U<?W+d7o0Q@lcjWtH{1`E^af3$v7P^e+clsH0?Sw9shg=fTRe@YU!R~S^j`HLWT+7@6jL=U|=%6HP+B#@1bg#CUVuJfsu?+INyX>F>od|U8BI_U_<cL_PYZ>hBuVVx?_Qu9`Mdx_UZDAQ;3-W!%;aJ%bPU&0fU+WrPZ_zLC<D-{dOwjl+OMJS})IhJL28mqCTm{0^#lsKf`p@&So1jv*ZrB@Ey=vrb=F>>4<!hGrbYl=$8Lv3|o26?8#A_)*B5@<XD9^78t!tKo`wrz^4daxS=D-{5pS8pf>?HC+I6dLP)ntOnU0eP6^xg|hYnPaf1Z)!c;n-<4U0!T9t(pUX9n}@&u5N)XB=eEXV5zOotK`9pf?sJNc;RgnWQFRCZ6wUo%^45ODBFPZOPB~|jMou@A2*}WbYIk#%7ir^<aW(+%8}vs56af%#-39T*a)6R{AI^+<hXVij$qf9NMFl|<oV@<ZFKWD58dOs3#iPMwvxTQl$UV>^;zhp>8e{98CV%llnV$Qp}bA=_4Km7g7|iDg}Rq;Bi5>KTts+_(0)4*Tq6%v7kbk*9Io-Shxx}ZqCU@Y%l6zZOoMs)NMiv5&KC?HO@U(oN+uPVX~b{#YbiUY^Y9ascm8z^?500}`}%*SDg9*Wxs*Dc04mA~6xuxU=4R%tBg=D#uRI=sqkE9RBE-arVF0s*52j-AFym8ZyNUA#QoJQys|*^IK4m(;3f@S&<sbXV@{cK`?5!W6qRE&1wLjBSGc0L)Bnbf;{mdKfJZ95SCbyUMFdR)>>M0KO?xuf<#uGd1CjCZ98hkY5vil_d+$`?p$Z~ZlgoAJYe3qiRlZJ>W5acYlEvrF!^nRY!%i7Q)b+qN2w$|1@vb<Xg$&>Tr7xM#lC29j&#PKqfuSgzpQi?sa(_oAX$5CQX4p516mHO8mSzaV7smnQX1qyRr#Yv^?sf1E>unq9(Bg>PdklfrLC2ZXWU&2!z*D&R3b~*vRoy8(eXFneETs*)csTllHB9yI7eJ>xg%*aG+ZO!l*;RX11&_5$rKpmwQ)frqyv+Vg9C|gc|xEVy`IG1Sht`wQ)c@Zm{LeFE7IZWN<SDP_Y9$79Xg|vziJwxC*A#rqtTK=p8!Q4(GSvh~rzT2eeI_L{?MBe9Zbn@|cU~;;HNp0$1)}&spy8_xNbGd`WpHJL*WyZ^e?xHha<y^yVB+?&QZX+eEE~U((`ZpH8svlW|6XQQBeOlQu`Q{XT*n~G~Vi!B=R2II3u?`($baK&@sgR1M0GWI#U(CRsb3;MTpJhN(>W4w(x7;Sd`_PL%$#Hb5WA1^oZWfcv06GS>9AteD6;+CU)*<OuXZ?JVOXnL65_(*Qinz@~^*6UMu5=1QS#_b0ssjYDermWVDhq1T-l(sLq0Z9v#h)K{$RdV9G%F}7EW1bD0UeYnr-N0x0EgO0(vG7}Wf4wfv@kb5In61gQxKx~-lo>+W5pTR6!0~<x0`#tub0Q-%!}Y}cJG7AHb(xZky%-m!wFnOk3Oths*Y2lnxtfuSqgGb`I+68_XW9{g~Pc5fdf92qTRW4w9Qz!jxD`YFQA;dOr`I5e$^F4wWy}io8ZfN^Z+c*C*pGf=3Sh@ql?~lo&@qLaz%+Nk9qXGl3)7`=KN;eJ$I&9AzME#=W3)f=<czfPOGL~+g$}?w+4(fysQ_bSE;6Z5)Mvv2s&FkN+UB24|5eJ9FrNwZ7@5DcCT92`cmEK*ivlEAP`|NLuqLG>C{+F0t2kE`P1p)-u}VCLC5L%6HK51W`YeQ1crA9)sq0p5IMmF|51-d8EFWEL~}F)>O>#ZAX?-K=O13JUFWEiDeJ3l-v?Q`O&NjHr;%Nu4mBn+eBcF)`z}G&B6Rt_D7E{brw#bP99t@K=`x^#j5;D#!7vjN9)V)lad*}{v}zO3QEFF-uT;*kp89-jsn2ClaBGi%;!Kvalldlr$WfS4<l!!_8ys21WTY>U;CyzuG|~Bp?;9)~<~36ijxE)<boqy{>2nHY>Gk|m$1}$_B~*T7LZ--*yW}}WWd>5bE~5J|$~4*&1+(w&p1aexn3XW)fbKk7X*LJI1gv>&F2(FZCFe&-UPIaI*wU{{kK;)2yaGP@8AjzxW}dg){dE6Iuv51C%RB(ddpC+jX;e4)vm}N+L%YdYf<b)Ie2m&++6or?vIZpL9Atx`Xtmto`JD;1X!j|S(`=Zp5-O;37RLAYR+eK7oDquwWLKbylsXX^s>ez4F`T$GEzfssDd?+@o|7jp2#EnIZS<u7I%bAs>gDgxm+vdldVVyfs8If}p|Q>Ugc|LgHP!^0M{K&~dN7v3$!G)`IvHs2EaA0EEVnD(@l2=NwL4PxBB)qlsR|<9H4r%iH6y^BONM2-0Fyk)vjZgT3S@i_l>9UoMqlqyeCH|Mn&24Xhl})GFdqBS>%CS1q$4>qxt1KpZnKHF-TIC2ts~v?>NU7-91Ct}X44kVXjXNYW#t!Fc5Q8{cXubZEun6|k8xo6i6|pZL3tfd3Q6TFcZQ7{o@<>ta`H7yVOofvA`AR&AVh(|&M+!!JR*kW@Fhe|6FIU|N2JCAv<Z9TQ*l|@f^`<jZ@dI0b~L^iUW`5f#t@G$B6RzcD{}wn(5_VHE#O4`3+QT+!1?SU@x~^yk~q2X$2ert0OGD)A6w7b<}A$K8`OZ5Jg4)V_#)5)UV@+a-*<O6egbm@hQ_OcNI)k&KU&-jmlX+e3_*+)5!yw?0i7x6TCOUw=wZ?uaQ_5ZD$uwLhsTb<?b;>YL1CXqBN^#3);~kH`e%@4(SQHnq4Q(zlDdHpF_}n`bnMqF-lD_1Umad9G2*~hRM@lPf)H!KyR~B@Yf1$vO$62`@CE?rpX=!Cy_OEdo!31FO7*nbu3h=N1SYjOFM(y3KKf;j75zjBB8OD{*{Eb>nj=K%qNZMYUAv%n`R<Y#trW5psxT8QEY)stCM-{-*&>LoSF2Czid|79LUeY~(<wcwPAOi>BZ)>On36^Q55t@Deyv4LXQjvw1qUY#*S;CeVCmza@43!v7&k@gOPm>9a7TG7ql^rHu$JLY-nzr;!&1dMgfFT?NEbX}hr0X}S60;#VP3LkveVFu{U^RRdi3st5Ka>#i{;sXN_sPK6SH2nC%(3DHaZr^wWWi>klKiAIz6At@|oKelNa+H4CzM9zUhOdbluOZI5xTD?Aq0|SAAtCUG#lF4*Q<#ySmFGaUw7^VCtd{{yoE*mYe;KmdT`qTJZ?)>?uU$3kWfWA&H!CWdqlO9@2FduQ>gcspkFRERHeE*D7;3kMQ=8dZe#!rHT{t63g6`v9%T-wK1wC31?I*m+$zY<CLHlu;3-rU%5Ok@C6ag#sP4jBG=k8;i6e{C(up7`4{d7K}EQ9Bx(qwXYp)7sWh=G7YoD&OZzpy=iHg49lFwk?Zks~G4&>b0w>A$JO)OuHX5Z93JMARg4ID&7{#+jb`TzR%rkasfYcBl)$BsZxm_8C>ZQzHmUZEtA$NB?2FG3L2FF~TatK>BPCL}KOHG#m!}(jz2V5B!<U`)H)|DSWD&@H$ul`&db~E+0x^~Iv3Ys%-agt(6*&4cA1-VP>8l5$A?TrrAn;7tY=ZCW*!x%q$tzHb?bK+8jYcCtS5FLiC%A?hGt)-`Sw2b)K46MRrv%G*R$(TF~KZ$$W;tk<|R2&~8doFRRoryVZ#EqhB*RgXVBE?oQzd}5C!e`k!4=yc4$||=DOF^cfAB$dQ%P|%I3H@P1SBkD(v(5<v<_|B1VyHkN{IK2)FqGC${^(;IqIlI^Ag2<!j=;m}{uB}`qZ&ciu21JA9?ut<^4caIPnVqdrPje=phNch;{A<Ga{X?Q!%}b^A+uOJ;gAE-sj|)%kdWNIKQj|rckNnoPB_F>t&N1tVy&-)t8gsaS^=o}Rk2r2ZiO_~#iSO0{iAB+(tS0jK?>7`^RarrFU4)Ax`lp5{EDB~3jRxcZ{}zcuZwH)CN?;`@SBrB?kmB``@6Y6FLagADJ%1oAk*A_7lcoIMQnld>tSUl2?b``Nq`DN6Nol^M1adbqAqmDmCs9#+#khM%+mpWXL3u}tkD%|%vZ)Q@=Gjf!y&3B``=w>KfJ88Tu?|++(2Mf1w5dfbk@G;Su&C6+*^i){)Kn1p-?rg{VEZ_($UKZMiGR*KqdJI*7mtKdK9X-8xAaqO}Q#Xl_wKBQ(@;D)svzSUm}j+QQQ@5M6+&W!?%mdt=I%WIhSw>aN!TFl;P2Q;!$*eBE?0uP|IqWam>3d5FN#gn%lJP(sHZeKzX<T46;Dl<$K}DyEx52ssIww?WNJS3<&&P8tEK4xo8%f0HBhrD59h!1edzvrEe1>(T5cAt7ZBSflrd3aR7d^TpwM#jGUWYkXkIy%2K6UHmap|3!`Q#-VIWg%%jM%+{(Ty>)z#RLg%omnjk;!RfOS2b+m-R{63@{90fVtr5{8*nPAuDA|obzkMk+4`N{1f7gQ0jpS$8YcK+icC08MAX>EP+kb23#`kN&1qj4xIRA68<e)jEQ@T<T5jvT4Qk`T$!Fw=>yP^&$dyg|-qOc&w>JQC;1Z@IYVc4J$OU8-Uwa(Hxoh{L&Ecas0A1oI+Gzw|Ts&fCkHLYLmXA1eRmB^ci%zW=kc4kH}D2r-<xUV!_Dswj50zJ22_;<M5hm+jS$l!p*6=V)$VPECoW<B6lNfse3Xd--A^j?B1Krll(%Xff5F_}R3bKNbJ3i=g^N$yB}!#4Z@Z@-mat3%x}=Hw#<lPcvR;tTC_$HGt(O0=0OT$3-a6>fAt(t1*RgE>H*UJwV&OM*oy=dq>eeJ~$O(B_7foyu%vcUCpv!iuFo|!yem3BUIu&uy;MR8l-F^8AV%JPV9`e;mEv?t-ScluF%!v=K7+KV;I?;c+dRC1VimGG_amT4SlAVV2ei3aX6~Ihy;PoWt4MCZj02IQah4AESz<CBL4jslJyuD8Rp~WvZP&Aqm1|q3Lpt_8DKaxHq~xN<x{?u+CpH)Yks-$huMOnW^XJV0+XuwEb%_`%H!6#D56)e`?2hx#>F3Axh3%e1Lb*|F-lCQLvdVZ9W0~5bK=Yrd^xvkFZm~;0U}=C`w~p&Q{)GjKQav-qT-WEmT%1aljYe9nClNL<a@4h{>ZLfUZV_@H>4rR-SPhB%}{}aKXmej9_2@qH3{)ODqUpA6s*;QPu5ydW<$(@7jE>@d=^TXOFjdx&eVqoB?F$+F!55|nb9u1QHIvFPX(ZrLotS?Uv!%$?k061=^T~T&ofOf5ZTiFF<)ES3tMymi81tq8t8oh<4^gzq|(zx%gg_gS&m$laQlqTz&xn~I-I7Nj$IuYfB5K)<Ijxl;2oN+8JNtQQ|tVIzvyvs2Q6sZw8cav1vLYW`Mb+d_+dC?Y2?k|K(;dd%bz#EsXN{J><OnP=b%Q3O@k3$_5&s(#AL+dFZe68J6^X?OD{-L!QVumgN2)17vrf-ZXKDK=&W+Tjt%Rn`J7p(>&+#c(HhVKYn#hwojStpuzzxWBWSl`N%bv3N`E>-8*~!K+1(v12Vkm{Ik7(+f-VFDaC6<yB2hjZ&*NZ}EumHAH{!Gtk*R;iTiPz5G{22OQ%7{AXG5abO5@;S7MJmZZ5-(N_-%n_)K#fgYrpuArf0kaV#4_6-#OlSCP!(jZ*T32U$>rj_V%csTzwOhcP1D@G6{EQK0G?@czt8COZ<+RkwNt=SVxYqiwBJ4H4_YZV<w-lyvDck)hY$E*dZ(+59ID7AF#r497%r>=xsb7xrz+YY&^h6%;%H8Fe_)HX9-CKP1p93BOt;75LpR+@)uNM#E-J#`sr0rF(J9TyPikRTQMM=;`!3~eH;EZ*dR`5Bqp>0B=)NyAr7T{vHavO3_+Y=C|n{7^iT96%uD3DDpqo}7k_`Ed(Fg5I>`rBNJjf^;pV6u>7`Q6?Z6~hKeVK$R7=EIm<!<}27bbRpepYuH73d=%}wzc8pC>M2+Ls=SVV53LS*WM5f*||kS{>qlRn8YE#|ORIwKv0qjgZw_k-#zP=$8gOTbM$=4ytcA6bK)m>ajo4{U_&2pG)fvpRK;9AOI%Sj2T0P6xd}&)<^ou2y{KL1fWmh=>yqy1U{U%nr17UxXF22^^I?dFd{!5o<iILi5Fx$SEK;;7?0Q((>`i>02K-6@4{a-Y=`r)c3Fswa-NA7j_<HNnl-7xTAPP=8&~dKsk0Q#s)SxHBLbE=Esddd|(4-pd)_40SdV|*F)s&b`yxuz$I|-nx+DihL@j5or<C(F(nm^Mb$%KO;F?!aWb1xvOhPQq&+0CGOE?#99^t&WvXK7Oe99u;i@D^O1b!I$OKK5wo+XYJ6EI>DSKNqI-SGeuzh=aZQuq|dgAYs$a#;=bl~XCs(Ef#EUs$8CYk^9Iw?$T)C4noU7gIcM?6@0R^+=o8t?W(t~D`*2TcFQ>y$Wh7Eso?Ij<eULYi<2VyYiGa^qn$Dz(&{WmS@4Wh^&l?q|b%R)*N#FkQg_(8LQmadosz_JE`ELG!SHyr|BCZa#Y-udaKgVh_c5Iq_UR*gy#PQRlFlPC)7Pa<LCHBlG-|g_<G9)PPhG`Gh~5wV>tI)>roZ&#XPA41+B`J_f<IERQ+5+~V3o5EW<(ee7o4E3IJ|fBun*AtEzePDRDh&U-0c(tgk0dC3@AzO7=vLAUpXu%K9%@zIPw$RQc<#94IF_kA>1Q=e-$$-?R=np>A)ypu8SyTC(1%#1hMfPvXgXt@F(G!5l>e+oPf#ZD9+hi&eRWafmYhls^fFctwURHjkz!rY2QsaY@`rqhnahj5jDHvAGBb2vNi<qD*P?ja`Py00jM$#Bl&gx2%T6X1km<ln|I&(4gw0v07>y1jY?)dk3?5tKM>{=6((yntW^O@Nxz?VOrJF^R)*?V=ytRD_AEe9-~-)}YRHqz>yL^>%Q}jE`Jm!2ST+C{_v!>lYqmTmEo;(l0bfpNzd(<|oj^@C-`Cj@+gZ`tjIT^7q;?nX|`WgdWhz7`Rkk{y@$0e7h0Z&Ca^HYT;dgXjvUkYMz6rIZ6|v5|wLc;HAE!S|{}&W!aIuol)die7=ct4P84w=L#(PG02(8eT-kpQKHwv0th^%#%@4_c)vZw%y6O8M@${jxh{DB8-nAw9vo+|Cf&6<Oe93rp}5qMo&#_-Im3LL`M<;sQ{F=gFMT;fd2%@Otz__Yyy3ji$Y|yvg`Wk6&3Dnux+^CN;5@Cdkwk#7e9^dwC4u>!A3Qu};vXM_F?X-hYT}5TIczGr3B;;ZlW_7Un?lBR>nKO&c6cf!MyKC>E;fo=S8QJ<Csyz;#xBa`#bt{P08&$w#vi%oWwpJ9P5Hg@lFPtp6V`RHRNc6X8ItLnZ7wI8_!P%)ZqT!{cCM1LL7<Hb^bgC;1wqI)5{H+A%A3s4XG)r0zJ&N(YG@oQR#8ncT1I<mPfIzpGfZBD#7h-Sgvu8LH9d-<9Lpk~PIDk?3eM7Y!aucwg3L*$a2V3iqLF_w7LH=eM=CpEt>+*8`!jF)yd_Et@OR3c?c_u}u_(--aT;gs5+x_&zsyse>*4)FW(d=rn!>b5NnwE}Q#JjKuu~F>mZ9fJJ5kGiw7=&Fp79={7!;@xVg$m7nTwSwM+k4s^CXE~YW+EK2wB(motHjxm;OI|h5ir}VAIq=>&Hv~$q!$5zp*w*IrLhJl{oTUiGFolbsFnNfIbLE=$9f+Kc$`93=mKTC7OK7C-3KzSB&lW8}pww;iIs>=ZLSV0`AFd)&N;53BwJ;e>-?_%Kj2Nm!&0d(%c-izvl>=DMj`+^1sZuWH@}BXJh!Vjh5}j`1L_YL$y<YssPfp9B1)oKWT?C2zh+PnF+072CxXlbT_aZ59)z-I=t$!^CyP`QC+M$z-Jnub&AGeVKa9Y@S&NCUAuwBbyyE4x+38j;o(1CYO6Z6;d*hP!FA|Hiv(UiBFVcT;R*n)0HTkN3pi`XlJ_Mv+kbB6P$Lo&>Tnb5?Wi7((hrv}{EaNU7km2$O}FU?rvr>5RVwtDyL5AF??pY#6mHLP^P3+Ue8cWl!i|<7ye-$CxCaXS^iO+#-l5ww(zIOY;)y`ux-C5#vdtIcaXny#WmpJ0@R*$qKNLbMfRxSEt-Du%939PS$=ibS*Rb%z2ryVJ1HY7aTxZPYO#J(Mj&Pt-h<UCIbp=BcHAf;oZxfD)e-5(phCBNPN*eTC!uY|weSKKFFppRfW^l^>o+GfQ0^Q4%Re@yQ*h#JWb^lfb*Hjw#Cc&wo0j8Kip*aj&J<qR9K_ZTm@mV~_#}64(_L6{RTWP|%QNPHQ9wWxc0MtL#JmCAMMTPXtnglpG?xTnCQw|~bCZ54t_!&}mzu?Upv#w4}HR2Rc@qwQZTfhR9`WmZzDCABP@}jM+4BS=**j2)v<?&HPekqXlaQYd>S$WXkA`Pq?0C+wYNmMp=K6Gko6k_`#^R**K_@1Ooiodd}c}5Y8l6}Jyd}}BBVkX-gdguv;7JcZzwkh5CUoyo-v=Yl+onmQ!uTxVmc<V>_xqbHTrhn-Un~`aKFE|8ear6XI!A;zLmrX+lCcKlKM|f&rLSy7os~v;FpKt02>(mte`#}_p=hGRv&^qn;OOF~Y{aXH_bfh6pgqj37&{LS9!IX&GX)QRv`>BB6UHZ{O_PE>m$(d1rR3@51QN9s;M%C?_i?w!YQ|W>Edv@cA94vOG5!vWM`i`o&22*KGlLl_yS|;GuaTC98V~%0u8{6a;Ct#NbSo2;j_g!@(G*n$%8*?B#+38A*h9l5R=ICIPH&DYG<x_l^pQvcr_Q?fFmc~$cGc+W$@DKF=+UBjL5lB3?&dGh#w@?(o$h_ioHrG5M61CX`c>6WL!x9e!iu=Mz2d<ry-Fh3x522`Hgue=xZ@j;4312wvU3q10t}DW23S(260iDN-qMf*cL$oWPe{_?i_cWG~MsVLws#*pYx~&rw@40PRug1C#SOt|z`Ffd7@m|i(WljV5Jn#ORX+{gcIIIDNyw$)bj?0xzz<~)p`Bcd(+?hIzx^L`1x^L%KEu&prju@nitC3Amu3md&o|(jgFMy~q$uH`BZXPgYkbE0)KUF^|CR_g1T6xvOgT!)PUO>1b0-$cJ+`gSMwTyNV-Pi*bxiAs9UP(W_cH>WHsHUQKwcO>;(0^NdO+IP!q1q>Kq<GUUEGS7bzWs)H&=zGlSZjc`^x>l)hFIYiMmtF!=9HVVm6zmD!`r_1qo-Fl=lubtyH&E>wqRIbcx0Vn7^Q?&PRfEmMb$+3aHwZT^I6dcTz=s(k?9eY4Zr8hx-tU>?N<~Soafon!5c+PIHB;tHLpH`QpFx?Bi7;}Ajw5p(B0{l6#d_}c234)EdKYb{bK8zL;TRY-Bvm(zSRRjC!DlQlBT*tFQ05cnzal*WvJ5}d98vPVj8!l2GJ;(dEpKUsCZ}W|H4|ltCkBlr?h4sF7$dkr1edQjKho}rrQ9oyv85zT|=*qE+A}Bs0~yBPZ~?Z;0x%PsBsYuKZ_W~FP3^KOr)NW%8YgM_n=#foHPxiGWYGww56<<LWzhdal4d?-28>aD+f;T)|Ixi<&H8oo1-3GFyZSYosUMoKQ;@}QNf&1JQjv7_H6I<)lXZEklJ5E9>W!~pNuJE(xT=@lj;sIus92YPgE2@2^o4$yUi)$75KbFan$Y)T}uk*IHNi8-Q|+uDg?*gVhqm5M=!gW*aliV3vL;Ll)8a1f#q&iyjv~aZ0+2{JeKI$mR&9ZFWvd_8T%8;(q<-qks~+P0Xuc%_`y7R@EI09KpAC?1;f*V^VNb~@I_KA8I}rxBqK4D9dI&^Wpk7N?n<m)TX3+G<}L*&b`!^;0hTNN^ZUV2{CGoaei_9nf8V|uZVy5)Lp!mR4m%%Cy1v^6&kss~=hd*GW9q)0?zWU>E?VO76h>%9apsTtQ+|12a!(3>5IQUNG|PKZ6MxhD7z~n*;+fx^%>6oKV!DtLQil#wc{!wE@DQOl(2yoAB2;;_X>k$55KDY99u|^1alo9=dCfFFM#GhUPzMf@)`Y@f+q8LQKic`vMGcteriXuwd%h$Qyokm0o<Jt0eFH;)W|ul59??D~s{gI!mMzU5%ejgosW<~2q{BKOq5TZ2W*GocAuXOeo?;hZA<V<jWdP$OvvE8k9nFyr|4ig@Wslft1KO4O=oBB-p_o*sWjrJQ$mV$=K0R@Qll=4Q%fkp;bgYl%C{x~FfdN&_p{axMzMbW@6bV@Zi4U)3c%=t93jC`6*J1`iA&l|ovoOB5-R`lTlc1lBV1waX1jP*k3nXT>jijQ)AvtTqF42KGt^*7=aFHD9ULN^}%~=G0B}dG~Hbt+9I2^*$WykhHm{ZdxI*OgpwUpw%@1>a5PclZSpbMJC<D74P)p&!<p*gs<BEnDoX!JPsl26LXnTfvD`zdh)97Jr|h&^VHzBrQZG0aLs#4bNmdYDobDk{v$kAD5;om<S6$2`a$)zrZdn*RKKZX;ps30uJb>-WdwExam*-7=f`(b%#cqW8nH?&&<6nTgev@f_u<DlCz=aXhA!0i?^bETKCS4W&*!l;W8Jl3B`1e`4Cj6C&8Mhv%LdlOW=GpquQ2PEARXY!rC?Y`KUj%UwAIF2>uq@Ex^P;!(xmZSoc1pIaGO_w1^YX|?=p=<Kft#2<%O?+dc5x?+zs7lA*fbUtb>0@C+#=Pzj~5?-1QtyH6eU-;tK03fxbNy-cc9Fpij9~%P`{2hNL8s#CDpamNbM;HRcwJ96EJLw)Cxl7CtS$KLqBvuV{{vLbeZsfJuqny0=;NjHREHC|nJ?f|&)|Rm^J=DL+ZKBj;Ld`OVv`T*ou8eaZ2Qn`o?(Ox}NJ)@0mm%$MSNKT0J>Bjq9${}!3xY`SoQ*M60F7p5%0Y@Y<S}v3IjRjQpB{(<!6ZNve?0aU4X~94e#Ie0x8mdfesdtMzf|nnV%`Gdd|Rp5sZ>kU%%8^NV>rZ3%|!>D7j?HXR{KKk_Kz0>t&}%^(mnyL3f&%-r}`U8^gvfkN>Ymav3OzU*I?$pTY`a@#~bNL;DZe?v*UW)J;O@u2K78Wyn}XyI5+j8KeQpZBwsn4CkNE4nq#pB@qQBoY6-mP2mvQdzOFQ}PM-7>)sxDb$mK;OsgNz@NXu)!w|Mmv2Hl^S3AE2c|B2G78>S?K)AOgvJOWtw8x688?jLk(Nxe6CMLO)?4A}V;L_^Jb1WTh2ze#uY_D#%MR8Rg7Bc3&L2mXuMby3M{%~Ip%;he|pwm|v8Vc@6Jc)UQ1D~!oC!+dJkewxit(7>|rDg3<?PbMHY>>nM94yg>^;qeP9v@uLg>jZU+#il|KsUus=JeQ9$tVhEm-kLHZJL~nyuc%g?U@aZY{^v2Com=5Wl;(g@yOW;Ai|9#Pd7>)S%d~NnnpciviP8b)Ci6m&sX=v*)>o^=G=$!&6Wy&zG#Z^w;IZ7$%Bd!X;kE@H<$W<`EzDZ?hjEOh!}!-%t77G07x-3w(@MXbj7I29E)pDX_ptg*CNsyYaLO4|7Cqa1P4fYfp1bTeUM2fA0n6PeC2DCIY}n8!hh7IIr5Koe$LaazM_we-4%!K)a1Qury~CZ$Uwi~OroB%-w;E_59@GRezg~nUf?~ruUUl)c4ZxiDK&O;9FrO5b{%HpWvlsoWdvmDcaaa=%;R5y>z)@OGl26N9j%dTt*fGpbp}h(WBJyn#&u6UfWA2djF_@L?vSp+CY>I|KlR&z9tMQ#rlYgMuP4(F+S+?+Tx&h|&q9$}`-^CLMTF@L6(BP2-jUI8-6vUn>uyXW86brliP636Xw+ua}d+NLIws!I^K=GM4`&+ecmwh-4*2LEGbM-;erI>0tDc*S8@K(#t@x2Q0YyT<!#Ld$~ZY)eScRqZof&dKxBbfT*4Lpg;FtLklVWAsjUGY4_0G(v<88u3q*=N`_-e}|KYq&rp@M_xwsRr}vk&#^FpV6^;SraSikJ$6W%wxkvG_s`qlOFzz|Nm?;Le-gHU-Im*_*#*yAZ52P^__~o6;U33aoK4rI62R$_?t3DN|LaKg=NpKiUl3twV@DY|6HQL@{qGI;K3IN1h4DY)a}(y4qipr?7um2*Nf_>ame|EB^6cW=EE$BqX#{WvyhsnGD=s?iU(8iBh1)HF0HO2Q`ltcXOHnXT{B)l$n5>0$fM~H+B@AQGAKW6+{dHf<13`lI)`9BHGTw^l=6MxhhSryot-9p6+H4XRq9ErE>&f_%1#$>DCKj=?+-V6g{lK^uqFWgA*BRe2|(_Yx5L|41wxL)-#Qsw{1#AP7P=&onWkx{;;os~#WkP~*HroYLr#N3=kGtLn4}DAge5yzo@xhHd25@?Ldze@i~~=Bx5Ua68S&@*!f_q@fB?#yfpYBWo+x%AZdq}mv?TV@X+kz%ouCs_k-EJz;J?v0PD-3K_z5LvR>E6=#x*%h-&<f!n>2)jUjwMS4nX)p^Yrh}-gs%YwfU+jw~^R7=rZf(;Nouy^g!GxCHbv`D!{L{DWGpOrh6#*0*F2jqLQ?)aS?{2pkV*#MeJk$LjM~3HNQrVQT>&=yp~aYPoLlT-V}X!{e-)qUPL6zLqC0z2ZSq5KCpRx8iYK2VxG?o5Vdo6<&SF%>eA0*IZ^J1h9Axh#<TN;uL4xEc3k0r*n_VXGo>FSM^}!IrPa9Lq`=8xm!I=4bvPQk9Eqs`4~1EG_I5iR9f!lU7giY(%a82Bg0<TzEeCgu+A2&o;hAjb>t0Ft(($U4^4UY;jbYogy<$QYcPsH4GH?e|Y3^)gC*!Wf$T@lJmQ#}!(&-4~Sh}3@*&B3S%`>8@@|jh7wPq*RuDX%W9^+9Q!i%f?kWUvgOpq*Oz@^hE%6~tyKk-x>JMaB$NBEu$;vmZS=*gd7y^=9X@MeZXzSdvSAEMR)@7#oGr~4xd{4eYog(V7Jt-OipKEnX0+uG^DSrf+ISj0!P9<ywgzS`YIr(W2J*<xpu6T1^954&P>(yiduRsm~T0wgOIuqh|XZ~?-0Zbr4nwtU%uFVjqvuQ^g@#vUj@c=QP8G;GgBA=UIe?=D{<8|KSO=PLbn%wILOR7}2PNW_j7#f(V#+zw_04P@DhO)#ZSUGW<+Cr_a)xDP^%_;VGQhE{(+5Np*fa*L-F>9}-yD-pqOKMr<>RDZBU0L&X~fT4Bj3f}$U1>@3{)K3&trfGne`D`~34sIFfX7D51g>?vQd^f_X0OU`)ix;tqhuDtD@?{Be3`Z1=96t5h_F$=y`_{}WfkVMZ*Oj-<{`wGU@~H{Z7xr~<ebu`?yJ^3@z36?jQ7Q&xu6Dc`fd$QjI1gR7(4nX+$C3*dPD(O7bd>q+b+n~Yp=w@Ix8O|oxf*S(YI9<$GO3PP<;9oE87F8A{B>mSQE~`sdIM!A`d)>%kZDihe0Hf}@Fl)TjwLEME+ytuIL+bkPZ2<oRX}O)7M_7$v3qqeeJRS5eBC7}_oYLrI<T{RzXNF|X@79rYCrT%BkhO2!)@0`ALd(}kw`>aQZ=X#R3(d(G^K#9W#ypTS*G|1I=DQHTw+~;nTn7m?nd0m@GUT5NgNvJbt|C9UH?Dyt?Ln>K&+n+{kE$DD5+nl2lAJd@W=j|7eQhv!29+}*snxOJj1u&CeRJ$qg$9h`ZiH+yDKK!W|+R(MI3p`!ATTPCQW4113R&G8BtVj<cbfuilm!)5{ahf1!o&n5hjVSNW;ny?G(D5)wh;lL6LZZePenkhWWvDY7Z+=do5%KZ9$43D}Oza5ZdwSc>d^SI>mvVAlgNVaD^qQa)t_=YWmK9bka18ycw{BjQ@V>gIMXexnynSToO$g-*lO8s#0>GN^ZBS=zdZ03!?DqBwRcMs+F0+zf1&Nl&{K16a!<$q!$Q97PC|!<Kj&jo>w%J+C|&BSRy)sHJ<4R9alZDmh{_)Rw*_{en9-H7|L!ZnW6j$NUs1QEm|7QuMiLH9Lg@jMN+DQl|kajZ?Q1A9219QUZpM{Sy8v-E)vPAwt3a0sh>PF@XR`}Gc3DM5z$8)#}n~YF6NN?p?~P}R_@F&yKEXfP_|PC8}z^M%Jyqlg?#V(cwaw9FJ&|talBFx2K8gRQ$>KgnA!mF-v|I+Bw3{x{~|cxk08nBUdTjpHc%X%?>tRMUuaRx7OX9kzJl0$VFw{{R+YoyfGU{sXH7Oor-~r<F6Q}i;yJn@4d>ITXO-ao(5F^LYE`4~o{~~}wP<_h!8Z%C#j?7XKvV!Kl{q!Dt&le#aVjJ6zLDG(A0>j8#%_8Cc9LTkfbg;2^LznJ6#KL}t7sseujH;n5Yk7Fq5|URWIV=rneB^#_{&disb8clU?XHnh8Mn^79|F`7;FNVgKEG~wKqp4OjuAL@hvOUS%BCCK8YPiJKk9U;lsNgnOHVKUlo~A`1YPhkC;_=Ed2xxE4<h{ZQfco7H#on-|5PG>Swr6fNuDpDQH;8EPSk!WtO(ehnFq}4#(b_<lE_og?WU%fm45;_>N=`(l1$UVHah-n(?gXqE%jl*vPi)|H2eMc@ZwhUr{f*m7mNoAo2D@jN{1JW;9t-7~wY;OpvF8*sTp>o?>_-C`Num6!Ynnz?io|_!@6KJ1=o5Xfna79|HSh{9D+WR#%|bRx#mSiLcszA74AIrRXOn21SphjH30-jI;cCQ#bnqJNIxYBzeBw0!(C9w#|bg<Xzs_iACf5y9aje;VSE6=l%H&+uu2Cwlv@jfAeLZd@dc!A@m=-(Si?^&S!SweKChM*)w`KMIii2PQxhavkuMC8qg@`+WN>W3tvbXjT}=;w~si^gI^sNFS3`l_D)`vi_DZ`9ikU&K=g5V$-1iFK#J}VZs#C*7jYRx^DnRt?$f*w&5}Ioko~}J??GUmH@JZ<A@q11LPeV)h>7>{mu71MRAUg)KnKDqC@J8BJ#ZF+%GJvCG0tCN>2f}b>db#!b31|3vU`p>jArl>=;%?n(D8e@27VV8!)BO42knpkJrBseMxk#tPM`gI8MmO}1AV!$scm$$llPWF!4t6(7Zg`$#px>Y3%RQ|Hy=-~&$SCV?BPuUsE}4O#Oq%8u{UTflQ8hKt=b(Qw_3=gVRn9o{K*va#j)0Z_@}-0%RjgBL>5ZcMm-lFCux#T=t&_?0X@GhrsfT=&=2g?zopnq=5swfxk1<HJn~!#6cZhw`YqfK@|DOHFnoE3*Q4mk`^TN$uzlGZ?ofyS5&XZsoxPpT&R)yqKHn40HRR8o$tfsFDR6f5``Vljh+yOaXm8w3cWuOa?}rT_>qTiLd~lQs0AaIcAnCB|uMNxFLH}$mM96)fyPoYV@02Tn^mecUBb?NRkU3a`)AMYbpsr0OKAPnNFJv;UiEaT{N17U5_s-fE5ipxHOXefqvgizuGwPj@D$;v1+`W$PV>Ch<%L-a-z%<Y~TxTWWX|!AeC>)?oqxosM>{E1Eepuo(-rim)i_1PVg}<X6bXp0iKQGY<=(n%3@|jZqjeZVBuu$Ng|L@=YtN)3Bh{HI+AO3^=`{VB92vPq|*bR*r{<D9jztHWD_kA*ef0v)2Z2#!cc<sOX&-K@i?+-^}9QhHi{h1de#(V$AztP{D9KQ7T?&-autnsS8@$dfo|L*_&zyC>p=fE5L$9v)(k?Q{U?49q0*`qPszc#3w9K7h>^J!AR((loA6>~%w@BJ75v+>^j%kKV&-V^ne@&nCy^PkKQaC|?W9MhXT&Q7HHHQ@YD4LA=*qmB;et?(N*2>g$YiF)wjA-yOWi=TeV;+gT@fBnDc?;Y)VhZE8Pzr&zPGC>$`{BMO&l4VwL_0eDaFaIAC%lk?9Kul41Z|QIRH~)kFhPUq@?Q^2Y#G7C}I5hf_JC6a#zcofXe$jc+5!1Bl$r)eaKQYFAaeOa8G1HlAYxJM~Pm{tIont;<D|wH;xc^7vE4=WJColOja|ESn@BX*{(%Kluo#T;MYc3BggV_JoSf~f%{g-@fsmL1(;Qul>#dv&hKhf4`&bRe9|Ly;-zd71FKA6C6`u6Sr2b!@G#vIZC00"

st.markdown(r"""
<style>
:root{--bg:#080d18;--panel:#0e1525;--card:#121b2e;--card2:#162035;--border:#1c2d47;--border2:#243450;--blue:#3b82f6;--cyan:#22d3ee;--green:#34d399;--yellow:#fbbf24;--red:#f87171;--orange:#fb923c;--text:#dde6f5;--text2:#94a3b8;--text3:#64748b}
.stApp{background:var(--bg);color:var(--text)}
[data-testid="stSidebar"]{background:var(--panel);border-right:1px solid var(--border)}
.block-container {
    max-width: 1600px;
    padding-top: 4.5rem !important;
    padding-right: 1.4rem !important;
    padding-bottom: 2rem !important;
    padding-left: 1.4rem !important;
}
.brand{font-weight:800;letter-spacing:.08em;color:var(--cyan);font-size:1.05rem}.brand-sub{font-size:.72rem;color:var(--text3);font-family:monospace;margin-bottom:.8rem}
[data-testid="stMetric"]{background:linear-gradient(145deg,var(--panel),var(--card));border:1px solid var(--border);border-radius:10px;padding:.65rem .8rem}
[data-testid="stMetricLabel"]{color:var(--text3)}[data-testid="stMetricValue"]{font-size:1.28rem}
[data-testid="stExpander"]{background:var(--card);border:1px solid var(--border);border-radius:10px;margin:.35rem 0;overflow:hidden}
[data-testid="stExpander"]:hover{border-color:#3b82f680;box-shadow:0 5px 18px #0005}
.stButton>button,.stDownloadButton>button{border-radius:8px;font-weight:700;border-color:var(--border2)}
.stButton>button:hover,.stDownloadButton>button:hover{border-color:var(--blue);color:#fff}
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea,[data-testid="stSelectbox"]>div>div{background:var(--card);border-color:var(--border2)}
code{font-family:Consolas,'JetBrains Mono',monospace!important;color:var(--cyan)!important;white-space:pre-wrap!important}
.category-title{font-weight:800;letter-spacing:.07em;text-transform:uppercase;margin:1rem 0 .2rem}.hint{color:var(--text3);font-size:.75rem}.danger{color:var(--red)}
@media(max-width:900px){.block-container{padding:.8rem}.brand{font-size:.95rem}}
</style>
""", unsafe_allow_html=True)

SCHEMA = """
CREATE TABLE IF NOT EXISTS categories(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT NOT NULL UNIQUE COLLATE NOCASE,
 icon TEXT NOT NULL DEFAULT '📁',
 color TEXT NOT NULL DEFAULT '#3b82f6',
 sort_order INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS commands(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 original_id INTEGER UNIQUE,
 category_id INTEGER NOT NULL,
 title TEXT NOT NULL,
 command_text TEXT NOT NULL,
 purpose TEXT NOT NULL DEFAULT '',
 expected_result TEXT NOT NULL DEFAULT '',
 risk_level TEXT NOT NULL CHECK(risk_level IN ('None','Low','Medium','High')),
 usage_type TEXT NOT NULL CHECK(usage_type IN ('User','Admin','User/Admin')),
 notes TEXT NOT NULL DEFAULT '',
 sort_order INTEGER NOT NULL DEFAULT 0,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(category_id) REFERENCES categories(id) ON UPDATE CASCADE ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS ix_commands_category ON commands(category_id);
CREATE INDEX IF NOT EXISTS ix_commands_risk ON commands(risk_level);
CREATE INDEX IF NOT EXISTS ix_commands_usage ON commands(usage_type);
"""

@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    con = sqlite3.connect(DB_PATH, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.execute("PRAGMA busy_timeout=30000")
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def factory_data() -> dict[str, Any]:
    return json.loads(gzip.decompress(base64.b85decode(_FACTORY_PAYLOAD)).decode("utf-8"))


def initialize_database(force_reset: bool = False) -> None:
    with connect() as con:
        if force_reset:
            con.execute("DROP TABLE IF EXISTS commands")
            con.execute("DROP TABLE IF EXISTS categories")
        con.executescript(SCHEMA)
        if con.execute("SELECT COUNT(*) FROM commands").fetchone()[0] > 0:
            return
        data = factory_data()
        category_ids = {}
        for order, (name, meta) in enumerate(data["categories"].items(), 1):
            category_ids[name] = con.execute(
                "INSERT INTO categories(name,icon,color,sort_order) VALUES(?,?,?,?)",
                (name, meta["icon"], meta["color"], order),
            ).lastrowid
        for order, item in enumerate(data["commands"], 1):
            con.execute(
                """INSERT INTO commands(original_id,category_id,title,command_text,purpose,
                   expected_result,risk_level,usage_type,notes,sort_order)
                   VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (item["id"], category_ids[item["category"]], item["title"], item["cmd"],
                 item.get("purpose", ""), item.get("result", ""), item.get("risk", "None"),
                 item.get("usage", "User/Admin"), item.get("notes", ""), order),
            )


def get_categories() -> list[dict[str, Any]]:
    with connect() as con:
        return [dict(row) for row in con.execute(
            """SELECT c.*,COUNT(x.id) command_count FROM categories c
               LEFT JOIN commands x ON x.category_id=c.id GROUP BY c.id
               ORDER BY c.sort_order,c.name"""
        )]


def get_stats() -> dict[str, int]:
    with connect() as con:
        return dict(con.execute(
            """SELECT COUNT(*) total,COUNT(DISTINCT category_id) categories,
               COALESCE(SUM(risk_level='High'),0) high,
               COALESCE(SUM(risk_level='Medium'),0) medium,
               COALESCE(SUM(usage_type='Admin'),0) admin FROM commands"""
        ).fetchone())


def query_commands(search: str, category_id: int | None, risk: str, usage: str,
                   page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    clauses = ["1=1"]
    params: list[Any] = []
    if search.strip():
        term = f"%{search.strip()}%"
        clauses.append("(x.title LIKE ? OR x.command_text LIKE ? OR x.purpose LIKE ? OR x.expected_result LIKE ? OR x.notes LIKE ? OR c.name LIKE ?)")
        params.extend([term] * 6)
    if category_id:
        clauses.append("x.category_id=?")
        params.append(category_id)
    if risk:
        clauses.append("x.risk_level=?")
        params.append(risk)
    if usage:
        clauses.append("(x.usage_type=? OR x.usage_type='User/Admin')")
        params.append(usage)
    where = " AND ".join(clauses)
    offset = (page - 1) * page_size
    with connect() as con:
        total = con.execute(f"SELECT COUNT(*) FROM commands x JOIN categories c ON c.id=x.category_id WHERE {where}", params).fetchone()[0]
        rows = con.execute(
            f"""SELECT x.*,c.name category,c.icon,c.color,
                ROW_NUMBER() OVER(PARTITION BY x.category_id ORDER BY x.sort_order,x.id) category_sequence
                FROM commands x JOIN categories c ON c.id=x.category_id
                WHERE {where} ORDER BY c.sort_order,x.sort_order,x.id LIMIT ? OFFSET ?""",
            [*params, page_size, offset],
        ).fetchall()
    return [dict(row) for row in rows], int(total)


def get_command(command_id: int) -> dict[str, Any] | None:
    with connect() as con:
        row = con.execute("SELECT x.*,c.name category FROM commands x JOIN categories c ON c.id=x.category_id WHERE x.id=?", (command_id,)).fetchone()
        return dict(row) if row else None


def save_command(data: dict[str, Any], command_id: int | None = None) -> None:
    title = data["title"].strip()
    command_text = data["command_text"].strip()
    if not title or not command_text:
        raise ValueError("Title and PowerShell Command are required.")
    values = (data["category_id"], title, command_text, data["purpose"].strip(),
              data["expected_result"].strip(), data["risk_level"], data["usage_type"], data["notes"].strip())
    with connect() as con:
        if command_id:
            cursor = con.execute(
                """UPDATE commands SET category_id=?,title=?,command_text=?,purpose=?,expected_result=?,
                   risk_level=?,usage_type=?,notes=?,updated_at=CURRENT_TIMESTAMP WHERE id=?""", values + (command_id,))
            if cursor.rowcount != 1:
                raise LookupError("Command not found.")
        else:
            sort_order = con.execute("SELECT COALESCE(MAX(sort_order),0)+1 FROM commands").fetchone()[0]
            con.execute(
                """INSERT INTO commands(category_id,title,command_text,purpose,expected_result,
                   risk_level,usage_type,notes,sort_order) VALUES(?,?,?,?,?,?,?,?,?)""", values + (sort_order,))




def export_json() -> bytes:
    with connect() as con:
        rows = [dict(row) for row in con.execute(
            """SELECT x.id,c.name category,x.title,x.command_text cmd,x.purpose,
               x.expected_result result,x.risk_level risk,x.usage_type usage,x.notes
               FROM commands x JOIN categories c ON c.id=x.category_id ORDER BY x.id"""
        )]
    return json.dumps(rows, ensure_ascii=False, indent=2).encode("utf-8")


def import_json(payload: bytes) -> tuple[int, int]:
    data = json.loads(payload.decode("utf-8-sig"))
    if not isinstance(data, list):
        raise ValueError("The JSON file must contain an array of commands.")
    added = skipped = 0
    with connect() as con:
        category_map = {row["name"].casefold(): row["id"] for row in con.execute("SELECT id,name FROM categories")}
        for item in data:
            try:
                title = str(item["title"]).strip()
                command_text = str(item.get("cmd", item.get("command_text", ""))).strip()
                category = str(item.get("category", "Uncategorized")).strip() or "Uncategorized"
                risk = str(item.get("risk", "None"))
                usage = str(item.get("usage", "User/Admin"))
                if not title or not command_text or risk not in RISK_LEVELS or usage not in USAGE_TYPES:
                    raise ValueError
                key = category.casefold()
                if key not in category_map:
                    category_map[key] = con.execute(
                        "INSERT INTO categories(name,sort_order) VALUES(?,(SELECT COALESCE(MAX(sort_order),0)+1 FROM categories))", (category,)
                    ).lastrowid
                duplicate = con.execute("SELECT 1 FROM commands WHERE title=? COLLATE NOCASE AND command_text=?", (title, command_text)).fetchone()
                if duplicate:
                    skipped += 1
                    continue
                con.execute(
                    """INSERT INTO commands(category_id,title,command_text,purpose,expected_result,
                       risk_level,usage_type,notes,sort_order) VALUES(?,?,?,?,?,?,?,?,
                       (SELECT COALESCE(MAX(sort_order),0)+1 FROM commands))""",
                    (category_map[key], title, command_text, str(item.get("purpose", "")),
                     str(item.get("result", "")), risk, usage, str(item.get("notes", ""))),
                )
                added += 1
            except Exception:
                skipped += 1
    return added, skipped


def clear_filters() -> None:
    for key in ("search", "risk", "usage"):
        st.session_state.pop(key, None)
    st.session_state.active_category = None
    st.session_state.page = 1


def render_form(command: dict[str, Any] | None) -> None:
    cats = get_categories()
    names = [item["name"] for item in cats]
    category_ids = {item["name"]: item["id"] for item in cats}
    selected = names.index(command["category"]) if command and command["category"] in names else 0
    with st.form(f"command_form_{command['id'] if command else 'new'}"):
        left, right = st.columns(2)
        category = left.selectbox("Category", names, index=selected)
        title = right.text_input("Title *", value=command["title"] if command else "")
        command_text = st.text_area("PowerShell Command *", value=command["command_text"] if command else "", height=150)
        left, right = st.columns(2)
        purpose = left.text_input("Purpose", value=command["purpose"] if command else "")
        expected_result = right.text_input("Expected Result", value=command["expected_result"] if command else "")
        left, right = st.columns(2)
        risk = left.selectbox("Risk Level", RISK_LEVELS, index=RISK_LEVELS.index(command["risk_level"]) if command else 0)
        usage = right.selectbox("Usage", USAGE_TYPES, index=USAGE_TYPES.index(command["usage_type"]) if command else 2)
        notes = st.text_input("Notes / Cautions", value=command["notes"] if command else "")
        if st.form_submit_button("Save Command", type="primary", use_container_width=True):
            try:
                save_command({"category_id": category_ids[category], "title": title, "command_text": command_text,
                              "purpose": purpose, "expected_result": expected_result, "risk_level": risk,
                              "usage_type": usage, "notes": notes}, command["id"] if command else None)
                st.success("Command saved successfully.")
                st.rerun()
            except Exception as error:
                st.error(str(error))


@st.dialog("Add Command", width="large")
def add_dialog() -> None:
    render_form(None)


@st.dialog("Edit Command", width="large")
def edit_dialog(command_id: int) -> None:
    command = get_command(command_id)
    if not command:
        st.error("Command not found.")
        return
    render_form(command)


@st.dialog("Command Preview", width="large")
def preview_dialog(command_id: int) -> None:
    command = get_command(command_id)
    if not command:
        st.error("Command not found.")
        return
    st.subheader(f"#{command['id']} — {command['title']}")
    st.caption("Use the copy icon in the code block to copy the command.")
    st.code(command["command_text"], language="powershell")
    left, right = st.columns(2)
    left.markdown(f"**Purpose**  \n{command['purpose'] or '—'}")
    right.markdown(f"**Expected Result**  \n{command['expected_result'] or '—'}")
    left, right = st.columns(2)
    left.markdown(f"**Risk Level**  \n{command['risk_level']}")
    right.markdown(f"**Usage**  \n{command['usage_type']}")
    st.markdown(f"**Category**  \n{command['category']}")
    if command["notes"]:
        st.warning(command["notes"])
    if st.button("✏️ Edit This Command", type="primary", use_container_width=True):
        st.session_state.pending_edit = command_id
        st.rerun()
def on_reset_filters() -> None:
    """Clear UI filters without deleting or changing database records."""

    st.session_state["search"] = ""
    st.session_state["risk"] = "All Risks"
    st.session_state["usage"] = "All Usage"
    st.session_state["active_category"] = None
    st.session_state["page"] = 1


initialize_database()
for key, value in {"active_category": None, "page": 1, "pending_edit": None}.items():
    st.session_state.setdefault(key, value)

if st.session_state.pending_edit is not None:
    pending_id = st.session_state.pending_edit
    st.session_state.pending_edit = None
    edit_dialog(pending_id)

categories = get_categories()
summary = get_stats()

with st.sidebar:
    st.markdown('<div class="brand">⚡ PS TOOLKIT</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="brand-sub">{summary["total"]} Commands · {summary["categories"]} Categories</div>', unsafe_allow_html=True)
    if st.button(f"📋 All Commands  ·  {summary['total']}", use_container_width=True,
                 type="primary" if st.session_state.active_category is None else "secondary"):
        st.session_state.active_category = None
        st.session_state.page = 1
        st.rerun()
    st.caption("CATEGORIES")
    for item in categories:
        if st.button(f"{item['icon']} {item['name']}  ·  {item['command_count']}", key=f"cat_{item['id']}",
                     use_container_width=True,
                     type="primary" if st.session_state.active_category == item["id"] else "secondary"):
            st.session_state.active_category = item["id"]
            st.session_state.page = 1
            st.rerun()
    st.divider()
    st.caption("DATA MANAGEMENT")
    upload = st.file_uploader("Import JSON", type=["json"], label_visibility="collapsed")
    if upload and st.button("Upload Commands", use_container_width=True):
        try:
            added, skipped = import_json(upload.getvalue())
            st.success(f"Imported {added}; skipped {skipped}.")
            st.rerun()
        except Exception as error:
            st.error(f"Import failed: {error}")
    st.download_button("↓ Export JSON", export_json(), f"ps_toolkit_{date.today()}.json",
                       "application/json", use_container_width=True)

search_col, risk_col, usage_col, size_col, add_col, reset_col = st.columns([4, 1.45, 1.45, 1, 1, 1])
search = search_col.text_input("Search", placeholder="Search commands, titles, purpose, category...", key="search", label_visibility="collapsed")
risk_choice = risk_col.selectbox("Risk", ["All Risks", *RISK_LEVELS], key="risk", label_visibility="collapsed")
usage_choice = usage_col.selectbox("Usage", ["All Usage", *USAGE_TYPES], key="usage", label_visibility="collapsed")
page_size = size_col.selectbox("Page size", PAGE_SIZES, index=1, label_visibility="collapsed")
if add_col.button("＋ Add", type="primary", use_container_width=True):
    add_dialog()
reset_col.button(
    "↺ Reset Filters",
    use_container_width=True,
    help="Clear search, category, risk and usage filters",
    on_click=on_reset_filters,
)
risk = "" if risk_choice == "All Risks" else risk_choice
usage = "" if usage_choice == "All Usage" else usage_choice
rows, total = query_commands(search, st.session_state.active_category, risk, usage,
                             st.session_state.page, page_size)
total_pages = max(1, math.ceil(total / page_size))
if st.session_state.page > total_pages:
    st.session_state.page = total_pages
    st.rerun()

metric_cols = st.columns(6)
for column, (label, value) in zip(metric_cols, [
    ("📋 Total", summary["total"]), ("📂 Categories", summary["categories"]),
    ("🔍 Showing", total), ("🔴 High Risk", summary["high"]),
    ("🟠 Medium Risk", summary["medium"]), ("🛡 Admin Only", summary["admin"]),
]):
    column.metric(label, value)

nav_left, nav_mid, nav_right = st.columns([1, 3, 1])
if nav_left.button("← Previous", disabled=st.session_state.page <= 1, use_container_width=True):
    st.session_state.page -= 1
    st.rerun()
nav_mid.markdown(f"<p class='hint' style='text-align:center'>Page {st.session_state.page} of {total_pages} · {total} matching commands · Code blocks include a native copy button</p>", unsafe_allow_html=True)
if nav_right.button("Next →", disabled=st.session_state.page >= total_pages, use_container_width=True):
    st.session_state.page += 1
    st.rerun()

if not rows:
    st.info("No commands match your filters.")
    if st.button("Clear Filters"):
        clear_filters()
        st.rerun()
else:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for command in rows:
        grouped.setdefault(command["category"], []).append(command)
    for category, items in grouped.items():
        meta = items[0]
        st.markdown(f'<div class="category-title" style="color:{meta["color"]}">{meta["icon"]} {category} · {len(items)} shown</div>', unsafe_allow_html=True)
        for command in items:
            label = f"{command['category_sequence']:02d}  ·  {command['title']}   |   {command['risk_level']} · {command['usage_type']}"
            with st.expander(label):
                st.caption(command["purpose"] or "No purpose specified")
                st.code(command["command_text"], language="powershell")
                details_left, details_right = st.columns(2)
                details_left.caption(f"Expected: {command['expected_result'] or '—'}")
                details_right.caption(f"Notes: {command['notes'] or '—'}")
                view_col, edit_col = st.columns(2)
                if view_col.button("👁 View", key=f"view_{command['id']}", use_container_width=True):
                    preview_dialog(command["id"])
                if edit_col.button("✏️ Edit", key=f"edit_{command['id']}", use_container_width=True):
                    edit_dialog(command["id"])
                