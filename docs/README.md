# Documentation Index

Welcome to the Water Meters Segmentation project documentation!

---

## 📚 Main Documentation

Start here for understanding and using the system:

| Document | Description | When to Read |
|----------|-------------|--------------|
| **[WORKFLOWS.md](WORKFLOWS.md)** | ⭐ **Start here!** All pipelines explained | First time setup, debugging workflows |
| **[USAGE.md](USAGE.md)** | Step-by-step usage guide | Daily operations (uploading data) |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | System design and components | Understanding system design |
| **[BRANCH_PROTECTION.md](BRANCH_PROTECTION.md)** | Two-layer protection: hooks + GitHub rules | Understanding security model |

---

## 🔧 Technical Documentation

For developers and advanced users:

| Document | Location | Description |
|----------|----------|-------------|
| **Project README** | [../README.md](../README.md) | Main project overview and quick start |
| **Tests README** | [../WMS/tests/README.md](../WMS/tests/README.md) | Unit tests documentation |
| **Terraform README** | [../devops/terraform/README.md](../devops/terraform/README.md) | Infrastructure as Code docs |

---

## 🤖 For AI Assistants

If you're an AI assistant working on this project:

| Document | Location | Purpose |
|----------|----------|---------|
| **CLAUDE.md** | [../devops/CLAUDE.md](../devops/CLAUDE.md) | Project context and rules for AI assistants |
| **PLAN.md** | [../devops/PLAN.md](../devops/PLAN.md) | Implementation phases and priorities |

---

## 📖 Reading Guide

### For New Users:
```
1. Read ../README.md (project overview)
2. Read WORKFLOWS.md (understand the system)
3. Read USAGE.md (learn how to use)
4. Setup BRANCH_PROTECTION.md (one time)
```

### For Developers:
```
1. Read ARCHITECTURE.md (system design)
2. Read ../devops/PLAN.md (implementation phases)
3. Read ../devops/terraform/README.md (infrastructure)
4. Read ../WMS/tests/README.md (testing)
```

### For Debugging:
```
1. Check WORKFLOWS.md (which workflow failed?)
2. Check USAGE.md troubleshooting section
3. Check GitHub Actions logs
4. Check ../devops/CLAUDE.md (known issues)
```

---

## 🗂️ Documentation Structure

```
Water-Meters-Segmentation-Autimatization/
├── README.md                    # Main project overview
│
├── docs/                        # 📚 Main documentation (YOU ARE HERE)
│   ├── README.md                # This index
│   ├── WORKFLOWS.md             # All workflows explained
│   ├── USAGE.md                 # How-to guide
│   ├── ARCHITECTURE.md          # System design
│   └── BRANCH_PROTECTION.md     # GitHub setup
│
├── devops/                      # 🔧 Infrastructure (submodule)
│   ├── CLAUDE.md                # AI assistant context
│   ├── PLAN.md                  # Implementation plan
│   ├── README.md                # Devops overview
│   └── terraform/
│       └── README.md            # Terraform docs
│
└── WMS/tests/
    └── README.md                # Unit tests docs
```

---

## 🔗 Quick Links

- **GitHub Repository:** https://github.com/Rafallost/Water-Meters-Segmentation-Autimatization
- **GitHub Actions:** https://github.com/Rafallost/Water-Meters-Segmentation-Autimatization/actions
- **Pull Requests:** https://github.com/Rafallost/Water-Meters-Segmentation-Autimatization/pulls
- **Issues:** https://github.com/Rafallost/Water-Meters-Segmentation-Autimatization/issues

---

## 💡 Tips

- **Confused?** Start with [WORKFLOWS.md](WORKFLOWS.md) - it explains everything
- **Want to upload data?** See [USAGE.md](USAGE.md)
- **Setting up?** See [BRANCH_PROTECTION.md](BRANCH_PROTECTION.md)
- **Curious about design?** See [ARCHITECTURE.md](ARCHITECTURE.md)

---

**Last updated:** 2026-02-08
