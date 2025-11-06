***REMOVED***!/bin/bash
***REMOVED*** Security scanning script for local development
***REMOVED*** Run this before committing to catch security issues early

set -e

echo "🔒 Running Security Scans..."
echo ""

***REMOVED*** Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' ***REMOVED*** No Color

***REMOVED*** Check if security tools are installed
check_tool() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}✗${NC} $1 not found. Install with: pip install -r requirements-security.txt"
        return 1
    else
        echo -e "${GREEN}✓${NC} $1 found"
        return 0
    fi
}

echo "Checking for security tools..."
check_tool bandit || exit 1
check_tool semgrep || exit 1
echo ""

***REMOVED*** Run Bandit
echo -e "${YELLOW}Running Bandit (Python security linter)...${NC}"
if bandit -c .bandit -r custom_components/ -f screen; then
    echo -e "${GREEN}✓ Bandit: No security issues found${NC}"
else
    echo -e "${RED}✗ Bandit: Security issues detected${NC}"
    EXIT_CODE=1
fi
echo ""

***REMOVED*** Run Semgrep
echo -e "${YELLOW}Running Semgrep (multi-language security scanner)...${NC}"
if semgrep --config=.semgrep.yml custom_components/; then
    echo -e "${GREEN}✓ Semgrep: No security issues found${NC}"
else
    echo -e "${RED}✗ Semgrep: Security issues detected${NC}"
    EXIT_CODE=1
fi
echo ""

***REMOVED*** Run Safety (dependency vulnerability scanner)
echo -e "${YELLOW}Running Safety (dependency vulnerability scanner)...${NC}"
if command -v safety &> /dev/null; then
    if safety check --json 2>/dev/null | grep -q '"vulnerabilities": \[\]'; then
        echo -e "${GREEN}✓ Safety: No known vulnerabilities in dependencies${NC}"
    else
        echo -e "${YELLOW}⚠ Safety: Some dependencies have known vulnerabilities${NC}"
        safety check
    fi
else
    echo -e "${YELLOW}⚠ Safety not installed, skipping dependency scan${NC}"
fi
echo ""

***REMOVED*** Summary
if [ ${EXIT_CODE:-0} -eq 0 ]; then
    echo -e "${GREEN}✓ All security scans passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Security issues found. Please fix before committing.${NC}"
    exit 1
fi
