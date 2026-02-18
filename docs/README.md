# Documentation Index

Welcome to the Water Meters Segmentation project documentation!

## Dokumentacja główna

Zacznij tutaj żeby zrozumieć i używać systemu:

| Dokument                                         | Opis                                        | Kiedy czytać                       |
| ------------------------------------------------ | ------------------------------------------- | ---------------------------------- |
| **[WORKFLOWS.md](WORKFLOWS.md)**                 | Wszystkie pipeline wyjaśnione               | Pierwsze uruchomienie, debugowanie |
| **[USAGE.md](USAGE.md)**                         | Przewodnik krok po kroku                    | Codzienne operacje (upload danych) |
| **[ARCHITECTURE.md](ARCHITECTURE.md)**           | Projekt systemu i komponenty                | Zrozumienie architektury           |
| **[QUICKSTART.md](QUICKSTART.md)**               | Szybki start — minimalny setup              | Nowe środowisko, onboarding        |
| **[BRANCH_PROTECTION.md](BRANCH_PROTECTION.md)** | Dwie warstwy ochrony: hooki + reguły GitHub | Zrozumienie modelu bezpieczeństwa  |

## Dokumentacja techniczna

Dla programistów i zaawansowanych użytkowników:

| Dokument             | Lokalizacja                                                    | Opis                                   |
| -------------------- | -------------------------------------------------------------- | -------------------------------------- |
| **Project README**   | [../README.md](../README.md)                                   | Główny przegląd projektu i quick start |
| **Tests README**     | [../WMS/tests/README.md](../WMS/tests/README.md)               | Dokumentacja testów jednostkowych      |
| **Terraform README** | [../devops/terraform/README.md](../devops/terraform/README.md) | Infrastructure as Code                 |
| **Helm README**      | [../devops/helm/README.md](../devops/helm/README.md)           | Helm chart — serving modelu na k3s     |
| **Scripts README**   | [../devops/scripts/README.md](../devops/scripts/README.md)     | Skrypty infrastrukturalne i MLOps      |
| **KNOWN_ISSUES.md**  | [KNOWN_ISSUES.md](KNOWN_ISSUES.md)                             | Znane problemy i obejścia              |
| **MONITORING.md**    | [MONITORING.md](MONITORING.md)                                 | Prometheus + Grafana                   |
| **CREDENTIALS.md**   | [CREDENTIALS.md](CREDENTIALS.md)                               | Zarządzanie credentials AWS Academy    |

## Dla AI Assistantów

| Dokument      | Lokalizacja                  | Cel                               |
| ------------- | ---------------------------- | --------------------------------- |
| **CLAUDE.md** | [../CLAUDE.md](../CLAUDE.md) | Kontekst projektu i zasady dla AI |
| **PLAN.md**   | [../PLAN.md](../PLAN.md)     | Fazy implementacji i priorytety   |

## Przewodnik czytania

### Nowy użytkownik:

```
1. ../README.md          (przegląd projektu)
2. QUICKSTART.md         (szybki start)
3. WORKFLOWS.md          (jak działa system)
4. USAGE.md              (jak używać)
5. BRANCH_PROTECTION.md  (jednorazowy setup)
```

### Deweloper:

```
1. ARCHITECTURE.md                    (projekt systemu)
2. ../devops/scripts/README.md        (skrypty)
3. ../devops/terraform/README.md      (infrastruktura)
4. ../WMS/tests/README.md             (testy)
```

### Debugowanie:

```
1. WORKFLOWS.md          (który workflow padł?)
2. KNOWN_ISSUES.md       (znane problemy)
3. USAGE.md              (sekcja troubleshooting)
4. Logi GitHub Actions
```

## Struktura plików

```
Water-Meters-Segmentation-Automatization/
├── README.md                    # Główny przegląd projektu
│
├── docs/                        # Dokumentacja (TUTAJ JESTEŚ)
│   ├── README.md                # Ten indeks
│   ├── WORKFLOWS.md             # Wszystkie workflow wyjaśnione
│   ├── USAGE.md                 # Przewodnik użytkownika
│   ├── QUICKSTART.md            # Szybki start
│   ├── ARCHITECTURE.md          # Projekt systemu
│   ├── BRANCH_PROTECTION.md     # Setup GitHub
│   ├── KNOWN_ISSUES.md          # Znane problemy
│   ├── MONITORING.md            # Prometheus + Grafana
│   └── CREDENTIALS.md           # AWS credentials
│
├── devops/                      # Infrastruktura (submoduł)
│   ├── CLAUDE.md                # Kontekst dla AI
│   ├── PLAN.md                  # Plan implementacji
│   ├── scripts/README.md        # Skrypty infrastrukturalne
│   ├── helm/README.md           # Helm chart
│   └── terraform/README.md      # Terraform docs
│
└── WMS/
    ├── README.md                # Kod ML — model, trening, serving
    └── tests/README.md          # Testy jednostkowe
```

## Szybkie linki

- **GitHub Repository:** https://github.com/Rafallost/Water-Meters-Segmentation-Automatization
- **GitHub Actions:** https://github.com/Rafallost/Water-Meters-Segmentation-Automatization/actions
- **Pull Requests:** https://github.com/Rafallost/Water-Meters-Segmentation-Automatization/pulls

**Last updated:** 2026-02-15
