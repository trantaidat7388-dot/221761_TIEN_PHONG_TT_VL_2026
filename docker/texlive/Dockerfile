FROM texlive/texlive:latest

# Useful tools for debugging and automation inside CI/CD pipelines.
RUN tlmgr update --self --all || true

WORKDIR /workspace

CMD ["xelatex", "--version"]
