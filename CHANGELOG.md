# Changelog

## 0.1.0 (2026-07-22)


### ⚠ BREAKING CHANGES

* requires-python is now >=3.10 (narwhals 2 requires 3.10+, and Python 3.9 reached end of life in October 2025).

### Features

* add data model and create_upset figure factory (M1) ([1c45732](https://github.com/PhylaTech/dash-upset/commit/1c4573242ae6d43b88a8ec7cbe26e33a729efd6f))
* add deviation (compute, sort, hover) ([568067f](https://github.com/PhylaTech/dash-upset/commit/568067ff420866e43e70af351c091e6b7e608c64))
* add intersection modes (distinct/intersect/union) ([29b80db](https://github.com/PhylaTech/dash-upset/commit/29b80db65938eb77108ff230b9d4fe86288c359d))
* add show_percentages bar labels ([f3fde6c](https://github.com/PhylaTech/dash-upset/commit/f3fde6cd1ffb3719e3ffb1cb2074bc28d528f175))
* add subset filtering (min/max size, min/max degree, top-N) ([12136f2](https://github.com/PhylaTech/dash-upset/commit/12136f25729ef533dbd8a33f449413204e7a629e))
* add theme system to create_upset (light/dark/auto + CVD palettes) ([1c0c6b0](https://github.com/PhylaTech/dash-upset/commit/1c0c6b088908b0f3dab485ab70bc23f76fcd6972))
* add UpSet Dash component + dataframe input (M2) ([181962e](https://github.com/PhylaTech/dash-upset/commit/181962e6338ed018ee89680ef220a782b949fbf9))
* adopt Option B and implement M1 (data model + create_upset) ([cdd3abb](https://github.com/PhylaTech/dash-upset/commit/cdd3abb47d204a93c9f990f1c415b759c34aae6d))
* back UpSet with a compiled React component exposing selection props ([5409507](https://github.com/PhylaTech/dash-upset/commit/540950763a6fe4655f532edef4698f49fdf801a8))
* back UpSet with a compiled React component exposing selection props ([362f676](https://github.com/PhylaTech/dash-upset/commit/362f676c22f3028847dcea18ae5c30c1c0c67615))
* make from_indicators dataframe-agnostic via narwhals ([446c10b](https://github.com/PhylaTech/dash-upset/commit/446c10b9264a2562007331ef1e4cf96999e90183))
* show_percentages bar labels (M3) ([ab24201](https://github.com/PhylaTech/dash-upset/commit/ab242017446440d8207dfeaefcd01d5f4e5771b9))
* theme system for create_upset (light/dark/auto + CVD palettes) ([2c1ddc4](https://github.com/PhylaTech/dash-upset/commit/2c1ddc48632a3a320f0a9ef66842a7f71c358532))
* UpSet Dash component + Plotly-idiomatic dataframe input (M2) ([c1157a8](https://github.com/PhylaTech/dash-upset/commit/c1157a8111026245f70c40074cc6524d741a9dc6))
* vertical orientation; cross-filter drill example + from_counts sep ([#16](https://github.com/PhylaTech/dash-upset/issues/16)) ([0cfd33b](https://github.com/PhylaTech/dash-upset/commit/0cfd33bfef4d3419b8da16d85e7686b2817b7772))


### Bug Fixes

* ship complete third-party license notice for the bundled component ([#17](https://github.com/PhylaTech/dash-upset/issues/17)) ([353f7be](https://github.com/PhylaTech/dash-upset/commit/353f7be91f71adc0f490e3151ff7d8d60ad555dc))


### Documentation

* add CLAUDE.md session handoff for fresh dash-upset sessions ([d809fa6](https://github.com/PhylaTech/dash-upset/commit/d809fa603c8f5e616da9414030517bbba6ed7ee8))
* add competitive survey of the UpSet ecosystem ([fe9e957](https://github.com/PhylaTech/dash-upset/commit/fe9e9577673c1192bfa43238373eba79aba72702))
* add landing-page site matching dash-seqviz.com design ([ec77408](https://github.com/PhylaTech/dash-upset/commit/ec7740851707abfe02c349a8aa31568aa7211982))
* add on-site API reference page; point nav Docs to it ([d02dad7](https://github.com/PhylaTech/dash-upset/commit/d02dad7b97a6c08c752e950ed1eeeffae9802f36))
* adopt naturalist-press house style (warm/Bricolage/rust) ([4785c2c](https://github.com/PhylaTech/dash-upset/commit/4785c2cdf6c55dde46d0a311b365f61442f024fe))
* build full site IA to match dash-seqviz (examples, detail, explorer) ([efbffbf](https://github.com/PhylaTech/dash-upset/commit/efbffbfde09110b59e5cd481187486fc3f24e53f))
* feature UpSet component + df/sets as primary API ([eacc74b](https://github.com/PhylaTech/dash-upset/commit/eacc74bb298dc13fcf7e50399970c015aece41ad))
* feature UpSet component + df/sets as the primary API ([20f1deb](https://github.com/PhylaTech/dash-upset/commit/20f1debfe14654977487dfabf46b138861b8247c))
* fix landing-page nav to in-page anchors ([60d8714](https://github.com/PhylaTech/dash-upset/commit/60d87142c3d5fdec4a0ef766b432ee39ef148e09))
* footer "Made with ❤️ by PhylaTech" ([eb1932d](https://github.com/PhylaTech/dash-upset/commit/eb1932d3044f4047e5dcf30b798d40002c534343))
* footer reads "Made with love by PhylaTech" ([e390368](https://github.com/PhylaTech/dash-upset/commit/e390368d9ee4b9d2e0e9db4192782d2102ee7214))
* full site IA (Examples, Example detail, Component Explorer) ([9e7d150](https://github.com/PhylaTech/dash-upset/commit/9e7d150e4b0bdfba7193b9fcb5aad52d53138bcd))
* match dash-seqviz layout (workbench explorer, install tabs, brand) ([#15](https://github.com/PhylaTech/dash-upset/issues/15)) ([83be580](https://github.com/PhylaTech/dash-upset/commit/83be580921b4c45916301ef2dbe1086b49118ebd))
* naturalist-press redesign + prose Reference + theme ([f5843c5](https://github.com/PhylaTech/dash-upset/commit/f5843c540e96a648decce99554f5d21b247e3e21))
* on-site API reference page (nav Docs no longer links to GitHub) ([68aeb5c](https://github.com/PhylaTech/dash-upset/commit/68aeb5ceccddf4461bb873763d36b01225bcdb13))
* record Option B (Plotly-native) as the rendering engine ([096dd2b](https://github.com/PhylaTech/dash-upset/commit/096dd2bcc3c9c30334e606ef6ca3df8cbba42277))
* record UpSet 2.0 (BSD-3) as the Option C candidate engine ([45ff0b1](https://github.com/PhylaTech/dash-upset/commit/45ff0b1c6d7e6128470b3cad730969155ee84acf))
* rewrite Reference as human-readable prose; nav Docs -&gt; Reference ([3868e6c](https://github.com/PhylaTech/dash-upset/commit/3868e6c7971fc284c296e8f3e34036f9c4507f42))
