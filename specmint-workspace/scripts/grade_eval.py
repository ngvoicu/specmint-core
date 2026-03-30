#!/usr/bin/env python3
"""Grade specsmith eval runs by checking assertions against transcripts and outputs.

Usage:
    python grade_eval.py <run-dir> --eval-id <N>

Reads transcript.md and output files from <run-dir>/outputs/, evaluates
assertions from the parent eval_metadata.json, and writes grading.json.
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime, timezone


def read_file_safe(path: Path) -> str:
    try:
        return path.read_text(errors="replace")
    except OSError:
        return ""


def list_output_files(outputs_dir: Path) -> list[str]:
    if not outputs_dir.is_dir():
        return []
    return [f.name for f in sorted(outputs_dir.iterdir()) if f.is_file()]


def check_assertion_eval0(assertion: str, transcript: str, output_files: list[str], outputs_dir: Path) -> tuple[bool, str]:
    """Grade assertions for eval 0: forge workflow fidelity."""
    a = assertion.lower()

    if "research" in a and "saved" in a and "research-01" in a:
        has_research = any("research" in f.lower() for f in output_files)
        if has_research:
            research_files = [f for f in output_files if "research" in f.lower()]
            content = read_file_safe(outputs_dir / research_files[0])
            if len(content) > 100:
                return True, f"Found research file '{research_files[0]}' with {len(content)} chars of content"
            return False, f"Research file exists but has only {len(content)} chars (likely empty/stub)"
        # Also check transcript for evidence of saving research
        if "research-01.md" in transcript:
            return True, "Transcript mentions saving research-01.md (file may be in .specs/ dir)"
        return False, "No research-01.md file found in outputs and no mention in transcript"

    if "interactive questions" in a and "asked" in a:
        # Look for question marks in the transcript that aren't just quoting the prompt
        lines = transcript.split("\n")
        question_lines = [l for l in lines if "?" in l and len(l) > 20]
        # Filter out lines that are just quoting the original user prompt
        original_prompt_fragment = "SSE or WebSockets"
        genuine_questions = [l for l in question_lines if original_prompt_fragment not in l]
        if len(genuine_questions) >= 2:
            sample = genuine_questions[0][:100]
            return True, f"Found {len(genuine_questions)} question lines. Example: '{sample}'"
        return False, f"Only found {len(genuine_questions)} genuine question lines in transcript"

    if "pauses" in a or ("stops" in a and "waiting" in a):
        if "[WAITING FOR USER INPUT" in transcript or "STOPPING HERE" in transcript:
            return True, "Agent explicitly stopped and waited for user input"
        if "waiting for" in transcript.lower() and ("answer" in transcript.lower() or "response" in transcript.lower() or "input" in transcript.lower()):
            return True, "Agent indicated waiting for user response"
        return False, "No evidence that agent stopped to wait for user input"

    if "no spec" in a.lower() and "created" in a:
        spec_files = [f for f in output_files if f.upper() == "SPEC.MD" or f.upper().endswith("/SPEC.MD")]
        if not spec_files:
            # Also check transcript
            if "wrote SPEC.md" in transcript or "created SPEC.md" in transcript or "Save to: .specs/" in transcript:
                if "interview" in transcript.lower() and transcript.lower().index("interview") < transcript.lower().index("spec.md") if "spec.md" in transcript.lower() else True:
                    return False, "Transcript suggests SPEC.md was created before interview completed"
            return True, "No SPEC.md found in outputs"
        return False, f"SPEC.md was created: {spec_files}"

    if "application code" in a and ("not" in a.lower() or "no " in a.lower()):
        code_extensions = {".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".rs", ".java"}
        code_files = [f for f in output_files if Path(f).suffix in code_extensions and f not in ("transcript.md",)]
        # Exclude transcript, research, interview files
        excluded = {"transcript.md", "response.md", "metrics.json", "user_notes.md"}
        code_files = [f for f in code_files if f not in excluded and not f.startswith("research") and not f.startswith("interview")]
        if not code_files:
            return True, "No application code files found in outputs"
        return False, f"Found code files: {code_files}"

    if "directory structure" in a and "initialized" in a:
        if ".specs" in transcript or "mkdir -p .specs" in transcript:
            return True, "Transcript shows .specs/ directory was initialized"
        specs_files = [f for f in output_files if ".specs" in f or "research" in f.lower()]
        if specs_files:
            return True, f"Found .specs-related files: {specs_files}"
        return False, "No evidence of .specs/ directory initialization"

    return False, f"Unknown assertion: {assertion}"


def check_assertion_eval1(assertion: str, transcript: str, output_files: list[str], outputs_dir: Path) -> tuple[bool, str]:
    """Grade assertions for eval 1: resume active spec."""
    response = read_file_safe(outputs_dir / "response.md") if "response.md" in output_files else transcript

    if "identified" in assertion.lower() and "active spec" in assertion.lower():
        if "user auth system" in response.lower() or "user-auth-system" in response.lower():
            return True, "Response mentions 'User Auth System'"
        return False, "Response does not mention the active spec 'User Auth System'"

    if "progress count" in assertion.lower() or "5/12" in assertion:
        if "5/12" in response:
            return True, "Response includes '5/12' progress count"
        # Check for any X/12 pattern
        match = re.search(r"(\d+)/12", response)
        if match:
            return True, f"Response includes '{match.group(0)}' progress count"
        return False, "No progress count found (expected 5/12 or similar)"

    if "auth-06" in assertion.lower() or "google oauth callback" in assertion.lower():
        if "auth-06" in response.lower() or "oauth callback" in response.lower() or "google oauth" in response.lower():
            return True, "Response mentions AUTH-06 or Google OAuth callback handler"
        return False, "Response does not mention AUTH-06 or Google OAuth callback"

    if "resume context" in assertion.lower():
        context_keywords = ["token exchange", "google.ts", "callback handler", "oauth", "user lookup", "jwt"]
        found = [k for k in context_keywords if k in response.lower()]
        if len(found) >= 1:
            return True, f"Resume context present: found keywords {found}"
        return False, f"No resume context keywords found. Checked: {context_keywords}"

    if "compact format" in assertion.lower():
        labels = ["resuming", "progress", "phase", "current", "context"]
        found = [l for l in labels if l.lower() + ":" in response.lower() or l.lower() + " " in response.lower()]
        if len(found) >= 3:
            return True, f"Compact format with labels: {found}"
        # Check for structured output (short, with clear sections)
        lines = [l for l in response.strip().split("\n") if l.strip()]
        if len(lines) <= 15 and any(":" in l for l in lines):
            return True, f"Compact format: {len(lines)} lines with structured labels"
        return False, f"Only found {len(found)} of expected labels {labels}. Response has {len(lines)} lines."

    return False, f"Unknown assertion: {assertion}"


def check_assertion_eval2(assertion: str, transcript: str, output_files: list[str], outputs_dir: Path) -> tuple[bool, str]:
    """Grade assertions for eval 2: spec-then-stop."""
    a = assertion.lower()

    if "recognized" in a and "forge" in a:
        forge_evidence = ["forge" in transcript.lower(), "skill.md" in transcript.lower(), "spec smith" in transcript.lower()]
        if any(forge_evidence):
            return True, "Agent recognized request as forge workflow trigger"
        return False, "No evidence of forge workflow recognition"

    if "research" in a and "conducted" in a:
        research_keywords = ["codebase", "package.json", "dependencies", "structure", "glob", "grep", "read"]
        found = [k for k in research_keywords if k in transcript.lower()]
        if len(found) >= 2:
            return True, f"Research evidence: {found}"
        return False, f"Limited research evidence. Found: {found}"

    if "interview questions" in a and "asked" in a:
        lines = transcript.split("\n")
        # Check for lines with question marks
        question_lines = [l for l in lines if "?" in l and len(l) > 30]
        # Also check for numbered question items (e.g., "1. **Tech stack**: ...")
        numbered_q_lines = [l for l in lines if re.match(r'\s*\d+\.\s+\*\*', l) and len(l) > 30]
        # Also check for a "Questions Asked" section header
        has_questions_section = any("questions asked" in l.lower() for l in lines)
        genuine_questions = question_lines + numbered_q_lines
        if len(genuine_questions) >= 2:
            return True, f"Found {len(genuine_questions)} questions. Example: '{genuine_questions[0][:80]}'"
        if has_questions_section and len(numbered_q_lines) >= 1:
            return True, f"Found 'Questions Asked' section with {len(numbered_q_lines)} numbered items"
        return False, f"Only {len(genuine_questions)} question lines found"

    if "stopped" in a and "waited" in a and "self-answer" in a:
        if "[WAITING FOR USER INPUT" in transcript or "STOPPING HERE" in transcript:
            return True, "Agent stopped and waited for user input"
        if "waiting for" in transcript.lower() and ("answer" in transcript.lower() or "response" in transcript.lower()):
            return True, "Agent indicated waiting for user response"
        return False, "No evidence agent stopped to wait"

    if "application code" in a and ("not" in a or "no " in a):
        code_extensions = {".ts", ".tsx", ".js", ".jsx", ".py", ".go"}
        excluded = {"transcript.md", "response.md", "metrics.json", "user_notes.md"}
        code_files = [f for f in output_files
                      if Path(f).suffix in code_extensions
                      and f not in excluded
                      and not f.startswith("research")
                      and not f.startswith("interview")]
        if not code_files:
            return True, "No application code files in outputs"
        return False, f"Found code files: {code_files}"

    if "premature implementation" in a:
        impl_keywords = ["implementing", "writing code", "created file", "src/", "app/api/"]
        found = [k for k in impl_keywords if k in transcript.lower()]
        if not found:
            return True, "No implementation activity found in transcript"
        # Check if implementation happened AFTER spec was written
        return False, f"Found implementation indicators: {found}"

    return False, f"Unknown assertion: {assertion}"


def check_assertion_eval3(assertion: str, transcript: str, output_files: list[str], outputs_dir: Path) -> tuple[bool, str]:
    """Grade assertions for eval 3: research depth."""
    a = assertion.lower()
    all_content = transcript
    for f in output_files:
        all_content += " " + read_file_safe(outputs_dir / f)

    if "context7" in a or "library documentation" in a:
        keywords = ["context7", "resolve-library", "query-docs", "library doc", "get-library", "documentation for"]
        found = [k for k in keywords if k in all_content.lower()]
        if found:
            return True, f"Context7/library docs evidence: {found}"
        return False, "No Context7 or library documentation lookup found"

    if "web research" in a or "websearch" in a or "webfetch" in a or "best practices" in a:
        keywords = ["websearch", "webfetch", "web search", "web fetch", "searched for", "best practices", "documentation", "searched online"]
        found = [k for k in keywords if k in all_content.lower()]
        if found:
            return True, f"Web research evidence: {found}"
        # Also check for URL references
        if "http" in all_content.lower() or "www." in all_content.lower():
            return True, "Found URL references indicating web research"
        return False, "No web research evidence found"

    if "library comparison" in a or "comparing" in a:
        keywords = ["comparison", "compare", "alternatives", "vs ", "versus", "| library", "| need", "evaluated", "candidates"]
        found = [k for k in keywords if k in all_content.lower()]
        if found:
            return True, f"Library comparison evidence: {found}"
        return False, "No library comparison evidence found"

    if "research" in a and "saved" in a:
        research_files = [f for f in output_files if "research" in f.lower()]
        if research_files:
            content = read_file_safe(outputs_dir / research_files[0])
            if len(content) > 100:
                return True, f"Research file '{research_files[0]}' with {len(content)} chars"
            return False, f"Research file exists but only {len(content)} chars"
        if "research-01.md" in all_content:
            return True, "Transcript mentions saving research-01.md"
        return False, "No research file found"

    if "interview questions" in a and "asked" in a:
        lines = all_content.split("\n")
        question_lines = [l for l in lines if "?" in l and len(l) > 30]
        numbered_q_lines = [l for l in lines if re.match(r'\s*\d+\.\s+\*\*', l) and len(l) > 30]
        genuine_questions = question_lines + numbered_q_lines
        if len(genuine_questions) >= 2:
            return True, f"Found {len(genuine_questions)} questions"
        return False, f"Only {len(genuine_questions)} questions found"

    if "stopped" in a and "waited" in a:
        if "waiting for user input" in all_content.lower() or "stopping here" in all_content.lower():
            return True, "Agent stopped and waited for user input"
        if "waiting for" in all_content.lower() and ("answer" in all_content.lower() or "response" in all_content.lower()):
            return True, "Agent indicated waiting for user response"
        return False, "No evidence agent stopped to wait"

    return False, f"Unknown assertion: {assertion}"


def check_assertion_eval4(assertion: str, transcript: str, output_files: list[str], outputs_dir: Path) -> tuple[bool, str]:
    """Grade assertions for eval 4: spec quality (diagrams, library table, testing, coherence)."""
    a = assertion.lower()
    all_content = transcript
    for f in output_files:
        all_content += " " + read_file_safe(outputs_dir / f)

    if "architecture diagram" in a or ("diagram" in a and ("ascii" in a or "mermaid" in a)):
        has_mermaid = "```mermaid" in all_content
        has_ascii_flow = any(c in all_content for c in ["→", "──", "-->", "graph TD", "graph LR", "erDiagram", "stateDiagram", "flowchart"])
        if has_mermaid:
            return True, "Found Mermaid diagram (```mermaid block)"
        if has_ascii_flow:
            return True, "Found ASCII diagram or flow indicators"
        return False, "No architecture diagram found (no Mermaid or ASCII art)"

    if "library" in a and ("choices" in a or "comparison" in a or "table" in a):
        table_patterns = ["| library", "| need", "| alternatives", "library choices", "library comparison"]
        found = [p for p in table_patterns if p in all_content.lower()]
        if found:
            return True, f"Library table found: {found}"
        return False, "No library choices/comparison table found"

    if "testing strategy" in a:
        test_keywords = ["testing strategy", "unit test", "integration test", "e2e test", "end-to-end", "edge case"]
        found = [k for k in test_keywords if k in all_content.lower()]
        if len(found) >= 2:
            return True, f"Testing strategy present: {found}"
        return False, f"Limited testing strategy. Found: {found}"

    if "concrete" in a and "file paths" in a:
        path_patterns = [r'src/', r'\.ts\b', r'\.tsx\b', r'\.js\b', r'app/', r'components/', r'lib/', r'routes/']
        found = [p for p in path_patterns if re.search(p, all_content)]
        if len(found) >= 2:
            return True, f"Concrete file paths found: {found}"
        return False, f"Few concrete file paths. Found: {found}"

    if "coherence" in a or "logic review" in a:
        review_keywords = ["coherence", "logic review", "reviewed the spec", "checking", "verified", "consistent", "review before"]
        found = [k for k in review_keywords if k in all_content.lower()]
        if found:
            return True, f"Coherence/logic review evidence: {found}"
        return False, "No coherence or logic review evidence found"

    if "phases" in a and "status markers" in a:
        phase_markers = ["[pending]", "[in-progress]", "[completed]"]
        found = [m for m in phase_markers if m in all_content]
        if len(found) >= 2:
            return True, f"Phase status markers found: {found}"
        return False, f"Few phase markers. Found: {found}"

    return False, f"Unknown assertion: {assertion}"


def check_assertion_eval5(assertion: str, transcript: str, output_files: list[str], outputs_dir: Path) -> tuple[bool, str]:
    """Grade assertions for eval 5: implement command."""
    a = assertion.lower()
    all_content = transcript
    for f in output_files:
        all_content += " " + read_file_safe(outputs_dir / f)

    if "recognized" in a and "implement" in a:
        impl_keywords = ["implement", "implementation", "phase 1", "implement phase"]
        found = [k for k in impl_keywords if k in all_content.lower()]
        if len(found) >= 2:
            return True, f"Implementation trigger recognized: {found}"
        if found:
            return True, f"Implementation trigger found: {found}"
        return False, "No implementation trigger recognition"

    if "identified" in a and "active spec" in a:
        spec_keywords = ["quick auth", "quick-auth", "registry", "active spec"]
        found = [k for k in spec_keywords if k in all_content.lower()]
        if found:
            return True, f"Active spec identified: {found}"
        return False, "Active spec not identified"

    if "phase 1 tasks" in a or "found phase" in a:
        task_keywords = ["qa-01", "qa-02", "qa-03", "qa-04", "phase 1", "auth middleware", "user model", "token"]
        found = [k for k in task_keywords if k in all_content.lower()]
        if len(found) >= 2:
            return True, f"Phase 1 tasks found: {found}"
        return False, f"Limited Phase 1 task references. Found: {found}"

    if "implement" in a and ("write code" in a or "attempted" in a):
        code_keywords = ["implementing", "creating", "writing", "function", "export", "import", "const ", "middleware", "jwt", "token"]
        found = [k for k in code_keywords if k in all_content.lower()]
        if len(found) >= 2:
            return True, f"Implementation activity: {found}"
        return False, f"Limited implementation activity. Found: {found}"

    if "checkbox" in a or "task checkbox" in a:
        checkbox_keywords = ["[x]", "check off", "checked off", "mark as done", "mark as complete", "completed task", "- [x]", "checkbox"]
        found = [k for k in checkbox_keywords if k in all_content.lower()]
        if found:
            return True, f"Checkbox update evidence: {found}"
        return False, "No checkbox update evidence"

    if "registry" in a and "updated" in a:
        reg_keywords = ["registry", "progress", "updated", "registry.md"]
        found = [k for k in reg_keywords if k in all_content.lower()]
        if len(found) >= 2:
            return True, f"Registry update evidence: {found}"
        return False, f"Limited registry update evidence. Found: {found}"

    return False, f"Unknown assertion: {assertion}"


def check_assertion_eval6(assertion: str, transcript: str, output_files: list[str], outputs_dir: Path) -> tuple[bool, str]:
    """Grade assertions for eval 6: researcher agent spawning."""
    a = assertion.lower()
    all_content = transcript
    for f in output_files:
        all_content += " " + read_file_safe(outputs_dir / f)

    if "researcher" in a and "spawned" in a:
        spawn_keywords = ["spawn", "specsmith:researcher", "researcher agent", "task tool", "parallel research", "research pass", "launched"]
        found = [k for k in spawn_keywords if k in all_content.lower()]
        if found:
            return True, f"Researcher spawn evidence: {found}"
        return False, "No evidence of researcher agent being spawned"

    if "output path" in a or "research notes" in a and "path" in a:
        path_keywords = ["research-01.md", ".specs/", "output path", "save to", "save findings"]
        found = [k for k in path_keywords if k in all_content.lower()]
        if found:
            return True, f"Research output path specified: {found}"
        return False, "No research output path specified"

    if "context7" in a or "library documentation" in a:
        keywords = ["context7", "resolve-library", "query-docs", "library doc", "documentation for", "parallel"]
        found = [k for k in keywords if k in all_content.lower()]
        if found:
            return True, f"Context7/library docs evidence: {found}"
        return False, "No Context7 or library documentation evidence"

    if "library comparison" in a:
        keywords = ["comparison", "compare", "alternatives", "vs ", "| library", "| need", "candidates", "evaluated"]
        found = [k for k in keywords if k in all_content.lower()]
        if found:
            return True, f"Library comparison evidence: {found}"
        return False, "No library comparison evidence"

    if "risk assessment" in a:
        keywords = ["risk", "breaking changes", "security", "performance", "scalability", "migration", "what could go wrong"]
        found = [k for k in keywords if k in all_content.lower()]
        if len(found) >= 2:
            return True, f"Risk assessment evidence: {found}"
        return False, f"Limited risk assessment. Found: {found}"

    if "interview" in a and "stopped" in a:
        if "waiting for user input" in all_content.lower() or "stopping here" in all_content.lower():
            return True, "Agent stopped and waited for user input"
        if "waiting for" in all_content.lower() and ("answer" in all_content.lower() or "response" in all_content.lower()):
            return True, "Agent indicated waiting for user response"
        lines = all_content.split("\n")
        question_lines = [l for l in lines if "?" in l and len(l) > 30]
        numbered_q_lines = [l for l in lines if re.match(r'\s*\d+\.\s+\*\*', l) and len(l) > 30]
        if len(question_lines) + len(numbered_q_lines) >= 3:
            return True, f"Found {len(question_lines) + len(numbered_q_lines)} questions (implies interview)"
        return False, "No evidence of interview and stopping"

    return False, f"Unknown assertion: {assertion}"


def check_assertion_eval7(assertion: str, transcript: str, output_files: list[str], outputs_dir: Path) -> tuple[bool, str]:
    """Grade assertions for eval 7: forge with acceptance criteria."""
    a = assertion.lower()
    all_content = transcript
    for f in output_files:
        all_content += " " + read_file_safe(outputs_dir / f)

    if "acceptance criteria" in a and ("interview" in a or "question" in a):
        ac_keywords = ["acceptance criteria", "what does done look like", "what does 'done' look like",
                       "done look like", "conditions that must be true", "definition of done",
                       "how will you know", "success criteria", "verify that"]
        found = [k for k in ac_keywords if k in all_content.lower()]
        if found:
            return True, f"Acceptance criteria question found: {found}"
        # Check for question marks near acceptance-related words
        lines = all_content.split("\n")
        ac_questions = [l for l in lines if "?" in l and any(w in l.lower() for w in ["done", "criteria", "accept", "success", "verify", "complete"])]
        if ac_questions:
            return True, f"Found acceptance-related questions: {ac_questions[0][:80]}"
        return False, "No acceptance criteria question found in interview"

    if "research" in a and "saved" in a:
        return check_assertion_eval0(assertion, transcript, output_files, outputs_dir)

    if "pauses" in a or ("stops" in a and "waiting" in a):
        return check_assertion_eval0(assertion, transcript, output_files, outputs_dir)

    if "no spec" in a.lower() and "created" in a:
        return check_assertion_eval0(assertion, transcript, output_files, outputs_dir)

    if "application code" in a and ("not" in a.lower() or "no " in a.lower()):
        return check_assertion_eval0(assertion, transcript, output_files, outputs_dir)

    if "directory structure" in a and "initialized" in a:
        return check_assertion_eval0(assertion, transcript, output_files, outputs_dir)

    return False, f"Unknown assertion: {assertion}"


def check_assertion_eval8(assertion: str, transcript: str, output_files: list[str], outputs_dir: Path) -> tuple[bool, str]:
    """Grade assertions for eval 8: implement progress tracking."""
    a = assertion.lower()
    all_content = transcript
    for f in output_files:
        all_content += " " + read_file_safe(outputs_dir / f)

    if "identified" in a and "active spec" in a:
        keywords = ["quick auth", "quick-auth", "registry", "active spec", "active"]
        found = [k for k in keywords if k in all_content.lower()]
        if found:
            return True, f"Active spec identified: {found}"
        return False, "Active spec not identified"

    if "found phase" in a or "phase 1 tasks" in a or "started implementing" in a:
        keywords = ["qa-01", "qa-02", "qa-03", "qa-04", "phase 1", "current task", "← current"]
        found = [k for k in keywords if k in all_content.lower()]
        if len(found) >= 1:
            return True, f"Phase 1 tasks found: {found}"
        return False, f"Limited Phase 1 task references. Found: {found}"

    if "implement" in a and ("write code" in a or "attempted" in a or "at least one" in a):
        code_keywords = ["implementing", "creating", "writing", "function", "export", "import",
                         "const ", "middleware", "jwt", "token", "created file", "wrote"]
        found = [k for k in code_keywords if k in all_content.lower()]
        if len(found) >= 2:
            return True, f"Implementation activity: {found}"
        return False, f"Limited implementation activity. Found: {found}"

    if "checkbox" in a and ("updated" in a or "changed" in a):
        checkbox_keywords = ["[x]", "- [x]", "check off", "checked off", "mark as done",
                             "mark as complete", "completed task", "checkbox"]
        found = [k for k in checkbox_keywords if k in all_content.lower()]
        if found:
            return True, f"Checkbox update evidence: {found}"
        # Check for Edit tool calls on SPEC.md changing checkboxes
        if "spec.md" in all_content.lower() and "[x]" in all_content:
            return True, "Found [x] in SPEC.md-related content"
        return False, "No checkbox update evidence"

    if "registry" in a and "updated" in a and "progress" in a:
        reg_keywords = ["registry.md", "progress", "/12", "/8", "/4"]
        found = [k for k in reg_keywords if k in all_content.lower()]
        if len(found) >= 2:
            return True, f"Registry update evidence: {found}"
        # Check for Edit calls on registry.md
        if "registry.md" in all_content.lower() and ("progress" in all_content.lower() or "updated" in all_content.lower()):
            return True, "Registry.md was edited with progress/date"
        return False, f"Limited registry update evidence. Found: {found}"

    if "current marker" in a and "moved" in a:
        marker_keywords = ["← current", "<- current", "current marker", "move current",
                           "moved current", "next task"]
        found = [k for k in marker_keywords if k in all_content.lower()]
        if found:
            return True, f"Current marker movement: {found}"
        return False, "No current marker movement evidence"

    return False, f"Unknown assertion: {assertion}"


def check_assertion_eval9(assertion: str, transcript: str, output_files: list[str], outputs_dir: Path) -> tuple[bool, str]:
    """Grade assertions for eval 9: implement registry consistency."""
    a = assertion.lower()
    all_content = transcript
    for f in output_files:
        all_content += " " + read_file_safe(outputs_dir / f)

    if "identified" in a and "active spec" in a:
        return check_assertion_eval8(assertion, transcript, output_files, outputs_dir)

    if "scoped" in a and "phase 1" in a:
        scope_keywords = ["phase 1", "implement phase 1", "phase 1 only", "tasks in phase 1",
                          "scoped to phase"]
        found = [k for k in scope_keywords if k in all_content.lower()]
        if found:
            return True, f"Phase 1 scoping evidence: {found}"
        return False, "No phase 1 scoping evidence"

    if "checkbox" in a and ("updated" in a or "completed" in a):
        return check_assertion_eval8(
            "Task checkbox was updated in SPEC.md: changed from - [ ] to - [x]",
            transcript, output_files, outputs_dir
        )

    if "phase marker" in a and "updated" in a:
        marker_keywords = ["[completed]", "[in-progress]", "phase.*completed",
                           "phase status", "phase marker"]
        found = [k for k in marker_keywords if k in all_content.lower() or re.search(k, all_content.lower())]
        if found:
            return True, f"Phase marker update evidence: {found}"
        return False, "No phase marker update evidence"

    if "registry" in a and "progress" in a and ("updated" in a or "reflect" in a):
        return check_assertion_eval8(
            "Registry (.specs/registry.md) was updated with new progress count after task completion",
            transcript, output_files, outputs_dir
        )

    if "registry" in a and "spec.md" in a and "consistent" in a:
        # Check for re-read/verify step
        verify_keywords = ["re-read", "verify", "confirm", "consistency", "match",
                           "registry.*spec.md", "spec.md.*registry"]
        found = [k for k in verify_keywords if k in all_content.lower() or re.search(k, all_content.lower())]
        if found:
            return True, f"Consistency verification evidence: {found}"
        # Check if both files were read/edited
        if "registry.md" in all_content.lower() and "spec.md" in all_content.lower():
            return True, "Both registry.md and SPEC.md were referenced"
        return False, "No consistency verification evidence"

    return False, f"Unknown assertion: {assertion}"


def grade_run(run_dir: Path, eval_id: int) -> dict:
    """Grade a single run directory."""
    outputs_dir = run_dir / "outputs"
    transcript_path = outputs_dir / "transcript.md"
    transcript = read_file_safe(transcript_path)
    output_files = list_output_files(outputs_dir)

    # Load assertions from eval_metadata.json
    metadata_path = run_dir.parent.parent / "eval_metadata.json"
    if not metadata_path.exists():
        metadata_path = run_dir.parent / "eval_metadata.json"
    if not metadata_path.exists():
        # Try one more level up
        for p in [run_dir.parent.parent.parent / "eval_metadata.json"]:
            if p.exists():
                metadata_path = p
                break

    assertions = []
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text())
        assertions = metadata.get("assertions", [])
        eval_id = metadata.get("eval_id", eval_id)

    # Choose checker based on eval_id
    checkers = {0: check_assertion_eval0, 1: check_assertion_eval1, 2: check_assertion_eval2, 3: check_assertion_eval3, 4: check_assertion_eval4, 5: check_assertion_eval5, 6: check_assertion_eval6, 7: check_assertion_eval7, 8: check_assertion_eval8, 9: check_assertion_eval9}
    checker = checkers.get(eval_id, check_assertion_eval0)

    expectations = []
    for assertion in assertions:
        passed, evidence = checker(assertion, transcript, output_files, outputs_dir)
        expectations.append({
            "text": assertion,
            "passed": passed,
            "evidence": evidence,
        })

    passed_count = sum(1 for e in expectations if e["passed"])
    total = len(expectations)
    pass_rate = passed_count / total if total > 0 else 0.0

    grading = {
        "expectations": expectations,
        "summary": {
            "passed": passed_count,
            "failed": total - passed_count,
            "total": total,
            "pass_rate": round(pass_rate, 4),
        },
        "execution_metrics": {
            "output_chars": sum(len(read_file_safe(outputs_dir / f)) for f in output_files),
            "transcript_chars": len(transcript),
            "total_tool_calls": 0,
            "total_steps": 0,
            "errors_encountered": 0,
        },
        "timing": {},
        "claims": [],
        "user_notes_summary": {"uncertainties": [], "needs_review": [], "workarounds": []},
        "eval_feedback": {"suggestions": [], "overall": "Automated grading via grade_eval.py"},
    }

    return grading


def main():
    if len(sys.argv) < 2:
        print("Usage: python grade_eval.py <run-dir> [--eval-id N]")
        sys.exit(1)

    run_dir = Path(sys.argv[1]).resolve()
    eval_id = 0
    if "--eval-id" in sys.argv:
        idx = sys.argv.index("--eval-id")
        eval_id = int(sys.argv[idx + 1])

    grading = grade_run(run_dir, eval_id)

    output_path = run_dir / "grading.json"
    output_path.write_text(json.dumps(grading, indent=2) + "\n")
    print(f"Grading saved to {output_path}")

    summary = grading["summary"]
    print(f"Result: {summary['passed']}/{summary['total']} passed ({summary['pass_rate']*100:.0f}%)")
    for exp in grading["expectations"]:
        status = "PASS" if exp["passed"] else "FAIL"
        print(f"  [{status}] {exp['text'][:70]}")
        print(f"         {exp['evidence'][:100]}")


if __name__ == "__main__":
    main()
