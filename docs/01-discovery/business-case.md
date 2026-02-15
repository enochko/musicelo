# Business Case: MusicElo v3.0

**Project:** MusicElo v3.0 — Personal Music Ranking and Discovery System
**Date:** February 2026
**Author:** Enoch Ko
**Stage:** Discovery and Problem Definition
**Version:** 1.0

---

## Executive Summary

MusicElo v3.0 is a personal music ranking and discovery system that solves the problem of transparently understanding and organising music preferences within large catalogues. While primarily a personal tool, the project serves strategic career development goals by demonstrating product management, software engineering, data science, and AI-assisted development capabilities to potential employers and professional stakeholders.

**Primary Value:** Personal utility in music organisation and preference understanding
**Secondary Value:** Portfolio demonstration of product thinking and technical execution
**Tertiary Value:** Foundation for potential future open-source contribution

---

## Strategic Alignment

### Personal Goals

**Immediate (2026):**

- Solve genuine personal frustration with music ranking
- Create a transparent alternative to opaque streaming recommendations
- Develop a systematic approach to preference quantification
- Demonstrate effective use of AI to enhance software product development

**Medium-term (2026–2027):**

- Build a portfolio project demonstrating end-to-end product development
- Practise product management principles in a real-world context
- Document software engineering best practices
- Create a shareable case study for professional networking

**Long-term (2027–2028):**

- Potential open-source contribution to the music tech community
- Foundation for data science capstone project (if aligned with interests)
- Demonstration of systems thinking for career advancement

### Professional Development Objectives

**Skills to Demonstrate:**

1. **Product Management:** Discovery, problem definition, requirements gathering, stakeholder analysis
2. **Software Engineering:** System design, API integration, algorithm implementation, documentation
3. **Data Science:** Glicko-2 algorithm application, similarity detection, preference modelling
4. **Project Management:** Structured development process, artefact creation, iterative improvement
5. **AI-Assisted Development:** Effective use of AI to enhance software product development

**Target Audiences:**

- Potential employers (demonstrating product thinking beyond current IT/accounting role)
- Current employer leadership (showing initiative and structured problem-solving)
- Academic advisors (foundation for potential thesis/capstone work)
- Professional network (showcasing technical depth)

---

## Problem Worth Solving

### User Impact

**Current State:**

- Persistent frustration with inability to definitively rank favourites from a 300+ song catalogue
- Reliance on opaque recommendation systems without understanding reasoning or context
- Playlists become disorganised due to lack of time and mental bandwidth for systematic curation
- Improved playlist quality valued over time savings — the issue is quality, not time

**Emotional Value:**

- Confidence in expressing music preferences
- Satisfaction from data-driven self-understanding
- Joy of rediscovering forgotten gems
- Enhanced listening experience through better playlists
- "Passive curation" — emotional enjoyment from music organisation without dedicated effort

### Market Context (Future Consideration)

The broader problem space includes music streaming users who lack transparency into recommendation algorithms, K-pop fandoms that engage deeply with artist catalogues, and quantified self enthusiasts who seek data ownership and understanding. These represent potential future audiences but are not the current scope.

---

## Expected Value and ROI

### Personal ROI

**Time Investment:**

| Phase | Estimated Hours |
|-------|----------------|
| Discovery and Planning | 20 hours ✓ |
| Development (MVP) | 60–80 hours |
| Documentation | 20 hours |
| **Total** | **~100–120 hours over 6–9 months** |

**Non-Time Value:**

- Enhanced listening satisfaction (unquantified but significant)
- Systematic understanding of personal preferences
- Reduced decision fatigue around music choices
- Portfolio asset with multi-year professional relevance
- Personal relevance and satisfaction extending years to decades

**ROI Assessment:** Payback on time alone is unlikely to be meaningful. True value comes from emotional enjoyment during time not spent curating, plus portfolio impact — making ROI positive within 1–2 years professionally. Personal relevance extends well beyond that.

### Professional ROI

**Career Development Value:**

- Differentiates profile with product thinking beyond current IT/accounting role
- Demonstrates end-to-end ownership and execution
- Portfolio piece for Product Manager or Data Scientist roles post-Masters
- Conversation starter in interviews and networking

**Estimated Career Impact:**

- Potential salary uplift from PM-capable data science role: $10–20K AUD
- Interview conversion improvement: 10–20% (tangible product demonstration)
- Professional credibility enhancement: Moderate to High

**Portfolio Value:** Reusable across multiple contexts (technical blog, GitHub, LinkedIn). Demonstrates skills beyond academic coursework, shows initiative and intrinsic motivation. Professional longevity of 3–5 years; personal longevity of years to decades.

---

## Portfolio Gap Analysis

### Current Portfolio Status

- No formal computer science, software engineering, or product management training
- No shareable programming projects (all employer work is on employer systems)
- Data science capabilities from degree program not yet demonstrated

### What MusicElo v3.0 Fills

- **Product Management:** End-to-end discovery, definition, requirements, stakeholder analysis
- **Software Engineering:** Full-stack development, API integration, cross-platform architecture
- **Data Science:** Applied statistical algorithm (Glicko-2), preference modelling, historical evolution tracking
- **Real-world impact:** Personal utility project, not just an academic exercise
- **AI-Assisted Development:** Effective collaboration with AI for development

**Differentiation:** Typical data science portfolios feature ABS data, Kaggle competitions, or sports analytics. MusicElo uses personal data with actual user impact, combining product thinking with technical execution and demonstrating initiative beyond coursework requirements.

---

## Opportunity Costs

### What This Project Competes With (2026)

- Full-time employment
- Part-time university (Master of Data Science)
- Physical health (exercise routine)
- Korean language learning

**Trade-off decisions:** Korean language lessons reduced to maintenance level until next break period. Extended timeline accepted if coursework demands increase. Project treated as an iterative side project, not deadline-driven.

---

## Risks and Constraints

### Technical Risks

**Spotify API Restriction Risk (Medium–High):** Spotify's February 2026 [Development Mode changes](https://developer.spotify.com/blog/2026-02-06-update-on-developer-access-and-platform-security) impose new constraints: Premium account required, one Client ID, and a maximum of five authorised users. Several endpoints were deprecated in November 2024 and February 2026 (audio features, artist top tracks, artist popularity scores). However, core MusicElo requirements remain supported: playlist read/write, track metadata (including ISRC), playback control, album/artist catalogue browsing, and search. The five-user limit is acceptable for a personal project.
- Mitigation: validate specific endpoint availability during Phase 1; if critical endpoints are further restricted, YouTube Music becomes the primary platform with MusicBrainz for metadata.

**Note on Apple Music:** Some developers have [suggested Apple Music as a more stable API platform](https://old.reddit.com/r/spotify/comments/1qz1g6o/approximately_20005000_spotify_apps_are_about_to/o47om2t/) given Spotify's direction. Apple Music's MusicKit API offers comprehensive library and playback access but requires a paid Apple Developer Program account ($99 USD/year) and an Apple Music subscription. This is a design-phase consideration — the cost and platform switch are not justified at this stage given that Spotify's core endpoints still serve MusicElo's needs.

**Data Availability Risk (Medium):** Spotify/YouTube Music APIs may not export needed metrics (play counts, skip rates, listening history). Embedded player interaction may not be available for comparison UI during playback.
- Mitigation: start with available data (Favourites playlist, Liked Songs), expand as APIs permit.
- Fallback: focus on manual comparison inputs if passive learning is blocked.

**Algorithm Complexity Risk (Low–Medium):** Glicko-2 implementation may be more complex than anticipated.
- Mitigation: use existing open-source implementations or self-implement from the public domain algorithm at glicko.net.
- Fallback: simpler Elo algorithm if Glicko-2 proves too complex.

**Scalability Risk (Low):** Performance with 1,000+ song library may degrade. Not critical for personal use; optimise only if needed.

### Project Risks

**Scope Creep Risk (Medium–High):** Feature ideas may expand beyond MVP (multi-user support, social features, advanced analytics).
- Mitigation: strict adherence to v3.0 scope; document future ideas in a v4.0 backlog. Portfolio value comes from completion, not feature breadth.

**Time Commitment Risk (Medium):** Masters coursework may compete for attention; cross-platform development increases development time.
- Mitigation: treat as iterative side project. Extended timeline acceptable; completion more important than speed.

**Motivation Risk (Low–Medium):** Loss of interest if initial results don't meet expectations; v2 failure memory may impact confidence.
- Mitigation: set minimum viable success criteria; celebrate incremental wins; 90/10 passive/active design addresses v2 UX failures. Even incomplete project demonstrates product thinking. Can pause or abandon at any phase — sunk cost acceptable.

---

## Success Metrics

### Personal Success Criteria

**Tier 1 — Minimum Viable Success:**

- [ ] Can rank top 50 TWICE songs with >80% intuitive agreement
- [ ] System successfully answers "what's my favourite song?" with confidence
- [ ] Rankings are transparent (audit trail of comparisons and listening history)
- [ ] 90% passive / 10% active input balance achieved

**Tier 2 — Expected Success:**

- [ ] Passive learning from playlists successfully infers preferences
- [ ] Forgotten favourite songs discovered
- [ ] Generated playlists feel more coherent than platform shuffle or existing playlists
- [ ] Cross-platform functionality works on both desktop and mobile

**Tier 3 — Exceptional Success:**

- [ ] Cross-artist ranking beyond the TWICE ecosystem
- [ ] Emotional journey playlist generation works reliably
- [ ] System becomes primary music player
- [ ] Historical ranking tracking shows preference evolution (monthly snapshots)
- [ ] Intra-playlist scoring enables effective promotion/relegation workflow

### Professional Success Criteria

**Portfolio Quality:**

- [ ] Comprehensive documentation suitable for case study
- [ ] Code quality demonstrates engineering best practices
- [ ] Clear articulation of product thinking and decision rationale

**Skill Demonstration:**

- [ ] Problem definition artefacts meet PM standards
- [ ] Technical implementation shows data science and engineering integration
- [ ] Effective AI-assisted development demonstrated throughout
- [ ] Cross-platform architecture demonstrates full-stack capability

**Visibility:**

- [ ] GitHub repository with clear README and documentation
- [ ] LinkedIn post or blog article explaining project
- [ ] Included in job applications and interview discussions

---

## Minimum Completion Criteria

If the project must be abandoned at any phase, minimum for portfolio value:

1. **Product design artefacts** (problem statement, user research, business case, stakeholder analysis) ✓
2. **Technical architecture design** (system design, data model, API integration plan)
3. **Algorithm implementation and validation** (Glicko-2 working with sample dataset)

Even without full UI/UX or deployment, these artefacts demonstrate product thinking, technical architecture capability, statistical algorithm application, and end-to-end problem-solving approach.

---

## Alternatives Considered

### Alternative 1: Use Existing Tools (Rejected)

Options included Spotify's algorithm, YouTube Music recommendations, manual spreadsheet ranking, and Apple Music smart playlists. None provide transparency, comparative ranking, passive learning from usage patterns, or portfolio value.

### Alternative 2: Wait for Streaming Platform Improvements (Rejected)

Spotify and YouTube Music may eventually add transparency features, but the timeline is uncertain. This approach doesn't address the portfolio development goal and loses personal agency and customisation.

### Alternative 3: Simpler Personal Rating System (Considered)

A simple 1–10 rating per song with manual playlist organisation. Rejected because it doesn't solve the comparative ranking challenge (all TWICE songs are "8–9" — they all feel good in different ways), offers no passive learning, and provides minimal technical demonstration. Retained as a potential fallback if Glicko-2 proves too complex.

### Alternative 4: Focus Only on Playlist Generation (Rejected)

Skip ranking entirely and focus on similarity detection and emotional journey playlists. Rejected because it doesn't solve the "what's my favourite song?" problem, provides a less clear portfolio narrative, and requires a ranking foundation for playlist quality anyway.

---

## Investment and Resources

### Financial Investment

**Direct Costs:**

- Spotify Premium subscription (if needed): ~$12/month × 6 months = $72 AUD
- Cloud hosting (if chosen over local): $10–20/month × 6 months = $60–120 AUD

**Total financial: ~$0–192 AUD** (minimal)

**Opportunity Costs:** Estimated ~$5,000 AUD (120 hours × ~$40/hour opportunity cost)

**Net Investment:** Primarily time-based; minimal financial outlay.

### Technical Resources Required

- Python development setup (already available)
- Cross-platform development tools
- API credentials: Spotify Developer, YouTube Music, MusicBrainz (free tier)
- Version control: GitHub
- Libraries: Glicko-2 implementation (open-source or self-implemented from public domain), Spotify API wrapper, YouTube Music API client, MusicBrainz API client, data analysis stack (pandas, numpy)
- Infrastructure: Local development (primary); optional cloud hosting for mobile access

---

## Decision Recommendation

### Proceed with MusicElo v3.0 Development

**Rationale:**

1. **Genuine Problem:** Solves real personal frustration with clear success criteria.
2. **Strategic Value:** Portfolio asset with multi-year professional benefit.
3. **Manageable Scope:** 100–120 hours over 6–9 months is feasible alongside coursework.
4. **Low Risk:** Minimal financial investment; time risk mitigated by iterative approach.
5. **Learning Opportunity:** Integrates product management, engineering, data science, and AI-assisted development.
6. **v2 Lessons Applied:** 90/10 passive/active design addresses previous UX failures.

**Conditions for Success:**

- Maintain strict scope discipline (defer v4.0 features to backlog)
- Prioritise MVP completion over feature richness
- Document process for portfolio value regardless of technical outcome
- Accept extended timeline if coursework demands increase
- Implement optional features only if straightforward to build

**Go/No-Go Criteria:**

- **GO if:** Spotify API allows playlist read/write and track metadata access in Development Mode ✓ (confirmed — core playlist and track endpoints survive February 2026 changes)
- **GO if:** Glicko-2 library exists or self-implementation is feasible ✓
- **GO if:** MusicBrainz API provides adequate TWICE discography metadata
- **GO if:** Cross-platform framework available for desktop + mobile development
- **WATCH:** Spotify API endpoint availability — further restrictions may require pivoting metadata source to MusicBrainz or reconsidering Apple Music
- **PAUSE if:** Masters workload exceeds 25 hours/week consistently
- **CANCEL if:** Personal interest wanes after any phase (sunk cost acceptable)

---

## Next Steps

### Immediate (Next 2 Weeks)

1. Complete foundational research artefacts ✓
2. Validate Spotify API availability under new Development Mode restrictions (confirm playlist, track metadata, ISRC, and playback endpoints function as expected)
3. Validate YouTube Music and MusicBrainz API data availability
4. Research Glicko-2 Python implementations
5. Define technical architecture and data model

### Phase 1 (Weeks 3–6)

1. Set up development environment and API credentials
2. Build basic data import pipeline from Spotify
3. Implement canonical song identification and deduplication
4. Implement Glicko-2 ranking with 5-level comparison system
5. Prototype cross-platform architecture

### Phase 2 (Months 2–4)

1. Build comparison input interface (desktop + mobile)
2. Implement passive learning from playlist structure
3. Develop basic playlist generation with export
4. Implement monthly historical snapshot system
5. User testing and refinement

### Phase 3 (Months 5–6)

1. Documentation and code cleanup
2. Portfolio case study writeup
3. GitHub repository publication
4. Professional sharing

---

## Appendix: Value Frameworks

### Kano Model Analysis

**Basic Needs (Must-Have):** Transparent ranking of TWICE songs; ability to answer "what's my favourite song?"; 90/10 passive/active input balance; cross-platform support.

**Performance Needs (Linear Value):** Accuracy of rankings vs. intuition; playlist generation quality; playback reliability on both platforms.

**Excitement Needs (Delighters):** Emotional journey playlist generation; cross-artist ranking beyond the TWICE ecosystem; passive learning that "just works"; historical ranking evolution tracking; visual memory association metadata; intra-playlist scoring for promotion/relegation.

### Value vs. Effort Matrix

**High Value, Low Effort:** Manual comparison interface with 5-level system (proven from v2); playlist structure analysis (simple heuristics); canonical song identification via ISRC.

**High Value, High Effort:** Cross-platform architecture; emotional similarity detection; both Spotify and YouTube Music playback integration; playlist generation with emotional journey consideration.

**Low Value, Low Effort:** Basic visualisation of rankings; export functionality.

**Low Value, High Effort:** Social features; Apple Music integration.

**Uncertain Value/Effort (Implement if Straightforward):** Intra-playlist Glicko-2 pools; visual memory metadata; context tagging via ML.

**Prioritisation:** Focus on high-value initiatives; start with low-effort items to build momentum; implement uncertain items only if they prove straightforward during development.

---

## Revision History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2026-02-14 | 1.0 | Initial discovery phase documentation | Enoch Ko |

---

## Document Status

**Status:** Approved — Ready for Requirements Definition Phase  
**Next Phase:** Solution Exploration and Requirements Specification  
**Outstanding Items:** None — all business case questions answered
