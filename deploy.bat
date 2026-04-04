@echo off
REM ============================================
REM GitHub Push Script - ai-pk-game
REM ============================================
REM This script will:
REM 1. Commit all local changes
REM 2. Push to GitHub
REM 3. Create gh-pages branch for GitHub Pages
REM ============================================

echo.
echo ============================================
echo   AI Battle Arena - GitHub Deployment
echo ============================================
echo.

cd /d "%~dp0"

echo [1/3] Adding all changes to git...
git add -A

echo.
echo [2/3] Committing changes...
git commit -m "feat: Add landing page, badges, GitHub Actions workflow

- Add landing page (index.html) for better presentation
- Add shields.io badges for stars, license, python
- Add GitHub Actions for auto stats update
- Update README with topics"

echo.
echo [3/3] Pushing to GitHub...
git push origin main

echo.
echo ============================================
echo   Done! 
echo ============================================
echo.
echo Next steps:
echo 1. Go to: https://github.com/lxztry/ai-pk-game/settings/pages
echo 2. Set Source: gh-pages branch
echo 3. Your landing page will be live at: https://lxztry.github.io/ai-pk-game
echo.
pause
