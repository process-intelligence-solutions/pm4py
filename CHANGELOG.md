# Changelog of pm4py


## pm4py 2.7.14 (2024.XX.YY)

### Added

### Changed

### Deprecated

### Fixed

### Removed

### Other


---


## pm4py 2.7.13 (2024.07.11)

### Added

### Changed
* 75c893999e32b3a1a6081db854b9a3cd10eaaa44
  * Dockerfile refactoring
* 7b80dad1fcc6955730357f46754c4a511b83ee58
  * updating requirements list
* 52459f95d42e2fc39568b0d685bd794c319f205a
  * refactoring dependencies generation script
* 928ecf5f8192ff1ef7944c5b0a7be7c530814ad9
  * refactoring OpenAI query interface
* 5fee9b4ac61c227ac77cbd28b888a7321ba401bf
  * refactor OCEL object repr
* 6c1ea7a38b3ef18fe9d490164ecebd85c432915f
  * possibility to set the title in pm4py visualizations

### Deprecated

### Fixed
* 954c2fbdc258b90bcba85001592a5d2950a79724
  * bug fix temporal profile conformance checking
* cd8f9fb9f49a5955f0a26f547770aefa8ff222b8
  * issue with closing in-memory files when parsing a XES from string
* d51bd9e24aed442f011917d6b77793b118bbf89f
  * minor fix OCEL interleavings computation
* 39d769cad1327c47d5948b0c40be4a90e41fcce7
  * removed indeterminism in TBR with duplicate transitions
* 2fb8e6bffcac11b14fe13f152ac0b096cdc0d03a
  * penwidth assignation in DFG edges
* c753425ffd63da55fc0d3e71ab5b5fb62a2bf359
  * OCEL exporters consistency check
* e98d795c977348dcbe7495d62c8975fae0b9499c
  * LTL filters documentation in the simplified interface

### Removed

### Other
* ed708047252f96f3bf103ba81d6139b433c39b85
  * printing Python versions in tests and examples
* c48882b88326608dc5c6a4101b8123c71a852e18
  * parameter to enable/disable visualizations
* 607d2eb601299a23335f8c1976cc59f63bcae5f2
  * added example for Inductive Miner LC

---


## pm4py 2.7.12.1 (2024.04.17)

### Added

### Changed
* 5641f9f2c830b567c138524a0b5e705a3836102a
  * minor change OCEL names_stripping
* c48882b88326608dc5c6a4101b8123c71a852e18
  * parameter to enable/disable visualizations' view

### Deprecated

### Fixed
* 1c6887fda74d2b0a36f483351a6978738517e61e
  * bug fix inductive miner infreuent
* e7e8ebf6894d9bc85febc43c82613d185e16ee3b
  * solving performance bottleneck in IM
* 4811bbde07f6639deb7c87bdda61504de0889873
  * resolved indeterminism in IM fallthroughs
* df1db968adf8bb5f483410be0ceef2928c2b3e6c
  * missing tree sort in IM
* 4958e2b8407c01923e5b65c7e46a5f89d8f927dc
  * missing fold of PT objects in IM
* 8e404c6c2b53cf14687d1f82d53a4a0fc4ac99d6
  * fixed folding of PTs
* a871cbc4bdeaa81013fbfa7a6ec5054d494cb329
  * fixed parsing of PTs
* a72cd92410653bf2f0b2ff35ab5d06bf73a95305
  eddae51259114caf4e1447beee4981f2e00bcb9c
  69dcf7a836a5af3ab5da64701f43e3d8cf6b07aa
  * fixed WF-net-to-PT conversion
* 0980ac460d69beb9ede4403a3ed002c1cd30536e
  * fixed docstring OCEL flattening
* 6f9c67f48ad89e88d58c2481e85c6f3de9e6e1a5
  * fix small issues with stochastic Petri net
* 6781a90df2ba8d90155e7b5135520076843cac33
  * bug fix DECLARE discovery and conformance checking
* 7330d5100c8b8916eba9e4b0f31e8fa1f9157c98
  * bug fix log skeleton discovery (always after, always before)
* ec2f0b5b43d83a7b9fa154456241e3c685fcb721
  * bug fix log-to-prefix-tree discovery (final nodes)
* d580fedd4b770ed85f6864cd6d435db2477684f2
  * bumping release number. forcing numpy<2 and pandas<3
* 4f8bbf6d884e25c5474479fd86fe7331076ac2fe
  * bug fixes for Pandas >= 3.0 future support

### Removed

### Other


---


## pm4py 2.7.12 (2024.03.21)

### Added
* 458ee9abf2fc155a7531be96992c9a0c27f8cb81
  * maximum number of consecutive occurrences of the same activity in pm4py.get_variants
* b4c914722605b37f787e156f407ea9333a8dd959
  * more general between and activity split filters

### Changed
* 100b95c22a47eace59fc631541b2c34c9179765d
  09d4e7a07f92fddd90c1b1bbe572308380d7c8f3
  * changed BPMN visualizer
* f7b44a41a79760e4f092be2bf98087ea48b63de4
  * changed BPMN conversion
* db98b6fbf16847eceab4b53216cc1a1096936785
  * improved BPMN support (collaboration, gateways, ...)

### Deprecated

### Fixed
* e3b8172e4c005dcb633c9018b9b9439d84580f7b
  * fixing random variables support
* bb759da149b434d0e279256c8c6d397b06079729
  * fixing sampling
* a816fb5f000a907b603b44aba1470463109028f0
  * bug fix OC-DFG visualization
* 419a95362472c0807b73f4eb3d601f70b3d7c986
  * bug fix POWL visualizer

### Removed

### Other


---


## pm4py 2.7.11 (2024.03.01)

### Added
* 0fcb1dc2939db30b7129f62bda0d235bd5242428
  * improved string representation of hierarchical models
* 0b0d09226574916c5d33c000cbc2a4ffa0a13e7a
  b56ff781c99ce3126c1ec45d502c16d1c2f3b0b6
  * BPMN layouting in the frontend
* b39a7326faf2afb55b8880ce420cdda4a03ffa5c
  * activity split filter (Pandas dataframes)
* 6a7cfeaa06d405591d13b6055bf890b8b4a6b3b9
  * float dtype and padding in log_to_target transformaiton methods

### Changed
* 56799b618ad1ab727705e24f40aa13a793552326
  * refactoring BPMN-GraphViz visualization method
* c56bd55b83133d231f37ac8c89190efb440bb826
  * moving hierarchical models indentation to separate class
* d865660c5370640b4c5c013239f6940f145d9e93
  * refactoring log-to-OCEL

### Deprecated

### Fixed
* c2278110acbbbf36e8fe5055e0b76f867e833da4
  * bug fix POWL package
* d36d0d2ff8133bc979638b7f3405f96225e06ced
  * bug fix discover_dfg_clean
* 64ce3341d40c073f274bdda9842fd92a0798a33f
  * fixed typing of get_variants method
* ffd0761e8f5490382b33de4fa8187f1ed80ce802
  * fixed stochastic Petri net PNML importing
* c9654d8089c5aa0e930ee932b222cc09be25d8a5
  * fixed typing of pm4py.filter-variants
* 8475c194929f74bf4e402b24c637299d8c28042a
  * fixed export of multi-swimlanes BPMNs
* d32e236cc99ec1b5de198466fe0966752adeb805
  * fixed incongruency in BPMN visualizer
* b40821da2612ae1921aec30da2333dc4e1151f1a
  * fixed exception handling in OpenAI requests
* e8f0b84bc7de65f090e0e96799486acaaad7572f
  * fixed incongruency between filter on EventLog
* 771cfcd6f2321a9106781e15c97895b26d5acbf3
  * fixing behavior of between filter when act1 == act2
* e1c84d7f6d6425f40a23ea3c539a0c110c331a3c
  * ensuring float return for feature extraction methods in pm4py
* 1b5a2932a60131f648ae476e6b97230c241f5d6e
  * fixing POWL visualization image importing

### Removed

### Other
* c4d24d54013e2a18856af840ffbad7c76e86c371
  81fa8017fbd25352fd87961bc4dcc1406c4e0dda
  * Process tree to POWL utility

---


## pm4py 2.7.10 (2024.01.29)

### Added
* f5316b9e856e16a0a7a25c27f11b73546654c4e9
  * methods for simplicity and generalization in the simplified interface
* c874ba919de25a2a0a69bc1adb324a25484ddc07
  * key/mouse events logger for Windows with screenshots recording

### Changed
* 1c93795884140f27d5eae5d2eade1823c93a92d2
  * refactoring Scikit-Learn usage throughout the project
* bd1ac4fd04019b3022bfff55553e590aefbd21cb
  * refactoring NetworkX usage throughout the project

### Deprecated

### Fixed
* 25ca20af830df69a983c6fd53bb2e456ccc11c25
  * removed circular dependency on pm4py.util
* 0da8c5f04f89dab8b9f5a3d31d8f5beb927e71d4
  * fixing OCEL 2.0 support
* 7b2c8ffee70c94c1acce7c28a7b366d5ed95bb6b
  * fixing TBR diagnostics computation

### Removed

### Other


---


## pm4py 2.7.9.2 (2024.01.16)

### Added

### Changed
* ab48f194ed0bbcd864683d313285e0db6a3ae570
  * refactoring DECLARE discovery
* ba3dd14250f3b713c495833d1ed16d42efb74c7a
  * moved LLM descriptions to separate methods

### Deprecated

### Fixed
* 99efc597545a1f0f717c90303db8ca3825062e63
  * bug fix DECLARE discovery
* 4e3cedf1dfdaa70da1e381930812676afc103b22
  * additional PNGs for POWL visualization

### Removed

### Other
* 73edc01f9e7d986d72dc90b88fe92c5265a5d09b
  * utility to convert live event stream to static event stream
* 8ba3e4868b4da409f46559abbb716256517712ee
  * annotating the SearchTuple alignments class with the description of its properties
* 847cf991df054edf81e2b13b70b0e6679a9a15ca
  * check if get_best_worst_cost calculation is always needed

---


## pm4py 2.7.9.1 (2023.12.14)

### Added
* efff63955c1dfd3a3c04c6bf5aecc53042da3b4c
  9ec7578c95d78f91c6c8fcb906f979b6e8680b10
  * description of POWL and process tree models

### Changed
* 3173effdb98dfe37ca3b6770d55aadbbd61b6b7c
  a48390b8be4495177d2e641fc6ae6e868f3544cb
  95853c91ed0c9dbba61fecedac2fd98c793b6933
  864052795e24494023a8b0c76c342db7c8a9305c
  abd315e4c37701dbbf540726496dfb45b3625992
  979cc906c9da648face900141be5f355821ffe61
  4feb5c2000ce82df38294ff3459a25e358d2e69e
  b13ea6458bbea9cc4099109cc28978aa2513a394
  293c282dd8a90eb89273f2f8b98b1279b6e46051
  c672a770bb1a7c58dee0f4f509a93126d0a6f11f
  5545895f299599799222ce90ff7b446caaf9e3bf
  6328037090236e6640a4efa51011e19001a5d300
  ef3de4c7b7803d80b8599d84426badca0c7dfc5d
  * major refactoring pm4py
* 8f494f541b5337ae6abc152afea9b6f09b81fef9
  691aa7d31ae401b16058220a656ffee89fc30eff
  6366dcb3bc08859d4f435b8ad44bdb38c515361d
  * refactoring OpenAI connector
* 376996620052fc23586edc393c73a43288e64164
  * refactoring POWL class and methods

### Deprecated

### Fixed
* 093637828f08618f2d149145dc1740cc2b631ecd
  * fixed BPMN 2.0 exporting (according to the specification)

### Removed

### Other
* f6d15493110e613321214fbf4465fc561e42a698
  * method to project DFG/edit distance alignments on log

---


## pm4py 2.7.9 (2023.11.20)

### Added
* e5bb3b43b47217128763157c9e64ba6b39b1672f
  * OCEL event types-to-object types visualizer
* be7e28440da6f69bfdad43b724931277f04efdbc
  * NetworkX visualization utility
* a17bb8e103b3ee46e46bef17885149070bf7e048
  * Context-based activity label splitting approach (BPM 2023)
* 6583504c6056c43868fe1158744fcc7655270dec
  * Filtering on trace segments
* 9dedaba837e561640a122e50927f7f5b13d4a334
  * Utility to get frequent trace segments
* 19c53e1fcf06c0566a3c697aec37f13345365d04
  * Utility for the computation of service times

### Changed
* fb0d9fb049f128bd979c962db54e3a305ecf5f09
  * Refactoring Pandas calls in pm4py
* 36e19d3f48dabf03509cf87ae6508c0576b089b4
  c38d10574587a3efa21d521f25de40e5ade4409b
  * adapt openai calls to v1 migration

### Deprecated

### Fixed

### Removed

### Other
* 19c53e1fcf06c0566a3c697aec37f13345365d04
  * refactored 'sojourn time' mis-spelling to 'service time' throughout the project

---


## pm4py 2.7.8.4 (2023.11.15)

### Added

### Changed
* a18ed64b90881e15d3ce561dcd7ecc0a56fe5039
  * refactor default XES importer variant specification
* b0d6fbd1c5c23506fb3648511326e83a3c3f89fe
  * refactor default alignments variant specification
* 0b7489571184096bacd195dd824af7c88a57c551
  * refactoring examples (default image format specification)
* de7ab79e285ed5aeb4f4b447fd7f8f1eabb9669c
  d6ef339b32c2e8439815ea589dab1bc0a9e5c851
  * refactoring unit tests entrypoint
* 47407dfdba5976abb78559072905745eb5d37e92
  51993c9a2282f0096e113dfc76b76b46b608bd33
  28f891287d0d61280fb745854c30dc7c301a4c36
  * small changes OCEL to NetworkX conversion

### Deprecated

### Fixed
* e74700dd9d8b965f7cfdb355d03cd582f8da4b2b
  * fixed POWL objects conversion
* e56444ad44a94ece5bd239983165d0754b15a713
  7205aeaa94ad885a9271c359780aa9fac00dee39
  * bug fix JSON-OCEL(2.0) importer/exporter

### Removed

### Other
* 911d5f8630504c3234b716713a58498ead38d2bb
  * converting back NX DiGraph to OCEL/EventLog

---


## pm4py 2.7.8.3 (2023.11.09)

### Added
* d06e2d36558e600208e182f096f07ea86923c1c4
  * RUSTXES importer variant
* 7026be7476ed34c138b1046781847cdd9e104715
  * POWL discovery and visualization in the simplified interface
* 40cd57230a5b0a9fd7821c71cbc2a17b0608e962
  * POWL parser from model string

### Changed
* 3f45baf9c0730d90ab35bce4d715b67306b24168
  * artificial start/end activity symbols specification in the simplified interface
* 215d6a67065074fb516b397a6b9e018cb41cf114
  * ocel_to_nx is now OCEL 2.0 compliant

### Deprecated

### Fixed
* 2e5d06da05e8e961b3f99a0194bd8bf072ce1e32
  * fixed rebase with timestamp format specification
* 753202cee239e62e47a29fd1bc8658f8f36a39d1
  * removed warnings (deprecation) in tests execution
* a209f0df4c16812ac1109150046357c625253106
  * unneeded workaround in managing datetimes inside Pandas
* be4b724582512a8bea207252d565b0ee62715f55
  * PNML importer now returns correctly the parsed stochastic map
* d587e49961dd9b3db76205da5ce9a9fee893dd79
  * dropping newlines in process tree parsing

### Removed

### Other
* 6e3b855c30479d2311458f9732732fc30a248270
  * changed execute_tests.py format
* c62f6fd480b67e466e4c906927413b9f2c87aff4
  * in tests and examples, provide possibility to try with different Pandas backends
* 5424eb9ed576a1ef4f0485ce186b0300bf1ace03
  * example to locate the features for a specific case using pm4py.extract_features_dataframe
* f72e73285e6309df1d5413b4afa7c821facae2e7
  * help desk log

---


## pm4py 2.7.8.2 (2023.10.18)

### Added

### Changed
* d219db5ece5ce68239b217072bf04ac576ded062
  * refactoring DFG utility to also output
    variant-specific paths statistics on request
* 86cbdb103410a692c15e35a1723f7107e573656e
  * removing unused imports throughout the code
* c37cdd31bfbd5742d769fa7a00cea2615e679e2e
  * increased test coverage by testing also the old EventLog methods

### Deprecated

### Fixed

### Removed

### Other
* 26ee9d9311f353327184f3f4b91378a1aa2cdc9d
  * dependencies sheet script


---


## pm4py 2.7.8.1 (2023.10.12)

### Added

### Changed
* b3d88dcfa6553beae4b289191d6aa29020daeeb2
  * refactor pm4py.llm.abstract_log_features (split in two methods)
* b9f74be6ffb68ac1b8c32d6c2cfb3cb3ae5d173c
  * playout variant selection in the simplified interface
* 5aedd3048a9780816f37ad7f89c65a3e56b5229c
  * support for log2log alignments in the simplified interface
* b254210f09d1844dee11b9ccd262baf62779edca
  * return legacy log option in pm4py.parse_event_log_string

### Deprecated

### Fixed

### Removed

### Other
* 9717be4fc6be34c9278ddd7f2d39a0cb8efc4ec2
  * verbose option configuration
* 671688effb5ccf01d5653726de6725810333af0a
  * support to OCEL 2.0 JSON specification


---


## pm4py 2.7.8 (2023.10.06)

### Added

### Changed
* 634b6a5ac1b40963baa76a42a10c3c22176aaf84
  f6993293d665e2f7b69c27ce0f09d2df4e889b0b
  f0240670292086cb3b6fe523b1646dcfa4c71ddc
  * Refactoring OCEL import/export
* c1379120480539f5578a52ce6d76effb4819b3c6
  * centralized enabling/disabling of TQDM progress bar + Disabling progress bar in tests
* 08c2c16d17d2cbe26224662032a298f6b0a409a9
  * avoiding the necessity of re-creating setup.py when new packages are added to pm4py
* a7dc86f7fd821b5dd229ff404b5afa3b5ad919b4
  * disable IM fallthroughs in the simplified interface

### Deprecated

### Fixed
* 063a6d64bae61f1b54444e0b34ec0926b504aa34
  * properly closing file objects in different pm4py importers/exporters (XES, PNML, PTML, ...)
* 35f13b65a0523f889748679fbe90cf2d041e1038
  * fixing XES importing warnings in obtaining the resulting pd.DataFrame
* ef548ef18f514ad6ad0a32a104f380b322ab72e7
  * fixing test/examples execution
* d1b39bde1b14f160c0fff42bdc6b172bb0ae760e
	* fix Petri net serialization
* e51c5e1e084a7fd7d13cb8d1381f868435762cca
	* fixing TBR diagnostics when the methods are called on pd.DataFrame

### Removed

### Other
* 49a472d002890b35e3f59ef93fd75f2e35455715
	* storing stable pm4py Python requirements for the old Python 3.8

---


## pm4py 2.7.7 (2023.09.22)

### Added
* 056d9e5714e2ad0a21fbcac0725ea4fb7aae260c
  * encoding specification in pm4py.read and pm4py.write classes

### Changed
* f81d62ad8dc8a76aabdf90763a8bd8b8e2ea2aa9
  * fixed compatibility with Python 3.12 (removed deprecation warnings)

### Deprecated

### Fixed

### Removed

### Other


---


## pm4py 2.7.6 (2023.08.28)

### Added
* 69e6692ff08868586f9d4d29c6b8e7dd6609c732
  * rankdir option for simplified interface's visualizations (and fixing here and there support in main methods).

### Changed
* 95bbaee94e177644ac12d526abbba0eafdf6eb00
  * refactoring of the textual abstractions of the DFG and variants (split in two methods + provision of primary and
    secondary performance metrics).
* 710b09619ebff74a0166e9518e2390289b0f686d
  * refactoring OC-Petri nets discovery and visualization.

### Deprecated

### Fixed

### Removed

### Other

---

## pm4py 2.7.5.2 (2023.08.30)

### Added
* 889f0531c0e307bfe56d933a294c61470a001e13
  * POWL feature

### Changed

### Deprecated

### Fixed
* 9105eb375cb2fee7d731862b3fe5bf1ce88d455c
  * various bug fixes OCEL import
* 0c483e52b6ea41a4df8b83ad5e39e3c1e2dc5539
  * bug fix OCEL 2.0

### Removed

### Other

---

## pm4py 2.7.5.1 (2023.08.28)

### Added
* 6760518dea19334a21442200bef647e4c07f3636
  * LLM abstraction of the temporal profile model
* 13d001c76e3de40786dce75e76e56a13a821173a
  * set of event logs for fairness assessment (hospital, hiring, lending, renting)
* e3044278b3e7d984c7fdf9e39554cc4551332739
  50f59379fb8f49bbe6eb1796c6664a6057225b95
  * added OCEL filters:
    * length of a connected components
    * presence of at least an object of a given object type
    * activity executed

### Changed
* 84629e2ea342348e30aa04a7d41ad7b39159b400
  * changed case-based text abstraction header text
* c3886beff7abc82db56c60835479f47a76e545d6
  * refactored log_to_interval_tree methods in two methods
      (log to intervals, and intervals to tree)
  * added queue-related examples
* da3a12f615dba3c46793a2d9977dfca11dad85b0
  * avoid annotation start/end edges in DFG with performance metrics
*  37fba9285cfde95309142e4404f9cfbcb2b9296c
  * visualizations support nanoseconds granularity when needed
* afb6f6ba74c03f422ce8d8417f840f6eb6aa3a6e
  * inductive miner - parameter to disable the computation of fall-throughs
    and the strict sequence cut.
* 49e738a7aee6e05ecf0ec50cd6aaa4cd0668687d
  * inductive miner - optimization in the computation of the transitive relations

### Deprecated

### Fixed
* 12c9d877e5fb27b709d06c21310ab32868c2ea74
  * bug fix textual abstraction attributes LLM
* 3b9fb1ffc9646cf56a0b84a9b95dfdfd9b7fd565
  * small fixes pre-existing Jupyter notebooks
* 17f1340cc8a1095e6cdd8a8d85b92a3800a1e7f9
  * bug fix textual abstraction log skeleton
* 1217473888b97a00f34834b4746bb7f7e4744df3
  * bug fix PuLP solver with extremely low weights
* badbff239cf8a703e7d05c1cc2fc6d51af8aa7d7
  * bug fix WOFLAN when no basis vectors are identified
* f528509c6b5117aca6285686e78175dbcf4ba057
  * fixed path to Graphviz.JS
* ca79aa9b9e51ba3a95665d5d53c8e5ab5028bf12
  * minor fix TBR generalization parameters
* 57a30fb452a759bc71f707e67bf0f63118194b7f
  * method to sample OCEL connected components is fixed
* 051d98cd0bfbf86419fe68f6cb0c1f139855cfdf
  * fixed divergence from Github repo
* e0cbce6b90a16ef1e21edca45b83d69e1743674c
  * fixed typo in OCPN discovery method
* 0af7368ce306678466df759ca15359c1e3901bcd
  * fixed discover_petri_net_inductive multi_processing parameter
    default value.
* 23aae39adf83f199a3b53533c45cbae4c7a9354e
  * bug fixes OCEL feature extraction
* a3faf71ac4eddb22f1bc80a35c752b6b9d98df99
  * bug fix direct conversion process tree -> BPMN (loops with several REDOs)
* fa242485e6c99dded04d1d9c10ee1ed81ea96252
  * bug fix OCEL2.0 SQLite importer
* 0e1b0daad489eb8100cddd2105e6405862a184de
  * fixed parameters in OCPN discovery

### Removed
* bf5574a34a31b93024dd9feb54acc5cc475640bd
  * change-of-mind on format_dataframe deprecation warning

### Other
* 916ea3163119afe7aa0fc9f6c43624147d6c0f9f
  * reference to published paper in OCEL feature extraction
* 549aa7c6766f1a51425a7a65673173c55d9731e9
  * updated reference to PM4Py website
* 20ce84db4e195937c77280c950ff12083fc5833b
  * example for log granularity change
* 0de0be4fa11183f034fbb61e936dee365bbdea4a
  * example for the management of stochastic Petri nets
* 570df6c21a03e6ac37ba2d7c9af160e8b175a68f
  * manual creation of the constraints of the log skeleton (example)
* 959a685696da725180be0675fd00aaede9bb17bd
  * examples for LLM-based fairness
* 7a98fe6b943db9d2402a4b867e8f6a441cdde243
  * docstring for OC-DFG discovery

---

## pm4py 2.7.5 (2023.06.30)

### Added
* f6d5a343808b350e83caac8cb0480e2ca671bfb4
  * method in the simplified interface to get the curently enabled transitions
* 44964d19b7052350f21d637c1a55048026d2b165
  * replay prefix using TBR (to obtain a marking)
* eb49b29863c65102ada2443ae66d7fe529a3d91e
  * OCEL relational validation
* a128100af8182070453df161a22dbb54d1c08458
  * LLM textual abstraction of a single case object
* 0f5b5668a8f134a36e65349f835bf4e1835ae9ea
  * LLM textual abstraction of the log skeleton
* 3287c53c83f0198b47c56a3ef7b15ed8d6e09b3f
  * LLM textual abstraction of EventLog features
* 7892697f04e14bbfecb7842139a82daf939aefbe
  * restored OpenAI query executor

### Changed
* e414949a69e0376c0299955ecf7cb7d27f7cf349
  * removed deprecation warning dotted chart and performance spectrum' packages
* 8f4ebdf93c3cbb57e7427238871d4b2e048f357c
  * added warning for dropping rows with empty case ID/activity/timestamp in format_dataframe
* 1b35a81e58ee145d5c82029c1110234ac3899856
  * added the possibility to specify the cae ID in project_on_event_attribute
* 6a4025f9a430ea32da29dd4142a51473ba16c5ef
  * optimization connected components filtering OCEL
* c1028d56269e775167c3cb89827e02a57d263384
  * minor changes OCEL 2.0 XML importers/exporters
* 3287c53c83f0198b47c56a3ef7b15ed8d6e09b3f
  * max_num_edges parameter in simplified interface's DFG visualization
* 8e04c243a2de3e344832f719e085a0630b3a5f1c
  * removing point border in dotted chart
* c5056add3101b7a846a630d67062f5ca9b8c84d3
  * deug parameter for Petri nets visualization in simplified interface
* b11d3ae66c1ddf3be244f233efd8c7b1a02124e2
  * moved "pm4py.algo.querying.openai" to "pm4py.algo.querying.llm"
  * moved "pm4py.openai" to "pm4py.llm" (simplified interface)

### Deprecated

### Fixed
* 437a8c8b885b8e11557ff20e9a5635eeaf4c919c
  * fix problem OCEL copy/deepcopy
* 2705b6b6be171bf821570f58027db531e7290801
  * small fixes feature extraction event log
* 8a588ff40143f585faf643a5f9cb9f7137ab32e6
  * small fix textual abstraction OCEL features
* 63108ee30c05a60a99f58a1fbb31dd33228c76fc
  * fixing DFG visualization when some activities do not appear in the DFG (single activity cases)
* 30932c4de18ea55dace9678cb87a784d7eb438af
  * bug fix Alpha Miner on Pandas dataframes
* 5cc3ded30c7f15ebe13d0a74894ca7f18f8a96e4
  * fix heuristics net visualization's background color issue

### Removed

### Other


---

## pm4py 2.7.4 (2023.05.08)

### Added
* 546cff5c7d91810b068777870ae20dab2b110150
  * pm4py.openai.abstract_log_attributes method in the simplified interface
* e9ee619300f59713c481d9fd592b3eeefc489175
  * added get_diagnostics_dataframe method for temporal profile-based conformance checking
* 7a410f6cb33773cb218c5ce7df37ded4844df7b9
  * possibility to get GraphvizJS HTML output

### Changed
* 45dcc3de2ddf4348f8a7e31bae54529ec2ab9ad7
  * consistency checks when importing/exporting OCELs
* 9c4eb3a8512fbd20f7352341131ec2855b108b95
  * consistency checks OCEL feature extraction
* 091908c11a62b6708bb64adafa7a4168099b140d
  * footprints visualization in the simplified interface - comparison
* 69d50384784f67a74823a4a0af99a1ebf9f0c302
  * minor improvement log2ocel conversion
* 3e88d920caf8d0dc902af2dcc2c3dcb3d752bfe8
  * removed hard-coded prompts from OpenAI API
  * added abstract_ocel_ocdfg and abstract_ocel_variants abstractions

### Deprecated

### Fixed
* f8b77348b47c782a709cb6ee5646715c20e35710
  * fixed performance spectrum computation on Pandas dataframes

### Removed

### Other


--

## pm4py 2.7.3 (2023.04.12)

### Added
* e561089945951e91b2ecfe0f223b35bd2d351630
  * other NLP/LLM abstractions
* 42b0d2a6f6fe7430d382117bf0ce54e8fd60ce23
  * return diagnostics dataframe in pm4py.conformance methods&

### Changed
* 44fc2aecd0885534dd2083a4011be9e031c3a04a
  * improved integration possibilities with PowerBI
* f805fd46673be291584ce489bf9def73df1dba71
  * read constants from environment variables
* 6737019a6de4e15d6063506e5a7ea2e571fc167d
  * added DEFAULT_RETURN_DIAGNOSTICS_DATAFRAME option in constants
* 0ba6b34c19587357425cb27cccb23b12d70978a7
  * workaround for inconsistencies in pm4py.stats.get_trace_attribute_values

### Deprecated

### Fixed
* 7dfeac5ddc4f4f6a8b5410fc2e04016590b6f22a
  * fixed OCEL2 XML importer
  
### Removed

### Other


---

## pm4py 2.7.2 (2023.04.03)

### Added

### Changed
* c617471c12c1f07c092e32ccf6d76d5aa6c4ec2a
  * change X Axis in pm4py.view_events_distribution_graph
* cf744cb22cd6affb0a8d7ce26b9827c3e8b0b903
  * changes/fixes to the alignments table representation

### Deprecated

### Fixed
* d0ee4a8c8db76900444bc3e0026b0ea54581e9e7
  * fixed OCEL deepcopy
* 5fd45bdf5d3cf17f364669cba7a5fab549236e7a
  * major fix WOFLAN

### Removed

### Other


---

## pm4py 2.7.1 (2023.03.28)

### Added
* af4f00bca1ec7a3b0acc0421efe4bf895b324995
  * insertion graph-based O2O relationships in the OCEL
* 0bb0bad37311fd45113440d97f53a5c8255ce89c
  * insertion lifecycle-based E2O relations in the OCEL
* e6076a50216de31fdbd4dd00edd631a01c9e1bb7
  * another algorithm to split/sample OCELs (ancestors/descendants based)
* 564e2c0ec976291c283fc1b24c5ebc2b6e452f12
  * algorithm for textual representation of OCEL
* 3e5164b72835aaa29051f4fd6ce4329253a17f95
  * algorithm to cluster OCEL based on the lifecycle/interactions similarity
* 70131091d88e5e8f2627b4ff7f70f8d479bd7738
  * new GPT-4 queries
* f584641df13504f71c796752da1befc963f3ce3b
  * included some simplified single-SQL-query extractors

### Changed
* 70198faa1b674c3a4e4351ff251a9af504e16a4e
  * changing alignments interfacing in the simplified interface

### Deprecated

### Fixed
* 8f5d5057f24bce7c3825e3f6d34b15e15bc15025
  * wrong condition in the visualization of the alignments table

### Removed

### Other


---

## pm4py 2.7.0 (2023.03.23) -- Million Edition --

### Added
* ba126d3f4211cb237dae4b09dec5574224666237
  * initial OpenAI integration
* 05b6425637768312bf4768a252ee410c3bd5a35c
  * easy-to-use (local computer) log extractors for Outlook, Windows events registry, Mozilla Firefox and Google Chrome

### Changed
* b3c17fe017bd57889845f398e08fa95d94a8c800
  * add flow id to silent transitions in BPMN Petri net conversion

### Deprecated

### Fixed

### Removed

### Other

---

## pm4py 2.6.1 (2023.03.14)

### Added
* c9eac43f4b55883056a3540857b470ac18cc922e
  * extract_ocel_features method in the simplified interface
* d2744bf87b0ce80ddc8d42a5b935424c36ffb82f
  * possibility to conisder additional event attributes in the convert_log_to_ocel method

### Changed
* 84e85c6e4715fe58159f6cfb83248d1cfa28bc8e
  * possibility to return additional information during the conversion of BPMN to Petri net

### Deprecated

### Fixed
* e1b126c5adca8d5767375a6737a9d9378a9093c6
  * bug fix object-centric Petri nets discovery

### Removed

### Other

---

## pm4py 2.6.0 (2023.03.13)

### Added
* 73254a80b3430140fac2ff023a6e356edc48dd0f
  * ILP miner (process discovery in ILP)
* 7016026a2a514d529fe5cf9a49b4aa607d30183c
  * "timestamp grouping filter" and "consecutive activities"
    filters for Pandas dataframes
* 4ba2a9e873c972c96fed8f3912f0dbaa8dfc96a1
  * added pm4py.insert_case_arrival_finish_rate,
    pm4py.insert_case_service_waiting_time,
    pm4py.extract_outcome_enriched_dataframe
    methods to the simplified interface (Pandas dataframes)
* 18b250e38bcfeb08cda549df94de98ce5c5b484e
  * added baseline log clustering based on profiles
    (Song, Minseok, Christian W. Günther, and Wil MP Van der Aalst.
    "Trace clustering in process mining."
    Business Process Management Workshops: BPM 2008. )
* 690716015f2452702b8f045e35e2029659bbd226
  * log to target vectors (for ML purposes): next_activity, next_time, remaining_time

### Changed
* d6d2301dd0d2ea57cba76015eba124f726f4544e
  * introduced optional "lifecycle paths" feature
    in OCEL feature extraction

### Deprecated

### Fixed
* 0a1c6f9c6e0ff45a0e732978589ed17513899be8
  * fixed dependency on Simpy in __init__.py

### Removed

### Other
* a313db141148a960d7eb5126831bc1f8829a2ca4
  * made fundamental and optional requirements clearer

---

## pm4py 2.5.3 (2023.03.05)

### Added

### Changed
* ea0da47ff6faaddb087ffa2344c6139c30978dca
  * SVG position parser utility (replacing text-based parsing in Graphviz BPMN-based layout)
* 9ea35fe209982f87f478262e1398e8474b3be1ba
  * working variant for generator of all optimal alignments
* 3f07223236eb350a72db87c8a708dcea13c1a5a3
  * refactored df_statistics.get_dfg_graph method and DFG visualization
* 268311a99ee7d2df245026371ab7449538ffcff8
  * support for object versioning in OCEL

### Deprecated

### Fixed
* 5d4bbb60bf940f8c5d654de0c8ecaec8cbb44d48
  * fixes for Pandas 2.0
* ea09b4910874dbb165277a4de93286c05ac0ba5c
  * carefully performing SQLite3 import (DLL compatibility issues with Anaconda)
* 06217786793dc7fa22706ecc143778d8ebbe3d2e
  * fixed indeterminism in edges filtering during paths percentage filter

### Removed

### Other


---

## pm4py 2.5.2 (2023.02.11)

### Added

* be6ac2f1c611da6abcb6ea10df0280f7b9ecb0f0
  * added internal conversion method for Petri net type (classic, reset, inhibitor, reset_inhibitor)

### Changed
* 87280959eb1612d01bbd4183d951f2c33750fed6
  * added ADD_ONLY_IF_FM_IS_REACHED parameter to Petri net playout
* 38af1dabd9cf3478a6b728be5a602150ed837c7c
  * playout Petri net simplified interface: detecting the correct Petri semantics to be used
* ffffc623e6c52af2df0a4f3bb33fff5aa49b5588
  * added FM_LEQ_ACCEPTED parameter to Petri playout
* df84b4702fc81ab3427330f05c6b5dfb572f595e
  * possibility to decorate heuristics nets with performance from the simplified interface
* e418e25a0008828337a92b23f57a0980baa8f24a
  * changed convert_log_to_ocel to include automatically additional object types from the dataframe
* fbe086eaff9683562ada39a14fb6bdd86d52c50b
  * added constant for the default Gviz representation format in the simplified interface
* f746d8811fad34c082ddac3028f0269bdade0a15
  * more efficient WIP implementation for OCEL
* 57167b094edcaeb01fc14e7d495a6bbc2d9907eb
  * raising warning when parsing a XES log below Python 3.11 because of potential ISO-format parsing problems

### Deprecated

### Fixed
* b012df622c9bf28c3adf8cf4b53eaa2d6ec5efad
  * fixed JSON/XML-OCEL importing (missing coherency check)
* 5a4d5a276c0a6c2dd33ebe930cdf60b5183c48a1
  * setting correct variant when applying pm4py.discover_process_tree_inductive on a DFG object
* a5bc0b96d9b79ae8d4ea26be03f4b8154837f567
  * bug fix Murata (removal place from IM)
* 91c20ccd0d6c88d76519e174b7e11ab82ac6a180
  * bug fix process tree obj get_leaves function
* 480c4fd1a3f35f8312927defd09b4a89665e6f71
  * bug fix convert_ocel_to_networkx variant
* fc941525842a41bc5d712526ef17177d7f8be763
  12ef518b00f16c5e1b6b8d5d3fc749959bc836ad
  * fixed SNA visualization (variant & HTML)
  
### Removed

### Other


---

## pm4py 2.5.1 (2023.01.30)

### Added
* 23d5b0a81bbffbb69175aaa7cfa78e1ea0b78b6d
  * adapted OCEL object to optionally support O2O/E2E relationships.

### Changed
* 284bd275ae444a72e3c81662b7aded4921befde4
  * updating Scipy adopted LP solver from simplex to highs (4x faster)
* bc1f21ef4e83af66f1202ef82e389e5b5cb38ae8
  * moving utilities for sojourn/service/waiting/arrial/finish times computation on Pandas dataframes
* 7e59696b0d4c9fd659dc0594cff3c07fc504df5e
  * OCPN discovery - specification of the variant of inductive miner to be used
* b32cada268fea2a9fdfb420821d9877d9144770d
  * removed deprecation warning on Petri semantics

### Deprecated

### Fixed
* a6a1f14cfc1714a5039dd445ea14091e3e8579c7
  * removed extra parameters in pm4py.discover_petri_net_heuristics

### Removed

### Other


---

## pm4py 2.5.0 (2023.01.19)

### Added
* e246a681298282e280d0a5d8c90958e1e4bfa139
  * add cadoso and extended cardoso simplicity metrics
* 34303df3a72e8d0c699f9cb61938c6c08a989274
  * add discovery of Stochastic Arc Weight nets based on OCEL logs.
* 32b74bb6125e1e914caab404514b606ac119d4f0
  * add Murata simplification to the simplified interface (implicit place removal)   

### Changed
* e7f79a47d6349644ef33c137a9eea34e57b7224b
  * changed process tree conversion to Petri net to follow the standard DO-REDO paradigm instead of DO-REDO-EXIT
* 9adf32e3c934f9d9f458a1d87dfdda869358e79f
  * scaling positioning nodes BPMN layouter
* cc34a30e5a7dbac292f0bb784df28ade94215140
  * removed searchbox in docs theme (not working with current version of sphinx)

### Deprecated

### Fixed
* 479dc5c1afef98b2ae3b67b918568465b1c7c72b
  * bug fix inductive miner DFG missing parameters in LoopCutDFG

### Removed

### Other


---

## pm4py 2.4.1 (2023.01.09)

### Added

### Changed
* 9e815620924b2bae5a83b85539f38f344d4293d2
  * fontcolor support in visualizing invisibles.

### Deprecated

### Fixed
* 26fe3ea4ec65b668002163ae451436a4452f0b20
  * improved compatibility with Pandas 1.5.x (faster date processing)
* 93ee76af7cd23816d8891d6e7925011dc4d0399e
  * fixed compatibility with Python 3.8 in typing

### Removed

### Other

---


## pm4py 2.4.0 (2023.01.06)

### Added
* 7d3b0cb107452b9f7fa3d3c3e1c3609e3c5827dd
  * Murata algorithm (Berthelot implementation) to remove the structurally redundant places
* 6fc781328a550a339e6e48d03f0e75464ad5249a
  * expose in the simplified interface the reduction of invisible transitions
* 21a79b0132aaf5e2d6ac4efbb31995fba91dd46b
  * add support for calcuating stochastic languages of process models
  * add support for calculating EMD between two stochastic languages 
* 9186c5bac228383e3b2addba6e5205e6e0ce2a8d
  * add visualization of alignments in simplified interface
  * add visualization of footprint table in simplified interface
* 82e20325229a3ae4e9c045ab2cfec3070ab02005
  * add conversion of Petri net object to networkX 
* dfbd6c27c09ecb45c3dcf7edb35093455c09c429
  * add support for stochastic Petri nets
  * add support for stochastic arc-weight nets

### Changed
* c56c3ca6dd1068380ac7a0dc79f6fe64410e8d78
  * changed Petri net visualization in order to provide decorations for places/transitions/arcs
* 63371dbad1f9e9cf2e53a6b38977fd22f02661df
  * changed xes importer to support returning the legacy event log object 

### Deprecated

### Fixed
* 0bc31a7406f961122c3a124710d1a1ce8b6c74db
  * fixed Scipy lp solver in order to allow for variables integrality specification.

### Removed

### Other

---


## pm4py 2.3.4 (2022.12.23)

### Added
* 89ca01e1378cb2cfac21f5d58e0e4fea44ca2186
  * extraction of temporal features (system dynamics log) in pm4py

### Changed
* 7a40a3cff6b0b4a12b2fe4ca7bd08bf963917443
  * Improving the performance of streaming DFG discovery
* ec766d97c9b8557324ab11a862d6630091a92059
  * Removed Pyvis and Jsonpickle as explicit dependencies of the project
* 04691455f47bc4ec84bb26ec7c5f6d187db1d41f
  * Removed Sympy requirement (re-implemented null space in WOFLAN)
* b4fac01dff29ff34d6f0bb97e4398a101139d5b1
  * Enabling disable_variants by default in TBR when place fitness is required

### Deprecated

### Fixed
* 4b5c035f4a744c8de4efb7969a6f0abcfdd966d2
  * bug fix between filter on EventLog

### Removed

### Other

---

## pm4py 2.3.3 (2022.12.09)

### Added
* e2e4d357e2218a48f9b2d6b89690fbbe61cd6906
  * importing/exporting from/to SQLite

### Changed
* 246be6c1aa1a3216faebf1440c38d59485621f4b
  * Visualization of heuristics net - avoid totally unconnected nodes

### Deprecated

### Fixed
* 2e560757b4717a94e8f774de4b42bbb26bcdfc12
  * bug fix TBR decorations in Petri net
* 743151159a3f240ea6cf0756bd9ae24ac5cac10b
  * cope with changes in the deprecation/packaging packages

### Removed

### Other

---

## pm4py 2.3.2 (2022.12.02)

### Added
* 55cf77276573efcc6d67ed1a51871914ba34f84e
  * instantiation of some objects directly from the pm4py module.

### Changed
* f887397e9abf2e9f85b48b941aa2bd4a892600a0
  * parametrization scale factors current BPMN layouter
* 35171256a7378f55713cec3b835b3418ecf4d356
  * bug fix heuristics miner ++ on Pandas dataframes - Parameters are not passed

### Deprecated

### Fixed
* 523589e13dfb6f5a8070478c245fc2a8058751ec
  * raise exception when unsupported OCEL file format during read/write
* 394960d9eabcc0ac2eb40520b2866a3e21178d7c
  * fixed statistics.traces.generic.pandas.case_statistics.get_cases_description to support the start timestamp column
* 0bd2caf62742627f840a5cde5486a0b92eaafeeb
  * bug fix discovery DFG typed

### Removed

### Other

---

## pm4py 2.3.1 (2022.11.26)

### Added
* cde09b3bdc122e0f38d62c5cecba26a6d1d9e4b6
  * new variants of alignments - generating all optimal alignments

### Changed

### Deprecated

### Fixed
* 37dc750566da858c738a94ea242160cada28a43d
  37e7e92db973497b23b30610a005512bd2d3268a
  * fixed tests and examples
* 75ae8d12555d0fe354b55e3f99d09287ef4c5fd6
  * fixed pm4py.read_xes problem with some conversions to DF
* ea72675caf93f5e32bc146f6cef7f86d0769c747
  * fixed inductive miner entrypoint function

### Removed

### Other

---

## pm4py 2.3.0 (2022.11.25)

### Added
* 00a7ab36bda245d16a35ae6fff2bfb51d8ff8aea
    Adding several methods to the simplified interface (process discovery/conformance checking using log skeleton, temporal profile, batch detection).
* feeb1891f82014b3e86a4c5301c237226acc8fad
    OCEL - Visualization of object graphs (object interaction, object descendants, ...)
* 15964a428e2e0fc50dcc96570fba39f2e0d40099
    OCEL - Added some filters in the simplified interface
* fefe740338b702eafb7049a8f777f48f464d157d
  *  OCEL - insertion of an attribute pointing to the parent object
* 88c58a1c6809388be58db2ea6e64fb9b58d913d6
  * OCEL - sampling objects
* 40c741c8298584402cd9ea8e86bcca09f2bfd857
    OCEL - Method to get a temporal description of an object-centric log
* d63929cc36b1aba941f88efac05af3b25a384787
    OCEL - method for objects summary
* fdd87eb41e54ce8d179ae3030fd9e15ea74320e8
    OCEL - expansion of the set of objects during filtering on object identifiers
* 908d0aa843f1a4e9f4a6c69139a3be755c2e8555
  * OCEL - conversion to NetworkX DiGraph
* 5c7cc41b94810ec93f388f8014f2a3820d0063f2
  * EventLog - conversion to NetworkX DiGraph 
* e7b4f712e1bd9475c73be5bc82c9a22eb0b745b5
  * OCEL - objects interactions summary
* 43b5976f7040a77c0aa32f5a28c508eb19966fa1
  * OCEL - methods to merge duplicates
* 3cc1a19f42420e034a7489f1c695fea788e9087f
  * OCEL - methods to manage duplicates, sorting and time-delta for events
* 2c729e28e7f536acbd0919d88cf035a23542a3ae
  * OCEL - conversion event log to OCEL accepts several object types
  
### Changed
* f6b7714eaf79e1c57e4283163a51631f0ea8d964
	default variant representation is now a tuple of activities instead of a comma-separated string
* 642dcdf2cc538d384c1869436879d7d0602e3fa0
	refactoring PNML importing: auto-detection of final marking shall be optional
* 85cea58442348684440890612db8b5511491e0d2
	refactoring XES exporting in the simplified interface
* f60fd1ded3210adb91345be49343cd0dceaecc6d
	refactoring usage of type() and isinstance() throughout the code
* faabe5ee17ae6fb10e77637e614db5d764d66e93
	introduced proper ResetNet, InhibitorNet, and ResetInhibitorNet classes
* 070d0467bda22d81b4166c2b3646333a23897f81
	different OCEL exporters methods are now available for different outputs, instead of having a single method accepting a path with an extension
* c614474e477a02836bd36f0b40db4b8ef37b78a6
    made extension optional to write methods
* f89a1dfa797da4581c4cbbd8cde482caf2402ca4
  c768e5a33e5e2f872fd2dc0d45a11d589a130629
    documentation is taken inside docstrings and formatted using Sphinx
* 7640c79932ef974524ca4424f91c6b9416401a8d
    brand new implementation of the inductive miner, also with multi-processing support.
              the .apply method of the inductive miner is now returning a process tree object.
* cc74d5ebcd7181626d79d60b2a883ad061cd85ba
    re-implementation of business hours in a slot-based way.

### Deprecated

* 6184f7f9e4e323a222a28ed046686eb9f0d6b3e8
	deprecating the usage of the EventLog class
* fddc1c0936514d819be77c993913a96172680f0e
	deprecating some packages for removal in future release (hierarchical clustering, comparison, alignments with edit distance, decision mining, earth mover distance, log to interval tree)
 * 000f23ca65226d66f52d85f9b876ec68669f03e0
	deprecating the format_dataframe function.

### Fixed
* d066d3f49a996c30d151031d66de90db4f4d9a2e
  * Fixed issue with OCEL-CSV importing (Pandas index_col)
* c38348df9cf165fd94a2e69ba29601e1643e80ae
  * Fixed issue with OCEL-CSV importing (relations dataframe timestamp)

* 22ec9ab7220088ef7535760dd93197092d6bf04a
  5c0b0d439c1a613ff78d4d24b7a05b7aa4150ce3
  9b90c2c18b708d39e3c75f8b2e25433c7e8b447f
  ba6b55b84d1f7191d578e0d5535c49ef1930ce65
  4d5765052fe4085fc8f8340e72a353369705b878
    making methods directly working on Pandas dataframes
* ba6b55b84d1f7191d578e0d5535c49ef1930ce65
  4d5765052fe4085fc8f8340e72a353369705b878
  aea15814ba8f67a51fce1ec0beebd9a4a3721a19
    adding common parameters to simplified interface methods
* f8482b9e9aa4376543ad5d66d22fb04de0639530
    missing parameters in heuristics net discovery

### Removed

* d2a95d306362f54e08070b98193abbf8498ba70e
	removed all deprecated code for this release; standardized object definitions

### Other

---

## pm4py 2.2.32 (2022.11.10)

### Added

### Changed
* cfb9f37a15a6b990f32ceaab28f1e2153e36c23d
  * Update WOFLAN to include diagnostics in output

### Deprecated

### Fixed

### Removed

### Other

---

## pm4py 2.2.31 (2022.11.06)

### Added

### Changed
* cc232ddc00528a0e7d568565c6b8fe76e2e38f71
  * fine tuning existing BPMN layouter

### Deprecated

### Fixed
* 43026f0d22605bafd104c9c752511b3a00c3988c
  * missing encoding parameter in PNML importing/exporting
* 07493cc94e40652983eeb7b25f911654937f0ae6
  * bug fix Alpha Miner - check if the new place candidate pair has
    causal relations between all elements of the first and second part
    of the pair.
  
### Removed

### Other

---


## pm4py 2.2.30 (2022.10.13)

### Added

### Changed

### Deprecated

### Fixed
* 32a4fc9e4ab23418493f281fc262615f2ff4c436
  * Fixed trace filter
* 4c5599ff60f4e448198a1971a669c4bf3a4154fe
  * fixed issue with SNA HTML visualization

### Removed

### Other

---

## pm4py 2.2.29 (2022.09.16)

### Added

### Changed

### Deprecated

### Fixed
* d066d3f49a996c30d151031d66de90db4f4d9a2e
  * Fixed issue with OCEL-CSV importing (Pandas index_col)
* c38348df9cf165fd94a2e69ba29601e1643e80ae
  * Fixed issue with OCEL-CSV importing (relations dataframe timestamp)

### Removed

### Other

---

## pm4py 2.2.28 (2022.09.02)

### Added

### Changed

### Deprecated

### Fixed
* 1343827595d4cfd9f6b5743bb378443079ce281c
  * fixed sorting in DFG filtering
* acea877fd9000c8e6a62424c15d4a29c33d08eba
  * fixed bug of LocallyLinearEmbedding(s) with newer version of Scipy
* 55acf9c08d25886f384bb2e993d653af90874f3b
  * fixed construction of tangible reachability graph

### Removed

### Other

---

## pm4py 2.2.27 (2022.08.19)

### Added
* 58e266610e82cfcc41868313f7b9ccfd9975d49c
  * discover_objects_graph utility for OCELs.

### Changed
* 1cbd37ac4b54a4c0e943b506ed685435f003640b
  * performance improvement batch detection on Pandas dataframes.
* 94dd96e0095f7cb1ef8d1eb48bd3da0a3cd85793
  * minor changes to DFG variants simulation.

### Deprecated

### Fixed
* 98fd3c740d8b6ae2dfde4d7a018f181030f22175
  * fixed reflexivity in EventLog eventually_follows filter.
* 9423897cdf0ea293ff1b032a0d4fa49ba746709c
  * fixed chunk_regex XES importer.

### Removed

### Other

---

## pm4py 2.2.26 (2022.08.05)

### Added
* 2146fc42020f11a364a98b724d6c6a44fcbcbb41
  * trace filter

### Changed
* 5c06d520182317d140bd1b82d9d986c3edc81cf7
  6a2eb404ba240b2c04eb91e7cf1407f72c5ae3e5
  * minor fixes to DFG simulation
* fe1aa9c5efa7dc274e728a769625a784d7f87c6f
  * added default option for background color setup
* ac080d2702192b588cf80444dd44fe447d14ede9
  * background color as parameter in the simplified interface visualizations

### Deprecated

### Fixed
* 9c12ffba4e4d1043fa4ad2ffe8349b13d7fa06f3
  * fixed the exporting of Petri nets (Petri net name property)
* 7fdb3074c6924e5957f973a76ff34ae5dc7bc815
  * fixed the visualization of heuristics nets

### Removed

### Other

---

## pm4py 2.2.25 (2022.07.29)

### Added

### Changed
* ce94110076e3269c96a6eee61d7618f08f44472a
  * optimization in the calculation of the eventually-follows graph on Pandas dataframes.
* 3cca8f97bbd09f4ae5644dcc156489d4b2037028
  * optimization in the calculation of the performance directly-follows graph on Pandas dataframes.
* 4d8721787a50da397b265678be614c94894ea851
  * column reduction in DFG calculation on top of Pandas dataframes

### Deprecated

### Fixed
* d754ccdac680f610b2b628dc9830d92da6954dc1
  cb76238c29b986026f07261c11a1c09a667c9ab9 
  54970a58927ad0e17b173bff17705a10f5344d92
  ef575a8bf0519655bcf8a57b981c7fa3c018db7a
  * small fixes in OCEL utilities
* d0094fa4ccc815b57ccc519d15ccbda6399c2ef7
  * bug fix eventually_follows filter in LTL checker when timestamp_diff_boundaries is provided.
* eb8617de0cfcfebf7374b4545660158e4b4291b6
  * bug fix eventually_follows filter in LTL checker on EventLog objects.

### Removed

### Other

---

## pm4py 2.2.24 (2022.07.12)

### Added
* 43800f763a2aede807ad40231f771c6ef19e0098
	* added some examples for XES and OCEL generation out of a database

### Changed
* f72e011d38cec44823c00248039812a3fa0cfc7b
  * application of the strict sequence cut in inductive miner (IMCLEAN)

### Deprecated

### Fixed

### Removed

### Other

---

## pm4py 2.2.23.1 (2022.07.01)

### Added

### Changed
* 43e55f63d86e424e882617af7b0a483ffe653069
  * setting default alignments variant to Dijkstra when no linear solver (Scipy, CVXOPT) is available
* 5ff00475659c38792ebab685fb23b282c75c36c0
  209558a0d6d4c43708389a0002fc7c62bd9f89e9
  * optimizing retrieval and filtering of start/end activities from Pandas dataframes.

### Deprecated

### Fixed
* dc94e82825bd5994667dd9c6cf2e1908379db923
  * fixed problem(s) with the log skeleton
* 1bd50ff5354317d57297e63d140618ffa7a58ef6
  * bug fix in exporting OCEL(s)
* 7c6c30ffcff04d3151f249556af9405402fdee83
  * fixed problem with WOFLAN algorithm (LP solving)

### Removed

### Other

---

## pm4py 2.2.23 (2022.06.24)

### Added
* 09c97115cfaafa033c595ddff089701a28bf1599
  * added starts-with and ends-with filter on Pandas dataframes.
* f373955163ad58e6da3d762380b4f9802ac806f0
  * new OCEL filters made available (event identifiers, object identifiers, collection of object types, connected component per object)
* 2051ff1f5985ec34362a16d1f369e062220d7d1b
  * new footprints visualizer (symmetric comparison between differences in footprint matrix)
* 0c6d023535f18318f1f7f78fec21f3565ce229cd
  * new OCEL statistics made available (temporal summary of the log, objects summary)

### Changed
* 1f36b168d33d6dd48f4e20fd16b7a71e25c6de67
  * allow exporting trace-by-trace to disk in .xes

### Deprecated

### Fixed
* 3396465f6d6944c84bbdfcf2bbe380b80c442350
  * fixed inductive miner example's path

### Removed

### Other

---


## pm4py 2.2.22 (2022.06.10)

### Added
* c7e04d3e8d4a3fc1859e50793a0693040602dd3c
  * add starts-with and ends-with filter

### Changed
* 9bb6ad473bf46b2ca6a378193e2e3042bed98d31
  * added the possibility to provide additional parameters to Matplotlib's plots
* 0489353a21ce7a4044d775ed505f476556d2b4e4
  * increased performance of the PM4Py's insert_partitioning method
* ab196c5a2ee1430dfd7cef4943f7275aa5405873
  * increased performance of dotted chart / performance spectrum representation
    by disabling automatic layouting in neato.

### Deprecated

### Fixed
* f45883421423ca49139adf24490625ad2980fc92
  * Fixing OCEL processing when an event has empty object map
* e45a136198b7dbf546d97a65095d2b126133a754
  * Fixed problem with footprints discovery on loops (process tree / Petri nets)
* 3b2082f744966e9c453013df41c15828b971e94d
  * Alignments: Timeout results in an exception on fitness calculation

### Removed

### Other

---

## pm4py 2.2.21 (2022.05.12)

### Added
* 65ff8ae3d9bca71f0cf7be507c9e0eba68b85c42
  * add chunk-based xes importer (CHUNK_REGEX)

### Changed
* d982c534aac373c347a083739b68fd3ac2b29e42
  * changed dimension of endpoints in BPMN models layouting
* 7473a72877e29261780adf746d134b406a912dd7
  * interventions to increase PM4Py's compatibility across different platforms

### Deprecated

### Fixed
* 882aa20b20ec593e0a7d01e027a6f1afa8d44f84
  * fixed XES line-by-line importer for booleans attributes
* f6542cd12413f073eb51173804f68502e3026f46
  * fixes XES line-by-line deserialization
* 363580b757c027ff583d33dcff83e00b3be97659
  * fixed issues with Pandas dataframe's index usage in the library
* 58a763b4099b40c67f23a6eb45c621d1b9a9d324
  * fixed OCEL default constructor to set default columns in the dataframes
* 8470f22047667d1d30415a08965af1015d66adbb
  * fix division by zero error in alignment-based fitness (side case for empty trace/model combination) 

### Removed

### Other

---

## pm4py 2.2.20.1 (2022.04.10)

### Added

### Changed
* 344fb7258df17ce0d4ffe7425b678943f6f2ff11
  * Minor refactoring to management of inhibitor / reset arcs (importing)

### Deprecated

### Fixed
* ad2cba1d8f9487dbb03ec418643b329b30e80ee0
  * Minor fixes to the retrieval of the parameters in several parts of the code
* 65e1f1b0bbd0747fe81eb049780874608a395d6e
  * Fixed bug in eventually follows filter (simplified interface)
* 60cd060edeeaa17c8b5bdaba7bb1035fc385d514
  * Fixed XES exporting when attribute value type is a Numpy type (numpy.int64, numpy.float64, numpy.datetime64)
* cd5e55e712697a28cbfe0182e96556531b520667
  * Bug fix feature selection and extraction on Pandas dataframes

### Removed

### Other

---

## pm4py 2.2.20 (2022.04.01)

### Added

### Changed
* 762fa3ec987705f12a42decb13862323f600e3c9
  * apply explicit conversions to event log throughout pm4py code base 

### Deprecated

### Fixed
* 1bcadff3acacfda2463cf9325f873004e15ed915
  * Bug fix / efficiency change on the format_dataframe utility function.
* d8797f574d605ad1591c66a96c1f54346c856878
  * Fixed missing import in DFG performance visualization.
* f4f5a0eee8218be5c575fe8b42ab59e335979d53
  * Fixed hardcoded parameter in feature extraction interface
* e61fb3f7a763a89cfb221b3c37c1b140620f5df9
  * Fixed performance DFG visualization when all values are provided
* fb9c152afdf6b91c3b26efa09d8233e99c55b907
  * Fixed progress bar behavior in TBR-based ET-Conformance

### Removed
* 639aeb64bf5febf5f5719622d6d90c4a3c5cd8be
  * Removed ORTOOLS as available linear solver.

### Other

---

## pm4py 2.2.19.2 (2022.03.04)

### Added

### Changed
* f5575aa8
  * Cleaning unused parameters in PTAndLogGenerator
* 65137038
  * Changed WOFLAN linear problem solving to default interface

### Deprecated

### Fixed
* 150184d3
  * Small bug fixes BPMN importer
* 7221385a
  * Issue in DFG visualization when the provided start/end activities are not in the graph

### Removed

### Other

---

## pm4py 2.2.19.1 (2022.02.11)

### Added
* a193603e
  * Event-Object Feature Extraction on OCEL
* 8da05972
  * Prefixes and Suffixes filters for Event Logs + Exposition in Simplified Interface

### Changed

### Deprecated

### Fixed
* cbf848ef
  * Bug fix BPMN importer
* ff0dfc4b
  * Closed security issue within dependencies

### Removed

### Other

---

## pm4py 2.2.19 (2022.01.25)

### Added
* eea18398
  * possibility to return the Pydotplus graph inner object in the Heuristics Net visualization.
* 52ddbf75
  * support for different attribute keys for the source / target events in the DFG discovery and paths filtering on Pandas dataframes.
* 29bd86a6
  * possibility to specify different shifts for the different working days of the week, inside the business hour module.
* f1e124a4
  * possibility to move an attribute at the event level in an OCEL to the object type level.
* 0da4c3f6
  * custom semantics for Petri net to reachability graph conversion.
* c7c7ed5f185b492f7b6206b04f037a119b80541b
  * add "week of the year" option in get_events_distribution method
* 5b5c04874e449bda60463ade6e2cf1a8218e6908
  * add prefix/suffix filter for pandas data frames
* 877701fa0e348a5bd58eb84ed984b60292db9f55
  * add additional features (useful for instance-spanning constraints) in trace-based feature extraction
* 7359807b60aa3b1ece798d1ef0cdd6a19fac9f6b
  * add rebase functionality to pm4py (changing the default activity/case identifier)
* 84742ce331dec418841d99fafb24a82c48c21e7f
  * add support for interleaved operator
* d7e232a987e4a0c15e28b9cf2ae6c15ce324031f
  * added various additional interaction feature extraction methods for OCEL
* 9caf5597d59ff9eb70879ba42dbfccd9785009af
  * add new thirdparty dependency structure in third_party folder

### Changed
* 74ce9b95
  * setting all the arcs of the Petri net visible when there is at least an arc with weight != 1, for coherence reasons. 
* 21832737
  * inferring the activity frequency from the DFG in a more generic way with regards to the type of the inputs.
* 87fe5afd
  * changed tau printing in process tree to string representation, from *tau* to tau, for coherency with the parse_process_tree operator.
* effce8d8
  * changed BPMN namespace in BPMN exporting to ensure compatibility with BPMN modelers.
* 2200a0f5d6d23a1f797199cb834b37e07d8d396e
  * add pn to nx converter that returns two dicts for node mappings (pn->nx and nx->pn)
* f9ad1a400846dbdb01f48714df0a3119069a05ea
  * ```pm4py.format_dataframe(df)``` no longer replaces columns, rather, it copies the data into fresh columns

### Deprecated

### Fixed
* 0ad488b1
  * Fixed problem in PTAndLogGenerator: silent transitions were added in some context also when the parameter "silent" was provided to 0.

### Removed
* d07a90873be85d95b15e562aabc6ab1f93b6b109
  * removed ```pm4py.general_checks_classical_event_log()```
* 034abb0d7a442572f8bd52109ac6ed5cba109d0c
  * remove dependency on ciso8601

### Other

---

## pm4py 2.2.18 (2022.01.06)

### Added
* c15c8897
    * add utility function to convert SNA results to NetworkX
* 8b300dbb
    * add several new statistics for OCEL logs
* 8da0f41a
    * add frequency-based visualization (using alignments) for process trees
* 54261cbb
    * add progress bar to token-based replay
* 225dcad7
    * add OCEL schema validators
* da6a4787
    * add reduction rules for R/I nets
* fefcd453
    * additional support for BPMN functionalities: exceptions and markings
* 417274fd
    * add support for feature extraction from OCEL logs
* 5f5ff573
    * add filter that checks relative occurrence of a specified attribute 

### Changed
* b82dd92e
    * revised implementation of the business hours module, now supports input of work calendars (workalendar package)
* 434e66af
    *  allow arbitrary arc weights visualized (reported at https://github.com/pm4py/pm4py-core/issues/303)

### Deprecated

### Fixed
* 76563e4b
    * fix bug in process tree alignment that generates NoneTypeError when multiple leaves have the same label
* 3b6800d0
    * minor bugfix in process tree playout (reported at: https://github.com/pm4py/pm4py-core/issues/305)


### Removed

### Other



## pm4py 2.2.17.1 (2021.12.18)

### Fixed
* 2eb36ce5
    * Bug fix in OCEL importing (timestamp parsing)
* 512c071e
    * Resolved security issue in data Petri nets' PNML parsing

---

## pm4py 2.2.17 (2021.12.14)

### Added
* 9b795123
    * add converter from data frame to activity/case table
* f28fc490
    * add possibility to add the case identifier in the feature table (see: https://github.com/pm4py/pm4py-core/issues/292)
* 12b6ec24
    * add interleaving DFG visualizer for visualizing inter-process dependencies
* af9c3262
    * add first/last occurrence index per activity in the feature table
* 9231a5d7
    * add support for conversion of interleaving data structure
* 06f54287
    * add support to merge two separate logs using an n:m case-relation table
* 146f49c2
    * add the possibility to stream OCEL events and define object-specific listeners
* 573c26c2
    * add feature extraction functionality that records the position of activities
* ff62d665
    * add case and event sampling to the simplified interface
* d8f71bc3
    * add activity-position summary in the simplified interface
* d4011ff1
    * add link analysis code for OCEL    

### Changed
* 79920a18
    * improved string representation of Petri net objects
* 9358fdf4
    * minor refactoring for interval detection in event log
### Deprecated

### Fixed
* 5dccbe61
    * fix faulty conversion of process trees to binary equivalent.
* 976cc601
    * fix for: https://github.com/pm4py/pm4py-core/issues/293
* 1e4f602b
    * fix for: https://github.com/pm4py/pm4py-core/issues/295
* be629d97
    * fix for visualizing multiple tokens in the initial marking in the same place
* a06cc1c8
    * fix for the correct use of the triangular distribution on generating process trees
* 51181d6c
    * fix support for generating multiple process trees in one go
* 9a0e2be1
    * general revision of the process tree generator code    


### Removed

### Other

---


## pm4py 2.2.16 (2021.11.16)

### Added

* 32af0c81
    * time-stamp based interleaving mining for OCEL logs
* 10dffb58
    * support probability visualization in transition system visualizer
* 51c069fb
    * add discovery of object-centric directly follows multigraphs
* fa3031aa
    * add several filters for OCEL.
* d4747f71
    * implementation of OCEL-based process discovery according to Reference paper: van der Aalst, Wil MP, and Alessandro
      Berti. "Discovering object-centric Petri nets." Fundamenta informaticae 175.1-4 (2020): 1-40.
* 9fbd1c45
    * add the support for generic network creation based on a given IN/OUT column in which events are connected if the
      columns match.
* 2b867f0d
    * add projection utility to fetch lists of event attributes

### Changed

* 43a076c8
    * add artificial timestamps to artificial start and end events
* d65f8077
    * case attributes are replicated in events of an event stream (for xes input)
* 9075cbfc
    * add trace attributes to the interval tree

### Deprecated

### Fixed

### Removed

### Other

---

## pm4py 2.2.15 (2021.10.15)

### Fixed

* 6e26b003
    * fixed pandas performance DFG discovery
* 92153184
    * fixed parameters usage in simulation packages
* ca6750d4
    * fixed hardcoded parameters in dataframe_utils

### Removed

* 53af01f6
    * removed strong dependencies on intervaltree and stringdist

### Deprecated

### Changed

* dcebaf8e
    * moving networkx dependency
* f19762ac
    * update IMD cut detection to use IM_CLEAN cuts (correct implementation of IM CUTS)
* d5d0b49c
    * change the visualization of initial and final markings
* fcc4eeb0
    * variant separator (between activities of the same variant) is now a pm4py constant, for increased compatibility
      with other tools, e.g., celonis.

### Added

* 32c396b8
    * add sanity checks on event logs objects in simplified interface
* 5b85d5dc
    * add utility to parse a collection of traces in string form to an event log
* a87a39c9
    * add support for importing XES 2.0
* b43d425b
    * add artificial start and end events to event logs
* d22dd490
    * add initial support for OCEL 1.0
* 829f091c & 56fca738
    * support for business hours in the pandas dfg calculation
    * support for business hours in the temporal profiles for pandas dataframes
    * support for business hours in pandas df case duration
    * support for business hours in filtering for case performance (pandas)
    * support for calculating of sojourn time with different aggregation metrics
* 841e3e55
    * add etc conformance for dfg models
* 04caa3d3
    * add dfg filtering that keeps the dfg connected

### Other

---

## pm4py 2.2.14 (2021.10.01)

### Fixed

* 706d42c0
    * bug fix paths filter for Pandas
* c5ecaa4f
    * bug fix numeric attribute filter XES (custom case attribute glue)

### Removed

### Deprecated

### Changed

### Added

* 8ba67034
    * added random variables that are able to check gamma and log normal distributions
* 1d22d99d
    * added dfg -> petri net translation that has unique labels (routing is performed by invisible transitions)
* 004ec93f
    * add support for log-level fitness in the alignment output
* 56efe270
    * add fitness value for the dfg-based alignments
* d9da1ab8
    * add raw performance values for the elements of the performance-based dfg
* 0eeda19d
    * when visualizing a dfg without log attached to it, i.e., incoming edges are used to count
* 03ee6b8e
    * allow counting of occurrences of activities/open cases/resource activities in a given time range
* ae5a3973
    * add various new filtering functionalities

### Other

* ac00be2f
    * added the specification of Python 3.9.x among the supported versions.
    * not suggesting anymore Python 3.6.x

---

## pm4py 2.2.13.1 (2021.09.21)

### Fixed

* 816fb4ad
    * fixed a bug in the Pandas case size filter (the constraints were not applied correctly).
* 40f142c4
    * fixed a bug in the format_dataframe function (columns were duplicated if already existing with the same name).
* 00d1a7de
    * reverted stream converter to old variant (in a slightly slower but safer way).

### Removed

### Deprecated

### Changed

* 991a09d4
    * introduce a time limit in the DFG playout.
* ae5d2a07
    * return the state of the process tree along with the alignment for the process tree alignments.
* 8b77384f
    * refactoring of the calculation of the fitness for Petri net alignments (scattered code).

### Added

### Other

* d58d34fd
    * upgraded Dockerfile to Python 3.9
* 50114175
    * resolved issue with the upcoming Python 3.10 release
* 89314905
    * security issue in requirements

---

## pm4py 2.2.13 (2021.09.03)

### Fixed

### Removed

### Deprecated

### Changed

* 5723df7b
    * xes exporter now reports on xes features and xmlns
* 3b632548
    * graphviz based visualizations now expose background color as a parameter

### Added

* 0592157b
    * new dfg playout including performance specification
* 85739ba0
    * allow pandas df to be used as an iterable for streaming simulation
* 2fa9993f
    * path filter that filters the cases of an event log where there is at least one occurrence of the provided path
      occurring in a given time range.
* a7ee73a8
    * added filter based on rework detection
* c03b6188
    * add petri net, reset/inhibitor net and data petri net semantics

### Other

---

## pm4py 2.2.12 (2021.08.19)

### Fixed

* a374bad3
    * https://github.com/pm4py/pm4py-core/issues/251
* e88a6546
    * https://github.com/pm4py/pm4py-core/issues/249
* 84511628
    * fix minor bug in the calculation of the handover and subcontracting metrics.

### Removed

### Deprecated

### Changed

* 01fd0402
    * The ```pm4py.view_petri_net()``` method now uses ```None``` as a default initial and final marking.
* 72ed7d0d
    * Improved performance of variant discovery of dataframes.

### Added

* 9a04357e
    * Add rework measurement at the case level in the ```pm4py.statistics.rework``` package.
* b725ca0b
    * add 'between' filter for ```pandas dataframes``` in the ```pm4py.algo.filtering.pandas``` package. The filter
      returns subsequences between the two given activities. It creates subtraces for every possible match.
* 211e3c56
    * added local linear embeddings to ```log_to_features.util```.
* 4b594228
    * add support for adding decision points to data petri nets.
* 9261270e
    * add support for performance dfg discovery in ```pm4py.discover_performance_dfg()```.

### Other

---

## pm4py 2.2.11 (2021.08.06)

### Fixed

* 207d69bd
    * bug fix in application of the filtering threshold in the IMf algorithm

### Removed

### Deprecated

### Changed

* d98cbb1c
    * changed deepcopy and copy functionality of logs for performance improvement
* f3b78a49
    * minor performance optimization in log conversion (log to dataframe)
* 71c0919f
    * improved performance for pands -> stream conversion

### Added

* f2101a72
    * added various additional features in log-based feature extraction
* 41873655
    * possiblity to directly get all performance metrics of the DFG elements
* 886b44ea
    * detection method for trace-level attributes stored at event level
* d5f9f866
    * add transition names to events, based on a given alignment
* 4802e7d8
    * add support for importing reset/inhibitor arcs and transition guards
* cc6488f7
    * add general support for reset/inhibitor nets
* e805cf5f
    * add support for data petri nets
* 1d3a2e7b
    * added case termination statistics for pandas data frames

### Other

---

## pm4py 2.2.10.2 (2021.07.26)

### Fixed

* 50ad39fa
    * Fixed blocking issue with properties of Pandas dataframes when format_dataframe is used (case ID column)
* 3708b98f
    * Fixed variants filter, when the output of get_variants_as_tuples is used

### Removed

### Deprecated

* Deprecated support to Pandas < 0.25 (due to future dropping)
* Deprecated auto-filters (due to future dropping)

### Changed

* Different interventions to fix the internal coherency of the project (usage of deprecated functions + missing imports)

### Added

### Other

---

## PM4PY 2.2.10 (2021.07.09)

### Fixed

### Removed

### Deprecated

### Changed

* 4964d6ea
    * minor refactoring (rename) in attribute statistics querying; ```get_attributes()```
      --> ```get_event_attributes()```
* 1148f6c0
    * use revised implementation of IM and IMf everywhere, deprecate old implementations

### Added

* 6750bf3a
    * add support for start time and end-time in timstamp conversion
* e24f5b70
    * computation of event-level overlap
* 8cec5f9e
    * add several case/event level statistic functions at the simplified interface level

### Other

---

## PM4PY 2.2.9 (2021.06.25)

### Fixed

* daf74e83
    * update imports in feature extraction
* 74be3e3c
    * minor bug fix in alpha plus (place that was created was not always added to the resulting Petri net)

### Removed

### Deprecated

### Changed

* d97b1790
    * drop deepcopy in event log sorting (enhances performance)
* 1d4e625b
    * revised IMf implementation (more close to ProM / PhD thesis Sander Leemans)
* 20aabd95
    * calculation of minimum self distance now adheres to the standard invocation structure

### Added

* 598c6ecb
    * simplified interface now stores properties (using attr attribute) to dataframes
* 1f7a3fa8
    * add computation of rework statistic (cases containing the same activity more than once)
* 32c7d330
    * add computation of cycle time (active time of process divided by the number of instances of the process)
* 8187f0e9
    * add distribution plots over different time-frames (matplotlib)
* 269d826c
    * add batch detection based on Martin, N., Swennen, M., Depaire, B., Jans, M., Caris, A., & Vanhoof, K. (2015,
      December). Batch Processing: Definition and Event Log Identification. In SIMPDA (pp. 137-140).
* d5326d46
    * compute case overlap of a case with all other cases

### Other

* 92a70586
    * performance optimization for calculation of performance spectrum
* b0fc57c4
    * performance optimization for Pandas datetime conversion non-ISO8601 (regular formats)

---

## PM4PY 2.2.8 (2021.06.11)

### Fixed

* c11bab8f
    * bug fix in eventually-follows filter
* d3fd1bc1
    * bug fix in activity frequency constraints of the log skeleton conformance checking

### Removed

### Deprecated

### Changed

* d96d9d69
    * improved performance of the df-based performance spectrum code
* 499d8a1c
    * improved performance of log conversions when (for internal use) deep copy is not required

### Added

* 4d679934
    * allow the possibility to filter on a trace attribute that has a type date (e.g., does the planned start date of
      the case fall in a given time window?)
* b7ef36e8
    * add properties object to trace attributes (used for internal storage of statistics, will not be exported to disk)
* d7029365
    * added some basic ML utilities for event logs, e.g., getting all prefixes of traces, get a train/test split
* 1ec5802e
    * new subtrace selection mechanism that gets all events inbetween two given activity labels (uses first match on
      both 1st and 2nd label)
* 9b65bbd9
    * allow specification of business hours in sojourn time computation of the DFG
* 4d529d6e
    * generic support for feature extraction

### Other

---

## PM4PY 2.2.7 (2021.04.30)

### Fixed

* 908e06d7
    * fix error in loop detection of inductive miner
* b7b63e0b
    * add internal log conversion in the flexible heuristics miner
* e9d61bdb
    * fix minor bug in bpmn model importing
* 52cc0c7a
    * fix minor bug in xes exporting (type of concept:name was not checked)

### Removed

### Deprecated

* 9c1a9610
    * various old utility functions are now deprecated

### Changed

* 424c9ad9
    * avoid warnings when visualizing long place names in debug visualization mode

### Added

* c2a9633e, 52e340b1
    * add simple visualization of performance spectrum.
* b6ae4b25
    * add simple dotted chart visualization to the simplified interface.
* 6e3a0bac
    * add properties attribute to event logs and event streams for storage of custom meta-data that is not exported to
      xes.
* fb142359
    * add version of dfg discovery that adds case-level attributes to nodes and edges
* d902609d
    * add basic visualization of events per time and cas distribution graphs

### Other

---

## PM4PY 2.2.6 (2021.04.23)

### Fixed

### Removed

### Deprecated

### Changed

* 766fafa7
    * minor refactoring and more generic invocation style for eventually follows-based filtering

### Added

* 353c7d6f
    * Heuristics miner is now able to filter on edges connecting to/from start/end activity
* d6412339
    * Parallel alignment computation can be directly invoked
      using ```pm4py.conformance_diagnostics_alignments(..., multi_processing=True)```
* de84e5f4
    * add ```pm4py.discover_bpmn_inductive(log)```

### Other

---

## PM4PY 2.2.5 (2021.04.16)

### Fixed

* 9854f62d
    * minor bug fix in etree xes exporter avoiding faulty None values
* bfe8fb32
    * support non-standard attribute symbols in line-by-line event log exporter

### Removed

### Deprecated

### Changed

* 3631fe58
    * default xes importer is set back to iterparse
* a7ff695a
    * large-scale restructuring of the underlying pm4py architecture
* 201879ad
    * changed the default maximum number of edges to be visualized in the DFG visualization to 100000 (was: 75)

### Added

* 66283964
    * sojourn-time-based coloring for dfgs
* 6639d3f3
    * organizational mining, e.g., ```pm4py.discover_handover_of_work_network(log)```
* 9c9ca14a
    * allow multiprocessing in alignment computation
* 279fd31f
    * add prefix tree vizualiation
* 748c768d
    * add 'old' pm4py visualization of the process tree as an alternative visualziation
* 408b37a9
    * add filter to check multiple ocurrences of certain attribute values in a case.

### Other

---

## PM4PY 2.2.4 (2021.04.01)

### Fixed

### Removed

### Deprecated

### Changed

* 56317d81
    * process tree based alignments no longer use trace-based process tree reduction (can still be used through utils)
* c1c1ffc8
    * minor optimizations to state-equation based alignment computation
* c95d45c9
    * large (internal) refactoring of pm4py object files and algorithms

### Added

* d14d3d27
    * added resource profiles to pm4py taken from Pika, Anastasiia, et al. "Mining resource profiles from event logs."
      ACM Transactions on Management Information Systems (TMIS) 8.1 (2017): 1-30.
* ab56d899
    * organizational mining according to https://arxiv.org/abs/2011.12445; contains several organizational group-based
      metrics
* 6a77a948
    * add serialization and deserialization to various pm4py objects; available through ```pm4py.serialize()```
      and ```pm4py.deserialize()```

### Other

---

## PM4PY 2.2.3 (2021.03.19)

### Fixed

* d1285706
    * fixed the consistency (w.r.t ProM) of align-etc conformance results

### Removed

### Deprecated

* c3cde455
    * deprecated (moved internally) the evaluation and simulation pacakges.
* a756f1fa
    * pm4py.objects.process_tree.pt_operator.py

### Changed

* 8474507b
    * make timestamp and performance-based trace filters inclusive on the boundaries provided
* b6154457
    * changed the equals functionality for event logs
* 9eff5646
    * classical inductive miner is rebuilt from scratch and thoroughly tested
* efc1c6e8
    * changed equals functionality of Petri nets and all their objects
* 02336ff4
    * font size is now a parameter of the object (Petri nets / Process Trees /...) visualization code

### Added

* 5de03f1e
    * added progress bar to all the alignment algorithms
* 24778a7c
    * added footprint comparison to simple the interface
    * added eventually follows discovery to the simple interface
    * added some additional statistics to the simple interface
* b2b1fdc5
    * add a faster alignment algorithm for process trees
* b7bc217f
    * more extensive support for the OR-operator in process trees
* be04ab2a
    * added performance visualization for heuristics nets
* 725f40f2
    * added boolean check on whether a trace/variant is fitting w.r.t. a given model (```pm4py.check_is_fitting()```)
* e172977c
    * added process tree parsing functionality (```pm4py.parse_process_tree()```)

### Other

* a756f1fa
    * the process tree operator class is now embedded within the process tree object definition (
      pm4py.objects.process_tree.process_tree.py)

---

## PM4PY 2.2.2 (2021.03.03)

### Fixed

* 1a5c080c
    * fix for timestamp conversion of dataframe formatting
* 19c615e1
    * fix bug in process tree exporter
    * change visualization of process trees (similar to PorM)

### Removed

### Deprecated

* 0e61f4b2
    * evaluation.soundness.wofland and evaluation.wf_net

### Changed

* 0e61f4b2
    * woflan and wf-net checks are moved to algo.analysis package
* 2e158ec4
    * minor improvements for A* performance
* d550f777
    * various renamings in the simplified interface of pm4py, several methods are deprecated.

### Added

* 65ef822c
    * generic support for the marking equation
    * generic support for the extended marking equation
* 92ba4aa7
    * variants can now be represented as a tuple of activities, rather than a single string

### Other

---

## PM4PY 2.2.1 (2021.02.15)

### Fixed

* ee11545a
    * fixed importing names of invisible transitions as stored in ```.pnml``` files
* 5efff284
    * handle warning messages thrown in the heuristics net visualization

### Removed

### Deprecated

### Changed

### Added

* 91b494ad
    * simple process tree reduction that removes parts that are guaranteed not to be needed for the alignment/replay of
      a trace
* f75ecff3
    * thread-safe implementation of ```dict``` for streaming based process mining
* 03d176f9
    * implementation of the Heuristics++ Miner
* 32443759
    * add support for using ```redis dict``` for streaming

### Other

---

## PM4PY 2.2.0 (2021.02.01)

### Fixed

* ee545f40
    * add additional check to timeout for the memory efficient implementation of A* approach for alignments
* a2a3f281
    * fix usage of integer values in pulp solver rather than binary variables.
* 6ba4322f
    * fixed conversion behavior lifecycle to interval logs

### Removed

### Deprecated

* 54e38ac8
    * ```pm4py.soundness_woflan()``` is now deprecated

### Changed

* c847e39c
    * bpmn graphs are now multi-di-graphs. also see: https://github.com/pm4py/pm4py-core/issues/203

### Added

* 54e38ac8
    * ```pm4py.check_soundness()``` replaces ```pm4py.soundness_woflan()```
* aa91fdf7
    * add typing information to ```pm4py.conformance.py``` (containing ```pm4py.conformance_alignments()``` etc.)
* 5d7890b2
    * added ```insert_ev_in_tr_index()``` utility to dataframe utils: possibility to insert the index of an event inside
      its trace (e.g. the start event gets 0, the event following gets 1). Allows us to quickly filter on prefixes
      directly at the dataframe level.
    * added ```automatic_feature_extraction_df()``` utility: possibility to extract the features of an event log
      directly starting from a dataframe. Also, an utility for the manual specification of the columns that should be
      considered in the event extraction is provided.
* f64c9a6b
    * add option to infer concurrency between to activities in a 'strict' manner in the log statistics.
      using ```srict=True```, implies that an overlap of '0' zero is not considered concurrent. also
      see: https://github.com/pm4py/pm4py-core/issues/201
* c0083f68
    * implementation based on Stertz, Florian, Jürgen Mangler, and Stefanie Rinderle-Ma. "Temporal Conformance Checking
      at Runtime based on Time-infused Process Models." arXiv preprint arXiv:2008.07262 (2020):
        * add temporal profile discovery
        * add offline conformance checking based on temporal profiles
        * add online conformance checking based on termporal profiles
* 4d3cf81c
    * support serialization of all pm4py visualizations
* 453805b4
    * compute alignments using edit distance (requires two sets of traces as an input, one represents the log, one
      represents (a subset of) the model behavior)

### Other

---

## PM4PY 2.1.4.1 (2021.01.22)

### Fixed

* 1231f518
    * strip text read from nodes in bpmn importing
* 0bc1b330
    * add type checking for bpmn conversion; i.e., if the input is already bpmn, it is returned.
* ea0c7e54
    * fix consistency in obtaining the case arrival statistics in
      ```pmpy.statistics.traces.log.case_arrival```; was median, changed to mean. also
      see: https://github.com/pm4py/pm4py-core/issues/200

### Removed

### Deprecated

### Changed

* 51be0910
    * set ```stream_postprocessing``` default value back to ```False``` for
      ``dataframe`` to ```stream``` conversion. Columns containing ```None``` values are no longer filtered by default (
      compliant with ```pm4py<=2.1.2```). also see: https://github.com/pm4py/pm4py-core/issues/199
* 8976ad45
    * drop the explicit dependency on ```numpy 1.19.3```
    * add explicit dependency ```pulp<=2.1```
* 1231f518
    * support ```sequenceflow``` operator node in bpmn file import
* 62618eeb
    * explicitly blacklist version 1.9.4 of ```numpy``` in the requirements.txt file.

### Added

### Other

---

## PM4PY 2.1.4 (2021.01.18)

### Fixed

* 35f2278a; 89c5f13b; 6a3579bc; 65fc182b; fa4448a6; c4e44311 c456c681; 6c6d96cc; e3770281; f091c43e; 6a20cf17; 69eb1ae7;
  ca780326; 36cb3963 e4f3b16f; c9f80d1f; 94c5a6e0; a713ef3d:
    * add fall-back to time-range filter if incorrect argument is passed
    * fix the copying of the 'meta attributes' of the filtered event log for the start activities filter
    * fix the copying of the 'meta attributes' of the filtered event log for the end activities filter
    * fix the copying of the 'meta attributes' of the filtered event log for the attributes filter
    * fix the copying of the 'meta attributes' of the filtered event log for the variants filter
    * fix the copying of the 'meta attributes' of the filtered event log for the directly follows filter
    * fix the copying of the 'meta attributes' for event logs in the ltl checker
    * fix the copying of the 'meta attributes' for event logs in the timestamp filter
* ffe29353:
    * create event log object before starting the parsing of XML file (in ITERPARSE_MEM_COMPRESSED)

### Removed

### Deprecated

### Changed

* 8f2d899a
    * allow to specify a cap on the number of times we visit the same marking in the extensive playout
    * allow to return the firing sequences of extensive playout instead of an event log
* b707377b
    * allow to return the firing sequences of basic/stochastic playout instead of an event log
* 9782f522
    * extended exception management in streaming algorithm interface: release locks if exception happen
* 0a741566
    * support importing of bpmn files that do not describe a name for gateways
* 583825d8
    * refactored variant-based filtering: added top-K and coverage percentage
* ba073f54
    * extended DFG filtering
* 8ebda3b1
    * exploit variants in the extensive footprints conformance checking
* dc754c78
    * change range(s) of timestamp filters to be inclusive (<=) rather than exclusive (<)

### Added

### Other

---

## PM4PY 2.1.3.2 (2021.01.08)

### Fixed

* b5cb7f0d; f1c0f037; 960d40e9
    * fix naming consistency in the filtering interface of pm4py.

### Removed

### Deprecated

### Changed

### Added

### Other

---

## PM4PY 2.1.3.1 (2021.01.07)

### Fixed

* f9f894ed
    * create an iterable that permits, theoretically, to iterate over the infinity of traces admitted by a DFG
    * the main ```apply()``` calls the iterable and stops with the usual criterias
    * the ```apply()``` can also return the variants of the log

### Removed

### Deprecated

### Changed

* 1c3666b7
    * minor refactoring of the filtering simplified pm4py interface

### Added

* 8b5dee65
    * add lambda-based filtering and sorting to simplified pm4py interface

### Other

---

## PM4PY 2.1.3 (2021.01.04)

### Fixed

* 388348f2
    * bugfix ```remove_flow``` BPMN function
* 3bd4fe0a
    * bug fix - DFG visualization needs deepcopy, otherwise it can remove element from the underlying DFG
* 92fde8cf
    * bug fix in Petri net playout in stop criterion
* 882468e1
    * compatibility with pulp version 1.6.x

### Removed

### Deprecated

### Changed

* 41ed5720
    * deepcopy of inputs:  since the dictionaries/sets are modified, a "deepcopy" is the best option to ensure data
      integrity.
    * ```keep_all_activities``` parameter in paths filter: decides if all the activities (also the ones connected by the
      low occurrences edges) should be kept, or only the ones appearing in the edges with more occurrences (default).
* 63ccc055
    * IM and IMf: removed dependency on ```pm4py.algo.filtering``` package
* 8a5788fa
    * more advanced to bpmn conversion in the simplified interface
* 66e0c074
    * refactoring conversion parameters log->stream and improved stream compression
* 73054b04
    * improved performance of the line-by-line xes importer
    * increased XES-standard conformity
* e6136ce5
    * improved performance of the xes exporters
    * increased XES-standard conformity
    * progress bar for exporting enabled
* 3b692b33
    * added parameter to enable/disable progress bar in importing in ITERPARSE
    * compression from file - XES compression moved from general entrypoint to single variant
* 68ff7d00
    * more efficient importing of .xes.gz files
* 4aad427e; 67a42d23
    * get predecessors and successors of a dfg node (in dfg utils)
* 0888ab26
    * added minimum trace length in process tree extensive playout

### Added

* 6a946fbd
    * allow to compute alignments directly on the dfg using dijkstra
* 50722bb8
    * DFG playout including Markovian probability of traces

### Other

---

## PM4PY 2.1.2 (2020.12.18)

### Fixed

* 2fb0b807
    * support nodes with the same label in BPMN layout algorithm

### Removed

### Deprecated

### Changed

* 96a7681c
    * significant memory footprint reduction for iterparse-based event log importing
* 8270a46e
    * significantly faster 'line-by-line' xes exporter
* aae4be33
    * advanced DFG filtering in (activities percentage, paths percentage) ensuring reachability from start and end
* d38f4c97
    * number of occurrences as a start or end activity is visualized in the DFG visualization

### Added

* 97cc315c
    * add (de)serialization functionality for pm4py objects

### Other

---

## PM4PY 2.1.1 (2020.12.07)

### Fixed

### Removed

### Deprecated

### Changed

* 43e7ce9e
    * full conversion of WF-nets to BPMN models

### Added

* 029d30f5
    * add visualizing and exporting BPMN models
* f76dd379
    * added conversion to simplified interface

### Other

---

## PM4PY 2.1.0.2 (2020.11.29)

### Fixed

### Removed

### Deprecated

### Changed

### Added

### Other

* f18c3e17
    * downgrading ```numpy``` to 1.19.3 for Windows 10 2004 compatibility problems
    * skip blocking ```scikit-learn``` installation for Python 3.9

---

## PM4PY 2.1.0.1 (2020.11.26)

### Fixed

* f6cdf1a9
    * hotfix problem in XES importer reading of parameters

### Removed

### Deprecated

### Changed

### Added

### Other

---

## PM4PY 2.1.0 (2020.11.24)

### Fixed

* a0a7fd09
    * bug fix in the inductive miner: sequence cuts were to maximal, leading to underfitting models (involving too many
      skips)
* 5b32725a
    * fix use of deepcopy in event log conversion
* 33103b5c
    * fix get-variants behavior for event log / df (yielded different results)

### Removed

### Deprecated

* 0138f93d
    * deprecated ```pm4py.write_csv()```; conversion and subsequent pandas export should be used.

### Changed

* 3b8fcd4a
    * apply invisible transition reduction on Petri nets obtained by Heursistic Miner

### Added

* 6afd8ab9
    * support for importing/exporting BPMN files;
    * supported elements: tasks, xor, and, or gateways
    * conversion of BPMN to WF-net
    * conversion of Process Tree to BPMN
* 848a1610
    * conversion of dataframes to event streams / event logs now detects the use of XES Extensions
* 8874f7b4
    * add statistics on concurrent activities
    * discover eventually follows relations with concurrent activities

### Other

---

## PM4PY 2.0.1 (2020.11.13)

### Fixed

* 4c115dbb
    * fix bug in hash function of traces
* 0dd8f28e
    * fix bug in the alpha+ algorithm (was adding artificial start/end to the underlying event log)

### Removed

### Deprecated

### Changed

* commit c51b1f02
    * parametrizing size of the thread pool in streaming package

### Added

* 8e07d847
    * add (unbounded) dfg discovery on an event stream
* 16e3f7f5
    * integration of the wf-net to process tree algorithm described in https://doi.org/10.3390/a13110279
* 1a26f678
    * allow creation of 'live' streaming objects directly from xes and csv files
* b08564ed
    * start minor support for interval-based process models
* 36cb7130
    * added support for generic dictionaries in streaming conformance checking

### Other

* 81579e19e
    * relaxing the importing of some dependencies (pandas, pulp, graphviz, intervaltree)
      to make a basic set of functionalities of pm4py work even without those dependencies
* ed45eafc
    * fixing circular dependencies issues and added partial compatibility with Python 3.4

---

## PM4PY 2.0.0 (2020.10.14)

### Fixed

* 1a8f9281
    * bug fix in ```pandas``` case size filter

### Removed

* 7a89d4dd
    * remove deprecated factories

### Deprecated

### Changed

* 62801513
    * improved performance of token-based replay with duplicate labels

### Added

* f408a181
    * add streaming token-based replay and footprint-based comparison
* fde08b03
    * output conformance checking diagnostics in a dataframe

### Other

* a9c5aa34
    * compatibility with Python 3.9 (limited to windows)

---

## PM4PY 1.5.2.2 (2020.09.29)

### Fixed

* 2d4a8b67e25164838030dca709816918ddbf9279
    * fixed dependencies on factories. fixed some release notes. fixed some deprecations.

### Removed

### Deprecated

### Changed

### Added

* 0d75241676a736919952e5c9ab96ab2be4c71046
    * added utility for trace attributes filtering

### Other

* d8433ac1bbb57082b19b3b97bc726b353096c76e
    * better specification of 'stable' requirements

---

## PM4PY 1.5.2.1 (2020.09.25)

### Fixed

a6fde4ccfdf0465d8919d3c72d4400bce8d4ab0e

* fixed some deprecation warnings for external libraries

### Removed

### Deprecated

### Changed

### Added

* a5befe62f84af0f3dbe734c713cc8c2c1fc22a04
    * added WOFLAN to the simplified interface

### Other

---

## PM4PY 1.5.2 (2020.09.24)

### Fixed

* 7bf3aea0b4638f6eceaa192ec37e17370e47f560
    * fixing a parameter issue on stochastic playout

### Removed

### Deprecated

### Changed

### Added

* 13cd96da7fe22427839f1b21dd38a5ac8ff8c231
    * provide alternative visualizations through Matplotlib of the main visualizations
* e7e3dfa11264a7e737ca7b65165eb7f719817f59
    * add utility to remove an arc

### Other

* c42bad174247eb13134e0cb4acb0703c301aa869
    * fixed compatibility with Python 3.5

---

## PM4PY 1.5.1 (2020.09.15)

### Fixed

### Removed

* 9e926a5d1a373d124a041c72f909eb34083f4649
    * removed the old soundness check

### Deprecated

### Changed

* 526342e3e96c7386dc7451ac0d9ec74c76b86b4f
    * performance improvement of the 'less memory' alignment variant
* 83c71eaaa9bb4ee55e2f773dd3fc9704c6324704
    * generalization of the heuristics miner visualization
* 7e7d9ba9e9b4f94d9801f5c8df3c5e4b3afd5971
    * improved speed of event log sampling
* 11d06ba2a44fd7d0a83e439b6615befad5e3c4ba
    * faster process tree playout (recursive, ignoring PT statespace)
* ce3a8609013bd7f5890b52cb44e155b57b2fc1c0
    * allow adding (arbitrary) data to transition system

### Added

### Other

---

## PM4PY 1.5.0 (2020.08.31)

### Fixed

* 30b9059fac3d59abac1c973637bd66388d7dd6db
    * bug fix in parameter parsing of log conversions

### Removed

### Deprecated

### Changed

* 3c9ed4b5e1860e2494d3b68668e3e1021ee59585
    * apply invisible transition reduction in process tree to Petri net transformation
* 26ac905fed4703724805f8fb1b5daa21475df147
    * minor optimizations in process tree alignment approximation algorithm
* c5b5ffdd51cd832be14d3078948e29f88f6c2673
    * add time-out parameter to decomposed alignment calculation
* 4a5fb9ff5ab395529062ce92747b9624a1799b0e
    * add bipartite graph matching for correlation mining to obtain exact matching results
* acc46269040a3b60bdcc6f5afe9ea55ddb5549e1
    * minor performance improvement of process tree playout
* 5dd0fe17d5a07a2096afc647306a5673d86508ba
    * apply trace-level directly on pandas data frames
* 4c35335da6a6d4419b68a49af3cbd358eca8881d
    * add 'COUNT' functionality for log/dfg statistics, e.g., in how many cases does act 'A' appear?

### Added

* 3bb5125f1849985ec9e2ba7962a287a25ede8e43
    * new implementation of the (classical) Inductive Miner, based on the PhD thesis of Sander Leemans. The
      implementation covers the following fall through functions:
        * empty trace
        * strict tau loop
        * tau loop
        * activity once per trace
        * activity concurrent
        * flower loop
* 1639d7a17660b4641a58cb435f7061d4168ce422
    * implemention of 'WOFLAN', based on the PhD thesis of Eric (H.M.W.) Verbeek.

### Other

---

## PM4PY 1.4.1.1 (2020.08.13)

### Fixed

* 76df914ad48b93a72127b0d79e5547669d3148db
    * fixed bug in less-memory alignments when im == fm

### Removed

### Deprecated

### Changed

### Added

### Other

---

## PM4PY 1.4.1 (2020.08.10)

### Fixed

### Removed

### Deprecated

### Changed

* fc724c4c9e00a388b94efea50be46412c1351bc5
    * refactoring correlation miner
    * increased scalability of the correlation miner
* e18021f06e4431628a84b441acf136d44c9baed6
    * revision/enrichment of simplified API

### Added

* 9cfd4183968118f488c95ab0bbd7e3e9b66ba355
    * alignments approximation on process trees (https://arxiv.org/pdf/2009.14094)
* f9a898da47367f86bf616a7bc8dc796be1b3e440
    * discovery of log skeleton from the list of variants

### Other

---

## PM4PY 1.4.0 (2020.08.03)

### Fixed

* c5fa9dee9bf7e4eed56785eadc423b59214d3df0
    * compatibility with latest IPython API
* 616623b358d1e1a9aa789f43e2c8cf7670ee4d79
    * clean-up in linear solver functionality
    * bug fix in usage of PulP result vector

### Removed

### Deprecated

### Changed

* 4616952ee5c184d35d26e986b298e1e586b38b3f
    * minor refactoring of the alignment code
* 3477e5345068018fa6aa91e04b6da4184e4d3c94
    * update of verions of package dependencies

### Added

* cba7a2e574aa15709d0a2dda35f8a27da9200f42
    * [beta release] simplified 'pythonic' method invocation (see ```examples/simplified_interface.py```)
* ade44e6d78551c454b477f36cbe3248a5d4e6c8b
    * added the 'correlation miner' to pm4py (https://is.tm.tue.nl/staff/rdijkman/papers/Pourmirza2017.pdf)
* 9564b54a7111916c7bc3d6f1e4c56f3829978efe
    * add visualization of conformance checking results on process tree
* 988258a2c655d17201c5b1a7120d19ab5954dbe3
    * added 'extensive' playout for process trees (for footprint comparison)

### Other

---

## PM4PY 1.3.5.2 (2020.07.24)

### Fixed

* a31467a560b940a2cb426751e032b4ea79bbb29f
    * add cast to Event class in event conversion
* 0febe4eda5772685498da2d79d144effdf61ce20
    * fix in alpha miner; conflict check yielded self-loops in some cases

### Removed

### Deprecated

### Changed

### Added

### Other

---

## PM4PY 1.3.5.1 (2020.07.22)

### Fixed

* 844459e366e77ebf88a8d01728064048d71a3e6f
    * remove ```pyemd``` from requirements as it requires a full C studio installation; can be installed and used *
      optionally*

### Removed

### Deprecated

### Changed

### Added

### Other

---

## PM4PY 1.3.5 (2020.07.20)

### Fixed

* 6cdf4483548027420b0a54c681a3ecfd515ab8f3
    * bug fix for de/recomposition approach to handle duplicated labels
* 58149e7f085bbedb47e31d58d10e37d686e46a72
    * small fix in importing of parquet files
* b08675fe8c03207c4701d2eb8b91c234e3ddbe1b
    * fix in IMdf; the noise threshold was overridden before
* 772ea5d5af9ab2fa3a424b91670d81487ab2667b
    * minor fix for timestamps that end with symbol 'Z' (Zero timestamp)
* 1e13cbdb011dff175850c4c665283bf60e0db84c
    * fix Scipy dependency for tree generator

### Removed

### Deprecated

### Changed

* 921328cd06d8870ecaa601d53cfde30a6015aec7
    * parameterize simplicity metric to use a given 'K' for reference
* 8403093c3e18c1493f4fd72bc83914dadb03e4c2
    * change the color scheme for net comparison

### Added

* 143f60a0b4fb265ba5e9d997efddf8f8d66458c3
    * add support for process tree importing (.ptml files)
* 4b9132f2835f574d9e7e5af113e5fc96bd821ccf
    * add new A* version that encodes the states of the state-space differently (up to 10% memory reduction)
* 93e6e84c4ea78afc562f4ba6cee42de8718eb4cb
    * add 'stochastic' playout, i.e., use token-based replay on a given log to guide the playout of a given Petri net
* 107797c5d1be1d742e6522a14231f4f9fce1cb38
    * add EMD-based process model evaluation ('Earth Mover's Distance' between log/model)
* 1e02596bc90b6fc22a8c89e80567bdddc2c8f1b7
    * add process tree based footprint computation

### Other

---

## PM4PY 1.3.4 (2020.07.06)

### Fixed

### Removed

### Deprecated

### Changed

* f05ba60e2faa28b2f2e2d7ef65e0ac415ae298e8
    * improved memory performance of Dijkstra-based alignments, restriction of model-move scheduling is applied (only
      one of many is chosen)
* eaed442d10a5b4c9eead3966cef473e2c3f0d61b
    * improved efficiency of reachability graph computation

### Added

* a42d0f087c94cb9e7914532f7ae0228af3a7f9ce
    * add 'extensive' playout, which allows to generate all traces in the language of a model up-to a given length.
* eaed442d10a5b4c9eead3966cef473e2c3f0d61b
    * added footprint-based conformance checking

### Other

* b99da02411259897f1df52f9a9a62153228dab8a
    * ```PuLP<=2.1``` is forced (for now, due to excessive console output of v2.2.)
    * new version of ```Pyvis``` requires additional dependencies (Apache, BSD, MIT licenses), which are now specified

---

## PM4PY 1.3.3 (2020.06.22)

### Fixed

* 1278713e2209d7b1e2287afbd9d80097db028617
    * minor fixes in (to-be-deprecated) Parquet importer and exporter

### Removed

### Deprecated

### Changed

* 59630ed8456d9e7842e05fee4c53ff1a3d1389a0
    * improved memory performance of Dijkstra-based alignments

### Added

### Other

---

## PM4PY 1.3.2 (2020.06.08)

### Fixed

### Removed

### Deprecated

### Changed

### Added

* 98e6d6d6219cceeeb2421392e9981ec808d2a468 (Merge Request #89)
    * Support importing and exporting of '.dfg' files (similar to ProM 6.10)
* 7ca768b7fcd1eea468bcdb1c1e8c9397676b511a (Merge Request #90)
    * add a detailed list of all third-party dependencies (README.THIRD_PARTY.md)
* e0685638c6c0c171583108e23f752ebef70d033e (Merge Request 94)
    * new version of Dijkstra based alignment computation

### Other

---

## PM4PY 1.3.1 (2020.05.25)

### Fixed

* d51430106dea70473777c6868a3676c027faf607
    * fix paths filter for Pandas dataframe when dataframe is not sorted

### Removed

* c7a76e0aaffb5dbcad769b2fbc52fd8c03703769
    * cleanup of the petri net impoprter/exporter, i.e., stochastic/layout information is now stored in the 'properties'
      object of places/transitions/nets

### Deprecated

### Changed

* 00d7c405628033e8f383a845e61a84205f7bbc83
    * color scheme of the log-log comparison (pm4py.algo.enhancement.comparison.petrinet)
* e84c7dc88907b408b4caf97524dd69a378e1859e
    * update the README.md file
* 332de04112cf780cbc711553e34ca4b835ee8425
    * add parameters object to transient analysis call to dfg learner
* f0976015c2b5b7384135855e75b36f69fb44a4db
    * add final marking to the basic playout of Petri nets
* e0d43c6dd5ee2492eabfd14c507b430088ec9cf0
    * allow prefixes in petri net attribute names (petri net importing)

### Added

* 095f35a3bf9f9c3bea0d518c72c76380f38b77b2
    * add support for (correctly) importing lists from .xes files

### Other

---

## PM4PY 1.3.0 (2020.05.11)

### Fixed

* 112dc3fc56f0d5e3f3ae0c737a5b0b001be31ba5
    * typo in Petri net weight (reporter: dominiquesommers)
* 4a74ef159d03d3cf3ca43bd7c99f5f97da16baf8
    * problems in the evaluation of replay fitness of recomposed alignments
* 1f40a17dcade522d308b56a9f53b40c5b8a95dfc
    * cleaning circular dependencies. relaxing some absolutely strict dependencies for some border-line configurations.
* 9780ef609db7bbb24323d3584abc2338f24252d3
    * copying of Event/Trace/EventStream/EventLog objects (reporter: M.Pegoraro)
* 51802f0828a6d207a5185c06a71bdb3a9faa1a46
    * problem with sampling log (reporter: jacksbrajin)
* b1f16bf087691181adcf5616aa85e3e454a7169c
    * fixed problem with the discovery of 2-loops in the Heuristics Miner (reporter: czwilling)
* c96dcb16064ed156a1f48075445113bb5afc6264
    * fixed ```get_variants_acyclic()``` function in petri utils (authorship: M.Pegoraro)

### Removed

### Deprecated

* b4cea4be6fe6ff90f58c405f9f0acb4dbac973f4
    * factories are deprecated

### Changed

* b4cea4be6fe6ff90f58c405f9f0acb4dbac973f4
    * factories have been renamed

### Added

* e8f250fec6781c088da8204923ad8817f1b5d689
    * decision point mining with alignments (for any scikit classification approach) is now integrated.
* 4ff811ab80b5df15e5ec1da082b4f76c72dcf684
    * trace attribute hierarchical clustering (MSc Thesis Yukun Cao; FIT/RWTH)
* 4fca12c1608818348bbd51e390140a8f7e79d7f6
    * alignments decomposition/recomposition
* f8d52aa69a3d720d45a93b35c79b4241bb8f7691
    * possibility to provide the final marking to the playout factory
* 9a5a64ea2941d69be07ee0e93b771c80f5820166
    * hash functions for event log objects
* 9f76d2e61dbc1cc74fccafac6f60d9ce69b7c791
    * added ```table_to_stream()``` auxiliary function in dataframe_utils

### Other

---

## PM4PY 1.2.13 (2020.05.11)

### Fixed

* 531b767d85bb4c95996ae0c9644a958f75aad120
    * utilities of Petri nets (acyclic net variants (M. Pegoraro); strongly connected components by NX graph)

### Removed

### Deprecated

### Changed

### Added

* c9cebbfab9c82bf8edbe8851a000fd1b1f31f8be
    * ```properties``` object to all members of the Petri net class (including transitions/places/arcs)

### Other

---

## PM4PY 1.2.12 (2020.03.18)

### Fixed

* ef3b4b62fd186df46236a8af9aa890358dbcd1bc
    * problem in the generation of logs from process trees
* 548c57a6d2340dcaba7ef11464ebe193f8fb9c5c
    * filter by variants percentage
* c49a9c441feb65a74d5c5da774fdda79295665cc
    * problems of the token-based replay with the count of tokens at global and local level
* f554aec318717ee1fb7f81c4e0acbd6da7e7bc34
    * continuous time Markov Chain steady-state analysis
* e05145de972944f211f2763656eb6e41aa64e0b5
    * revised process tree fold and tau reduce functions
* c3f66b8cb8667c2f204a1da899a216656386c2fa
    * ignore comments in .pnml files

### Removed

* 31e1cd29437d6b183357bbc5c103131484d390b3
    * problematic dependencies ortools and pyarrow in the project (when installed, can be used, but no more required by
      default)

### Deprecated

### Changed

### Added

* f554aec318717ee1fb7f81c4e0acbd6da7e7bc34
    * converting a performance DFG to a Q-matrix for transient analysis
* cc766164f2397fe2cb33f8278372469e25cfecd6
    * business hours module supports full-days shifts (e.g. from 0 to 24)
* cc766164f2397fe2cb33f8278372469e25cfecd6
    * backwards state space exploration (supports duplicate transitions) for token-based replay
* 1b3c32916fe0ccbc4d3f73a44cc68e2ca83a810e
    * Visual log comparison on a Petri net by plasma coloring

### Other

---

## PM4PY 1.2.11 (2020.02.21)

### Fixed

* 6f320562a836cd949dbbe6ec7751f8f9514b01ec
    * parameter object for calling alignment code directly
* 471f414820c7b3f919aa97ccdc684d40cf132b3c
    * dependency problem with ORTools and PyArrow
* 157fadffd3b953c105e67f4909547f097d77ea0a
    * reduce inernal (cyclic) dependencies within pm4py
* f38b6089b7eb6a4518a9c33e9775120874352657; af1328e2dad82f0a059e00942167a29cb918c85f;
  e8e1ab443f2dedb2cd348f35bc49eed412d66e1d
    * hash and equals function of process trees
* 229bd7ed78ea80aefbb6c7fcfa173edda682c1c7
    * refactoring of the Monte Carlo simulation.
        * extend the simulation to support arc weights that are provided by the replay (e.g. informed transition pickup)
        * extend the simulation to support more than one resource per place through semaphores
        * maximum execution time per simulation thread
        * general refactoring of the code
        * introduce logging information about the simulation
        * improving documentation
        * improving clarity of the code
* f5132302e06aa49f26ab3264bb3147d0660a11c0
    * performance of log generation from process trees
* 9e64f2635123aa5c3146fb2ad03863cbf93175df
    * fixed incongruency in variants statistics (was there for log, not for dataframes)
    * increased coverage of tests, and made some of them more lean
    * introduced some additional tests on the new functionalities
    * updated Dockerfile
    * updated setup with new packages
    * removed remainings of the SIMPLE algorithm in the tests folder
* 382162c648fb8e32b0145a6ff9427af8a7fb39fa
    * fixed parameters initialization to make it uniform for the rest of the project for all the versions of IMDF
    * added missing documentation in factory (was there only in the versions)
    * moved log conversions from factory to specific versions (since they are indeed version specific, if later we
      include the log version)
    * removed some useless calculations on the new DFG based versions (were there, but never used!)
    * introduced two new methods, apply_variants and apply_tree_variants, that are able to apply inductive miner from a
      list of variants
    * separated DEFAULT_VARIANT from DEFAULT_VARIANT_DFG (indeed, the first in future versions may become the log)
    * increased number of tests in the tests/ folder for inductive miner

### Removed

* 502c5d722d483c567f0e08c16da0bb4c87a94e36
    * remove the empty performance spectrum visualizer folder

### Deprecated

### Changed

* e8b030afd37559c93f79e1dd030fdc540aa62135
    * provide fast-parquet library as an alternative to read/write parquet files.

### Added

* 557472bc78900d90beb0757279ef29b89aa410b1
    * integrate LogSkeleton for process discovery and conformance checking
* 90ba7bf1495fdac7ccef3112efa95687c46a5dd1
    * importing and exporting of Petri net weights

### Other

---       

## PM4PY 1.2.10 (2020.01.31)

### Fixed

* f571ec65ca544a9322b89cf96299d03da65de5a0
    * import DFG to PN
    * process tree parsing
* dca5cc602ba8381e5d4e265341dfc5a5292a80c0
    * problem with alignments when transitions have empty preset
* 68643cb109503e54787f98eb8f40650e37aa151e
    * process tree hashing
* 9d27f132d40638933be00f9d178e9a1167d36166
    * conversion between the log types

### Removed

### Deprecated

### Changed

* 945fd64e481c0fbf020da7f71cb1a7974ae9629c
    * make visualization deterministic for process trees, Petri nets and DFGs
* 15be58abb314c679ddf3b65fa6832c680768c413
    * generic parsing of dates (removed strict dependency on ciso8601)

### Added

### Other

---

## PM4PY 1.2.9 (2020.01.24)

### Fixed

* be0a282be033765c9d1d7f1a7ba541a11c046834
    * matplotlib backend settings

### Removed

### Deprecated

### Changed

* ed42182f32eba37df71d9f466ad165036f8d1086
    * full support for numpy v1.18
* d1a418f8fa2513a469149383fe69df9a4e6fea06
    * full support pandas v1.0

### Added

### Other

---

## PM4PY 1.2.8 (2020.01.10)

### Fixed

* 6908a34c73c74c42aac3ddf31b964fcae680919e
    * inductive miner sequence cut detection
* 881f1fa4e76b9e35c2d80ab7d241183b2d6871c0
    * 'Best effort fix' for graphviz based visualizations

### Removed

### Deprecated

### Changed

### Added

### Other

---

## PM4PY 1.2.7 (2019.12.20)

### Fixed

* programming error in the alignments code
* ```should_close``` for XOR node in PT generation
* ```execute_enabled``` for parallel and OR node in PT generation
* process tree children setter function

### Removed

* ```copy.copy``` for parent nodes of childs in log generation from process tree
* windows platform reuquirement for ortools/pyarrow

### Deprecated

### Changed

* recursion depth in token-based replay invisibles exploration
* consider only fitting traces in the Align-ETConformance count
* consider all the optimal alignments (as described in the paper) and not only the first one
* moving of utilities and making the search function using Dijkstra (since we are looking for fit paths) instead of A*
* LTL checker: making existing filters more performant (A eventually B eventually C)

### Added

* LTL checker: introducing A eventually B eventually C eventually D
* LTL checker: introducing time boundaries for each arc of the eventually follows relation

### Other

___

## PM4PY 1.2.6 (2019.11.29)

### Fixed

* bug fix in the 'escaping edges' based precision

### Removed

### Deprecated

### Changed

### Added

* Pyarrow serialization integration (supporting in-memory and to .pkl file serialization)

### Other
