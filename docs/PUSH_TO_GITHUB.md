# Push To GitHub

If automatic push is not completed, run:

```powershell
cd "C:\Users\24186\Documents\动态模型"
git branch -M main
gh repo create high-wind-cascading-pscad --private --source . --remote origin --push
```

If `origin` already exists:

```powershell
git remote set-url origin https://github.com/wangziwei1111/high-wind-cascading-pscad.git
git push -u origin main
```

