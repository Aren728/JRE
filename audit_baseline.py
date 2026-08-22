import os
import re
from pathlib import Path

def find_files(directory, pattern):
    return [str(p) for p in Path(directory).rglob(pattern) if not any(x in str(p) for x in ['.git', '__pycache__', '.pyc'])]

def extract_imports(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    imports = re.findall(r'from\s+(src\.\w+\.\w+)\s+import', content)
    imports += re.findall(r'import\s+(src\.\w+\.\w+)', content)
    return list(set(imports))

def check_tier2_validation():
    tier2_domains = ['spirituality', 'business', 'litigation', 'assets', 'health']
    report = []
    for domain in tier2_domains:
        config_exists = os.path.exists(f"config/domains/{domain}.toml")
        service_exists = os.path.exists(f"src/jrs/domains/{domain}/service.py")
        validation_exists = os.path.exists(f"tests/integration/jrs/validation/test_{domain}_validation.py")
        report.append(f"- {domain.capitalize()}: Config={config_exists}, Service={service_exists}, Validation={validation_exists}")
    return "\n".join(report)

def check_health_safety():
    health_model = "src/jrs/domains/health/models.py"
    if os.path.exists(health_model):
        with open(health_model, 'r') as f:
            content = f.read()
        has_safety = "_validate_no_medical_terms" in content or "forbidden" in content.lower()
        return f"Health Safety Gate Present: {has_safety}"
    return "Health domain not found."

def check_jre021():
    jre021 = "src/jre/rectification/service.py" # Adjust path if different
    if os.path.exists(jre021):
        return "JRE-021 (Rectification) service.py exists. (Manual review of interface required)"
    return "JRE-021 not found at expected path."

print("Generating Read-Only Baseline Audit...\n")

report = []
report.append("# JRS v1.0 Read-Only Baseline Audit\n")

# 1. Engine Exposure & Orchestrator Calls
report.append("## 1. Orchestrator Dependencies")
orchestrator_files = find_files("src/jrs", "*orchestrat*") + find_files("src/jrs", "*pipeline*")
for f in orchestrator_files:
    report.append(f"\n### {f}")
    report.append("Imports: " + ", ".join(extract_imports(f)))

# 2. Tier-2 Validation Status
report.append("\n## 2. Tier-2 Domain Validation Status")
report.append(check_tier2_validation())

# 3. Health Safety Check
report.append("\n## 3. Health Domain Safety Check")
report.append(check_health_safety())

# 4. JRE-021 Status
report.append("\n## 4. JRE-021 (Rectification) Status")
report.append(check_jre021())

# 5. Temporal Windows Check
report.append("\n## 5. Temporal/Transition Mechanisms")
temporal_files = find_files("src/jrs/temporal", "*.py")
for f in temporal_files:
    report.append(f"- {f}")

# Write to file
with open("AUDIT_REPORT.md", "w", encoding="utf-8") as f:
    f.write("\n".join(report))

print("Audit complete. Review AUDIT_REPORT.md")
