## Documenation notes for azcam ##

- /azcam/azcam/docs if doc root
- mkdocs is used for doc rendering
  - write html to **docs/site** root folder
  - mkdocs.yml defines mkdoc pars
  - mkdocs_deploy.bat builds and deploys to github (https://github.com/mplesser/azcam/ **gh-pages** branch) of azcam which appears at https://mplesser.github.io/azcam/ after online build

- pdoc3 is used for python code documentation as it supports attributes
 - writes html **docs/code** folder which has to be deployed to  