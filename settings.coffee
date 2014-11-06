module.exports =
  title: "Teleport"
  sectionOrder: ["python", "spec"]
  sections:
    home:
      title: "About"
      subMenuShow: false
    python:
      title: "Python"
      github: "teleport.py"
      star: true
      repoLink: true
      checkouts: [
        { version: '0.2', branch: '0.2-maintenance' }
        { version: '0.1', branch: '0.1-maintenance' }
      ]
      subMenuShow: true
      subMenu: [
        { version: 'master' }
        { divider: true }
        { version: '0.2' }
        { version: '0.1' }
      ]
    spec:
      title: "Specification"
      github: "teleport"
      star: false
      repoLink: true
      checkouts: []
      subMenuShow: true
      subMenu: [
        { version: 'latest' }
        { version: '1.0' }
      ]
