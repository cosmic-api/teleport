module.exports =
  title: "Teleport"
  sectionOrder: ["home", "python", "spec"]
  sections:
    home:
      title: "About"
      star: true
      repoLink: true
      subMenuShow: false
    python:
      title: "Python"
      star: true
      repoLink: true
      subMenuShow: true
      subMenu: [
        { version: 'latest' }
        { divider: true }
        { version: '0.2' }
        { version: '0.1' }
      ]
    spec:
      title: "Specification"
      star: true
      repoLink: true
      subMenuShow: true
      subMenu: [
        { version: 'latest' }
        { divider: true }
        { version: '1.0' }
      ]
