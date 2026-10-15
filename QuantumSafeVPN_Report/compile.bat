@echo off
echo ============================================================
echo   Compiling QuantumSafe VPN LaTeX Project Report
echo ============================================================

pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex

echo.
echo ============================================================
echo   Compilation Finished! Output: main.pdf
echo ============================================================
pause
