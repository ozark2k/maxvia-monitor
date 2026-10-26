const fs = require('fs');

// We have the raw input in the conversation transcript or we can extract it from the prompt
const userInput = `--- PERFIL 01 ---
LOGIN: 61578625648358
SENHA: NLAS_EoxNHfP
2FA: ZUX7DFNZKHBFSKD7QEGWT5NF3MI5JDH5
EMAIL: woodburgposis8672@hotmail.com
SENHA EMAIL: I93Nt3cF336
EMAIL BACKUP: nkuqas@fextemp.com
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @fextemp.com)


--- PERFIL 02 ---
LOGIN: 61578149626091
SENHA: NLAS_UxDXvgv
2FA: 4RUBVVSVJRA3J53WQSDINDQCSXY7HLDC
EMAIL: oatiszecher82@hotmail.com
SENHA EMAIL: cT3Zl54D
EMAIL BACKUP: 9j6mgbcx@qabq.com


--- PERFIL 03 ---
LOGIN: 61578121127461
SENHA: NLAS_EkiVKb8
2FA: JQS4BMNWLKYT46F6A7S3C5Z6572P2JJH
EMAIL: englinscheidegger993@hotmail.com
SENHA EMAIL: 4rO2Rh2Wp
EMAIL BACKUP: 2awjubjd@qabq.com


--- PERFIL 04 ---
LOGIN: 61578172245209
SENHA: NLAS_IWQLoEc
2FA: W6UAHBQ67N6F3KWHX2FKGMYIQATBSGSG
EMAIL: mengsteabalvira6363@hotmail.com
SENHA EMAIL: Am809xNM
EMAIL BACKUP: yyyyt@fextemp.com
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @fextemp.com)


--- PERFIL 05 ---
LOGIN: 61578598766411
SENHA: NLAS_SfsEFAE
2FA: CFJJIMCD27N7PELILHSEO5K7KSOGH5YY
EMAIL: xdcxgjrwtw71089@hotmail.com
SENHA EMAIL: u6IXb174994
EMAIL BACKUP: ucyfuq@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 06 ---
LOGIN: 61578384121603
SENHA: NLAS_6Ewmuuo
2FA: V2T6IT6NDRI2ZTSIBS43JPH7TUJXFLVP
EMAIL: bowlickknaack8737@hotmail.com
SENHA EMAIL: 2LQ480v65k
EMAIL BACKUP: uefop@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 07 ---
LOGIN: 61578377104518
SENHA: NLAS_1By7qEI
2FA: PNFYFJDIQN7HMUJBGHOAFDKX677LAZYQ
EMAIL: bughpartis246@hotmail.com
SENHA EMAIL: C50G5YvB
EMAIL BACKUP: yvozo@fextemp.com
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @fextemp.com)


--- PERFIL 08 ---
LOGIN: 61578816830932
SENHA: NLAS_1APb63D
2FA: U2OLWJIG6N5K4Y3EYF3POZXUIJI6UWNN
EMAIL: mcenenypasquini54@hotmail.com
SENHA EMAIL: 9z3yJ6492
EMAIL BACKUP: dyocs27q@nqmo.com
SITE DO BACKUP: https://mail.td/ (Selecionar @nqmo.com)


--- PERFIL 09 ---
LOGIN: 61578221233444
SENHA: NLAS_AE3UKGp
2FA: UKXXXKCR2NA74RNJUHHJ2Y4S5LDK3SFV
EMAIL: teachoutpiccinich07@hotmail.com
SENHA EMAIL: 12Eh7I9z
EMAIL BACKUP: 6b1g1fqq@nqmo.com
SITE DO BACKUP: https://mail.td/ (Selecionar @nqmo.com)


--- PERFIL 10 ---
LOGIN: 61578195014277
SENHA: NLAS_zs52vnM
2FA: FNF6DJNDC5HGELFHHG44CCOQKUD3GA6E
EMAIL: wolgastrose780@hotmail.com
SENHA EMAIL: 6H5990E4x7MC
EMAIL BACKUP: 9c1dbd4f@nqmo.com
SITE DO BACKUP: https://mail.td/ (Selecionar @nqmo.com)


--- PERFIL 11 ---
LOGIN: 61578606300314
SENHA: NLAS_HCBUnHQ
2FA: UMQGA6MOP266PHB34E3D26VI45RFJBER
EMAIL: teruelhazeltine536@hotmail.com
SENHA EMAIL: W6Nqc4W6r241
EMAIL BACKUP: 6av237bk@nqmo.com
SITE DO BACKUP: https://mail.td/ (Selecionar @nqmo.com)


--- PERFIL 12 ---
LOGIN: 61578501903262
SENHA: NLAS_UDLxSyz
2FA: DULV3NN5ZXRN5GM62K5X3P25LACRY77G
EMAIL: hjlxpcpj040@hotmail.com
SENHA EMAIL: tpH6RZ34W
EMAIL BACKUP: j1aq8yg2@nqmo.com
SITE DO BACKUP: https://mail.td/ (Selecionar @nqmo.com)


--- PERFIL 13 ---
LOGIN: 61578632968965
SENHA: NLAS_JZLjYkG
2FA: QTGUWSQAJ5VYUPM5TZV2Q7AQHWFY7MCE
EMAIL: manganofenwick5391@hotmail.com
SENHA EMAIL: HJI12NkC9D8
EMAIL BACKUP: 6dz2jbas@nqmo.com
SITE DO BACKUP: https://mail.td/ (Selecionar @nqmo.com)


--- PERFIL 14 ---
LOGIN: 61578674997622
SENHA: NLAS_nb6MpBG
2FA: SQ5VCATSQ5UEXDA36XQGPMWP4YHOE4UG
EMAIL: garinglasiter524@hotmail.com
SENHA EMAIL: 932oQ1OHC
EMAIL BACKUP: 9wp6v915@nqmo.com
SITE DO BACKUP: https://mail.td/ (Selecionar @nqmo.com)


--- PERFIL 15 ---
LOGIN: 61578328868208
SENHA: NLAS_AbSEKqI
2FA: K3TBZ7OENUCTVBYN6W5R52ORFXL4KKJL
EMAIL: siedleckikiltz38@hotmail.com
SENHA EMAIL: 50Z39W6Ie
EMAIL BACKUP: c27poarz@nqmo.com
SITE DO BACKUP: https://mail.td/ (Selecionar @nqmo.com)


--- PERFIL 16 ---
LOGIN: 61578378005817
SENHA: NLAS_O0fN2my
2FA: 7WA6YPEJFNSJHMXWIFVZUTHCTVPSZ6MX
EMAIL: cauffmansawaia9345@hotmail.com
SENHA EMAIL: eh4N05g1z51
EMAIL BACKUP: d0ta1vrm@nqmo.com
SITE DO BACKUP: https://mail.td/ (Selecionar @nqmo.com)


--- PERFIL 17 ---
LOGIN: 61578646018596
SENHA: NLAS_cdJWLlZ
2FA: QSQCPAICJT2B2GJBWIMHY77YB4RZUW5T
EMAIL: gngunehlz0949@hotmail.com
SENHA EMAIL: l62GKMeYV2
EMAIL BACKUP: 52duifbw@nqmo.com
SITE DO BACKUP: https://mail.td/ (Selecionar @nqmo.com)


--- PERFIL 18 ---
LOGIN: 61578622349371
SENHA: NLAS_GVGFnDb
2FA: PWVPWX2TUHBUMNJXYWGKGVYBZADMXXTT
EMAIL: tcnorbhhr836@hotmail.com
SENHA EMAIL: 01A1URQ09A
EMAIL BACKUP: md9o41d7@nqmo.com
SITE DO BACKUP: https://mail.td/ (Selecionar @nqmo.com)


--- PERFIL 19 ---
LOGIN: 61578729864254
SENHA: NLAS_O40H3tb
2FA: T7CFL7K2VREISUX4ZN3HEOURPXYJ4P4E
EMAIL: pinkstonspyies722@hotmail.com
SENHA EMAIL: 9Eh3EW014282
EMAIL BACKUP: kpwcx1rg@nqmo.com
SITE DO BACKUP: https://mail.td/ (Selecionar @nqmo.com)


--- PERFIL 20 ---
LOGIN: 61578267491277
SENHA: NLAS_yYtCIbw
2FA: GY4AKR7OULRQSLCRZYPC7D25YTO5C6HK
EMAIL: rvloewlnpj9989@hotmail.com
SENHA EMAIL: C9uI1jHUCf
EMAIL BACKUP: 0rrqv6zr@nqmo.com
SITE DO BACKUP: https://mail.td/ (Selecionar @nqmo.com)


--- PERFIL 21 ---
LOGIN: 61577658891680
SENHA: NLAS@5CkfHCM
2FA: IRMXPADXTPPITE2XRIFDWIEJOYUTETCE
EMAIL: dierasyusimzvps@hotmail.com
SENHA EMAIL: CQo0KggLjG
EMAIL BACKUP: f665q6lkrwj0@5smail.email


--- PERFIL 22 ---
LOGIN: 61577371079763
SENHA: NLAS@pRR0FoH
2FA: PQJ6UKJCVPYFKBPKUEGPMORDMRARBKHI
EMAIL: balakgdilox71sfwz@hotmail.com
SENHA EMAIL: bcW9BDuBjKd
EMAIL BACKUP: mh5l6emm0d09@v5sl.5smail.email


--- PERFIL 23 ---
LOGIN: 61577407678459
SENHA: NLAS@8n95BwF
2FA: JGMAKZ6FWSWNKRPYM7GZOPAD2ZVCD4IX
EMAIL: ngugipgendyv6i0u@hotmail.com
SENHA EMAIL: YBOWWUGklMnx3
EMAIL BACKUP: uxukafe@fexbox.org
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @fexbox.org)


--- PERFIL 24 ---
LOGIN: 61577223367551
SENHA: NLAS@nxh25Yy
2FA: HTLESKYCYKTNHZXF66M6GVCCHQW74CVL
EMAIL: brozoccrastdaykyf@hotmail.com
SENHA EMAIL: yOPlWCIDajn
EMAIL BACKUP: ahogyy@fexbox.org
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @fexbox.org)


--- PERFIL 25 ---
LOGIN: 61577272384645
SENHA: NLAS@GxciGWi
2FA: TGLZNPT3ZVK5W5IVCP3HG43EGA3JRZUU
EMAIL: tamkeuzerkandcp@hotmail.com
SENHA EMAIL: MPSr5braTEv9
EMAIL BACKUP: oj3l4ntm040n@1q4.5smail.email


--- PERFIL 26 ---
LOGIN: 61577692310886
SENHA: NLAS@pSw6U9E
2FA: OSUVUIFECCCMECRC3I3AQ764UWOEXX6O
EMAIL: dyettstrest4hog9n@hotmail.com
SENHA EMAIL: geh35OrBvH2G
EMAIL BACKUP: eyoyd@fexbox.org
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @fexbox.org)


--- PERFIL 27 ---
LOGIN: 61577258945201
SENHA: NLAS@ekfbsNi
2FA: END6CAFPZHPFQGN3EZTTKGU7DTR4I7UT
EMAIL: pizziokassajbc6@hotmail.com
SENHA EMAIL: MhU21xPhXrnt6u
EMAIL BACKUP: fcovp@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 28 ---
LOGIN: 61577691170427
SENHA: NLAS@J8jnnwq
2FA: NQDH35TUMKOMNVJWNT7XATAELKURGVH2
EMAIL: rekhadnorahupk@hotmail.com
SENHA EMAIL: IG8hta1PmAyT7
EMAIL BACKUP: 8wdov7d9qgf0@25uo.5smail.email


--- PERFIL 29 ---
LOGIN: 61577360370008
SENHA: NLAS@mq2aL4O
2FA: 5ERRWTPJHKXBQGU6QVQUHNVG2IHEX7SJ
EMAIL: selicvmandyfsn@hotmail.com
SENHA EMAIL: TkIbfHSucyY
EMAIL BACKUP: xumpeuh2mo09@o3zld.5smail.email


--- PERFIL 30 ---
LOGIN: 61577215807828
SENHA: NLAS@Rtv5VBW
2FA: I4ZN3KZ27USL5R4WVP6CJH56RJP6T4SX
EMAIL: kettlokenna59hn@hotmail.com
SENHA EMAIL: TOZajkGJqq9EU
EMAIL BACKUP: guogseg@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 31 ---
LOGIN: 61577474336583
SENHA: NLAS@hfFjXZb
2FA: 5R75AMYLFKZSPMVOP5IFD3LUU7PFRNGA
EMAIL: sowerkstych85wa@hotmail.com
SENHA EMAIL: zuMIPxjx1eQRsQ
EMAIL BACKUP: mpbqs0zbnsl0@p9ei.5smail.email


--- PERFIL 32 ---
LOGIN: 61577255646178
SENHA: NLAS@LkdKw2g
2FA: PP263LSLYCG75U56O3PXWJS7ZK5CHXD5
EMAIL: sanesvurwahjdls@hotmail.com
SENHA EMAIL: PIvzB8LmswApv
EMAIL BACKUP: fpateu@fexpost.com
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @fexpost.com)


--- PERFIL 33 ---
LOGIN: 61577333611583
SENHA: NLAS@kvTSgrW
2FA: 4QTOUGKVZKJ53CATBUF4IR6IPJNUMTL4
EMAIL: panovxdrentfknapb@hotmail.com
SENHA EMAIL: elyzEhtBQulTS
EMAIL BACKUP: aacety@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 34 ---
LOGIN: 61577605283659
SENHA: NLAS@bVRsj4o
2FA: ZUN6Q3WQFQU6YDQEP5S4KAW7PXU32M6F
EMAIL: gerbaypoortglgx@hotmail.com
SENHA EMAIL: JGWzFONU24a56
EMAIL BACKUP: dyxexy@fexbox.org
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @fexbox.org)


--- PERFIL 35 ---
LOGIN: 61577384609008
SENHA: NLAS@B2NoKFA
2FA: ZNKM6XFEI245BHE3S5N6GKC7NBIOUMEO
EMAIL: dumagvaydanfay@hotmail.com
SENHA EMAIL: zRYXKGad4i
EMAIL BACKUP: ehamafy@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 36 ---
LOGIN: 61577636153008
SENHA: NLAS@x2NfCjS
2FA: Y2Y3SZXP6YDOJJTEHEHWPILVEZ6T5YGV
EMAIL: voghtoplooganqyc2@hotmail.com
SENHA EMAIL: mYXtLstROTtg5
EMAIL BACKUP: aadwvad@fexpost.com
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @fexpost.com)


--- PERFIL 37 ---
LOGIN: 61577631532701
SENHA: NLAS@DclFEz4
2FA: S2SJS6WCCUBF6R6HMDLRCMNCTUI3CD5G
EMAIL: lappeitracy5rn@hotmail.com
SENHA EMAIL: tcZuE7IR8btWR
EMAIL BACKUP: pousyuy@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 38 ---
LOGIN: 61577537575894
SENHA: NLAS@ANXW5h9
2FA: 26LP23NCB77T4WIJQMXZ6GJKDMVAO32I
EMAIL: pilesaburbaxzjixy@hotmail.com
SENHA EMAIL: birTfPKrXEC
EMAIL BACKUP: 2dktmpxntbk0@5smail.email


--- PERFIL 39 ---
LOGIN: 61577067285508
SENHA: NLAS@uWoCmzr
2FA: OTFBCWBFR2SPRYEOIR6KNWWP3BJKASQE
EMAIL: cumbyfengelec9@hotmail.com
SENHA EMAIL: uFqxRzWoch
EMAIL BACKUP: ukosy@fexpost.com
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @fexpost.com)


--- PERFIL 40 ---
LOGIN: 61577022167499
SENHA: NLAS@U9AoeTR
2FA: YLBUUC7RV6DSR7CZMFAVSKCGL6PPP67T
EMAIL: slivavpignak55x@hotmail.com
SENHA EMAIL: qDTnntkSpcO
EMAIL BACKUP: aswhof@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 41 ---
LOGIN: 61577158810586
SENHA: NLAS@AXJZvcD
2FA: RWPLYVJ3H2TTL3PYHXJ74IQPQALSDWSE
EMAIL: loslikgambabaio@hotmail.com
SENHA EMAIL: mFrj5jyDpa1k
EMAIL BACKUP: xmsaoga@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 42 ---
LOGIN: 61577182419531
SENHA: NLAS@XjYEYEL
2FA: 3GFLALRDQ754HFR7NS3GF65F75SPGDHX
EMAIL: kaltzzdemici2b@hotmail.com
SENHA EMAIL: QhwJyhSxaJK
EMAIL BACKUP: stemaaf@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 43 ---
LOGIN: 61577230656790
SENHA: NLAS@sgfkO6C
2FA: MPGNBUFKHUQ2HZWDPOWTX7XSIRUF2JTH
EMAIL: piedeselkes9fhe@hotmail.com
SENHA EMAIL: jpLyXhhpLMvhz
EMAIL BACKUP: afybc@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 44 ---
LOGIN: 61577305233688
SENHA: NLAS@lfYM4yo
2FA: MLNXQ3CO7IQDCBR7YVP4NPQQQ4QMB6ZN
EMAIL: smoothwalla2llux1@hotmail.com
SENHA EMAIL: oGOEGZglXLV
EMAIL BACKUP: foggv@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 45 ---
LOGIN: 61577041816446
SENHA: NLAS@loMav8F
2FA: C6QNQA4IMFFSF34ZDUYRTB3VGGLTSXWP
EMAIL: suongebudakzkq@hotmail.com
SENHA EMAIL: cALOAeDyanVPoL
EMAIL BACKUP: fazuhyq@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 46 ---
LOGIN: 61577593945016
SENHA: NLAS@31GR06m
2FA: K2E4RLHCFGB6FFOZDQ4PEMQUIY6J32JZ
EMAIL: cotiebalofswex5@hotmail.com
SENHA EMAIL: SY0HZwCv6F6
EMAIL BACKUP: nevyxw@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 47 ---
LOGIN: 61577686190099
SENHA: NLAS@gC0C7Z0
2FA: Z4BEYOIARB7GDIIJVIRKDIZ45S2ONB2I
EMAIL: ahunancoatldmk3e@hotmail.com
SENHA EMAIL: VXlQBUVlZf5
EMAIL BACKUP: vabyso@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 48 ---
LOGIN: 61577310963381
SENHA: NLAS@aJxfSyE
2FA: 3LJIZZLFCAO5TLG3I7FBTCEWO7N3PHXK
EMAIL: salemyglock1q6fuw@hotmail.com
SENHA EMAIL: DJU5zm2Q8PC3k9
EMAIL BACKUP: dtedomg@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 49 ---
LOGIN: 61577287054256
SENHA: NLAS@0YPhWoE
2FA: 7KAYQEZJQW6MA7QINRIA7DIR5B2OCINJ
EMAIL: johesmmatsuoex8@hotmail.com
SENHA EMAIL: eUTJfwTTBY5p
EMAIL BACKUP: ocytezo@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 50 ---
LOGIN: 61577194028733
SENHA: NLAS@9j42LOn
2FA: NNPOEF2PXM5FXK733CYGTOZKGM5PTAE4
EMAIL: dugieasimosg1a@hotmail.com
SENHA EMAIL: RYI4E5e4KI9
EMAIL BACKUP: nhacuud@mailbox.in.ua
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailbox.in.ua)


--- PERFIL 51 ---
LOGIN: 61577146181429
SENHA: NLAS@GESIxvy
2FA: PVWOECN5PBKJHO2DPYE56U7NEMS2JSPJ
EMAIL: hierlgserna0j0@hotmail.com
SENHA EMAIL: FWmwGEqwW4
EMAIL BACKUP: yvxykum@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 52 ---
LOGIN: 61577273914597
SENHA: NLAS@rnebGjG
2FA: HREU3EDESAVG32XR4C5TM5SYM3UFYYN2
EMAIL: rhuleparino9vgqzt@hotmail.com
SENHA EMAIL: YgY6KWDwAde897
EMAIL BACKUP: ehxyhuy@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 53 ---
LOGIN: 61577174138987
SENHA: NLAS@IXpXKpY
2FA: SLN4JKRSTFJNQ54GK4IZVLUIZDTCFWZ5
EMAIL: koumaddenosvb77u@hotmail.com
SENHA EMAIL: KRrVDRm2HPdmv
EMAIL BACKUP: govukap@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 54 ---
LOGIN: 61577265275402
SENHA: NLAS@Pcfvzdv
2FA: 6GW3KD73WEPWWMREANH44J3E4WPOLWGM
EMAIL: mamoundischvzzve@hotmail.com
SENHA EMAIL: SCrMttsTzU20
EMAIL BACKUP: oomecwp@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 55 ---
LOGIN: 61577041126748
SENHA: NLAS@qTtQshw
2FA: 7BLVB3BBBTXVA262HTGFTKSDYS75ZNG3
EMAIL: sossoathuersyrb3@hotmail.com
SENHA EMAIL: AkG37rl1d1Z
EMAIL BACKUP: uxbny@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 56 ---
LOGIN: 61577570725735
SENHA: NLAS@QTWmcBG
2FA: WQHBG5DJBMQNQQHNQRTSEI7WNJIP5NAS
EMAIL: yafehcrucco8mvjfc@hotmail.com
SENHA EMAIL: QqMp1CebXYi
EMAIL BACKUP: oxcauk@rover.info
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @rover.info)


--- PERFIL 57 ---
LOGIN: 61577243974759
SENHA: NLAS@61EZldL
2FA: I5XXMQ7WP2RXSLS5GB4262I4NASO64GE
EMAIL: shifaetolby7vp@hotmail.com
SENHA EMAIL: Soac0CJGtd0e
EMAIL BACKUP: apdemg@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 58 ---
LOGIN: 61577248264840
SENHA: shajib15
2FA: XUQUKW4DRUSYWKOV3IFRRQIVKBAOO26M
EMAIL: takaigmabinwilym9@hotmail.com
SENHA EMAIL: nHWw8VNZlvC
EMAIL BACKUP: kbcloezhtm@aakkmail.com


--- PERFIL 59 ---
LOGIN: 61577567815156
SENHA: NLAS@9C3Ioba
2FA: JUFA6MH7BRQBEJQWEVUAYNIS3SV4MDGF
EMAIL: jungkhsibril37p99@hotmail.com
SENHA EMAIL: VZnR8agzXOWzV
EMAIL BACKUP: bgowtek@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 60 ---
LOGIN: 61577232036699
SENHA: NLAS@MOyWwEk
2FA: JCP64M2FSKCC4XHYCPIYDUQG2JCQOMLY
EMAIL: latenrhugannvk8w@hotmail.com
SENHA EMAIL: McnY7xlzBmG
EMAIL BACKUP: apeyav@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 61 ---
LOGIN: 61577370839008
SENHA: NLAS@tYpHRCJ
2FA: FXTOKGCJR3C34XHA4Y6K2NBVRXXJCEEZ
EMAIL: borrokdeenymna08@hotmail.com
SENHA EMAIL: dVDsDRR7hlx
EMAIL BACKUP: zaagw@fexpost.com
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @fexpost.com)


--- PERFIL 62 ---
LOGIN: 61577365859863
SENHA: NLAS@i59wADv
2FA: ADKI2O6WIMLNMEKN6LINMNBS35LZZAPR
EMAIL: fraisslydentvq6@hotmail.com
SENHA EMAIL: DEcKr0QcW8kRsn
EMAIL BACKUP: ucykpu@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 63 ---
LOGIN: 61577706020170
SENHA: NLAS@b58kdEZ
2FA: B4GME3N7JM4P5D7A2IVRF4E357DPLIC5
EMAIL: leevyvkusekd3tg3d@hotmail.com
SENHA EMAIL: aGRoD6Bq99TD
EMAIL BACKUP: bpu5d6d44lj0@onuexf.5smail.email


--- PERFIL 64 ---
LOGIN: 61577578343744
SENHA: NLAS@wfpxgss
2FA: CSEXUVY56QGL275MYIXS7FX6VD3MQX4H
EMAIL: terriflizzo7gt7m1@hotmail.com
SENHA EMAIL: YzhimIfI5o4
EMAIL BACKUP: fefponq@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 65 ---
LOGIN: 61577669241084
SENHA: NLAS@7EIje1P
2FA: OHGIYFS3BBANOY6Q6ULFPQWMS5F7FF4X
EMAIL: masurhknust13eua6@hotmail.com
SENHA EMAIL: Ye9iB5LRwQYyI
EMAIL BACKUP: hl4eeison4q0@k0bur.5smail.email


--- PERFIL 66 ---
LOGIN: 61577237046236
SENHA: NLAS@tzoaC0R
2FA: FGRZXREBKUMAKUJVQMH5JHUKV2ARSJCH
EMAIL: aynesrmonas3nq@hotmail.com
SENHA EMAIL: SgJPqZWctffiL
EMAIL BACKUP: nmedy@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 67 ---
LOGIN: 61577320412335
SENHA: NLAS@6hd7ZKu
2FA: MWEP4ZXRIUVC456O6THF7QT4EOBN2V7E
EMAIL: helsabmicekqcpc@hotmail.com
SENHA EMAIL: pk4BHBYrVFV8c
EMAIL BACKUP: rgkh32p5cf0b@m1r36c.5smail.email


--- PERFIL 68 ---
LOGIN: 61577234257146
SENHA: NLAS@SFHnLr4
2FA: 4QTZ74CL6AV3OKLXOWH6ZMB6WBIUEMWO
EMAIL: nozumqseltzqn1@hotmail.com
SENHA EMAIL: HEwjBC6a3wWO2
EMAIL BACKUP: msute@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 69 ---
LOGIN: 61577646592417
SENHA: NLAS@fuBgI4y
2FA: K3S2YK3VZTGM557RBW7OGXJKUJ6DY4RR
EMAIL: ursinesabra03ek@hotmail.com
SENHA EMAIL: nafpSWQg2k9
EMAIL BACKUP: 6a56sxmyg3b0@813o.5smail.email


--- PERFIL 70 ---
LOGIN: 61577302113795
SENHA: NLAS@cbGhNkp
2FA: 2U5ULY4UELSPGYGGKKIJOMTVIHRQ3VSR
EMAIL: voguencilmio5b@hotmail.com
SENHA EMAIL: Eiv1a8rzVFqaha
EMAIL BACKUP: subzmed@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 71 ---
LOGIN: 61577201468434
SENHA: NLAS@RWLVi3u
2FA: D4IKD4D7PTOYCP3CDQSFLLMTTCVXCRLZ
EMAIL: solanscoteynmpo0@hotmail.com
SENHA EMAIL: InAwQBGo4GOZT
EMAIL BACKUP: qazsu@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 72 ---
LOGIN: 61577297643468
SENHA: NLAS@Os7LiRM
2FA: J3QGFAJLGYL4OB2OV5RR4WXE42I7S6BS
EMAIL: soineavoelzf8hxs2@hotmail.com
SENHA EMAIL: srJOvNm7xNpJ2
EMAIL BACKUP: nhacuud@chitthi.in
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @chitthi.in)


--- PERFIL 73 ---
LOGIN: 61577189589109
SENHA: NLAS@v0BQZbP
2FA: MMGYAOTKFDLGM472TJDRVAC4G7TMTCRU
EMAIL: munochmaryly0s0@hotmail.com
SENHA EMAIL: HorwYRh02StTo
EMAIL BACKUP: z1616zzwl80x@d282e.5smail.email


--- PERFIL 74 ---
LOGIN: 61577194838189
SENHA: NLAS@EXvwz7G
2FA: Z26O4ASMIDR76IUBNXSBFP37AHBFK444
EMAIL: bedkehfulsecf9k2t@hotmail.com
SENHA EMAIL: SOlIxtj6YzDri
EMAIL BACKUP: dwpg7qt401p0@ka8s.5smail.email


--- PERFIL 75 ---
LOGIN: 61577267555297
SENHA: NLAS@fUkWGT1
2FA: B33WUTMPT6QA2SWA7UDSWSCZPWJBUTEE
EMAIL: lemosikubisvk97@hotmail.com
SENHA EMAIL: yFAOwUfV39738
EMAIL BACKUP: gebyk@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 76 ---
LOGIN: 61577352421029
SENHA: NLAS@mPcHS47
2FA: R2IZJR5EUSWJ3ZCTLHMFNFRIRI5WCMSC
EMAIL: yokanknalanezumbu@hotmail.com
SENHA EMAIL: qzRG6tjedHY4
EMAIL BACKUP: qoagyt@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 77 ---
LOGIN: 61577689190998
SENHA: NLAS@p8MbB6h
2FA: QXII2C7TFEUTZ7OQ7NCOVA27YTA2DPPA
EMAIL: peesoekruis7r2xu0@hotmail.com
SENHA EMAIL: OyUisd6zHbeE
EMAIL BACKUP: kfh3sjvqqy0d@pt3v8kj.5smail.email


--- PERFIL 78 ---
LOGIN: 61577139581386
SENHA: NLAS@MogcFAL
2FA: BYHLRXQJUVDOFF4GNRGPY5HFGFTAVG57
EMAIL: bilbyulatifi6uk@hotmail.com
SENHA EMAIL: MA47cy5CTS5D
EMAIL BACKUP: np6978x8zqh0@ie7e.5smail.email


--- PERFIL 79 ---
LOGIN: 61577643292765
SENHA: NLAS@Hph2MBY
2FA: YHKHG42GIVICTSPGPJ2K4IRYLIJLJ4MK
EMAIL: seronflarck1gh7lx@hotmail.com
SENHA EMAIL: YjZ2hcv2H3F
EMAIL BACKUP: uznop@fexbox.org
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @fexbox.org)


--- PERFIL 80 ---
LOGIN: 61577266595485
SENHA: NLAS@PfMWV2y
2FA: 2Q4ANG6FPOZDCAWOLHYB7TK7CJCUXLQS
EMAIL: grodeutrupey9j28@hotmail.com
SENHA EMAIL: yKFBGUwiPvwV
EMAIL BACKUP: ytgafc3765@fexpost.com
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @fexpost.com)


--- PERFIL 81 ---
LOGIN: 61577153741361
SENHA: NLAS@XhAwG13
2FA: WB4RUXHDTNP37FR3VU4TDRBFXTXYWKHU
EMAIL: cofieyzvara6lmay8@hotmail.com
SENHA EMAIL: ORiR0I3BSDyS
EMAIL BACKUP: ci6crt99li80@n6ux46.5smail.email


--- PERFIL 82 ---
LOGIN: 61577342371479
SENHA: NLAS@IFg3PHJ
2FA: EC67DNN74VKIJ37XSXDGVEMFKNLRJZW5
EMAIL: holumeseveyohsl@hotmail.com
SENHA EMAIL: VDfjWWtpjczET
EMAIL BACKUP: socud275228@fexpost.com
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @fexpost.com)


--- PERFIL 83 ---
LOGIN: 61577096142436
SENHA: NLAS@qqCjDZs
2FA: GPD23SDHC56S6XE5Q3V7ZZR4RVPNLSUX
EMAIL: menzezassamk7w@hotmail.com
SENHA EMAIL: DTqHFLvjcOBJ
EMAIL BACKUP: vevodfe@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 84 ---
LOGIN: 61577412808168
SENHA: NLAS@6PlMLI6
2FA: PSFS7VUQOL6AJOBH3HRKAY7S7NXKO6KZ
EMAIL: murryrpruynvmt@hotmail.com
SENHA EMAIL: mBPqRmFgKpB4s
EMAIL BACKUP: euuqf275228@fexpost.com
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @fexpost.com)


--- PERFIL 85 ---
LOGIN: 61577331992188
SENHA: NLAS@I3UBeOY
2FA: QRXE3622QNZ6WSUAYSH6EYPIZFJYXOY4
EMAIL: rossiniambitious412@hotmail.com
SENHA EMAIL: RSHS0n5H34
EMAIL BACKUP: hosabd@fexbox.org
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @fexbox.org)


--- PERFIL 86 ---
LOGIN: 61577679530042
SENHA: NLAS@0LcPyob
2FA: H636FZWXXX3WC67VKDRHPEEZFAWN6QRP
EMAIL: gadengrorkey7kqqs@hotmail.com
SENHA EMAIL: JxmsEoqWci1
EMAIL BACKUP: pxyfow@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 87 ---
LOGIN: 61577296531882
SENHA: NLAS@5WPGmIO
2FA: 5GKMAQWBQRTTTZPIFTQD745ULUHEWCCI
EMAIL: conerdemamigexg7h@hotmail.com
SENHA EMAIL: szawWSDAJ8
EMAIL BACKUP: zvuugbu@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 88 ---
LOGIN: 61577634201814
SENHA: NLAS@MK8jFbx
2FA: 5MSCPFA5HXKVTAAQJ777BRWRTESAWZWI
EMAIL: flaumetolgaztipo@hotmail.com
SENHA EMAIL: ooKZB9cEDV6r
EMAIL BACKUP: bsuktgu@merepost.com
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @merepost.com)


--- PERFIL 89 ---
LOGIN: 61577279703582
SENHA: NLAS@IPUGqc6
2FA: EHEA5FCWQFN4MOHQ5XF3SDFJ6ZAQHJ7H
EMAIL: erdiecollerm8tqc@hotmail.com
SENHA EMAIL: dzGfrpfuGmDXp
EMAIL BACKUP: ohoze@merepost.com
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @merepost.com)


--- PERFIL 90 ---
LOGIN: 61577025976417
SENHA: NLAS@CD8rSNS
2FA: X532BNZAVD4ZSCZDAO4CGXHRFBCTVCEM
EMAIL: mekicxberone6vqyo@hotmail.com
SENHA EMAIL: dyNRo1aBlK3o
EMAIL BACKUP: muxacy@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 91 ---
LOGIN: 61577412597037
SENHA: NLAS@XdOA0ht
2FA: RQHKFLETB6HGRF7YLWPKJPSV35BVBPHM
EMAIL: kapesemitevtuh@hotmail.com
SENHA EMAIL: NifatamdmWnYGF
EMAIL BACKUP: yvexhyc@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 92 ---
LOGIN: 61577017486267
SENHA: NLAS@I86Id8I
2FA: F6B34MMXZ36QF42TSKCAXHB7EOMNF2JF
EMAIL: astinzavanakhz4h@hotmail.com
SENHA EMAIL: ONSTdNskTI4c
EMAIL BACKUP: osgex@merepost.com
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @merepost.com)


--- PERFIL 93 ---
LOGIN: 61577039985352
SENHA: NLAS@usyoIJe
2FA: PPEKVEKOXVH36HFMJV74WSJMPO7DQTFK
EMAIL: salarosurat7jl8@hotmail.com
SENHA EMAIL: Rx5i45nI0cx3
EMAIL BACKUP: peuxx@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 94 ---
LOGIN: 61577283482630
SENHA: NLAS@8nncsm4
2FA: IHXWKEGF5J6ZZQM77RORP3BUQILJM4SX
EMAIL: neviscmakos1hlw7@hotmail.com
SENHA EMAIL: crIpHbInSm4V
EMAIL BACKUP: cyqywup@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 95 ---
LOGIN: 61577569494119
SENHA: NLAS@enLsMXf
2FA: APMSHLONSYAJ6WAIHKTX5QVDZUHKW5NK
EMAIL: glivakmankosf64aw@hotmail.com
SENHA EMAIL: fDwri2UqmQpNNH
EMAIL BACKUP: abahf@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 96 ---
LOGIN: 61577301361002
SENHA: NLAS@Xb6KCUI
2FA: BJNBM23QGNSDRZ7DBRCH3PRXMJJU7MT5
EMAIL: kettydjoersps6o@hotmail.com
SENHA EMAIL: NphxBtwv1kVJ
EMAIL BACKUP: ossamun@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 97 ---
LOGIN: 61577011995654
SENHA: NLAS@hgr82Bc
2FA: URW3P3NBTTINN5CM3DVRBRC35URFSO3I
EMAIL: weethucemervun@hotmail.com
SENHA EMAIL: FFyaC6dQrwg
EMAIL BACKUP: okycuh@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 98 ---
LOGIN: 61577355329063
SENHA: NLAS@SWE4zKx
2FA: F25CVBC3RM3N4RJGVGVTMNP2LK4NRUU5
EMAIL: frazepsakyivhdqjj@hotmail.com
SENHA EMAIL: mYNihLmn7H8I2c
EMAIL BACKUP: yuefad@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 99 ---
LOGIN: 61577125300184
SENHA: NLAS@SJqI8pq
2FA: ZPA4TDS2ZVP7Q3UVUATF5NDT6BZ63X7V
EMAIL: sicalqkerche2i@hotmail.com
SENHA EMAIL: NA7QEuHKosyxC
EMAIL BACKUP: yayzuk@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)


--- PERFIL 100 ---
LOGIN: 61577362558619
SENHA: NLAS@qXvL2K1
2FA: VHXTJALPIWZ6DOHBGHYYLSEJ5NFSYD4Q
EMAIL: gliwazrover35a@hotmail.com
SENHA EMAIL: dVCcMNh24ze
EMAIL BACKUP: otzaeq@mailto.plus
SITE DO BACKUP: https://tempmail.plus/pt/#! (Selecionar @mailto.plus)`;

function resolveBackupService(emailBackup) {
  if (!emailBackup || typeof emailBackup !== 'string' || !emailBackup.includes('@')) return '';
  const domain = emailBackup.split('@')[1].toLowerCase().trim();

  const mailTdDomains = [
    'qabq.com', '6n9.net', 'sugtbt.com',
    'end.tw', 'nqmo.com', 'uuf.me', 'mail.td', 'hebb.me', 
    'txc.tw', 'bep.tw', 'vdu.me', 'yod.me', 'zxo.me', 
    'tmail.ws', 'givmail.com', '20mail.it', '20mail.eu'
  ];

  const tempMailPlusDomains = [
    'mailto.plus', 'fextemp.com', 'fexpost.com', 'fexbox.org', 'fexbox.ru',
    'mailbox.in.ua', 'rover.info', 'chitthi.in', 'any.pink', 
    'merepost.com', 'tempmail.plus', 'boxim.org'
  ];

  const fviaDomains = [
    'fviainboxes.com', 'fviadropinbox.com', 'fviamail.work', 'dropinboxes.com', 'fviainbox.com'
  ];

  const inboxesDomains = [
    'inboxes.com', 'getnada.com', 'getairmail.com', 'dropjar.com', 'inboxbear.com',
    'blondmail.com', 'chapsmail.com', 'clowmail.com', 'fivermail.com', 'getmule.com',
    'gimpmail.com', 'guysmail.com', 'replyloop.com', 'robot-mail.com', 'spicysoda.com',
    'tafmail.com', 'temptami.com', 'tupmail.com', 'vomoto.com'
  ];

  const moaktDomains = [
    'moakt.com', 'moakt.ws', 'moakt.cc', 'moakt.co', 'disbox.org', 'disbox.net',
    'tmails.net', 'tmpeml.com', 'teml.net', 'tmpmail.org', 'tmpmail.net', 'bareed.ws'
  ];

  const tempMailoDomains = [
    'temp-mailo.org', 'skynoname.com', 'mooncapt.shop', 'thosanlimited.shop', 
    'kuimkwzoi92.shop', 'idolpromote.shop', 'babytalk.shop', 'baohong.online', 
    'inlove.website', 'metuna.online', 'milaviala.online', 'mmoechannel.online', 
    'piazan.store', 'visaothenhi.space', 'kugdapcapcut.online', 'chiencapcut.site', 
    'bigbangfan.com', 'gdrfan.com', 'nutioan.online', 'vipgdr.com', 'prousa.online', 
    'ansart.shop', 'demdon.online', 'xoxoho.com', 'xohoxo.com'
  ];

  if (mailTdDomains.includes(domain) || domain.includes('mail.td') || domain.includes('qabq') || domain.includes('6n9') || domain.includes('sugtbt')) {
    return `https://mail.td/ (Selecionar @${domain})`;
  }

  if (tempMailPlusDomains.includes(domain) || domain.includes('tempmail') || domain.includes('mailto.plus') || domain.includes('fextemp') || domain.includes('fexpost') || domain.includes('fexbox')) {
    return `https://tempmail.plus/pt/#! (Selecionar @${domain})`;
  }

  if (fviaDomains.includes(domain) || domain.includes('fvia') || domain.includes('dropinbox')) {
    return `https://fviainboxes.com/ (Selecionar @${domain})`;
  }

  if (inboxesDomains.includes(domain) || domain.includes('inboxes.com') || domain.includes('getnada')) {
    return `https://inboxes.com (Selecionar @${domain})`;
  }

  if (moaktDomains.includes(domain) || domain.includes('moakt') || domain.includes('disbox')) {
    return `https://moakt.com (Selecionar @${domain})`;
  }

  if (tempMailoDomains.includes(domain) || domain.includes('temp-mailo') || domain.includes('capcut')) {
    return `https://temp-mailo.org/en/mailbox/ (Selecionar @${domain})`;
  }

  if (domain.includes('easyme.pro') || domain.includes('mailmomy.com') || domain.includes('282mail.com') || domain.includes('sbooks.pics')) {
    return 'https://www.easyme.pro/mailbox';
  }

  if (domain.includes('681mail')) {
    return 'https://681mail.com/';
  }

  if (domain.includes('5smail') || domain.includes('5scode') || domain.includes('reg.io.vn')) {
    return `https://5smail.email/ (Selecionar @${domain})`;
  }

  if (domain.includes('aakkmail')) {
    return `https://aakkmail.com/ (Selecionar @${domain})`;
  }

  return `https://${domain} (Selecionar @${domain})`;
}

// Process user input
const blocks = userInput.split(/--- PERFIL \d+ ---/g).map(b => b.trim()).filter(Boolean);
console.log('Total blocks found:', blocks.length);

let missingBackupCount = 0;
const processedBlocks = blocks.map((block, idx) => {
  const num = String(idx + 1).padStart(2, '0');
  const lines = block.split('\n').map(l => l.trim()).filter(Boolean);
  
  // Find fields
  let login = '', senha = '', twofa = '', email = '', senhaEmail = '', emailBackup = '', siteBackup = '';
  for (const line of lines) {
    if (line.startsWith('LOGIN:')) login = line.replace('LOGIN:', '').trim();
    if (line.startsWith('SENHA:') && !line.startsWith('SENHA EMAIL:')) senha = line.replace('SENHA:', '').trim();
    if (line.startsWith('2FA:')) twofa = line.replace('2FA:', '').trim();
    if (line.startsWith('EMAIL:') && !line.startsWith('EMAIL BACKUP:')) email = line.replace('EMAIL:', '').trim();
    if (line.startsWith('SENHA EMAIL:')) senhaEmail = line.replace('SENHA EMAIL:', '').trim();
    if (line.startsWith('EMAIL BACKUP:')) emailBackup = line.replace('EMAIL BACKUP:', '').trim();
    if (line.startsWith('SITE DO BACKUP:')) siteBackup = line.replace('SITE DO BACKUP:', '').trim();
  }

  // If siteBackup was missing, calculate it!
  const resolvedSite = resolveBackupService(emailBackup);
  if (!resolvedSite) {
    missingBackupCount++;
    console.log(`Missing site for profile ${num}: backup = ${emailBackup}`);
  }

  const outLines = [
    `--- PERFIL ${num} ---`,
    `LOGIN: ${login}`,
    `SENHA: ${senha}`,
    `2FA: ${twofa}`,
    `EMAIL: ${email}`,
    `SENHA EMAIL: ${senhaEmail}`,
    `EMAIL BACKUP: ${emailBackup}`,
    `SITE DO BACKUP: ${resolvedSite}`
  ];

  return outLines.join('\n');
});

console.log('Profiles with missing backup site:', missingBackupCount);

fs.writeFileSync('/Users/itallosousa/.gemini/antigravity-ide/scratch/perfis_100_completos.txt', processedBlocks.join('\n\n\n'), 'utf8');
console.log('Written to /Users/itallosousa/.gemini/antigravity-ide/scratch/perfis_100_completos.txt');
