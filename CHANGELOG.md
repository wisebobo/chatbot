# Changelog

## [Unreleased]

### Changed - 2026-04-18

#### Naming Convention Improvement: WRITE_ACTIONS → CHG_REQUIRE_ACTIONS

**Rationale:**
- `CHG_REQUIRE_ACTIONS` (Change Requiring Actions) better aligns with ITIL change management terminology
- More accurately describes the purpose: operations that require change management approval
- Distinguishes from generic "write operations" to emphasize the governance aspect

**Affected Files:**
- [`app/skills/controlm_skill.py`](file://e:\Python\chatbot\app\skills\controlm_skill.py)
  - Renamed `WRITE_ACTIONS` → `CHG_REQUIRE_ACTIONS`
  - Updated comments to reflect ITIL terminology
  
- [`docs/DYNAMIC_HUMAN_APPROVAL_GUIDE.md`](file://e:\Python\chatbot\docs\DYNAMIC_HUMAN_APPROVAL_GUIDE.md)
  - Updated all code examples to use `CHG_REQUIRE_ACTIONS`
  - Changed operation type labels from "Write" to "Change"
  - Added ITIL context to documentation

**Impact:**
- ✅ No breaking changes (internal constant only)
- ✅ Improved clarity and alignment with enterprise IT standards
- ✅ Better semantic meaning for future maintainers

**Migration:**
No migration needed. This is an internal implementation detail. If you have custom skills using this pattern, simply rename your constants accordingly:

```python
# Before
WRITE_ACTIONS = {"create", "update", "delete"}

# After
CHG_REQUIRE_ACTIONS = {"create", "update", "delete"}
```

---

## Previous Changes

### Added - 2026-04-18

- Dynamic human approval mechanism for skills
- Read vs write operation classification
- ITIL-compliant change management workflow
