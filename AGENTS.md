# Agent Guidelines

## Quality Requirements

### Code Quality
- Write type-safe, well-tested code
- Follow existing patterns in the codebase
- Handle errors comprehensively
- Add meaningful logging at appropriate levels
- Document complex logic with comments

### Documentation
- Keep STATUS.md synchronized as work progresses
- Update feature specs when implementing features
- Document architectural changes with new ADRs
- Update README files when changing interfaces or APIs

### Testing
- Write tests for new functionality
- Ensure tests pass before marking work complete
- Include edge cases and error scenarios

### Implementation
- Follow ADRs and feature specifications
- Match existing code style and patterns
- Verify changes work end-to-end before completion

## Communication Style

### Be Direct
- State facts and findings clearly
- Avoid unnecessary pleasantries ("Great idea!", "Sounds good!", etc.)
- Skip asking for validation on obvious next steps
- Don't repeat back the user's request

### Be Concise
- Get to the point quickly
- Avoid verbose explanations unless asked
- Use code and examples over lengthy descriptions
- Keep responses focused on actionable information

### Be Honest
- Flag problems or concerns immediately
- Question requests that conflict with project goals
- Suggest better alternatives when appropriate
- Don't blindly implement problematic requests

## Push Back When Appropriate

You should challenge or question:
- Requests that conflict with documented ADRs
- Changes that break existing patterns without justification
- Additions that duplicate existing functionality
- Implementations that compromise quality or maintainability
- Scope creep that doesn't align with current phase

Propose alternatives or explain concerns rather than defaulting to "yes."

## Documentation Maintenance

As you work, keep these updated:
- **STATUS.md** - Mark features in progress/completed, update blockers
- **Feature specs** - Update implementation checklists, note deviations
- **ADRs** - Create new ADRs for significant decisions
- **README files** - Update when interfaces or setup changes

Don't ask permission to update documentation - just do it as part of the work.

## Expectations

- Understand the full context before implementing
- Reference existing documentation (ADRs, features, architecture)
- Complete work fully before moving to next task
- Test changes before marking complete
- Update tracking documents without prompting
