# Stakeholder Analysis: MusicElo v3.0

**Project:** MusicElo v3.0 — Personal Music Ranking and Discovery System
**Date:** February 2026
**Author:** Enoch Ko
**Stage:** Discovery and Problem Definition
**Version:** 1.0

---

## Executive Summary

MusicElo v3.0 is a personal project with a single primary user/stakeholder, but serves multiple strategic audiences through portfolio demonstration. This analysis identifies all parties with interest in or influence over the project, their concerns, and engagement strategies.

---

## Stakeholder Map

### Power/Interest Matrix

```
                    HIGH INTEREST
                         │
    ┌────────────────────┼────────────────────┐
    │                    │                    │
    │   MANAGE CLOSELY   │   KEEP SATISFIED   │
H   │                    │                    │
I   │  • Primary User    │                    │
G   │    (Enoch)         │  (None identified) │
H   │                    │                    │
    │                    │                    │
P   ├────────────────────┼────────────────────┤
O   │                    │                    │
W   │   MONITOR          │   KEEP INFORMED    │
E   │                    │                    │
R   │  (None identified) │  • Future          │
    │                    │    Employers       │
    │                    │  • Current         │
    │                    │    Employer        │
    │                    │  • Academic        │
L   │                    │    Advisors        │
O   │                    │  • Professional    │
W   │                    │    Network         │
    │                    │  • r/TWICE         │
    │                    │    Community       │
    │                    │                    │
    └────────────────────┴────────────────────┘
                    LOW INTEREST
```

---

## Primary Stakeholder

### Enoch (User, Developer, Decision Maker)

**Role:** Primary user, sole developer, decision authority
**Power:** Complete — all decisions, resource allocation, scope control
**Interest:** Very High — personal problem, career development tool

**Needs and Expectations:**

- Solve the music ranking problem with a transparent, intuitive system
- Demonstrate product management, engineering, and AI-assisted development skills for portfolio
- Balance project with Masters coursework
- Maintain documentation quality for future reference
- Complete MVP within a 6–9 month timeline (flexible, not deadline-driven)

**Concerns and Constraints:**

- Time availability alongside academic commitments
- Technical feasibility (API limitations, algorithm complexity, cross-platform development)
- Scope creep diluting MVP completion
- Maintaining motivation through challenges
- v2 UX failures must not be repeated (90/10 passive/active design critical)

**Success Criteria:**

- Rankings feel intuitively correct (>80% agreement with top 50)
- Can confidently answer "what's my favourite song?"
- Portfolio-quality documentation suitable for sharing
- Project demonstrates end-to-end product thinking
- Passive ranking during natural listening works (not tedious like v2)
- Cross-platform functionality successful on both desktop and mobile

**Engagement Strategy:**

- Self-managed through structured phases and milestones
- Regular reflection on progress vs. coursework balance
- Strict scope discipline (v4.0 backlog for deferred features)
- Celebrate incremental wins to maintain motivation
- Can pause or abandon at any phase if interest wanes

---

## Secondary Stakeholders (Indirect Interest)

### Future Employers

**Role:** Evaluation of candidacy for Data Science / Product Manager roles
**Power:** Low (no project influence) → High (career impact)
**Interest:** Medium (portfolio piece among many factors)

**Needs and Expectations:**

- Evidence of product thinking and problem-solving
- Technical competency in data science and engineering
- Clear communication of complex technical concepts
- Initiative and self-directed learning capability
- Effective use and management of AI for software product development

**What They Look For:**

- Is this a genuine capability demonstration or a toy project?
- Does technical execution meet professional standards?
- Can the candidate articulate product decisions and trade-offs?

**Engagement Strategy:**

- Portfolio-quality documentation from the start (not retrofit)
- GitHub repository with professional README
- LinkedIn post or blog article explaining the project
- Prepared case study for interview discussions

**Communication Approach:** Focus on problem-solving process, not just technical solution. Emphasise product thinking and user research. Quantify impact and decision rationale. Highlight AI-assisted development capabilities and cross-platform architecture decisions.

---

### Current Employer Leadership

**Role:** Current employer; potential evaluator for internal opportunities
**Power:** Medium (career progression, project assignments)
**Interest:** Low–Medium (relevant to analytics capabilities)

**Needs and Expectations:**

- Demonstration of analytical thinking applicable to work
- Evidence of initiative and self-directed skill development
- Potential application to internal data and analytics projects

**Engagement Strategy:**

- Share high-level learnings if relevant to work discussions
- Frame as professional development investment
- Consider case study presentation for internal learning sessions (optional)

**Communication Approach:** Emphasise transferable skills (product thinking, data analysis, stakeholder research). Focus on methodology over music-specific content. Demonstrate time management and priority balancing.

---

### Academic Advisors

**Role:** Potential collaborators on capstone project or thesis direction  
**Power:** Medium (academic guidance, research direction)  
**Interest:** Low–Medium (depends on alignment with research interests)

**Needs and Expectations:**

- Rigorous application of statistical methods (Glicko-2)
- Academic-quality documentation and methodology
- Potential foundation for future research

**Engagement Strategy:**

- Keep the door open for future academic collaboration
- Document methodology to academic standards
- Consider research questions emerging from the project (preference modelling, ranking systems, temporal dynamics)

**Communication Approach:** Emphasise statistical foundations (Glicko-2, similarity metrics, preference evolution). Frame as applied statistics in a personal context. Highlight potential research directions.

---

### Professional Network

**Role:** Audience for portfolio sharing; potential collaborators  
**Power:** Low (no project influence)  
**Interest:** Low–Medium (varies by individual)

**Sub-communities:**

1. **LinkedIn connections** — professional audience, technical and non-technical mix
2. **r/TWICE community** — K-pop fans interested in ranking methodology and results
3. **University classmates** — professional and technical audience

**Engagement Strategy:**

- **LinkedIn:** Professional framing; post first after sufficient development
- **r/TWICE:** Share ranking results and methodology; post later, after data collection provides a reliable ranking
- **Classmates:** Technical discussion, AI collaboration approach

**Communication Approach:**

- LinkedIn: Professional non-technical framing, emphasise product thinking and portfolio value
- r/TWICE: Focus on ranking results with scores; methodology available in GitHub for interested parties
- Classmates: Technical details, cross-platform architecture, AI-assisted development

**Sharing Priority Order:** LinkedIn first (professional context), then r/TWICE later (requires time to collect sufficient data for a reliable ranking).

---

## Tertiary Stakeholders (Potential Future Interest)

### Open Source / Music Tech Community

**Role:** Potential users or contributors if the project is open-sourced  
**Power:** Very Low (currently not engaged)  
**Interest:** Very Low (no awareness of the project)

The project is licensed under MIT for open-source use, though additional documentation, testing, and generalisation would be needed before it is ready for meaningful community collaboration. Not a priority for v3.0 scope. Spotify integration (vs. YouTube Music only) supports this future possibility.

---

### Partner

**Role:** Personal support; accountability partner; prototype demonstration audience  
**Power:** Medium (personal life priorities)  
**Interest:** Low (not involved in the project, but supportive)

**Engagement Strategy:**

- Maintain transparent communication about time commitments
- Share progress once a prototype with UI exists for demonstration
- Celebrate milestones together
- Ensure the project remains enjoyable, not stressful

---

## Stakeholder Engagement Plan

### Weekly Cadence

**Primary User (Enoch):**

- Continuous self-reflection on progress, scope, motivation, and coursework balance

### Monthly Cadence

**Career Development Stakeholders (Employers, Network):**

- Indirect engagement through portfolio updates, LinkedIn, and GitHub commits

### Ad Hoc Engagement

**Academic / Professional Advisors:** Triggered by research opportunities or methodological questions.

**Personal Support (Partner):** Triggered by prototype demonstrations and milestone achievements.

**Community (r/TWICE):** Triggered post-completion, after sufficient data collection for reliable ranking.

**Friends/Classmates (Accountability Partners):** Triggered by design or prototype reality checks.

---

## Decision Authority Matrix

| Decision Type | Decision Maker | Consultation Required | Approval Required |
|--------------|----------------|----------------------|-------------------|
| Scope changes | Enoch | Self-reflection | None |
| Technical architecture | Enoch | Online research, AI assistance | None |
| Timeline adjustments | Enoch | Coursework schedule review | None |
| Feature prioritisation | Enoch | User research (self) | None |
| Portfolio sharing | Enoch | Consider professional context | None |
| Optional feature implementation | Enoch | Effort/complexity assessment | None |

**Key Principle:** Enoch has complete autonomy over project decisions; no external approvals required.

---

## Influence and Dependency Analysis

### What the Project Depends On

**External Dependencies:**

- Spotify API availability and stability (metadata, playback, playlist export/import)
- YouTube Music API documentation and access (playback, playlist export/import)
- MusicBrainz API (supplemental metadata)
- Open-source Glicko-2 library quality or public domain algorithm (glicko.net) for self-implementation
- Cross-platform development framework availability
- Personal time availability (employment and coursework permitting)
- AI assistance quality for coding and troubleshooting

**Internal Dependencies:**

- Sustained personal motivation
- Technical skill development (learning as needed with AI assistance)
- Discipline around scope management
- Effective 90/10 passive/active UX design to avoid v2 failures

### What Depends on the Project

**Career Development:** Portfolio differentiation for job applications; interview conversation material; demonstration of PM, engineering, and AI-assisted development capabilities; fills the gap of having no shareable programming projects from employer work.

**Personal Satisfaction:** Music organisation and preference clarity; intellectual curiosity fulfilment; applied learning from Masters coursework; "passive curation" without dedicated effort.

**Future Opportunities:** Potential academic research foundation; possible open-source contribution; community engagement opportunity.

---

## Risk Register (Stakeholder-Related)

### High Priority Risks

**Risk:** Loss of Personal Motivation  
**Impact:** High — project abandonment  
**Mitigation:** Set minimum viable success criteria; celebrate incremental wins; allow extended timeline; 90/10 passive/active design addresses v2 UX failures; can pause/abandon at any phase  
**Acceptance:** Even an incomplete project demonstrates product thinking if minimum completion criteria are met

**Risk:** Coursework Time Conflicts  
**Impact:** High — project delays or abandonment  
**Mitigation:** Flexible timeline; pause if coursework >25 hrs/week; resume between semesters  
**Acceptance:** Completion more important than speed

### Medium Priority Risks

**Risk:** Portfolio Quality Below Expectations  
**Impact:** Medium — reduced career benefit  
**Mitigation:** Professional documentation standards from the start; peer review before sharing; phased sharing (LinkedIn first, r/TWICE later)

**Risk:** Scope Creep Diluting MVP  
**Impact:** Medium — extended timeline, possible incompletion  
**Mitigation:** Strict feature deferral discipline; v4.0 feature backlog; implement optional features only if straightforward

**Risk:** Cross-Platform Complexity Overhead  
**Impact:** Medium — extended development time  
**Mitigation:** Research cross-platform frameworks early; leverage AI assistance for unfamiliar platforms  
**Acceptance:** Desktop-only MVP acceptable if cross-platform proves too complex

**Risk:** Repeating v2 UX Failures  
**Impact:** Medium — loss of motivation, project abandonment  
**Mitigation:** 90/10 passive/active design principle; continuous playback without required clicks; easy preference indication; frequent UX validation

### Low Priority Risks

**Risk:** Negative Professional Perception  
**Impact:** Low — unlikely given personal project nature  
**Mitigation:** Ensure no work time used; frame as professional development

**Risk:** Academic Conflict of Interest  
**Impact:** Very Low — unlikely for personal project  
**Mitigation:** Clarify IP ownership if used for capstone; cite sources properly

---

## Communication Plan

### During Development (Minimal)

- No public announcements until MVP is complete
- GitHub commits visible but not promoted
- Defer LinkedIn/blog content until Phase 3
- Share progress with partner when a prototype UI exists
- Informal reality checks with friends/classmates (accountability partners)

### Post-Completion Sharing (Phased)

1. **LinkedIn first:** Professional project summary and learnings (portfolio context)
2. **r/TWICE later:** Ranking results with scores; GitHub link for methodology (requires sufficient data collection)
3. **Classmates:** Technical discussion, AI collaboration approach, cross-platform architecture
4. **GitHub repository:** Comprehensive README and documentation for all audiences
5. **Resume/portfolio:** Include for job applications

---

## Success Metrics by Stakeholder

### Primary User (Enoch)

**Personal Utility:**

- [ ] Can answer "what's my favourite song?" confidently
- [ ] Rankings feel >80% intuitively correct
- [ ] Forgotten favourites discovered
- [ ] System becomes preferred over platform shuffle / existing playlists
- [ ] 90/10 passive/active balance achieved
- [ ] Cross-platform functionality works on desktop and mobile

**Professional Development:**

- [ ] Portfolio-quality documentation complete
- [ ] Project demonstrates PM + engineering + AI-assisted development integration
- [ ] Prepared case study for interviews
- [ ] GitHub repository professionally presented

**Learning Objectives:**

- [ ] Practical experience with Glicko-2 algorithm
- [ ] API integration competency demonstrated (Spotify, YouTube Music, MusicBrainz)
- [ ] End-to-end product development practised
- [ ] Structured documentation habits established
- [ ] Effective AI collaboration for development
- [ ] Cross-platform development skills acquired

### Future Employers

- [ ] Clear problem statement and user research
- [ ] Thoughtful technical decisions documented
- [ ] Clean code and professional standards
- [ ] Evidence of iterative thinking (v2 failures → v3 solutions)
- [ ] Effective use of AI for software product development

### Current Employer Leadership

- [ ] Structured analytical approach
- [ ] Initiative and self-directed learning
- [ ] Time management and priority balancing
- [ ] Transferable skills to consulting work

### Academic Advisors

- [ ] Sound statistical methodology
- [ ] Clear documentation of assumptions
- [ ] Potential research directions identified

### Professional Network

- [ ] r/TWICE: Engaging ranking results post
- [ ] LinkedIn: Professional case study
- [ ] Classmates: Technical knowledge sharing

---

## Accountability and Feedback Mechanisms

### Progress Sharing

**With Partner:** Share progress once a prototype with UI exists. Celebrate milestones together. Discuss time commitment if impacting personal time.

**With Friends/Classmates (Accountability Partners):** Show designs or prototypes for reality checks. Informal feedback on UX and concept.

### Public Validation

**r/TWICE Community:** Share ranking results and methodology post-completion. Focus on results (the community is primarily interested in rankings, not the technical build). Methodology available in GitHub for interested parties.

**LinkedIn Network:** Professional framing of project and learnings. Post first (before r/TWICE) for professional context.

### Failure Handling

If the project doesn't work out, minimum completion criteria still provide portfolio value. v2 already proved Glicko-2 scoring works (just UX issues). Documented learnings still demonstrate product thinking, and the v2 → v3 iteration story shows a growth mindset.

---

## Revision History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2026-02-14 | 1.0 | Initial discovery phase documentation | Enoch Ko |

**Next Review:** Post-Phase 1 completion (assess if stakeholder landscape has changed)

---

## Document Status

**Status:** Approved — Ready for Requirements Definition Phase  
**Next Phase:** Solution Exploration and Requirements Specification  
**Outstanding Items:** None — all stakeholder questions answered
