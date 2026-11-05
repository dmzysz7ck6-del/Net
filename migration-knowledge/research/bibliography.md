# Annotated bibliography

Generated from `research/references.json` by `python -m src.reporting.bibliography`. Labels: **V3** = verified against Crossref; **V2** = independently re-verified; **V1** = single-pass search match; **U** = unverified / no DOI; **X** = Crossref MISMATCH. Findings are abstract-level summaries unless stated otherwise.

### Doria Arrieta (O. A.); Fabio Pammolli; Alexander M. Petersen (2017). Quantifying the negative impact of brain drain on the integration of European science
*Science Advances 3(4): e1602232*. Link: https://pmc.ncbi.nlm.nih.gov/articles/PMC5389781 · **U** (unverified / no DOI)

- **Question:** Did EU enlargement (2004/2007) and the resulting high-skilled migration imbalance affect cross-border scientific collaboration and integration in Europe?
- **Data:** Millions of publications for 32 European countries, 1996-2012, across 14 subject areas, plus official intra-European high-skilled mobility statistics.
- **Methods:** Synthetic control method for the counterfactual level of cross-border collaboration, and difference-in-differences panel regressions relating collaboration to migration imbalance.
- **Findings:** Abstract-level: European cross-border collaboration would have been higher absent the 2004/2007 enlargement. Migration imbalance, mostly from newer to older member states, is a major factor. The authors argue that this hampers convergence in scientific competitiveness and recommend home-return incentives.
- **Relevance here:** A quasi-causal, country-level study linking official (non-bibliometric) high-skilled migration to co-authorship. It shows that migration can coincide with weaker, not stronger, collaboration with the origin (brain drain rather than bridge), which our residual analysis for SSA origins can test.

### Guy J. Abel, Joel E. Cohen (2019). Bilateral international migration flow estimates for 200 countries
*Scientific Data 6:82*. DOI: [10.1038/s41597-019-0089-3](https://doi.org/10.1038/s41597-019-0089-3) · **V1** (single-pass search match)

- **Question:** How can bilateral migration flows be estimated for all country pairs from bilateral stock data, and which estimation method performs best?
- **Data:** UN bilateral migrant stock data; estimates for 200 countries over five-year periods 1990-2015, checked against reported flow data where available. Code and estimates on Figshare.
- **Methods:** Six methods for deriving flows from changes in bilateral stocks, including closed demographic accounting approaches. Validation by correlation with reported flows.
- **Findings:** Abstract-level: the two closed demographic accounting methods performed better than the other four. The paper gives open, reproducible bilateral flow estimates for countries that do not publish flow data.
- **Relevance here:** Makes clear that UN DESA data are stocks (accumulated history), not flows, and gives an option for robustness checks with estimated flows. A stock-vs-flow mismatch is one possible explanation if migration and knowledge layers diverge, since scholarly mobility is closer to a flow.

### Jonathan Adams; Karen Gurney; Daniel Hook; Loet Leydesdorff (2014). International collaboration clusters in Africa
*Scientometrics 98(1): 547-556*. DOI: [10.1007/s11192-013-1060-2](https://doi.org/10.1007/s11192-013-1060-2) · **V1** (single-pass search match)

- **Question:** Is African international research collaboration organized in a uniform global pattern, or in regional clusters shaped by geography, history, culture and language?
- **Data:** African country co-authorship data (about 2011 publications, as described in the preprint). The data details were not verified from the full text.
- **Methods:** Co-authorship network mapping and clustering (VOSviewer maps).
- **Findings:** Abstract-level only. African collaboration is far from universal. It shows layers of internal clusters and external links, explained by regional geography and, more strongly, by history, culture and language rather than global influences. The authors call for analysis of bottom-up human factors to inform policy.
- **Relevance here:** Directly about the focus region. It predicts that co-authorship clusters for East African (Kenya, Uganda, Tanzania, Rwanda), West African (Ghana, Nigeria, Senegal) and Southern African origins follow linguistic and historical lines. These same factors also shape migration, so they are confounders to control when testing whether migration predicts collaboration.

### Ajay Agrawal, Iain Cockburn, John McHale (2006). Gone but not forgotten: knowledge flows, labor mobility, and enduring social relationships
*Journal of Economic Geography 6(5):571-591*. DOI: [10.1093/jeg/lbl016](https://doi.org/10.1093/jeg/lbl016) · **V1** (single-pass search match)

- **Question:** After an inventor moves away, do the social relationships they built while co-located keep sending knowledge flows (patent citations) back to their former location?
- **Data:** Patent citation data on mobile inventors and the locations they lived in before (abstract-level; an earlier version is NBER WP 9950, 2003).
- **Methods:** Compares citations flowing to an inventor's former location with a counterfactual in which the inventor never lived there. Separates flows within technology fields from flows across them.
- **Findings:** Abstract-level. Knowledge flows to a mobile inventor's former location are about 50% larger than if the inventor had never lived there. The authors attribute this to personal relationships formed during co-location in an institutional setting, which last across time, space and organizational boundaries. The effect is nearly twice as large across technology fields as within them.
- **Relevance here:** Gives the mechanism for why bibliometric scholarly mobility, meaning researchers who were once co-located, should predict co-authorship better than general migrant stocks. Supports entering mobility and migrant stocks as separate regressors in the PPML gravity model, and reading co-authorship residuals as traces of past researcher mobility.

### Ajay Agrawal, Devesh Kapur, John McHale, Alexander Oettl (2011). Brain drain or brain bank? The impact of skilled emigration on poor-country innovation
*Journal of Urban Economics 69(1):43-55*. DOI: [10.1016/j.jue.2010.06.003](https://doi.org/10.1016/j.jue.2010.06.003) · **V1** (single-pass search match)

- **Question:** Does the emigration of skilled innovators reduce or increase the access that innovators left at home have to knowledge?
- **Data:** Indian patent citation data (abstract-level). Earlier version: NBER WP 14592, 2008.
- **Methods:** Builds a model in which the optimal size of a diaspora depends on co-location effects versus diaspora effects in accessing knowledge, then estimates both using citation patterns of Indian inventors.
- **Findings:** Abstract-level. On average, innovator emigration has a net harmful effect on domestic knowledge access. However, knowledge reached through the diaspora is especially valuable for India's most important inventions, measured by citations received.
- **Relevance here:** Sets out the brain-drain versus brain-bank tradeoff for a poor origin country. Suggests alignment between diaspora destinations and knowledge partners may be strongest for high-impact output, which argues for stratifying SSA co-authorship by citation impact.

### Aliakbar Akbaritabar, Tom Theile, Emilio Zagheni (2024). Bilateral flows and rates of international migration of scholars for 210 countries for the period 1998-2020
*Scientific Data 11, article 816*. DOI: [10.1038/s41597-024-03655-9](https://doi.org/10.1038/s41597-024-03655-9) · **V1** (single-pass search match)

- **Question:** How can publication metadata be used to estimate yearly international migration rates and bilateral flows of publishing scholars for all countries, and how consistent are the estimates across Scopus and OpenAlex?
- **Data:** Bibliometric metadata from Scopus and OpenAlex. One summary says more than 36 million articles and reviews were used, but that figure may refer to the Scopus base used in the authors' related work. Country-level aggregated yearly rates and bilateral origin-to-destination flows for 210 countries and areas, 1998-2020. Earlier version: MPIDR Working Paper WP-2023-018, 'Global flows and rates of international migration of scholars'.
- **Methods:** Scholars are tracked over time through the countries of their publication affiliations. A slide deck from the group says a scholar's yearly country of residence is the modal country of their affiliations that year; I could not confirm this wording in the paper itself. Changes in that country count as migration events. The authors set out pre-processing steps and best practices for identifying migration, then aggregate to yearly rates and bilateral flows, and cross-validate scholar counts between Scopus and OpenAlex.
- **Findings:** Abstract-level only. Scholar counts in Scopus and OpenAlex are highly correlated for most countries. OpenAlex covers non-Western countries more extensively, but agreement with Scopus is highest in Western countries. A secondary source (OpenAlex blog) adds two points: migration events are less correlated between the two sources than scholar counts, although trends for the top country pairs are consistent, and flow magnitudes are much larger in OpenAlex than in Scopus. A later version (SMD 2.0, WP-2026-029) extends coverage to 1998-2024 with gender, field and subnational breakdowns.
- **Relevance here:** This is layer (2) of the project, the scholarly mobility flows. Limitations to plan around: (a) it covers only scholars who publish and are indexed, and inferred moves depend on affiliation strings and author disambiguation; (b) it is a flow measure, while UN DESA gives stocks; (c) the Scopus and OpenAlex versions disagree more for non-Western, including Sub-Saharan African, countries, and absolute flow levels are much higher in OpenAlex, so robustness checks should use both sources; (d) small origins such as Somalia and Rwanda will have sparse rows and many zeros, which suits PPML but makes rank and divergence metrics noisy. A further caution: co-authorship and mobility are both built from the same affiliation metadata (OpenAlex), so some alignment between layers (2) and (3) could be mechanical, especially where affiliation changes and multiple affiliations are confused.

### Assaf Almog, Tiziano Squartini, Diego Garlaschelli (2015). A GDP-driven model for the binary and weighted structure of the International Trade Network
*New Journal of Physics 17:013009*. DOI: [10.1088/1367-2630/17/1/013009](https://doi.org/10.1088/1367-2630/17/1/013009) · **V1** (single-pass search match)

- **Question:** Can country GDP drive a maximum-entropy model that reproduces both the binary and weighted structure of the trade network?
- **Data:** International Trade Network and country GDP.
- **Methods:** Maximum-entropy model preserving degrees and strengths (enhanced configuration model), with the model's hidden variables linked nonlinearly to GDP.
- **Findings:** Abstract-level: GDP relates nonlinearly to the model parameters. There is an asymmetry: binary properties can be inferred without knowing weighted ones, but the weighted structure cannot be recovered without binary information.
- **Relevance here:** Connects gravity-style mass variables (GDP, research output) to maximum-entropy network nulls. It suggests a 'fitness' null for co-authorship based on country research size, against which migration-driven excess links can be judged.

### Patricia Alonso-Álvarez; Nees Jan van Eck (2024). Coverage and metadata availability of African publications in OpenAlex: A comparative analysis (PDF title: 'Coverage and metadata completeness and accuracy of African research publications in OpenAlex: A comparative analysis')
*arXiv preprint arXiv:2409.01120 (cs.DL); no journal version found as of search*. Link: https://arxiv.org/abs/2409.01120 · **U** (unverified / no DOI)

- **Question:** How do OpenAlex, Scopus, Web of Science and African Journals Online (AJOL) compare in their coverage and metadata for publications in African-based journals?
- **Data:** Publications in African-based academic journals, 1996-2022, matched across OpenAlex, Scopus, WoS and AJOL by exact DOI match.
- **Methods:** Coverage overlap comparison and metadata-availability comparison (authors, affiliations, references, funders) across databases.
- **Findings:** Abstract-level only. OpenAlex has the most extensive coverage of these African publications. It has high coverage of publication and author metadata but performs worse on affiliations, references and funder information. Metadata availability is better for publications also indexed in Scopus or WoS.
- **Relevance here:** The most directly relevant evidence on OpenAlex quality for African research. Broad coverage helps the co-authorship layer, but weak affiliation metadata can drop or misassign country links for SSA origins. Caveat: the sample is African-based journals, not all African-authored work.

### Juan Pablo Alperin; Jason Portenoy; Kyle Demes; Vincent Larivière; Stefanie Haustein (2024). An analysis of the suitability of OpenAlex for bibliometric analyses
*arXiv preprint arXiv:2404.17663 (cs.DL); no journal version found as of search*. DOI: [10.48550/arXiv.2404.17663](https://doi.org/10.48550/arXiv.2404.17663) · **V1** (single-pass search match)

- **Question:** Can OpenAlex replace Scopus for bibliometric analyses, and how do coverage and metadata compare?
- **Data:** OpenAlex and Scopus records (secondary summaries mention a late-2023 OpenAlex snapshot). The study was done in collaboration with the OpenAlex team.
- **Methods:** Comparison of coverage and metadata between OpenAlex and Scopus across several dimensions, including country-level rank correlations.
- **Findings:** Abstract-level only. OpenAlex is a superset of Scopus and can be a reliable alternative for some analyses, particularly at the country level, but metadata accuracy and completeness issues remain. A substantial share of OpenAlex works lack affiliation/country information or references (from secondary summaries).
- **Relevance here:** Supports country-level OpenAlex co-authorship networks while flagging missing affiliations. Missing affiliations would bias co-authorship edges for origins with weaker metadata (likely including several SSA countries). The project should report the share of works with missing country codes per origin.

### Silvia Appelt; Brigitte van Beuzekom; Fernando Galindo-Rueda; Roberto de Pinho (2015). Which factors influence the international mobility of research scientists?
*OECD Science, Technology and Industry Working Papers 2015/02. Also a chapter in Geuna (ed.), Global Mobility of Research Scientists (Academic Press, 2015), pp. 177-213*. Link: https://ideas.repec.org/p/oec/stiaaa/2015-2-en.html · **U** (unverified / no DOI)

- **Question:** What bilateral factors explain international flows of research scientists between countries?
- **Data:** Bilateral scientist mobility measured from changes in affiliations reported by publishing scientists in a major global index of scholarly publications, 1996-2011.
- **Methods:** Gravity model of bilateral scientist flows, with geographic, socioeconomic and scientific distance, co-authorship (collaboration) intensity, tertiary student flows, R&D resources and visa restrictions as regressors.
- **Findings:** Abstract-level: geographic, socioeconomic and scientific distance correlate negatively with scientist mobility between two countries. Scientific collaboration is a major factor associated with mobility. Scientist mobility relies heavily on tertiary student flows in the opposite direction (destination to origin). Mobility is positively related to economic convergence and R&D resources, and negatively to visa restrictions.
- **Relevance here:** The reverse-direction counterpart to our component (b). It shows that bibliometric scholarly mobility and co-authorship are tightly coupled at the dyad level, so mobility is partly endogenous to collaboration. This supports lagged specifications and comparing the explanatory power of general migration (more exogenous to science) with scholarly mobility.

### Silvia Appelt, Brigitte van Beuzekom, Fernando Galindo-Rueda, Roberto de Pinho (2015). Which factors influence the international mobility of research scientists?
*OECD Science, Technology and Industry Working Papers, No. 2015/02, OECD Publishing*. DOI: [10.1787/5js1tmrr2233-en](https://doi.org/10.1787/5js1tmrr2233-en) · **V1** (single-pass search match)

- **Question:** What economic, geographic, scientific and policy factors explain bilateral flows of research scientists between countries?
- **Data:** A new mobility measure from changes in affiliations reported by publishing scientists in a major global index of scholarly publications (Scopus), 1996-2011, bilateral country pairs.
- **Methods:** Gravity-model estimation of bilateral scientist mobility flows, with distance terms (geographic, socioeconomic, scientific), economic and R&D conditions, visa restrictions, collaboration intensity and reverse-direction student flows.
- **Findings:** Abstract-level. Geographic, socioeconomic and scientific distance are negatively associated with scientist mobility between two countries. Scientific collaboration appears to be a major factor linked to mobility. Mobility increases with converging economic conditions and R&D resources, and is lower with visa restrictions. Scientist mobility is strongly associated with tertiary student flows in the opposite direction, which the authors read as multi-directional brain circulation.
- **Relevance here:** The closest gravity-model precedent. It shows collaboration and mobility are linked dyadically, which raises endogeneity concerns for the project's PPML specification (co-authorship regressed on mobility). It also shows that direction matters: the reverse student-flow result suggests including both directions of mobility and migrant stocks in dyadic models.

### Samin Aref, Emilio Zagheni, Jevin West (2019). The demography of the peripatetic researcher: Evidence on highly mobile scholars from the Web of Science
*Social Informatics (SocInfo 2019), Lecture Notes in Computer Science 11864, Springer, pp. 50-65*. DOI: [10.1007/978-3-030-34971-4_4](https://doi.org/10.1007/978-3-030-34971-4_4) · **V1** (single-pass search match)

- **Question:** Who are the highly mobile ('peripatetic') researchers who publish from three or more countries, and what global structure do their moves form?
- **Data:** Main affiliation addresses on more than 62 million Web of Science publications, 1956-2016 (arXiv 1907.13414).
- **Methods:** Tracking researchers' affiliation countries over time; defining super-movers as those with publications from at least three distinct countries; demographic and network description.
- **Findings:** Abstract-level. More than 90% of researchers show no international mobility. Peripatetic researchers form a global system with the USA and China as two large hubs and England and Germany as two smaller hubs. The paper frames the policy debate as shifting from brain drain to brain circulation.
- **Relevance here:** Methodological precursor to the MPIDR scholarly migration database. It shows that bibliometric mobility is rare and hub-concentrated, which supports degree- and strength-preserving nulls in the topology comparison.

### Peter M. Aronow, Cyrus Samii, Valentina A. Assenova (2015). Cluster-Robust Variance Estimation for Dyadic Data
*Political Analysis 23(4):564-577*. DOI: [10.1093/pan/mpv018](https://doi.org/10.1093/pan/mpv018) · **V1** (single-pass search match)

- **Question:** How should standard errors be computed in dyadic regressions, where any two dyads that share a member may have correlated errors?
- **Data:** Simulations and an empirical application to interstate disputes.
- **Methods:** Non-parametric sandwich-type dyadic-robust variance estimator for linear regression that allows dependence between all dyads sharing a unit, with consistency conditions. Extensions to directed and repeated dyads, weights, and GLMs such as logistic regression.
- **Findings:** Abstract-level: the estimator is consistent under stated conditions, and ignoring dyadic dependence understates uncertainty in dyadic regressions.
- **Relevance here:** Country-pair co-authorship, migration and mobility are dyadic. Dyad-robust standard errors (stricter than two-way origin/destination clustering, since i-j and j-k dyads share j) should be used, or at least reported as a robustness check, for the PPML and alignment regressions.

### Dany Bahar, Hillel Rapoport (2018). Migration, Knowledge Diffusion and the Comparative Advantage of Nations
*The Economic Journal 128(612):F273-F305*. DOI: [10.1111/ecoj.12450](https://doi.org/10.1111/ecoj.12450) · **V1** (single-pass search match)

- **Question:** Does international migration spread tacit productive knowledge, shown by countries starting to export new products?
- **Data:** Bilateral migration stocks and product-level export data across countries (abstract-level). Earlier versions: IZA DP 9788 and CESifo WP 5769.
- **Methods:** Relates migrant stocks from a product's exporters to the probability that the host country starts exporting that product within ten years. Migration is instrumented in a gravity framework.
- **Findings:** Abstract-level. A 10% increase in immigrants from countries that export a product is associated with roughly a 2% higher probability that the host country starts exporting it within a decade. Effects are stronger for highly skilled migrants, qualitatively similar for emigrants, and robust to gravity-based instrumentation.
- **Relevance here:** Evidence that generic bilateral migrant stocks carry knowledge in the productive or trade domain. That makes it a direct contrast for testing whether the same stocks carry scientific knowledge. The gravity-predicted migration instrument could be reused to address endogeneity in co-authorship PPML.

### Federico Battiston, Vincenzo Nicosia, Vito Latora (2014). Structural measures for multiplex networks
*Physical Review E 89(3):032804*. DOI: [10.1103/PhysRevE.89.032804](https://doi.org/10.1103/PhysRevE.89.032804) · **V1** (single-pass search match)

- **Question:** Which node-, edge-, local- and global-level measures capture the 'multiplexicity' of a network whose nodes are linked by several types of relation?
- **Data:** Real social multiplex: 78 individuals linked by mutual trust, common operations, exchanged communications and business relationships (the Noordin Top terrorist network).
- **Methods:** Defines multiplex measures: multi-degree and degree distributions across layers, edge overlap (pairwise o_ij = number of layers in which i and j are linked, plus a multiplex-level average), interlayer clustering and transitivity, multiplex spectral centrality, and shortest paths across layers.
- **Findings:** Abstract-level plus secondary descriptions: the proposed measures show structure that per-layer or aggregated analysis misses. The multiplex-level edge overlap equals 1/M when no edge appears in more than one of M layers and 1 when all layers are identical. Exact normalization (average over connected pairs or over all pairs) not confirmed from the full text.
- **Relevance here:** Edge overlap and degree/strength correlations across layers are direct, interpretable statistics for whether a migration edge (origin->destination) co-occurs with a scholarly-mobility or co-authorship edge. Observed overlap can be compared with overlap under degree/strength-preserving nulls.

### Nelius Boshoff (2009). Neo-colonialism and research collaboration in Central Africa
*Scientometrics 81(2): 413-434*. DOI: [10.1007/s11192-008-2211-8](https://doi.org/10.1007/s11192-008-2211-8) · **V1** (single-pass search match)

- **Question:** Do Central African research collaborations show neo-colonial ties (dominance of former colonial powers), and what roles do local researchers play?
- **Data:** Research papers from Central African countries (bibliometric data), plus a survey of reprint authors of Cameroonian papers.
- **Methods:** Bibliometric partner-share analysis combined with an author survey.
- **Findings:** Abstract-level only. About 80% of the region's papers involve a partner outside Central Africa, and about 35% include a former colonial power. France, the USA, the UK and Germany are the leading partners. Local researchers contribute intellectually, but their most common role is fieldwork.
- **Relevance here:** Evidence that colonial history structures African co-authorship partners. It motivates a colonial-tie covariate in the PPML model and a test of whether migrant-destination and collaboration-partner alignment is driven by shared colonial links (as with Francophone Senegal versus Anglophone East and West Africa).

### Stefano Breschi, Francesco Lissoni, Ernest Miguelez (2017). Foreign-origin inventors in the USA: testing for diaspora and brain gain effects
*Journal of Economic Geography 17(5):1009-1038*. DOI: [10.1093/jeg/lbw044](https://doi.org/10.1093/jeg/lbw044) · **V1** (single-pass search match)

- **Question:** Are patents by foreign-origin inventors in the US cited disproportionately by co-ethnic inventors in the US (diaspora effect) or by inventors in the home country (brain gain effect)?
- **Data:** EP-INV database of uniquely identified inventors on EPO patent applications, combined with IBM-GNR name analysis. Ten Asian and European origin countries.
- **Methods:** Citation-based tests separating co-ethnic diaspora effects inside the destination from knowledge flows back to the origin country, benchmarked against other channels such as co-invention networks and multinationals.
- **Findings:** Abstract/preprint-level. A diaspora effect does not necessarily become a brain gain for the origin. Most notably, no brain gain is found for India, where the diaspora effect exists but does not benefit the home country. Diaspora and brain gain effects matter less than other channels of knowledge transmission, especially co-invention networks and multinational companies.
- **Relevance here:** The closest conceptual match to the thesis that the migration network is not the knowledge network: a migrant presence at a destination need not create origin-destination knowledge ties, and collaboration networks themselves dominate. This motivates testing whether migrant stocks add explanatory power for co-authorship once collaboration or mobility structure is controlled.

### A. Colin Cameron, Jonah B. Gelbach, Douglas L. Miller (2011). Robust Inference With Multiway Clustering
*Journal of Business & Economic Statistics 29(2):238-249*. DOI: [10.1198/jbes.2010.07136](https://doi.org/10.1198/jbes.2010.07136) · **V1** (single-pass search match)

- **Question:** How can cluster-robust inference be done when errors are correlated along two or more non-nested dimensions?
- **Data:** Monte Carlo simulations (two-way random effects, placebo-law experiment) and re-analysis of empirical studies with two-way clustering.
- **Methods:** Multiway cluster-robust sandwich variance estimator (inclusion-exclusion combination of one-way cluster variances) for OLS and nonlinear estimators (logit, probit, GMM).
- **Findings:** Abstract-level: the estimator allows valid inference under non-nested multiway clustering, performs well in Monte Carlo, and is easy to implement in packages that already offer one-way clustering.
- **Relevance here:** Justifies two-way clustering by origin and destination country for gravity and dyadic regressions, since errors of all dyads sharing an origin (or destination) are correlated. ppmlhdfe and fixest support multiway clustering.

### Zaida Chinchilla-Rodríguez; Yi Bu; Nicolás Robinson-García; Rodrigo Costas; Cassidy R. Sugimoto (2018). Travel bans and scientific mobility: utility of asymmetry and affinity indexes to inform science policy
*Scientometrics 116(1): 569-590*. DOI: [10.1007/s11192-018-2738-2](https://doi.org/10.1007/s11192-018-2738-2) · **V2** (independently re-verified)

- **Question:** Can asymmetry and affinity indexes computed separately for scientific collaboration and scientific mobility reveal the strength of, and discrepancies between, bilateral research relationships, using the countries named in the 2017 US travel bans as a test case?
- **Data:** Bibliometric collaboration and author-mobility data for the countries in the 2017 US executive-order travel bans (Iran, Iraq, Libya, Somalia, Sudan, Syria, Yemen) and their partner countries.
- **Methods:** Affinity Index (AFI) and Probabilistic Affinity Index (PAI, also called the Proximity Index) computed for collaboration and for mobility links, plus asymmetry indexes, with the two layers compared for each country.
- **Findings:** Abstract-level: comparing collaboration and mobility from an affinity perspective can identify discrepancies between levels of collaboration and levels of mobility. The probabilistic affinity index is highly sensitive to country size. The authors argue that the approach can inform immigration policy and identify potential partnerships.
- **Relevance here:** The closest precedent for component (a). For each origin (including Somalia, a focus origin) it compares the partner profile of one network layer (bibliometric mobility) against another (co-authorship) and flags mismatches. Our project extends this with UN DESA general migrant stocks as a third layer and with formal divergence metrics (JSD, rank correlation, top-k overlap) and null models instead of affinity indexes alone. Its finding on size sensitivity motivates our degree- and strength-preserving nulls.

### Zaida Chinchilla-Rodríguez; Lili Miao; Dakota Murray; Nicolás Robinson-García; Rodrigo Costas; Cassidy R. Sugimoto (2018). A Global Comparison of Scientific Mobility and Collaboration According to National Scientific Capacities
*Frontiers in Research Metrics and Analytics 3: 17*. DOI: [10.3389/frma.2018.00017](https://doi.org/10.3389/frma.2018.00017) · **V2** (independently re-verified)

- **Question:** How do country-level networks of scientific mobility and international collaboration relate to each other, and how does this vary with national scientific capacity?
- **Data:** Bibliometric affiliation data, 2008-2015. Countries are linked when an individual is affiliated with both. National capacity comes from the Scientific and Technological Capacity Index (150 countries: 22 Advanced, 24 Proficient, 22 Developing, 80 Lagging).
- **Methods:** Construction and comparison of country mobility and collaboration networks, stratified by capacity group, using network positions and centrality.
- **Findings:** Abstract-level: there is a significant relationship between the flow of mobile researchers and co-publication with foreign partners in the more prolific countries, but mobility is always lower than collaboration. Relationships are size- and resource-dependent. Advanced and Proficient countries hold most mobile authors and international papers, and mobility is extremely low in Developing and Lagging countries. Country positions are not consistent across the two networks, which shows distinct roles for mobility and collaboration, with particular instability for lower-income countries.
- **Relevance here:** The closest global, multilayer topology comparison of a mobility network and a collaboration network (our multilayer and topology component). Its finding that the layers diverge most for lower-income countries directly anticipates our SSA focus. It does not include general (UN DESA) migration and does not use null models, which are our additions.

### Sergio Correia, Paulo Guimarães, Thomas Zylkin (2020). Fast Poisson estimation with high-dimensional fixed effects
*The Stata Journal 20(1):95-115*. DOI: [10.1177/1536867X20909691](https://doi.org/10.1177/1536867X20909691) · **V1** (single-pass search match)

- **Question:** How can PPML models with several high-dimensional fixed effects be estimated quickly and reliably, including checking whether the (pseudo-)ML estimates exist?
- **Data:** Software and methods paper (no substantive dataset; abstract-level).
- **Methods:** The ppmlhdfe Stata command, built on reghdfe: a modified iteratively reweighted least squares algorithm with accelerated HDFE demeaning and a new procedure to detect separation (non-existence of estimates).
- **Findings:** Abstract-level: ppmlhdfe estimates PPML with multiple HDFEs quickly, shares reghdfe syntax and features, and gives a more robust check for the existence of (pseudo-)ML estimates.
- **Relevance here:** The reference implementation for PPML with origin and destination (and possibly year) fixed effects. Its separation detection matters because many SSA dyads have zero co-authorship, and some fixed effects may perfectly predict zeros. Python/R ports (e.g. pyfixest, fixest) follow the same logic.

### Mathias Czaika, Sultan Orazbayev (2018). The globalisation of scientific mobility, 1970-2014
*Applied Geography 96, 1-10 (the task brief's attribution to Research Policy appears to be wrong)*. Link: https://www.sciencedirect.com/science/article/abs/pii/S0143622817305428 · **U** (unverified / no DOI)

- **Question:** How has global scientific mobility changed over four decades, in geographic range, centre of gravity and distance, and what are its bilateral determinants, including visa restrictions?
- **Data:** Bibliometric data on scientists' affiliation changes, 1970-2014; citing work describes it as Scopus. Also IMI Working Paper 146 (2018).
- **Methods:** Descriptive network and geography analysis of bilateral scientific mobility; citing work reports gravity-type regressions including visa restrictions.
- **Findings:** Abstract-level (Growth Lab and IMI pages). The range of origin and destination countries has widened. The centre of gravity of scientific production and migration destinations has shifted eastward. Average migration distances have grown as peripheral regions join the global science system. Visa restrictions are a statistically significant barrier to scientists' mobility. A citing source says scientists were found to be about three times as internationally mobile as non-scientists; this is not confirmed from the abstract.
- **Relevance here:** Supports including visa and policy-barrier covariates and long-run trends. The finding that scientists are far more mobile than the general population, if confirmed, implies scholarly mobility flows and UN DESA migrant stocks should differ in scale and probably in geography.

### Frederic Docquier, Hillel Rapoport (2012). Globalization, Brain Drain, and Development
*Journal of Economic Literature 50(3):681-730*. DOI: [10.1257/jel.50.3.681](https://doi.org/10.1257/jel.50.3.681) · **V1** (single-pass search match)

- **Question:** What do four decades of research say about the size, causes and development consequences of high-skill emigration?
- **Data:** Literature survey drawing on bilateral and skill-specific migration datasets and case studies (abstract-level). Working paper: IZA DP 5590.
- **Methods:** Review of theory and empirical work, plus three case studies.
- **Findings:** Abstract-level. High-skill emigration need not deplete the sending country's human capital stock and can generate positive network externalities. Case studies cover the African medical brain drain, European scientists moving to the US, and the Indian diaspora's role in India's IT sector. Concludes with implications for education, immigration and international taxation policy.
- **Relevance here:** Standard framing of brain drain versus diaspora externalities for SSA origins. Highlights that skill composition matters, while UN DESA stocks are not broken down by skill, which is a key limitation to discuss when comparing them with scholarly mobility.

### Manlio De Domenico, Vincenzo Nicosia, Alexandre Arenas, Vito Latora (2015). Structural reducibility of multilayer networks
*Nature Communications 6:6864*. DOI: [10.1038/ncomms7864](https://doi.org/10.1038/ncomms7864) · **V1** (single-pass search match)

- **Question:** How many layers of a multilayer network are informative? Can layers be aggregated without losing structural information?
- **Data:** Synthetic benchmark multilayers and real multilayer systems (protein-genetic, social, economic and transportation networks).
- **Methods:** Information-theoretic method that borrows from quantum theory: von Neumann entropy of layer Laplacians and Jensen-Shannon distances between layers, with hierarchical clustering of layers. It merges layers to maximize how distinguishable the multilayer is from its fully aggregated graph.
- **Findings:** Abstract-level: the number of informative layers in some real systems can be cut by up to 75% while keeping the multilayer distinguishable from its aggregate. Some layers are redundant, others are not.
- **Relevance here:** Gives a formal test of the title claim. If the migration and knowledge layers are structurally redundant, reducibility would merge them; if the knowledge layers stay distinct, that supports 'not the same network'. It also uses Jensen-Shannon distance between layers, which matches the project's per-origin JSD.

### Marco Dueñas, Giorgio Fagiolo (2013). Modeling the International-Trade Network: a gravity approach
*Journal of Economic Interaction and Coordination 8(1):155-178*. DOI: [10.1007/s11403-013-0108-y](https://doi.org/10.1007/s11403-013-0108-y) · **V1** (single-pass search match)

- **Question:** Can a gravity model reproduce the binary and weighted topological structure of the international trade network?
- **Data:** International trade network (bilateral trade flows).
- **Methods:** Fit gravity models and compare predicted with observed network statistics (link presence, weights, degree/strength, clustering), with and without fixing the observed binary structure.
- **Findings:** Abstract-level: the gravity model reproduces the weighted structure only when the binary architecture is fixed to the observed one. It performs very badly at predicting link presence, or flow levels when links must be estimated too, and it fails to capture clustering-type patterns.
- **Relevance here:** Warns that a PPML gravity model of co-authorship may fit intensities well while mispredicting which country pairs collaborate at all. This argues for reporting binary (link) and weighted (intensity) fit separately and for comparing gravity-implied topology with observed topology.

### Giorgio Fagiolo (2010). The international-trade network: gravity equations and topological properties
*Journal of Economic Interaction and Coordination 5(1):1-25*. DOI: [10.1007/s11403-010-0061-y](https://doi.org/10.1007/s11403-010-0061-y) · **V1** (single-pass search match)

- **Question:** Once bilateral trade is purged of what a gravity equation explains, what does the topology of the remaining ('residual') trade network look like?
- **Data:** Bilateral international trade flows among countries (exact years not confirmed in this pass).
- **Methods:** Estimate a standard gravity equation (size, distance, borders, trade agreements), use the residuals as edge weights of a residual network, and compare its topological statistics with those of the original network.
- **Findings:** Abstract-level: the residual network's structure is very different from the original and more complex. The original is geographically clustered around a few large hubs, while the residual network features many small, trade-oriented countries acting as local hubs or attracting large, rich partners whatever their location.
- **Relevance here:** The closest methodological precedent for the planned residual (observed vs expected) analysis: build a residual co-authorship network after a gravity model with or without migrant stocks and mobility, then study its topology. It shows that residual networks can expose structure hidden by size and distance, for example SSA origins over- or under-connected relative to diaspora size.

### Giorgio Fagiolo, Marina Mastrorillo (2012). The International-Migration Network
*arXiv:1212.3852 / LEM Working Paper 2012/23. The published version appears to be Physical Review E 88:012812 (2013), but the journal title wording was not confirmed.*. Link: https://arxiv.org/abs/1212.3852 · **U** (unverified / no DOI)

- **Question:** What is the binary and weighted topology of the international migration network, how did it change between 1960 and 2000, and can a gravity model account for it?
- **Data:** Bilateral migrant stocks from origin to destination countries, 1960-2000, treated as a weighted directed graph (abstract-level).
- **Methods:** Network statistics on the weighted directed migrant-stock network, compared against a parsimonious gravity model of migration.
- **Findings:** Abstract-level. The network is modular, with a small-world pattern, disassortative mixing, high clustering and power-law distributed weighted statistics. A parsimonious gravity model accounts for most of the observed topology, and socio-economic, geographical and political factors matter more than local network properties.
- **Relevance here:** Baseline topology of a migrant-stock layer of the same type as UN DESA. Shows that gravity models reproduce much of the migration topology, which supports using gravity-based expectations alongside degree- or strength-preserving nulls in the multilayer comparison.

### Giorgio Fagiolo, Marina Mastrorillo (2014). Does Human Migration Affect International Trade? A Complex-Network Perspective
*PLoS ONE 9(5):e97331*. DOI: [10.1371/journal.pone.0097331](https://doi.org/10.1371/journal.pone.0097331) · **V1** (single-pass search match)

- **Question:** How are the international migration network and the international trade network related, and does a country's position in the migration network affect bilateral trade?
- **Data:** Worldwide bilateral migration stocks and bilateral trade, 1960-2000 (abstract-level).
- **Methods:** Complex-network comparison of the two layers (correlation and centralities), plus gravity regressions augmented with migration-network centrality measures.
- **Findings:** Abstract-level. The migration and trade networks are strongly correlated, largely because of country size and geographic distance. Countries that are more central in the migration network trade more bilaterally, and intensive forms of centrality boost trade more than extensive ones. Note: a 2015 correction notice (DOI 10.1371/journal.pone.0126879) republished the revised version.
- **Relevance here:** A direct template for the multilayer comparison. Its key warning is that raw cross-layer correlation is mostly driven by gravity (size and distance), so migration-co-authorship alignment must be judged against gravity-based or strength-preserving nulls, not raw correlations.

### Ana Fernández; Esther Ferrándiz; María Dolores León (2016). Proximity dimensions and scientific collaboration among academic institutions in Europe: The closer, the better?
*Scientometrics 106(3): 1073-1092*. DOI: [10.1007/s11192-015-1819-8](https://doi.org/10.1007/s11192-015-1819-8) · **V1** (single-pass search match)

- **Question:** Which proximity dimensions (geographical, cognitive, institutional, organizational, social, economic) explain co-authorship between European universities?
- **Data:** 240,495 co-authored articles from 690 universities in the EU-15, 2006-2010. Results are reported for all disciplines and separately for Chemistry & Chemical Engineering, Life Sciences, and Physics & Astronomy.
- **Methods:** Gravity-equation econometric models of institution-pair co-authorship counts with multiple proximity measures.
- **Findings:** Abstract-level only. Geographical, cognitive, institutional, social and economic proximity matter substantially, while organizational proximity is weaker. Effects differ across disciplines.
- **Relevance here:** A gravity precedent with several proximities. It supports including social proximity (which migrant stocks and scholarly mobility can be read as proxying) next to geographic and economic distance in the PPML specification, and it warns about field heterogeneity.

### Chiara Franzoni, Giuseppe Scellato, Paula Stephan (2012). Foreign-born scientists: mobility patterns for 16 countries
*Nature Biotechnology 30(12), 1250-1253*. DOI: [10.1038/nbt.2449](https://doi.org/10.1038/nbt.2449) · **V1** (single-pass search match)

- **Question:** What shares of scientists are foreign-born across 16 core research countries, and what are their mobility patterns and reasons for moving?
- **Data:** GlobSci survey: corresponding authors of 2009 articles in four fields (including biology, chemistry, earth and environmental sciences, and materials) working in 16 countries; 17,182 respondents in 2011. NBER WP 18067.
- **Methods:** Cross-national survey of migration history, country of origin and reasons for mobility.
- **Findings:** Abstract and summary level. Switzerland had the highest share of immigrant scientists; India had the lowest, closely followed by Italy and Japan. There was wide cross-country variation in foreign-born shares and in emigration patterns.
- **Relevance here:** The main survey benchmark (GlobSci) against which bibliometric mobility estimates can be compared. It covers 16 mostly high-income countries and no Sub-Saharan origins as host countries, so it shows a coverage gap the bibliometric data partly fill.

### Richard B. Freeman; Wei Huang (2015). Collaborating with People Like Me: Ethnic Coauthorship within the United States
*Journal of Labor Economics 33(S1): S289-S318*. DOI: [10.1086/678973](https://doi.org/10.1086/678973) · **V1** (single-pass search match)

- **Question:** Do US-based scientists of the same ethnicity coauthor more than expected, and how does ethnic homophily relate to research impact?
- **Data:** Authorship of scientific papers by US-based authors, with ethnicity inferred from names (IZA DP 8432 is an earlier version).
- **Methods:** Comparison of observed ethnic co-authorship against the expectation from the ethnic composition of authors, and regressions of journal impact and citations on homophily.
- **Findings:** Abstract-level: persons of similar ethnicity coauthor together more frequently than predicted by their share among authors. Greater homophily is associated with publication in lower-impact journals and with fewer citations.
- **Relevance here:** Evidence that shared ethnic or national origin structures co-authorship beyond chance, which is the mechanism behind expecting diaspora stocks to predict collaboration. Its observed-versus-expected logic is analogous to our residual and null-model approach. It is within-country, not cross-border, so it does not show that migrants link destination and origin.

### Caroline Viola Fry (2023). Bridging the Gap: Evidence from the Return Migration of African Scientists
*Organization Science 34(1): 404-432*. DOI: [10.1287/orsc.2022.1580](https://doi.org/10.1287/orsc.2022.1580) · **V1** (single-pass search match)

- **Question:** Does the return migration of internationally trained African scientists raise the productivity and connections of non-migrant colleagues at the receiving African institutions?
- **Data:** Return of US-trained African HIV/AIDS researchers supported by the NIH Fogarty program, with publication records of non-migrant scientists at the receiving African institutions.
- **Methods:** Quasi-experimental design exploiting the timing of returnee arrivals at African institutions (difference-in-differences style comparison of exposed and unexposed non-migrants).
- **Findings:** Abstract-level: non-migrant scientists at the receiving African institutions publish more after a returnee arrives, especially those without prior ties to top global institutions. Returnees act as brokers connecting peripheral colleagues to central knowledge and networks.
- **Relevance here:** The strongest causal evidence found for SSA that migration (via return) builds collaboration links between Africa and destination science systems. It suggests the migrant-collaboration link runs through a narrow, science-specific channel (trained researchers) rather than general diaspora size, which is the distinction our general-migration-versus-scholarly-mobility comparison tests.

### Caroline Fry; Jeffrey L. Furman (2025). Migration and Global Network Formation: Evidence from Female Scientists in Developing Countries
*Organization Science 36(3): 1047-1071 (published online May 2023)*. DOI: [10.1287/orsc.2023.1683](https://doi.org/10.1287/orsc.2023.1683) · **V1** (single-pass search match)

- **Question:** When do migrant scientists from developing countries broker international connections for non-migrant scientists at home, and how does institutional context (gender parity) shape this?
- **Data:** PhD fellowship program of the Organization for Women in Science for the Developing World (OWSD), 1996-2016: female scientists from developing countries doing PhDs in another developing country. Panel of 3,179 non-migrant scientists in the published version.
- **Methods:** Panel analysis of whether non-migrants gain international co-authorship connections through migrant colleagues, interacted with home- and host-country gender parity.
- **Findings:** Abstract-level: female migrant scientists are more likely to share international connections with non-migrants at home when their home and host countries have high levels of gender parity. Institutional support is critical for migrant brokerage and the globalization of knowledge production.
- **Relevance here:** Developing-country evidence (including South-South migration) that migration translates into origin-country collaboration only under supportive institutional conditions. This gives a mechanism for heterogeneity across SSA origins in how well migrant destinations align with collaboration partners.

### Antonios Garas, Athanasios Lapatinas, Konstantinos Poulios (2016). The relation between migration and FDI in the OECD from a complex network perspective
*Advances in Complex Systems 19:1650009*. DOI: [10.1142/S0219525916500090](https://doi.org/10.1142/S0219525916500090) · **V1** (single-pass search match)

- **Question:** How are bilateral migration and FDI networks among OECD countries related, and does migration-network centrality affect FDI?
- **Data:** OECD bilateral migration and FDI data (abstract-level). Preprints: arXiv:1701.07729 and MPRA 75134.
- **Methods:** Network comparison and a gravity equation augmented with network variables.
- **Findings:** Abstract-level. Strong positive correlation between the migration and FDI networks, largely explained by country size and distance. Country pairs that are more central in the migration network show a stronger positive FDI relationship. An earlier 2015 MPRA version described a weaker relationship, so the versions differ on this point.
- **Relevance here:** A second multilayer migration-economy comparison with the same lesson: cross-layer overlap is largely gravity-driven, and migration-network centrality adds explanatory power. Provides a design and specification to adapt for the migration and co-authorship layers.

### Wolfgang Glänzel (2001). National characteristics in international scientific co-authorship relations
*Scientometrics 51(1): 69-115*. DOI: [10.1023/A:1010512628145](https://doi.org/10.1023/A:1010512628145) · **V1** (single-pass search match)

- **Question:** What national characteristics shape international co-authorship? Are bilateral co-publication links symmetric, and how does international collaboration relate to national research profiles and citation impact?
- **Data:** International co-authored publications by country (ISI databases, 1990s). Abstract-level only.
- **Methods:** Bibliometric indicators of bilateral co-authorship strength, with symmetry/asymmetry tests of country-pair links and field-level citation analysis.
- **Findings:** Abstract-level only. Not all bilateral links are symmetric. Internationally co-authored papers are cited more on average than domestic ones, but the citation gain from international collaboration varies a lot between countries and, within countries, between fields.
- **Relevance here:** The asymmetry of country-pair links matters directly when comparing directed migration stocks and directed scholarly mobility flows with undirected co-authorship. It supports normalizing per origin (each origin's partner distribution) rather than using raw symmetric counts.

### Qinchang Gui; Chengliang Liu; Debin Du (2019). Globalization of science and international scientific collaboration: A network perspective
*Geoforum 105: 1-12*. DOI: [10.1016/j.geoforum.2019.06.017](https://doi.org/10.1016/j.geoforum.2019.06.017) · **V1** (single-pass search match)

- **Question:** How did the global international scientific collaboration network evolve from 2000 to 2015, and which proximities and linkages explain country-pair collaboration?
- **Data:** Web of Science country co-authorship data, 2000-2015.
- **Methods:** Social network analysis (core-periphery structure, centrality) and Quadratic Assignment Procedure (QAP) regression on country-pair matrices.
- **Findings:** Abstract-level only, read on the ECNU repository and a mirror, not the publisher page. The network grew in nodes and ties and shows a core-periphery structure with a more competitive multi-centric core, with the USA as a top-level hub. In the QAP analysis, post-colonial links, a shared English language, economic and science-capability proximity, social proximity and international students are associated with more collaboration. Geographic distance has a negative but statistically insignificant effect.
- **Relevance here:** The closest network-plus-dyadic-regression analogue in this topic. It already enters a human-mobility dyadic variable (international students) and colonial ties as predictors of country-pair co-authorship. QAP is an alternative or complement to the planned permutation nulls.

### Gali Halevi; Henk F. Moed (2012). International Scientific Migration and Collaboration Patterns Following a Bibliometrics Line of Investigation
*arXiv preprint (CoRR abs/1212.5194). A related peer-reviewed paper is Moed & Halevi (2014), 'A bibliometric approach to tracking international scientific migration', Scientometrics 101(3): 1987-2001, DOI 10.1007/s11192-014-1307-6*. Link: https://arxiv.org/pdf/1212.5194 · **U** (unverified / no DOI)

- **Question:** Can Scopus affiliation data track international scientific migration, and do migration patterns differ from co-authorship (collaboration) patterns between countries?
- **Data:** Scopus affiliation countries of publishing authors for 17 countries (10 fast-growing and 7 established science systems).
- **Methods:** Synchronous and asynchronous bibliometric migration indicators compared with country-level co-authorship patterns, with error-rate estimation.
- **Findings:** Abstract-level and secondary coverage (Inside Higher Ed, Research Trends): international scientific migration patterns are different from collaboration patterns. Shared language and geographic proximity affect migration more strongly than co-authorship, and political tensions affect co-authorship more than migration. Results should be interpreted cautiously and combined with CV or survey data.
- **Relevance here:** The most direct early statement of our headline claim that the migration network is not the collaboration network, though here 'migration' means bibliometric scholarly mobility, not general population migrant stocks. We should cite it as a precursor and show that the divergence also holds, and is larger, when general migration (UN DESA) is the comparison layer.

### Keith Head, Thierry Mayer (2014). Gravity Equations: Workhorse, Toolkit, and Cookbook
*Handbook of International Economics, Vol. 4 (Gopinath, Helpman, Rogoff eds.), Elsevier, Ch. 3, pp. 131-195*. DOI: [10.1016/B978-0-444-54314-1.00003-3](https://doi.org/10.1016/B978-0-444-54314-1.00003-3) · **V1** (single-pass search match)

- **Question:** How should gravity equations for bilateral flows be estimated and interpreted in a way consistent with theory?
- **Data:** Survey chapter. Draws on bilateral trade data and the gravity literature; specific datasets not verified in this pass.
- **Methods:** Review of structural gravity theory and estimators (fixed effects, PPML and related methods) in a step-by-step cookbook format; earlier versions are CEPR DP 9322 and CEPII WP 2013-27.
- **Findings:** Abstract-level: naive estimation gives biased and often misinterpreted results. The authors recommend a toolkit of several theory-consistent estimators, not sole reliance on any one method.
- **Relevance here:** Standard reference for specifying origin/destination fixed effects (multilateral resistance) and for checking robustness across estimators (PPML vs alternatives) in the co-authorship gravity models.

### Jarno Hoekman; Koen Frenken; Robert J. W. Tijssen (2010). Research collaboration at a distance: Changing spatial patterns of scientific collaboration within Europe
*Research Policy 39(5): 662-673*. DOI: [10.1016/j.respol.2010.01.012](https://doi.org/10.1016/j.respol.2010.01.012) · **V1** (single-pass search match)

- **Question:** How do physical distance and territorial borders (regional, national, linguistic) affect research collaboration between European regions, and has their effect changed over time?
- **Data:** All co-publications between 313 regions in 33 European countries, 2000-2007 (Web of Science).
- **Methods:** Gravity equation of co-publication counts between regions, with distance and border/language dummies, estimated over time.
- **Findings:** Abstract-level only. European integration is weakening the effect of territorial borders, but sensitivity to physical distance has not fallen, so the preference for nearby partners persists. Collaboration propensity varies a lot between regions and countries, which the authors relate to size, quality and accessibility.
- **Relevance here:** A key methodological precedent for count-based gravity models of co-publication with distance, language and border terms. It provides baseline covariates and expected signs for the PPML co-authorship model before migrant stocks and scholarly mobility are added.

### Lei Hou; Yueling Pan; Jonathan J. H. Zhu (2021). Impact of scientific, economic, geopolitical, and cultural factors on international research collaboration
*Journal of Informetrics 15(3): 101194*. DOI: [10.1016/j.joi.2021.101194](https://doi.org/10.1016/j.joi.2021.101194) · **V1** (single-pass search match)

- **Question:** How do scientific size, economic size, geopolitical ties (shared intergovernmental organization memberships) and cultural links (language, religion) shape close collaboration between countries?
- **Data:** Country-pair international collaboration data. The data source and years were not confirmed, since only abstract-level material was seen.
- **Methods:** Dyadic country-pair analysis of collaboration intensity on scientific, economic, geopolitical and cultural covariates. The exact estimator was not confirmed.
- **Findings:** Abstract-level only. Countries with large and similar scientific and economic sizes are more likely to collaborate closely. Shared memberships in intergovernmental organizations strongly promote close collaboration. Shared language and religion also help.
- **Relevance here:** A recent country-pair determinants study that gives a covariate set for the PPML co-authorship baseline (mass terms, size similarity, shared IGOs, language, religion). Migrant stocks and scholarly mobility should be tested as additions to these predictors.

### Rodrigo Ito; Diego Chavarro; Tommaso Ciarli; Robin Cowan; Fabiana Visentin (2025). From drains to bridges: The role of internationally mobile PhD students in linking non-mobile with foreign scientists
*Journal of Development Economics 177: 103577*. DOI: [10.1016/j.jdeveco.2025.103577](https://doi.org/10.1016/j.jdeveco.2025.103577) · **V1** (single-pass search match)

- **Question:** Do internationally mobile PhD students and scientists from a developing country link non-mobile domestic scientists to foreign collaborators, and how durable are these links?
- **Data:** CVs, scholarship program records and OpenAlex publications reconstructing the mobility paths and co-authorship networks of 19,158 Colombian scientists, 1990-2021. UNU-MERIT WP 2024-009 is an earlier version.
- **Methods:** Individual-level panel and network analysis of co-authorship formation (triadic closure through mobile co-authors), comparing diaspora, returnee and intermittently mobile scientists.
- **Findings:** Abstract-level: co-authoring with mobile scientists makes non-mobile scientists more likely to collaborate with foreign researchers. These foreign collaborations tend to be short-lived and are sustained only through the mediation of a mobile scientist. Diaspora and intermittently mobile scientists also act as international bridges.
- **Relevance here:** A recent OpenAlex-based developing-country study tying scholarly mobility to the origin's foreign co-authorship partners. It supports scholarly mobility (not general migration) as the operative channel and warns that diaspora-mediated ties are fragile, which matters when interpreting cross-sectional alignment.

### Koen Jonkers; Laura Cruz-Castro (2013). Research upon return: The effect of international mobility on scientific ties, production and impact
*Research Policy 42(8): 1366-1377*. DOI: [10.1016/j.respol.2013.05.005](https://doi.org/10.1016/j.respol.2013.05.005) · **V1** (single-pass search match)

- **Question:** How do ties formed during a stay in a foreign research system affect returnee scientists' international collaboration patterns, output and impact after return?
- **Data:** Argentinean researchers who returned after working abroad, compared with non-mobile peers (bibliometric and CV data).
- **Methods:** Econometric comparison of returnees' collaboration with former host countries and of their productivity and impact.
- **Findings:** Abstract-level: highly skilled return migrants contribute to establishing ties between home and host research systems. Ties formed abroad shape returnees' collaboration patterns and research output upon return.
- **Relevance here:** Classic evidence that a country's collaboration partners mirror where its scientists went (former host countries), so scholarly mobility should predict collaboration better than general migrant destinations. This is a direct prior for our hypothesis on component (b).

### Maki Kato; Asao Ando (2017). National ties of international scientific collaboration and researcher mobility found in Nature and Science
*Scientometrics 110(2): 673-694*. DOI: [10.1007/s11192-016-2183-z](https://doi.org/10.1007/s11192-016-2183-z) · **V2** (independently re-verified)

- **Question:** Is country-level international scientific collaboration explained by researchers' international migration as well as by their motivation, and which way does causality run between mobility and collaboration?
- **Data:** Metadata of papers published in Nature and Science, 1989-2009 (country-pair counts).
- **Methods:** Count-data estimation on bilateral (country-pair) collaboration, with migration (mobility) variables and 'synergy' and 'difference' effects between countries. The direction of the mobility-collaboration relationship is tested.
- **Findings:** Abstract-level: international collaboration is explained by both researchers' international migration and their motivation (synergy and difference effects between countries). Researchers move to countries with better research environments, but networks created through collaboration are not a factor in migration. The relationship runs in one direction, from mobility to collaboration. The paper also notes a mechanical issue: when a researcher moves from A to B, a former A-B collaboration becomes domestic and a tie to A becomes international.
- **Relevance here:** The closest country-pair econometric precedent for using scholarly mobility to predict co-authorship (our component b). The mechanical reclassification point is directly relevant to our design, because Akbaritabar et al. mobility flows and OpenAlex co-authorship come from the same affiliation records, so the gravity models need lagging or disjoint author sets.

### William R. Kerr (2008). Ethnic Scientific Communities and International Technology Diffusion
*Review of Economics and Statistics 90(3):518-537*. DOI: [10.1162/rest.90.3.518](https://doi.org/10.1162/rest.90.3.518) · **V2** (independently re-verified)

- **Question:** Do US ethnic scientific and entrepreneurial communities transfer technology back to their home countries?
- **Data:** US individual patent records with an ethnic-name database used to identify the ethnicity of researchers. International patent citations (abstract-level).
- **Methods:** Name-based ethnic classification of inventors, then analysis of ethnic knowledge diffusion to home countries using citation patterns (abstract-level; full text not read).
- **Findings:** Abstract-level. US ethnic research communities serve as channels for technology transfer to their home countries. The transfers are particularly strong in high-tech industries and for Chinese economies. The related thesis and working paper report that international patent citations confirm knowledge diffusion through ethnic networks.
- **Relevance here:** The standard name-based approach to diaspora knowledge flows. It is an analogue for identifying SSA-origin scholars in OpenAlex and a warning about how reliable name-based ethnicity is for African origins. The evidence is concentrated on large Asian diasporas.

### Mikko Kivelä, Alex Arenas, Marc Barthelemy, James P. Gleeson, Yamir Moreno, Mason A. Porter (2014). Multilayer networks
*Journal of Complex Networks 2(3):203-271*. DOI: [10.1093/comnet/cnu016](https://doi.org/10.1093/comnet/cnu016) · **V1** (single-pass search match)

- **Question:** How can the many ad hoc notions of multiplex, interdependent and multilayer networks be unified in one general framework and terminology, and how do single-layer network diagnostics carry over to multilayer settings?
- **Data:** Review article, no new data. Surveys existing empirical datasets that can be represented as multilayer networks.
- **Methods:** Conceptual and mathematical framework (tensor-style multilayer representation, node-layer tuples, intra- and inter-layer edges), a terminology dictionary, and a review of multilayer generalizations of network diagnostics.
- **Findings:** Abstract-level: proposes a general multilayer formalism and dictionary of terms, shows how many existing multiplex and interdependent network types fit in it, and reviews attempts to generalize single-layer measures (degree, clustering, paths, centrality, communities) to multilayer networks.
- **Relevance here:** Gives the formal vocabulary for treating migration stocks, scholarly mobility and co-authorship as three layers on a shared country node set (a node-aligned, edge-colored multiplex). It is the standard citation for framing the topology-comparison part of the project.

### Jianhua Lin (1991). Divergence measures based on the Shannon entropy
*IEEE Transactions on Information Theory 37(1):145-151*. DOI: [10.1109/18.61115](https://doi.org/10.1109/18.61115) · **V1** (single-pass search match)

- **Question:** Can divergence measures between probability distributions be defined from Shannon entropy so that they avoid the absolute-continuity requirement of Kullback-Leibler-type divergences?
- **Data:** Theoretical paper, no data.
- **Methods:** Defines a family of entropy-based divergences, including the Jensen-Shannon divergence (and its generalized, weighted form), and derives bounds relating them to variational distance and Bayes misclassification error.
- **Findings:** Abstract-level: the proposed divergences do not need absolute continuity between distributions, are bounded, and are tied by derived bounds to variational distance and the probability of misclassification.
- **Relevance here:** The canonical citation for using JSD to compare an origin's migrant-destination distribution with its co-authorship-partner distribution. JSD stays finite when one distribution puts zero mass on destinations the other uses, which is common for SSA origins. Its boundedness (at most log 2) makes values comparable across origins.

### Rossana Mastrandrea, Tiziano Squartini, Giorgio Fagiolo, Diego Garlaschelli (2014). Enhanced reconstruction of weighted networks from strengths and degrees
*New Journal of Physics 16:043022*. DOI: [10.1088/1367-2630/16/4/043022](https://doi.org/10.1088/1367-2630/16/4/043022) · **V1** (single-pass search match)

- **Question:** Is the strength sequence enough to reconstruct or null-model a weighted network, or do degrees carry extra information?
- **Data:** Several real-world weighted networks (abstract-level).
- **Methods:** Analytical maximum-entropy 'enhanced configuration model' (ECM) that constrains both degrees and strengths, with information-theoretic model selection against strength-only models.
- **Findings:** Abstract-level: strength-only reconstruction can perform poorly. A non-trivial degree sequence cannot be reduced to the strength sequence, and constraining both gives much better reconstruction of higher-order patterns. Expected values come out analytically, with no sampling.
- **Relevance here:** Backs the plan to use degree- and strength-preserving nulls, not strength-only ones, when testing cross-layer overlap and topology. This matters because co-authorship layers are dense with many small weights, while migration layers are concentrated.

### Thierry Mayer, Soledad Zignago (2011). Notes on CEPII's distances measures: The GeoDist database
*CEPII Working Paper No. 2011-25*. Link: https://www.cepii.fr/CEPII/en/publications/wp/abstract.asp?NoDoc=3877 · **U** (unverified / no DOI)

- **Question:** How are CEPII's bilateral distance and geography variables built, and what do they contain?
- **Data:** Country-level geographic data (geo_cepii) for 225 countries, and a dyadic file (dist_cepii) with distances and pair dummies such as contiguity, common language and colonial links; city-level population data.
- **Methods:** Computes several bilateral distance measures, including population-weighted distances based on inter-city distances among the largest cities of each country (following Head and Mayer 2002), plus capital-to-capital and most-populated-city distances.
- **Findings:** Documentation paper: describes the construction and coverage of the GeoDist variables used throughout the gravity literature.
- **Relevance here:** Source of the distance, contiguity, common-language and colonial-tie covariates for the PPML gravity models of co-authorship. It should be cited as the data source and its weighted-distance definition used consistently.

### Jean-Baptiste Meyer, Mercy Brown (1999). Scientific diasporas: a new approach to the brain drain
*UNESCO MOST Discussion Paper Series No. 41 (SHS.99/WS/12), prepared for the World Conference on Science, UNESCO-ICSU, Budapest, 26 June-1 July 1999*. Link: https://unesdoc.unesco.org/ark:/48223/pf0000116330 · **U** (unverified / no DOI)

- **Question:** How are countries organizing their expatriate scientists and engineers into networks for development at home, and what lessons follow?
- **Data:** Inventory or review of existing science and technology diaspora networks. Later work cites it as an early list of such networks (record-level; full text not read).
- **Methods:** Descriptive survey and policy analysis.
- **Findings:** Record/introduction-level only. Although national experiences differ, the diaspora initiatives share the goal of systematically using expatriate experts, scientists and engineers for development at home. The authors draw early lessons and policy implications for more efficient use of S&T diasporas. Later studies use it as a baseline list of science diaspora networks. The specific counts and findings were not verified.
- **Relevance here:** The founding statement of the scientific diaspora option, useful for framing SSA scientific diasporas as policy objects that differ from total migrant stocks.

### Jean-Baptiste Meyer (2001). Network Approach versus Brain Drain: Lessons from the Diaspora
*International Migration 39(5):91-110*. DOI: [10.1111/1468-2435.00173](https://doi.org/10.1111/1468-2435.00173) · **V1** (single-pass search match)

- **Question:** Can networks of highly skilled expatriates turn the brain drain into a brain gain for origin countries?
- **Data:** Case studies of intellectual and scientific diaspora networks (abstract-level).
- **Methods:** Conceptual analysis using a connectionist or network approach, drawing on case-study evidence.
- **Findings:** Abstract-level. Highly skilled expatriate networks that connect diaspora members to their origin countries can turn brain drain into brain gain. Proposes an expanded concept of the network that includes actors and intermediaries, not only kinship or co-national ties.
- **Relevance here:** Defines the diaspora knowledge network as an organized, selective subset of the diaspora, separate from the migrant population as a whole. This supports the hypothesis that knowledge partners will not simply mirror migrant destinations.

### Ernest Miguelez, Claudia Noumedem Temgoua (2020). Inventor migration and knowledge flows: A two-way communication channel?
*Research Policy 49(9):103914*. DOI: [10.1016/j.respol.2019.103914](https://doi.org/10.1016/j.respol.2019.103914) · **V1** (single-pass search match)

- **Question:** Does inventor migration raise knowledge flows in both directions, back to home countries and into host countries?
- **Data:** Country-pair data for 1990-2010 on inventor migration and international patent citations (abstract-level).
- **Methods:** Country-pair gravity model of cross-country patent citations, with instrumental variables and country-pair fixed effects.
- **Findings:** Abstract-level. Inventor migration robustly increases knowledge flows to home countries under IV and pair fixed effects. The effect on flows into host countries does not hold up. The effects matter mainly when sending countries are developing countries and for knowledge diffusion within multinationals.
- **Relevance here:** Shows that the knowledge payoff of migration is directional and concentrated in developing origins, which is relevant to SSA. Supports keeping direction (origin to destination) in the mobility and migrant-stock layers even though co-authorship is undirected, and testing for asymmetry in residuals.

### Ernest Miguélez (2018). Inventor Diasporas and the Internationalization of Technology
*The World Bank Economic Review 32(1): 41-63*. DOI: [10.1093/wber/lhw013](https://doi.org/10.1093/wber/lhw013) · **V1** (single-pass search match)

- **Question:** Do diasporas of highly skilled (inventor) migrants increase cross-country inventive collaboration (co-patenting) and R&D offshoring between their host and origin countries?
- **Data:** PCT patent applications. Inventors with a migrant background are used as a proxy for the skilled diaspora in each country pair.
- **Methods:** Gravity models of bilateral international co-patenting (inventor-inventor co-inventorship and applicant-inventor links). Earlier versions are GREThA WP 2014-12 and World Bank Policy Research WP 7619.
- **Findings:** Abstract-level: inventor diasporas are strongly and robustly associated with international co-patenting, and the effect shrinks as interactions become more formal (stronger for inventor-inventor co-inventorship than for applicant-inventor offshoring). The Chinese and Indian diasporas do not drive the results. The working-paper version reports that a 10% larger inventor diaspora is associated with 1.5-2.2% more international patent collaborations (not confirmed in the published version).
- **Relevance here:** The methodological template for including a skilled-diaspora stock in a PPML gravity model of bilateral knowledge collaboration. It is the patent analogue of our co-authorship model, and its contrast between skilled diaspora and general migration parallels our comparison of scholarly mobility with UN DESA migrant stocks.

### Henk F. Moed; M'hamed Aisati; Andrew Plume (2013). Studying scientific migration in Scopus
*Scientometrics 94(3): 929-942*. DOI: [10.1007/s11192-012-0783-9](https://doi.org/10.1007/s11192-012-0783-9) · **V1** (single-pass search match)

- **Question:** Can Scopus author profiles and affiliation linking be used to measure international scientific migration, and how do migration patterns relate to international co-authorship?
- **Data:** Scopus author-affiliation histories for five countries (Germany, Italy, Netherlands, UK, USA), 1999-2010.
- **Methods:** Bibliometric tracking of author affiliation changes, compared with co-authorship patterns between the same countries.
- **Findings:** Abstract-level: language similarity between countries is a more important factor in international migration than in international co-authorship. Example balances are given (the Netherlands had a positive migration balance with the UK and a negative one with Germany). A secondary search summary attributes to the paper the result that having international co-authors increases the probability of international movement (not confirmed in full text).
- **Relevance here:** Early direct evidence that migration and co-authorship respond differently to the same dyadic factors (language), which supports treating them as distinct layers and expecting misalignment. Its scholarly-migration measure is the methodological ancestor of the Akbaritabar et al. (2024) flows we use.

### Eustache Mêgnigbêto (2013). International collaboration in scientific publishing: the case of West Africa (2001-2010)
*Scientometrics 96(3): 761-783*. DOI: [10.1007/s11192-013-0963-2](https://doi.org/10.1007/s11192-013-0963-2) · **V1** (single-pass search match)

- **Question:** Who are West African countries' co-authorship partners, and how much do they collaborate with each other compared with African and non-African countries?
- **Data:** Web of Science publications with at least one author affiliated in any of the 15 West African countries, 2001-2010.
- **Methods:** Descriptive bibliometric co-authorship partner analysis.
- **Findings:** Abstract-level only. The main African partners are South Africa, Cameroon, Kenya and Tanzania. The main non-African partners are France, the USA and the UK, which together account for over 63% of papers with a non-West-African address. West African countries collaborate less with each other and with other African and developing countries than with developed countries.
- **Relevance here:** Gives expected collaboration-partner profiles for Ghana, Nigeria and Senegal (France/US/UK dominance and weak intra-regional ties) to compare with their UN DESA migrant-destination profiles, which are often more regional (ECOWAS corridors). This is a likely source of misalignment.

### Omwoyo Bosire Onyancha; Jan Resenga Maluleka (2011). Knowledge production through collaborative research in sub-Saharan Africa: how much do countries contribute to each other's knowledge output and citation impact?
*Scientometrics 87(2): 315-336*. DOI: [10.1007/s11192-010-0330-5](https://doi.org/10.1007/s11192-010-0330-5) · **V1** (single-pass search match)

- **Question:** How much do sub-Saharan African countries co-produce knowledge with each other, compared with partners outside the region, and what is the citation impact?
- **Data:** Publications and citations of sub-Saharan African countries (bibliometric database). Abstract-level only.
- **Methods:** Co-authorship (co-production) and citation counts by country pair.
- **Findings:** Abstract-level only. Collaboration among sub-Saharan African countries is minimal and contributes only a small share compared with collaboration with foreign partners. The authors recommend student and staff exchange, regional conferences and research networks.
- **Relevance here:** Documents weak intra-SSA co-authorship. Since a large share of SSA migrant stock stays within the region (e.g., Somalia to Kenya/Ethiopia, Uganda to Kenya), this predicts a structural gap between the migration layer and the knowledge layer for the focus origins.

### Jamal El Ouahi; Nicolás Robinson-García; Rodrigo Costas (2021). Analyzing scientific mobility and collaboration in the Middle East and North Africa
*Quantitative Science Studies 2(3): 1023-1047*. DOI: [10.1162/qss_a_00149](https://doi.org/10.1162/qss_a_00149) · **V1** (single-pass search match)

- **Question:** How do scientific mobility and international collaboration networks of MENA countries compare in structure and in partner affinity?
- **Data:** Bibliometric publication and affiliation data for MENA countries, 2008-2017. A dataset is archived on Zenodo (10.5281/zenodo.5155979). The arXiv preprint is 2009.07815.
- **Methods:** Country-level mobility and co-authorship networks, degree and affinity indicators, and comparison of the two layers.
- **Findings:** Abstract-level from search snippets: international co-authorship is more frequent than international mobility. The mobility network is thinner than the collaboration network in terms of affinity between countries. The hubs differ: Saudi Arabia has the highest degree in mobility, while Turkey has the highest in collaboration.
- **Relevance here:** A regional precedent (including North Africa) for comparing the partner structure of a mobility layer with a collaboration layer and finding non-alignment, methodologically parallel to our per-origin alignment and topology comparison. Like the other CWTS/Sugimoto studies, it uses only scholarly mobility and no general migrant stocks.

### Christopher Parsons, Pierre-Louis Vezina (2018). Migrant Networks and Trade: The Vietnamese Boat People as a Natural Experiment
*The Economic Journal 128(612):F210-F234*. DOI: [10.1111/ecoj.12457](https://doi.org/10.1111/ecoj.12457) · **V1** (single-pass search match)

- **Question:** Do migrant networks causally increase trade with their origin country?
- **Data:** Distribution of Vietnamese refugees across US states and US state-level exports to Vietnam after the trade embargo was lifted in 1994 (abstract-level). Working paper: IZA DP 10112.
- **Methods:** Natural experiment: refugee dispersal across US states during a trade embargo, followed by embargo removal.
- **Findings:** Abstract-level. After trade restrictions were lifted in 1994, US exports to Vietnam grew most in states with larger Vietnamese populations, which themselves resulted from larger refugee inflows about 20 years earlier.
- **Relevance here:** A causal benchmark showing that refugee-origin diasporas can create economic ties. That bears on whether refugee-driven stocks such as the Somali and Ethiopian diasporas translate into scientific ties, and it provides an identification template.

### Ruimin Pei, Langqiu Li, Yiying Yang, Quan Zhou (2024). Co-evolution of international scientific mobility and international collaboration: a Scopus-based analysis
*Scientometrics 129(7), 4353-4378*. DOI: [10.1007/s11192-024-05081-5](https://doi.org/10.1007/s11192-024-05081-5) · **V1** (single-pass search match)

- **Question:** How have international scientific mobility networks and international collaboration networks co-evolved, and how closely aligned are they across countries?
- **Data:** Scopus-derived country-level mobility and collaboration networks over a long period; one summary gives the start year as 1788, possibly a typo, ending in 2020.
- **Methods:** Network analysis of mobility (talent flow) and collaboration networks over time and their alignment. QAP correlation is not confirmed from what I saw.
- **Findings:** Abstract-level (fragments). The global flow and collaboration networks are increasingly interconnected. There is a 'Matthew effect': a few dominant countries and many minor participants. Advanced countries show closer alignment between their collaboration and mobility networks than lagging countries. The paper offers policy suggestions on mobility and engaging peripheral countries.
- **Relevance here:** Direct precedent for comparing the mobility and collaboration layers. Its finding of weaker alignment for lagging countries matches the project's hypothesis for Sub-Saharan origins. It does not appear to include general migrant stocks or origin-specific distributional divergence with nulls.

### Alexander M. Petersen (2018). Multiscale impact of researcher mobility
*Journal of the Royal Society Interface 15(146), 20180580*. DOI: [10.1098/rsif.2018.0580](https://doi.org/10.1098/rsif.2018.0580) · **V1** (single-pass search match)

- **Question:** What are the effects of cross-border researcher mobility on citation impact, topic diversity, collaboration and international integration?
- **Data:** American Physical Society journals 1980-2009; 26,170 disambiguated prominent researcher profiles (dataset on Dryad).
- **Methods:** Matching mobile researchers to similar non-mobile researchers on pre-move profile attributes, followed by a 10-year window around each move. Outcomes cover individual impact, co-author diversity, collaboration network churn and international integration, across three time periods.
- **Findings:** Abstract and summary level. Mobile researchers gain up to a 17% citation advantage, attributed to a simultaneous increase in co-author diversity. Researchers completely curtail prior collaborations with their source country in 11% of cross-border moves. Effects appear across scales, from careers to collaboration network churn to international integration, and virtual channels do not appear to replace physical mobility.
- **Relevance here:** One of the few studies that directly links a move to later co-authorship. Most movers keep ties to the origin country (only 11% fully curtail them), so the mobility layer should predict origin-destination co-authorship in both directions, while collaboration networks also churn after moves. It covers physics only, mostly in high-income systems.

### Anastassios Pouris; Yuh-Shan Ho (2014). Research emphasis and collaboration in Africa
*Scientometrics 98(3): 2169-2184*. DOI: [10.1007/s11192-013-1156-8](https://doi.org/10.1007/s11192-013-1156-8) · **V1** (single-pass search match)

- **Question:** Which disciplines does African research emphasize, and what are African collaboration patterns at country and continental level?
- **Data:** African publications (bibliometric database). Abstract-level only.
- **Methods:** Co-authorship analysis at country and continental level, plus disciplinary profiling.
- **Findings:** Abstract-level only. Collaboration rates in Africa are substantially higher than in the rest of the world. Research emphasis leans toward medical and natural-resource disciplines rather than fields supporting knowledge-based economies.
- **Relevance here:** The very high international co-authorship share of African output means OpenAlex co-authorship edges for focus origins are dense and partner-heavy. This matters for null-model design and for full versus fractional counting. The medical emphasis suggests field-specific partner structures (e.g., global health funders).

### Nicolas Robinson-Garcia, Cassidy R. Sugimoto, Dakota Murray, Alfredo Yegros-Yegros, Vincent Lariviere, Rodrigo Costas (2019). The many faces of mobility: Using bibliometric data to measure the movement of scientists
*Journal of Informetrics 13(1), 50-63*. DOI: [10.1016/j.joi.2018.11.002](https://doi.org/10.1016/j.joi.2018.11.002) · **V1** (single-pass search match)

- **Question:** How can publication affiliation data be used to build a typology and indicators of scientific mobility?
- **Data:** About 16 million authors in Web of Science, 2008-2015 (arXiv preprint 1803.03449).
- **Methods:** A typology of mobility based on affiliation sequences. 'Migrants' break ties with their origin country. 'Travelers' add foreign affiliations while keeping origin ties, and are split into directional and non-directional. Country-level incoming and outgoing classifications are also built.
- **Findings:** Abstract-level. About 3.7% of authors were mobile. Travelers make up most mobile scholars (72.7% per one summary), but migrants have higher scientific impact; impact ranks migrants first, then directional travelers, non-directional travelers and non-mobile researchers.
- **Relevance here:** Key for interpreting the Akbaritabar flows. Multiple and concurrent affiliations ('travelers') sit on the boundary between mobility and collaboration. A traveler with a home affiliation and a foreign affiliation produces co-authorship-like cross-country links, so the scholarly mobility layer and the co-authorship layer are not independent. The paper's directional typology supports treating origin-to-destination direction explicitly rather than symmetrising.

### AnnaLee Saxenian (2005). From Brain Drain to Brain Circulation: Transnational Communities and Regional Upgrading in India and China
*Studies in Comparative International Development 40(2):35-61*. DOI: [10.1007/BF02686293](https://doi.org/10.1007/BF02686293) · **V1** (single-pass search match)

- **Question:** How are Indian and Chinese immigrant engineers and entrepreneurs in Silicon Valley influencing economic development in their home regions?
- **Data:** Qualitative evidence on transnational technical communities, returnees and cross-border venture capital (abstract-level; author's pre-print hosted at Berkeley).
- **Methods:** Comparative qualitative and case-study analysis.
- **Findings:** Abstract-level. Transnational communities of Indian and Chinese skilled migrants, including returnees, link Silicon Valley with their home regions and help upgrade them technologically. This shifts the pattern from one-way brain drain to two-way brain circulation.
- **Relevance here:** The source of the brain circulation concept. It suggests that the relevant knowledge layer is circulation (mobility and return), not static stocks. That supports treating Akbaritabar mobility flows as distinct from UN DESA stocks.

### Giuseppe Scellato; Chiara Franzoni; Paula Stephan (2015). Migrant scientists and international networks
*Research Policy 44(1): 108-120*. DOI: [10.1016/j.respol.2014.07.014](https://doi.org/10.1016/j.respol.2014.07.014) · **V2** (independently re-verified)

- **Question:** Do foreign-born (migrant) scientists have more international research collaborations than non-migrants and returnees, and do they keep collaborating with their country of origin?
- **Data:** GlobSci survey (2011) of scientists working in 16 countries, comparing foreign-born, native non-mobile, and returnee scientists. An earlier version is NBER WP 18613 (2012), 'Mobile Scientists and International Networks'.
- **Methods:** Survey-based econometric comparison of collaboration patterns by migration status and by where the PhD was obtained.
- **Findings:** Abstract-level: migrants are more likely to collaborate internationally, mainly those who did their PhD abroad and came to the destination for a postdoc or a job. A sizeable share of the foreign-born collaborate with researchers in their country of origin (a 'diaspora effect'). Migrants from a relatively stronger science base have superior networks to those from a weaker one.
- **Relevance here:** Individual-level micro-foundation for a migrant-to-origin co-authorship link. The result that network benefits depend on the origin's science base implies that for weak-science-base origins (many SSA focus countries) migrant destinations may not translate into collaboration partners, which is the mismatch hypothesis. Useful for interpreting PPML coefficients on migrant stocks by origin capacity.

### M. Ángeles Serrano, Marián Boguñá, Alessandro Vespignani (2009). Extracting the multiscale backbone of complex weighted networks
*Proceedings of the National Academy of Sciences 106(16):6483-6488*. DOI: [10.1073/pnas.0808904106](https://doi.org/10.1073/pnas.0808904106) · **V1** (single-pass search match)

- **Question:** How can the relevant backbone of a large, heterogeneous weighted network be extracted without a global weight threshold that discards small-scale but locally important links?
- **Data:** Real-world weighted networks, including a food web (abstract-level; full list not checked).
- **Methods:** Disparity filter: under a local null model, each node's strength is spread uniformly at random over its edges. An edge is kept if its normalized weight is significantly larger than this null at significance level alpha, for at least one endpoint. Compared with global thresholding and other backbone methods.
- **Findings:** Abstract-level: the filter keeps locally significant edges at all scales of the weight distribution, does not penalize small-scale interactions, and reportedly beats global thresholding at keeping structure while shrinking the network.
- **Relevance here:** Useful for building comparable backbones of the migration, mobility and co-authorship layers. Weights differ by orders of magnitude between South Africa/Nigeria and Somalia/Rwanda, so a local, strength-normalized filter avoids backbones that only show large origins. Alpha sensitivity should be reported.

### Paolo Sgrignoli, Rodolfo Metulini, Stefano Schiavo, Massimo Riccaboni (2015). The relation between global migration and trade networks
*Physica A: Statistical Mechanics and its Applications 417:245-260*. DOI: [10.1016/j.physa.2014.09.037](https://doi.org/10.1016/j.physa.2014.09.037) · **V1** (single-pass search match)

- **Question:** Does global migration increase bilateral trade, and for which product categories?
- **Data:** Global bilateral migration and trade networks, including product-level trade (abstract-level). Preprint: arXiv:1310.3716; IMT Lucca EIC WP 6/2013.
- **Methods:** A hypergeometric network filter isolates links where both migration and trade exceed their expected values given node totals, followed by spatial-econometric estimation.
- **Findings:** Abstract-level. Migration increases trade between countries, and the authors identify product categories where the effect is strongest.
- **Relevance here:** The hypergeometric filter is a margin-preserving null that applies directly to the planned observed-versus-expected residual analysis. It can identify country pairs over-represented in both the migration layer and the co-authorship layer.

### J. M. C. Santos Silva, Silvana Tenreyro (2006). The log of gravity
*Review of Economics and Statistics 88(4):641-658*. DOI: [10.1162/rest.88.4.641](https://doi.org/10.1162/rest.88.4.641) · **V1** (single-pass search match)

- **Question:** Are elasticities from log-linearized gravity equations estimated by OLS consistent, and if not, what estimator should be used?
- **Data:** Bilateral trade data, with an Anderson-van Wincoop gravity specification as the application (abstract-level).
- **Methods:** Shows analytically (via Jensen's inequality) that under heteroskedasticity OLS on log-linearized models is inconsistent for the elasticities, and proposes the Poisson pseudo-maximum-likelihood (PPML) estimator on levels.
- **Findings:** Abstract-level: log-linearized OLS gives biased elasticities under heteroskedasticity. In the application, OLS overstates the role of geographic distance, with the log-linear distance elasticity almost twice the PPML (levels) estimate.
- **Relevance here:** The foundational justification for estimating the co-authorship gravity model by PPML on counts, not OLS on log(1+y). This matters given the many zero or small co-authorship counts and heteroskedastic errors for SSA dyads.

### Tiziano Squartini, Diego Garlaschelli (2011). Analytical maximum-likelihood method to detect patterns in real networks
*New Journal of Physics 13:083001*. DOI: [10.1088/1367-2630/13/8/083001](https://doi.org/10.1088/1367-2630/13/8/083001) · **V1** (single-pass search match)

- **Question:** How can null-model expectations for network properties be obtained analytically and without bias, instead of by sampling randomized networks?
- **Data:** Real binary and weighted networks (abstract-level; applications include degree correlations and clustering in binary undirected networks).
- **Methods:** Maximum-entropy ensembles constrained on chosen local properties (degrees, strengths), with parameters fitted by maximum likelihood. Gives analytical expectations and standard deviations for topological properties in binary/weighted and directed/undirected networks.
- **Findings:** Abstract-level: gives exact expectations and standard deviations without generating randomized graphs. The authors argue that common quantities such as modularity rest on incorrect null expressions and supply corrected ones.
- **Relevance here:** The analytical basis for degree- and strength-preserving nulls (for example a weighted configuration model) for each layer. Observed edge overlap, reciprocity, clustering and per-origin partner distributions can then be expressed as z-scores, not compared raw across layers of different density.

### Cassidy R. Sugimoto, Nicolas Robinson-Garcia, Dakota S. Murray, Alfredo Yegros-Yegros, Rodrigo Costas, Vincent Lariviere (2017). Scientists have most impact when they're free to move
*Nature 550(7674), 29-31 (Comment)*. DOI: [10.1038/550029a](https://doi.org/10.1038/550029a) · **V1** (single-pass search match)

- **Question:** How common is international researcher mobility, and how is mobility associated with citation impact across countries and regions?
- **Data:** Web of Science papers 2008-2015: about 14 million papers and about 16 million authors, with mobility inferred from changes in country of affiliation.
- **Methods:** Authors are classified as non-mobile or mobile depending on whether their affiliation country changed during the window. Citation impact is compared between mobile and non-mobile authors by country and region.
- **Findings:** From secondary and press summaries; I did not see the full text. About 96% of authors were non-mobile and about 4% mobile. Mobile scholars had about 40% higher citation rates on average than non-mobile ones, with the advantage varying by region (about 10.8% for North Americans). The authors argue that restricting circulation harms science. Commentators note the result is correlational, since selection into mobility is not ruled out.
- **Relevance here:** This is the founding paper of the WoS-based mobility indicator programme and the companion to Wagner & Jonkers. It shows that bibliometric mobility covers a small, selective share of researchers, which helps explain why the scholarly mobility layer can diverge from general migrant stocks. It does not model co-authorship partner distributions.

### Claudia Noumedem Temgoua (2018). Highly skilled migration and the internationalization of knowledge
*Cahiers du GREThA (Université de Bordeaux) Working Paper n° 2018-16*. Link: https://econpapers.repec.org/RePEc:grt:wpegrt:2018-16 · **U** (unverified / no DOI)

- **Question:** Do Chinese and Indian highly skilled diasporas foster international knowledge networks (co-authorship and co-inventorship) among OECD destination countries?
- **Data:** OECD destination-country pairs, with bilateral co-authorship (publications) and co-inventorship (patents) and highly skilled diaspora stocks by origin (China, India; also Vietnam, Pakistan, Iran).
- **Methods:** Gravity model at the country-pair level. The search summary of the working paper text describes PPML estimation with co-authorship and co-inventorship as dependent variables, controlling for other migration variables.
- **Findings:** Abstract-level: OECD country pairs hosting sizeable portions of the Indian or Chinese highly skilled diaspora collaborate more on publications and patents, after controlling for other migration variables. Smaller diasporas (Vietnam, Pakistan, Iran) produce similar effects on co-authorship and co-inventorship.
- **Relevance here:** The closest precedent found for component (b): a PPML gravity model of bilateral co-authorship that separates a skilled-diaspora variable from other migration controls. Its dyads are destination-destination pairs linked by a shared third-country diaspora, whereas ours are origin-destination pairs with SSA origins, and it does not use bibliometric scholarly mobility. Journal publication status is unknown.

### Robert J. W. Tijssen (2007). Africa's contribution to the worldwide research literature: New analytical perspectives, trends, and performance indicators
*Scientometrics 71(2): 303-327*. DOI: [10.1007/s11192-007-1658-3](https://doi.org/10.1007/s11192-007-1658-3) · **V1** (single-pass search match)

- **Question:** How large is Africa's research output and how has it changed (1980-2004) in international and national/regional journals, and what do co-publication patterns show?
- **Data:** Research publications by Africa-based authors, 1980-2004, in international journals (Web of Science) and in national and regional journals.
- **Methods:** Descriptive scientometric trend and performance indicators, including international co-publication shares.
- **Findings:** Abstract-level only. Africa's share of worldwide science in international journals declined steadily over the period, while international co-publication grew considerably.
- **Relevance here:** Historical baseline showing African science becoming more internationally co-authored while its global share shrank. This makes partner choice (former colonial powers, the US, South Africa) central to comparing collaboration partners with migrant destinations.

### Luca Verginer, Massimo Riccaboni (2021). Talent goes to global cities: The world network of scientists' mobility
*Research Policy 50(1), 104127*. DOI: [10.1016/j.respol.2020.104127](https://doi.org/10.1016/j.respol.2020.104127) · **V1** (single-pass search match)

- **Question:** How is the world network of scientists' mobility structured at city level, and do global cities attract and retain the most productive scientists?
- **Data:** Disambiguated author publication histories at city level. The full-text PDF describes 3.7 million authors and 7,159 cities; another summary says about 2 million researchers and more than 2,000 cities over a decade. The source database is not confirmed from what I saw.
- **Methods:** Construction of a city-level mobility network and analysis of the centrality of global cities, plus the productivity of scientists they attract and retain.
- **Findings:** Abstract and full-text fragments. Global cities attract and retain the most productive scientists, benefiting from their central position in the international mobility network by attracting and retaining prolific scientists early in their careers.
- **Relevance here:** Shows that scholarly mobility concentrates on a few hubs, which matters for the multilayer topology comparison and for strength-preserving nulls, since hub concentration may differ from the more diffuse geography of general migrant stocks. City-level work also warns that country aggregation hides within-country concentration.

### Caroline S. Wagner; Loet Leydesdorff (2005). Network structure, self-organization, and the growth of international collaboration in science
*Research Policy 34(10): 1608-1618*. DOI: [10.1016/j.respol.2005.08.002](https://doi.org/10.1016/j.respol.2005.08.002) · **V1** (single-pass search match)

- **Question:** Why has international co-authorship grown so fast, and is the growth better explained by network self-organization (preferential attachment) than by national policy or funding?
- **Data:** International co-authorship links between countries, built from bibliometric (ISI/Web of Science) records. Abstract-level only; the exact years were not checked.
- **Methods:** Network analysis of the country co-authorship network, including degree distributions and tests of preferential attachment / self-organization.
- **Findings:** Abstract-level only. The authors describe international collaboration as a self-organizing network whose growth follows network dynamics (preferential attachment to well-connected countries) more than national or institutional incentives.
- **Relevance here:** This is the standard framing of the country-level co-authorship layer as a self-organizing network. It explains why the knowledge layer may follow its own core-periphery logic rather than the migration layer, which motivates the degree/strength-preserving null models and the multilayer topology comparison.

### Caroline S. Wagner; Han Woo Park; Loet Leydesdorff (2015). The continuing growth of global cooperation networks in research: A conundrum for national governments
*PLoS ONE 10(7): e0131816*. DOI: [10.1371/journal.pone.0131816](https://doi.org/10.1371/journal.pone.0131816) · **V1** (single-pass search match)

- **Question:** How has the global network of international co-authorship evolved, and what does its growth mean for national science policy?
- **Data:** Internationally co-authored publications between countries over about two decades (bibliometric database). Abstract-level only.
- **Methods:** Network analysis of country co-authorship networks over time.
- **Findings:** Abstract-level only. The share of internationally co-authored papers has more than doubled in 20 years and accounts for the output growth of advanced countries. The network acts as a new organization alongside national systems. Emerging countries, especially China, are participating more. International collaboration does not appear to threaten national science and may improve its quality.
- **Relevance here:** Background on the growth and densification of the co-authorship layer. Its claim that the network is a supranational structure supports testing whether co-authorship partners diverge from migration corridors.

### Caroline S. Wagner, Koen Jonkers (2017). Open countries have strong science
*Nature 550(7674), 32-33 (Comment)*. DOI: [10.1038/550032a](https://doi.org/10.1038/550032a) · **V1** (single-pass search match)

- **Question:** Is a country's openness to international engagement, through collaboration and researcher mobility, associated with the impact of its science?
- **Data:** Country-level indicators for a set of leading scientific countries: share of internationally co-authored papers and researcher mobility (inflows and outflows), plus citation impact.
- **Methods:** Construction of an openness index combining international collaboration and mobility, and correlation of openness with citation impact. A 2018 follow-up ('Openness and Impact of Leading Scientific Countries', arXiv 1810.07812) extends it.
- **Findings:** From secondary sources and the follow-up. There is a clear correlation between a nation's scientific influence and its links with foreign researchers: more open countries produce higher-impact science. The follow-up warns that the correlation does not imply all countries have equal potential to open up, and that results do not extend to unanalysed countries.
- **Relevance here:** Treats collaboration and mobility as two parts of one openness construct, a framing the project questions. It covers only leading countries, not Sub-Saharan Africa, so its pooling of mobility and collaboration may not hold for peripheral origins.

### Ludo Waltman; Nees Jan van Eck (2015). Field-normalized citation impact indicators and the choice of an appropriate counting method
*Journal of Informetrics 9(4): 872-894*. DOI: [10.1016/j.joi.2015.08.001](https://doi.org/10.1016/j.joi.2015.08.001) · **V1** (single-pass search match)

- **Question:** Which counting method (full or fractional, and which fractional variant) gives properly field-normalized indicators for countries and organizations?
- **Data:** Web of Science publications and citations (CWTS); also arXiv:1501.04431. Abstract-level only.
- **Methods:** Theoretical argument plus empirical comparison of full counting and several fractional counting variants.
- **Findings:** Abstract-level only. Full counting does not give properly field-normalized results, while fractional counting does. The authors recommend fractional counting for field-normalized studies, especially at country and organization level.
- **Relevance here:** Shapes how the OpenAlex co-authorship edges are weighted: full counts of papers per dyad versus fractional/author-share weights. The choice changes gravity estimates and partner distributions, especially for small African systems with very high international co-authorship shares. Both should be run as a robustness check.

### Xinyi Zhao, Samin Aref, Emilio Zagheni, Guy Stecklov (2022). Return migration of German-affiliated researchers: analyzing departure and return by gender, cohort, and discipline using Scopus bibliometric data 1996-2020
*Scientometrics 127(12), 7707-7729*. DOI: [10.1007/s11192-022-04351-4](https://doi.org/10.1007/s11192-022-04351-4) · **V1** (single-pass search match)

- **Question:** Who among researchers who leave Germany returns, and how does return vary by gender, cohort, discipline, destination and continued collaboration with German-affiliated researchers?
- **Data:** Scopus: about 8 million publications by about 1.1 million researchers who published at least once with a German affiliation, 1996-2020 (arXiv 2110.08340).
- **Methods:** Bibliometric identification of departure and return events from affiliation histories, with descriptive cohort analysis and models of return propensity including collaboration ties to Germany while abroad.
- **Findings:** Abstract-level. Return migration declines slightly in more recent cohorts, which for most disciplines coincides with fewer German collaboration ties. Women who leave are less likely than men to return. Keeping collaborations with German-affiliated researchers while abroad has a moderate positive association with return. Per a Population Europe digest, those who moved to high R&D-spending countries were less likely to return.
- **Relevance here:** Evidence that collaboration ties with the origin persist after emigration and predict return, so knowledge links run in both directions along migration corridors. It supports modelling both directions of mobility and treating origin-destination co-authorship as partly a diaspora tie. It is a single-origin case in a high-income country.

### Çağlar Özden, Christopher R. Parsons, Maurice Schiff, Terrie L. Walmsley (2011). Where on Earth is Everybody? The Evolution of Global Bilateral Migration 1960-2000
*The World Bank Economic Review 25(1):12-56*. DOI: [10.1093/wber/lhr024](https://doi.org/10.1093/wber/lhr024) · **V1** (single-pass search match)

- **Question:** What do complete global bilateral migrant-stock matrices look like for 1960-2000, and how has global migration evolved?
- **Data:** More than 1,000 census and population-register records, used to build bilateral migrant-stock matrices for 1960, 1970, 1980, 1990 and 2000, disaggregated by gender, mainly on a foreign-born definition.
- **Methods:** Harmonization of census and register data, with imputation and estimation to fill missing bilateral cells and reconcile definitions.
- **Findings:** Abstract-level: the global migrant stock rose from 92 million (1960) to 165 million (2000). Migration between developing countries was about half of all international migration in 2000, and developing-to-developed migration was the fastest-growing component. The US hosted about one fifth of the world's migrants.
- **Relevance here:** The methodological precursor of current bilateral stock data (the UN DESA estimates build on similar census-based harmonization). It documents that bilateral stocks are destination-census-based and partly imputed, which matters for SSA origins with large intra-African (south-south) migration that knowledge-network layers may not reflect.
