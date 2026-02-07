# Plan Implementacji Core Flow - GitHub Actions

**Data:** 2026-02-07
**Cel:** Skonfigurować GitHub Actions zgodnie z diagramem z PLAN.md

---

## 🎯 Docelowy Flow (z PLAN.md)

```
USER → Upload Data → Data QA → [PASS: Auto Branch+PR | FAIL: Error]
  → Training (3 attempts) → Quality Gate → [BETTER: Merge | WORSE: Reject]
  → Build → Deploy → Monitoring
```

---

## 📊 Aktualny Stan (PROBLEMY)

### ❌ Problem 1: Training się nie wykonuje
**Obserwacja:**
- Workflows "Train Model" w Actions pokazują "Completed" ale nie ma logów z treningu
- Model w MLflow nie zmienił się od 2 dni
- Workflow train.yml istnieje ale prawdopodobnie nie był wywołany z prawdziwymi danymi

**Przyczyna:**
- Workflow trigger: `paths: - 'WMS/data/training/**'`
- Ale images i masks są gitignored (dla DVC)
- Więc commit images nie triggeruje workflow!

**Weryfikacja potrzebna:**
```bash
# Sprawdź czy train.yml w ogóle się uruchomił z danymi
# Sprawdź MLflow czy są nowe runs
```

---

### ❌ Problem 2: Build/Deploy uruchamia się na każdy commit
**Obserwacja:**
- Release & Deploy odpalił się na commit z dokumentacją, fix AWS, itp.
- To marnowanie czasu i zasobów

**Potrzeba:**
- Build/Deploy tylko gdy:
  - Training zakończył się sukcesem i model się poprawił
  - LUB ręczny trigger

---

### ❌ Problem 3: Brak ochrony brancha main
**Obserwacja:**
- Każdy może pushować bezpośrednio na main
- Nie ma wymuszonego PR review
- Nie ma quality gate przed merge

**Potrzeba:**
- Branch protection rules
- Wymagany PR + status checks

---

### ❌ Problem 4: Brak automatic branch/PR creation
**Obserwacja:**
- User musi ręcznie tworzyć branch i PR
- Flow zakłada automatyzację tego

**Potrzeba:**
- Workflow który tworzy branch i PR po Data QA PASS

---

### ❌ Problem 5: Brak retry logic (3 próby)
**Obserwacja:**
- Training próbuje raz i kończy
- Flow wymaga do 3 prób z różnymi seeds

**Potrzeba:**
- Retry mechanism w train.yml

---

### ❌ Problem 6: DVC nie jest zintegrowany z workflows
**Obserwacja:**
- User musi ręcznie robić `dvc push`
- Workflows nie robią `dvc pull` przed treningiem

**Potrzeba:**
- Automatic DVC operations w workflows

---

## 🏗️ PLAN IMPLEMENTACJI

### 📁 Struktura Branchy (NOWA)

```
main ← protected, tylko PR merge
  ↑
  PR (auto-created)
  ↑
data/YYYYMMDD-HHMMSS ← user pushuje nowe images/masks tutaj
```

**Workflow:**
1. User tworzy branch `data/20260207-160000`
2. User dodaje images + masks
3. User pushuje branch
4. GitHub Action automatycznie:
   - Waliduje data (Data QA)
   - Jeśli PASS: tworzy PR
   - Jeśli FAIL: komentuje błąd na branchu
5. PR triggeruje training (do 3 prób)
6. Jeśli model się poprawił: auto-approve PR
7. User/Admin merguje do main
8. Merge triggeruje build + deploy

---

## 📝 ZADANIA DO WYKONANIA

### TASK 1: Branch Protection Rules (GitHub Settings) ⭐⭐⭐⭐⭐

**Gdzie:** GitHub → Settings → Branches → Add rule

**Konfiguracja dla `main`:**
```yaml
Branch name pattern: main
✅ Require a pull request before merging
  - Required approvals: 1
  - Dismiss stale PR approvals when new commits are pushed
✅ Require status checks to pass before merging
  - Required checks:
    - lint-and-test (from CI Pipeline)
    - train (from Train Model) - jeśli training był triggerowany
✅ Do not allow bypassing the above settings
✅ Restrict pushes to specific people/teams (optional - może admin tylko)
```

**Czas:** 10 minut
**Priorytet:** KRYTYCZNY (blokuje bezpośrednie pushe na main)

---

### TASK 2: Data Upload Workflow (NOWY PLIK) ⭐⭐⭐⭐⭐

**Plik:** `.github/workflows/data-upload.yaml`

**Trigger:** Push do branchy `data/**`

**Kroki:**
1. Checkout code with submodules
2. Setup Python
3. Install dependencies (including DVC)
4. **DVC Pull** (pobierz istniejące dane)
5. **Data QA** - validate new images/masks
6. **DVC Add** - track new data
7. **DVC Push** - upload to S3
8. **Create/Update PR** automatycznie
   - Jeśli PASS: create PR z title "Data update: YYYY-MM-DD"
   - Jeśli FAIL: comment na branch z błędami, **NIE tworzy PR**

**Pseudo-kod:**
```yaml
name: Data Upload & Validation

on:
  push:
    branches:
      - 'data/**'
    paths:
      - 'WMS/data/training/images/**'
      - 'WMS/data/training/masks/**'

jobs:
  validate-and-prepare:
    runs-on: self-hosted
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install dvc[s3]

      - name: DVC Pull existing data
        run: |
          cd WMS/data/training
          dvc pull || echo "No existing DVC data"

      - name: Data Quality Assurance
        id: qa
        run: |
          python devops/scripts/data-qa.py WMS/data/training/ \
            --output data_qa_report.json

          # Check if passed
          if grep -q '"status": "FAIL"' data_qa_report.json; then
            echo "qa_passed=false" >> $GITHUB_OUTPUT
            echo "❌ Data QA FAILED"
            cat data_qa_report.json
            exit 0  # Don't fail job, just set output
          else
            echo "qa_passed=true" >> $GITHUB_OUTPUT
            echo "✅ Data QA PASSED"
          fi

      - name: DVC Add & Push (if QA passed)
        if: steps.qa.outputs.qa_passed == 'true'
        run: |
          cd WMS/data/training
          dvc add images masks
          git add images.dvc masks.dvc .gitignore
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git commit -m "data: update DVC tracking for new training data"
          dvc push
          git push origin ${{ github.ref_name }}

      - name: Create Pull Request (if QA passed)
        if: steps.qa.outputs.qa_passed == 'true'
        uses: actions/github-script@v7
        with:
          script: |
            const branch = context.ref.replace('refs/heads/', '');
            const date = new Date().toISOString().split('T')[0];

            // Check if PR already exists
            const { data: prs } = await github.rest.pulls.list({
              owner: context.repo.owner,
              repo: context.repo.repo,
              head: `${context.repo.owner}:${branch}`,
              state: 'open'
            });

            if (prs.length === 0) {
              // Create new PR
              await github.rest.pulls.create({
                owner: context.repo.owner,
                repo: context.repo.repo,
                title: `Data update: ${date}`,
                head: branch,
                base: 'main',
                body: `## 📊 New Training Data

                This PR adds new training data validated by Data QA.

                ### Data QA Report
                ✅ All validation checks passed

                ### Next Steps
                - Training pipeline will run automatically
                - Model will be evaluated against baseline
                - PR will be auto-approved if model improves

                ---
                🤖 Auto-generated by Data Upload Workflow`
              });
            }

      - name: Comment on Branch (if QA failed)
        if: steps.qa.outputs.qa_passed == 'false'
        run: |
          echo "⚠️ Data QA validation failed. Please fix issues before creating PR."
          echo "Report:"
          cat data_qa_report.json
          # TODO: Add GitHub comment to branch (requires PR to exist)
```

**Czas:** 2-3 godziny
**Priorytet:** KRYTYCZNY

---

### TASK 3: Training Workflow - Retry Logic ⭐⭐⭐⭐⭐

**Plik:** `.github/workflows/train.yml` (MODIFY EXISTING)

**Trigger:** Pull request from `data/**` branches

**Zmiany:**
1. Zmień trigger z `push` na `pull_request`
2. Dodaj retry logic (do 3 prób)
3. Auto-approve PR jeśli model się poprawił
4. Comment na PR z wynikami każdej próby

**Kluczowe fragmenty do dodania:**

```yaml
on:
  pull_request:
    branches:
      - main
    paths:
      - 'WMS/data/training/*.dvc'  # DVC metadata changes
      - 'WMS/data/training/images/**'
      - 'WMS/data/training/masks/**'

jobs:
  train:
    runs-on: self-hosted
    strategy:
      matrix:
        attempt: [1, 2, 3]  # 3 attempts
      max-parallel: 1  # Run sequentially
      fail-fast: false  # Don't stop on first failure

    steps:
      # ... existing steps ...

      - name: Train model
        env:
          MLFLOW_TRACKING_URI: http://localhost:5000
          ATTEMPT_NUMBER: ${{ matrix.attempt }}
        run: |
          cd WMS/src
          # Use different seed for each attempt
          SEED=$((42 + ${{ matrix.attempt }}))
          python train.py --config ../configs/train.yaml --seed $SEED

      # ... quality gate steps ...

      - name: Auto-approve PR if improved
        if: steps.results.outputs.improved == 'true'
        uses: actions/github-script@v7
        with:
          script: |
            await github.rest.pulls.createReview({
              owner: context.repo.owner,
              repo: context.repo.repo,
              pull_number: context.payload.pull_request.number,
              event: 'APPROVE',
              body: '✅ Model improved! Auto-approving PR.\n\nFeel free to merge when ready.'
            });
```

**Czas:** 2-3 godziny
**Priorytet:** KRYTYCZNY

---

### TASK 4: Release Workflow - Trigger Only on Main Merge ⭐⭐⭐⭐

**Plik:** `.github/workflows/release-deploy.yaml` (MODIFY)

**Zmiany:**
```yaml
on:
  push:
    branches: [main]
    paths:
      - 'WMS/**'  # Only when actual code/model changes
      - 'docker/**'
      - 'devops/helm/**'
      - 'infrastructure/**'
  workflow_dispatch:  # Manual trigger allowed
```

Nie triggeruje na zmiany w dokumentacji, .github, itp.

**Czas:** 15 minut
**Priorytet:** MEDIUM

---

### TASK 5: Test całego flow end-to-end ⭐⭐⭐⭐⭐

**Scenariusz testowy:**

```bash
# 1. Utwórz branch data/
git checkout -b data/20260207-test

# 2. Dodaj nowe zdjęcie (np. skopiuj jedno istniejące i zmień nazwę)
cp WMS/data/training/images/image001.jpg WMS/data/training/images/image010.jpg
cp WMS/data/training/masks/image001.png WMS/data/training/masks/image010.png

# 3. Commit i push
git add WMS/data/training/
git commit -m "test: add new training image"
git push origin data/20260207-test

# 4. Obserwuj GitHub Actions:
# - Data Upload workflow powinien się uruchomić
# - Jeśli PASS: powinien utworzyć PR
# - PR powinien triggerować Training workflow
# - Training powinien próbować do 3 razy
# - Jeśli model improved: PR auto-approved
# - Merge PR → Release workflow builds + deploys

# 5. Weryfikuj:
# - MLflow: nowy run exists
# - ECR: nowy image tag
# - k3s: nowy pod z nowym modelem
```

**Czas:** 1-2 godziny (większość to czekanie na training)
**Priorytet:** KRYTYCZNY (weryfikacja że wszystko działa)

---

## 📋 SZCZEGÓŁY TECHNICZNE

### DVC Integration w Workflows

**Problem:** Images są gitignored, więc commit nie triggeruje workflow

**Rozwiązanie:** Workflow triggeruje na zmiany w `*.dvc` files

**W każdym workflow gdzie potrzebne dane:**
```yaml
- name: DVC Pull
  run: |
    cd WMS/data/training
    dvc pull
```

**Po training:**
```yaml
- name: DVC Push (if new model is better)
  if: model_improved
  run: |
    dvc add WMS/models/best.pth
    dvc push
```

---

### Retry Logic - Szczegóły

**Approach 1: Matrix Strategy** (ZALECANE)
```yaml
strategy:
  matrix:
    attempt: [1, 2, 3]
  max-parallel: 1
  fail-fast: false
```
- Każda próba to osobny job
- Widoczne osobno w UI
- Może być redundantne jeśli pierwsza próba sukces

**Approach 2: Loop w bash**
```bash
for attempt in 1 2 3; do
  python train.py --seed $((42 + attempt))
  if check_quality_gate; then
    break
  fi
done
```
- Jeden job, wiele prób
- Mniej redundancji
- Gorsze logi

**Zalecenie:** Użyj Approach 1 - lepsze logi, bardziej "GitHubowe"

---

### Auto-approve PR - Bezpieczeństwo

**Pytanie:** Czy auto-approve jest bezpieczne?

**Odpowiedź:** TAK, jeśli:
- Model przeszedł quality gate (metrics > baseline)
- Data przeszła Data QA
- Kod nie był modyfikowany (tylko data)

**Ale:**
- Admin może zawsze ręcznie review
- Branch protection może wymagać ludzkiego review mimo auto-approve
- Best practice: Auto-approve, ale **nie auto-merge** (human must click merge)

---

## 🚦 PRIORYTETYZACJA

### MUST HAVE (dla działającego systemu):
1. ⭐⭐⭐⭐⭐ TASK 1: Branch Protection (10 min)
2. ⭐⭐⭐⭐⭐ TASK 2: Data Upload Workflow (2-3h)
3. ⭐⭐⭐⭐⭐ TASK 3: Training Retry Logic (2-3h)
4. ⭐⭐⭐⭐⭐ TASK 5: End-to-end Test (1-2h)

**Total:** ~6-9 godzin pracy

### SHOULD HAVE (optymalizacje):
5. ⭐⭐⭐⭐ TASK 4: Release Trigger Optimization (15 min)

### NICE TO HAVE (później):
- Slack/Email notifications on PR
- Automatic rollback if deployment fails
- A/B testing dla nowych modeli

---

## 📅 TIMELINE

### Sesja 1 (2-3h): Core Setup
- [ ] TASK 1: Branch Protection
- [ ] TASK 2: Data Upload Workflow (start)
- [ ] TASK 4: Release Trigger Fix

### Sesja 2 (2-3h): Training & Testing
- [ ] TASK 2: Data Upload Workflow (finish)
- [ ] TASK 3: Training Retry Logic
- [ ] TASK 5: End-to-end Test (start)

### Sesja 3 (1-2h): Verification
- [ ] TASK 5: End-to-end Test (finish)
- [ ] Bug fixes
- [ ] Documentation update

---

## ✅ DEFINITION OF DONE

System jest gotowy gdy:

1. ✅ User może stworzyć branch `data/YYYYMMDD`
2. ✅ User może dodać images + masks i pushować
3. ✅ GitHub Action automatycznie:
   - Waliduje data (Data QA)
   - Tworzy PR jeśli PASS
   - Kommentuje błąd jeśli FAIL
4. ✅ PR automatycznie triggeruje training
5. ✅ Training próbuje do 3 razy z różnymi seeds
6. ✅ Quality gate porównuje z baseline
7. ✅ PR jest auto-approved jeśli model improved
8. ✅ Merge do main triggeruje build + deploy
9. ✅ Nowy model jest deployed na k8s
10. ✅ Wszystkie kroki są widoczne w GitHub Actions UI

---

## 🤔 PYTANIA DO ROZWAŻENIA

### Q1: Czy images powinny być w git czy tylko w DVC?
**Obecnie:** Gitignored, tylko .dvc files w git
**Zaleta:** Mały repo size
**Wada:** Workflow triggers są skomplikowane

**Alternatywa:** Małe images w git dla demo, duże w DVC
**Zalecenie:** Zostaw w DVC, ale trigger workflow na .dvc changes

---

### Q2: Czy auto-merge czy tylko auto-approve?
**Auto-approve:** ✅ ZALECANE - daje control, ale oszczędza kliknięcie
**Auto-merge:** ❌ Ryzykowne - brak human oversight

---

### Q3: Co jeśli wszystkie 3 próby failują?
**Obecnie:** PR comment "failed after 3 attempts"
**Lepiej:**
- Label PR as "training-failed"
- Request changes
- Block merge
- Notify team

---

## 📚 RESOURCES

**GitHub Actions Docs:**
- Matrix strategy: https://docs.github.com/en/actions/using-jobs/using-a-matrix-for-your-jobs
- PR automation: https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#pull_request
- Branch protection: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches

**DVC Docs:**
- DVC in CI/CD: https://dvc.org/doc/user-guide/how-to/ci-cd

---

## 🎯 NASTĘPNY KROK

**Polecam zacząć od:**
1. Branch Protection (5 min) - szybki win
2. Przetestuj training ręcznie (30 min) - see if it actually works
3. Jak training działa → implement Data Upload workflow
4. End-to-end test

**Chcesz żebym zaczął implementować?** Który task najpierw? 🚀
