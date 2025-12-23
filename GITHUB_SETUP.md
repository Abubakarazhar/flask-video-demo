# GitHub Repository Setup Guide

## Quick Setup (5 minutes)

### Step 1: Initialize Git Repository

```bash
cd /Users/abubakarsmacbook/Downloads/factory_safety_monitoring
git init
git add .
git commit -m "Initial commit: Factory Safety Monitoring System"
```

### Step 2: Create GitHub Repository

1. **Go to GitHub**: https://github.com/new
2. **Repository name**: `factory-safety-monitoring` (or your preferred name)
3. **Description**: "AI-powered real-time factory safety monitoring system using vision-language models"
4. **Visibility**: Choose Public or Private
5. **DO NOT** initialize with README, .gitignore, or license (we already have these)
6. Click **"Create repository"**

### Step 3: Connect and Push

After creating the repo, GitHub will show you commands. Use these:

```bash
# Add remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/factory-safety-monitoring.git

# Rename branch to main (if needed)
git branch -M main

# Push to GitHub
git push -u origin main
```

---

## Detailed Instructions

### Option A: Using GitHub Website (Easiest)

1. **Create Repository on GitHub**
   - Visit: https://github.com/new
   - Repository name: `factory-safety-monitoring`
   - Description: "AI-powered real-time factory safety monitoring system"
   - Choose Public or Private
   - **Don't** check any boxes (README, .gitignore, license)
   - Click "Create repository"

2. **Push Your Code**
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/factory-safety-monitoring.git
   git branch -M main
   git push -u origin main
   ```

### Option B: Using GitHub CLI (If Installed)

```bash
# Install GitHub CLI (if not installed)
# macOS: brew install gh

# Login to GitHub
gh auth login

# Create repo and push
gh repo create factory-safety-monitoring --public --source=. --remote=origin --push
```

---

## What Gets Uploaded?

✅ **Included:**
- All Python source code
- Configuration files
- Documentation (README, guides)
- Requirements.txt
- Deployment configs
- PRODUCT_BRIEF.md and PRODUCT_BRIEF.pdf

❌ **Excluded (via .gitignore):**
- Uploaded videos (*.mp4, *.avi, etc.)
- Environment variables (.env)
- Python cache (__pycache__)
- Log files
- Temporary files

---

## Important: Before Pushing

### 1. Check for Sensitive Information

Make sure you don't have:
- API keys in code
- Passwords
- Personal information

If you have a `.env` file, it's already in `.gitignore` and won't be uploaded.

### 2. Create .env.example (Optional but Recommended)

If you want to show what environment variables are needed:

```bash
cp .env .env.example
# Then edit .env.example to remove actual values
```

---

## After Pushing

### Add Repository Badges (Optional)

Add to your README.md:

```markdown
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
```

### Add Topics/Tags on GitHub

After pushing, go to your repo settings and add topics:
- `ai`
- `computer-vision`
- `safety-monitoring`
- `openai`
- `flask`
- `factory-safety`

---

## Troubleshooting

### "Repository not found"
- Check your GitHub username is correct
- Make sure the repository exists on GitHub
- Verify you have access (if private repo)

### "Permission denied"
- You may need to authenticate
- Use GitHub Personal Access Token instead of password
- Or use SSH: `git remote set-url origin git@github.com:USERNAME/REPO.git`

### "Large file" error
- GitHub has a 100MB file limit
- If you have large files, use Git LFS or remove them

---

## Next Steps

1. ✅ Push code to GitHub
2. 📝 Update README with screenshots/demo
3. 🏷️ Add topics/tags
4. 📄 Add LICENSE file (MIT, Apache, etc.)
5. 🚀 Set up GitHub Actions (CI/CD) - optional
6. 📊 Add GitHub Pages for documentation - optional

---

## Quick Commands Reference

```bash
# Check status
git status

# Add all changes
git add .

# Commit
git commit -m "Your commit message"

# Push
git push

# View remote
git remote -v

# Update remote URL
git remote set-url origin NEW_URL
```

---

## Need Help?

- GitHub Docs: https://docs.github.com
- Git Tutorial: https://git-scm.com/docs/gittutorial
- GitHub CLI: https://cli.github.com
